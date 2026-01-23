from firebird.driver import connect, driver_config
from .config import Config

def get_connection():
    """Establishes connection to the Firebird database."""
    try:
        # Using DSN as required by firebird-driver
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
    WHERE 
        V.DATA >= ? AND V.DATA <= ?
        AND V.TOTAL_VENDA > 0
        AND N1.ABC = 'S' -- Filter only allowed Levels
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

def get_levels(cursor, table_name, parent_id=None):
    """
    Fetches levels from a specified table. 
    If parent_id is provided, filters by PAI column.
    """
    query = f"SELECT CODIGO, DESCRICAO FROM {table_name}"
    params = []
    
    # N1 doesn't have PAI. N2..N4 have.
    # If parent_id is passed, we check if table has PAI column usually.
    # But strictly for N2, N3, N4 we know it is 'PAI'.
    if parent_id is not None:
        query += " WHERE PAI = ?"
        params.append(parent_id)
        
    query += " ORDER BY DESCRICAO"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def get_last_processed(cursor, n1_id):
    """Fetches the DATA_PROCESSAMENTO for a given N1 Level."""
    query = "SELECT DATA_PROCESSAMENTO FROM PRODUTOS_NIVEL1 WHERE CODIGO = ?"
    cursor.execute(query, (n1_id,))
    row = cursor.fetchone()
    return row[0] if row else None
