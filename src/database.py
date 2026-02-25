from firebird.driver import connect, driver_config
from .config import Config

def get_connection():
    """Establishes connection to the Firebird database."""
    try:
        # Using DSN as required by firebird-driver
        # Debug Args
        print(f"DEBUG CONNECT: DSN={repr(Config().dsn)}")
        conn = connect(
            database=Config().dsn,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='WIN1252'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def fetch_sales_data(cursor, start_date, end_date):
    """
    Fetches sales data grouped by product for ABC analysis.
    Exclude cancelled sales (VENDA.FISCAL = 'N' logic might differ, assuming typical cancelled flag or just all valid sales).
    Looking at Schema:
    VENDA: DATA, TOTAL_PRODUTOS, TOTAL_VENDA
    VENDA_ITEM: VENDA, PRODUTO, QUANTIDADE, VALOR_UNITARIO, TOTAL (calc)
    PRODUTOS: CODIGO, DESCRICAO
    """
    
    query = """
    SELECT 
        P.CODIGO,
        P.REFERENCIA,
        P.DESCRICAO,
        SUM(VI.QUANTIDADE) as QUANTIDADE_TOTAL,
        SUM(VI.QUANTIDADE * VI.VALOR_UNITARIO) as VALOR_TOTAL
    FROM 
        VENDA V
    JOIN 
        VENDA_ITEM VI ON VI.VENDA = V.CODIGO
    JOIN 
        PRODUTOS P ON P.CODIGO = VI.PRODUTO
    JOIN
        PRODUTOS_NIVEL1 N1 ON N1.CODIGO = P.CLASSIFICACAO_N1
    LEFT JOIN
        PRODUTOS_NIVEL2 N2 ON N2.CODIGO = P.CLASSIFICACAO_N2
    WHERE 
        V.DATA >= ? AND V.DATA <= ?
        AND V.TOTAL_VENDA > 0
        AND N1.ABC = 'S' -- Filter only allowed N1 Levels
        AND (N2.ABC = 'S' OR N2.CODIGO IS NULL) -- Filter allowed N2 Levels (NULL = no N2)
    GROUP BY 
        P.CODIGO, P.REFERENCIA, P.DESCRICAO
    """
    
    # Firebird driver executes parameter substitution
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchall()

def get_n1_levels(cursor):
    """Fetches Level 1 categories enabled for ABC analysis (ABC='S')."""
    query = "SELECT CODIGO, DESCRICAO FROM PRODUTOS_NIVEL1 WHERE ABC = 'S' ORDER BY DESCRICAO"
    cursor.execute(query)
    return cursor.fetchall()

def get_levels(cursor, table_name, parent_id=None, abc_only=False):
    """
    Fetches levels from a specified table. 
    If parent_id is provided, filters by PAI column.
    If abc_only is True, filters where ABC = 'S'.
    """
    query = f"SELECT CODIGO, DESCRICAO FROM {table_name}"
    params = []
    conditions = []
    
    # N1 doesn't have PAI. N2..N4 have.
    if parent_id is not None:
        conditions.append("PAI = ?")
        params.append(parent_id)
        
    if abc_only:
        conditions.append("ABC = 'S'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY DESCRICAO"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def get_n1_configs(cursor):
    """
    Fetches configuration for all Level 1 items.
    Returns list of dicts: {ID, DESCRICAO, TIPO_PROCESSAMENTO, MESES}
    """
    query = "SELECT CODIGO, DESCRICAO, TIPO_PROCESSAMENTO, MESES FROM PRODUTOS_NIVEL1 WHERE ABC = 'S' ORDER BY DESCRICAO"
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for r in rows:
        result.append({
            'CODIGO': r[0],
            'DESCRICAO': r[1],
            'TIPO_PROCESSAMENTO': r[2] if r[2] else 'V',
            'MESES': r[3] if r[3] else 24
        })
    return result

def update_n1_config(cursor, n1_id, tipo_proc, meses):
    """
    Updates configuration for a specific Level 1.
    """
    query = "UPDATE PRODUTOS_NIVEL1 SET TIPO_PROCESSAMENTO = ?, MESES = ? WHERE CODIGO = ?"
    cursor.execute(query, (tipo_proc, meses, n1_id))

def get_last_processed(cursor, n1_id):
    """Fetches the DATA_PROCESSAMENTO for a given N1 Level."""
    query = "SELECT DATA_PROCESSAMENTO FROM PRODUTOS_NIVEL1 WHERE CODIGO = ?"
    cursor.execute(query, (n1_id,))
    row = cursor.fetchone()
    return row[0] if row else None

# --- SUGESTAO_FORNECEDOR CRUD ---

def get_fornecedores_ativos(cursor):
    """Fetches active suppliers from CLIENTES (FORNECEDOR='S' and ATIVO='S')."""
    query = "SELECT CODIGO, NOME FROM CLIENTES WHERE FORNECEDOR = 'S' AND ATIVO = 'S' ORDER BY NOME"
    cursor.execute(query)
    return cursor.fetchall()

def get_sugestao_fornecedores(cursor):
    """Lists all SUGESTAO_FORNECEDOR records with supplier and type names."""
    query = """
        SELECT sf.CODIGO, sf.FORNECEDOR, c.NOME AS FORNECEDOR_NOME,
               sf.TIPO, n1.DESCRICAO AS TIPO_NOME, sf.PRAZO
        FROM SUGESTAO_FORNECEDOR sf
        LEFT JOIN CLIENTES c ON c.CODIGO = sf.FORNECEDOR
        LEFT JOIN PRODUTOS_NIVEL1 n1 ON n1.CODIGO = sf.TIPO
        ORDER BY c.NOME, n1.DESCRICAO
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for r in rows:
        result.append({
            'CODIGO': r[0],
            'FORNECEDOR_ID': r[1],
            'FORNECEDOR': r[2] or '',
            'TIPO_ID': r[3],
            'TIPO': r[4] or '',
            'PRAZO': float(r[5]) if r[5] else 0.0
        })
    return result

def save_sugestao_fornecedor(cursor, fornecedor, tipo, prazo):
    """Inserts a new SUGESTAO_FORNECEDOR record with auto-generated PK."""
    cursor.execute("SELECT COALESCE(MAX(CODIGO), 0) + 1 FROM SUGESTAO_FORNECEDOR")
    new_id = cursor.fetchone()[0]
    query = "INSERT INTO SUGESTAO_FORNECEDOR (CODIGO, FORNECEDOR, TIPO, PRAZO) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (new_id, fornecedor, tipo, prazo))
    return new_id

def delete_sugestao_fornecedor(cursor, codigo):
    """Deletes a SUGESTAO_FORNECEDOR record by CODIGO."""
    cursor.execute("DELETE FROM SUGESTAO_FORNECEDOR WHERE CODIGO = ?", (codigo,))

# --- SUGESTAO_DOLAR CRUD ---

def get_produtos_ativos(cursor):
    """Fetches active products (ATIVO='S'), returns (CODIGO, DESCRICAO)."""
    query = "SELECT CODIGO, DESCRICAO FROM PRODUTOS WHERE ATIVO = 'S' ORDER BY DESCRICAO"
    cursor.execute(query)
    return cursor.fetchall()

def get_sugestao_dolar(cursor):
    """Lists all SUGESTAO_DOLAR records with product names."""
    query = """
        SELECT sd.CODIGO, sd.PRODUTO, p.DESCRICAO AS PRODUTO_NOME, sd.DOLAR
        FROM SUGESTAO_DOLAR sd
        LEFT JOIN PRODUTOS p ON p.CODIGO = sd.PRODUTO
        ORDER BY p.DESCRICAO
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for r in rows:
        result.append({
            'CODIGO': r[0],
            'PRODUTO_ID': r[1],
            'PRODUTO': r[2] or '',
            'DOLAR': float(r[3]) if r[3] else 0.0
        })
    return result

def save_sugestao_dolar(cursor, produto, dolar):
    """Inserts a new SUGESTAO_DOLAR record with auto-generated PK."""
    cursor.execute("SELECT COALESCE(MAX(CODIGO), 0) + 1 FROM SUGESTAO_DOLAR")
    new_id = cursor.fetchone()[0]
    query = "INSERT INTO SUGESTAO_DOLAR (CODIGO, PRODUTO, DOLAR) VALUES (?, ?, ?)"
    cursor.execute(query, (new_id, produto, dolar))
    return new_id

def delete_sugestao_dolar(cursor, codigo):
    """Deletes a SUGESTAO_DOLAR record by CODIGO."""
    cursor.execute("DELETE FROM SUGESTAO_DOLAR WHERE CODIGO = ?", (codigo,))
