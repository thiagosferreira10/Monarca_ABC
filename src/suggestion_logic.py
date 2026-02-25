import pandas as pd
from datetime import datetime, date

IN_CLAUSE_BATCH_SIZE = 500

def execute_chunked_in_query(cursor, query_template, ids, extra_params=None):
    """
    Executes a query with an IN clause, splitting into batches to avoid
    Firebird's 1500 parameter limit.
    query_template: SQL string with a single {} placeholder for the IN list.
    ids: list of values to go into the IN clause.
    extra_params: additional params to append AFTER the IN params in each batch.
    Returns: combined list of all fetched rows.
    """
    if not ids:
        return []
    
    if extra_params is None:
        extra_params = []
    
    all_rows = []
    for i in range(0, len(ids), IN_CLAUSE_BATCH_SIZE):
        chunk = ids[i:i + IN_CLAUSE_BATCH_SIZE]
        placeholders = ','.join(['?'] * len(chunk))
        query = query_template.format(placeholders)
        params = list(chunk) + list(extra_params)
        cursor.execute(query, params)
        all_rows.extend(cursor.fetchall())
    
    return all_rows

def get_last_4_quarters(reference_date=None):
    """
    Returns labels and date ranges for the last 4 closed quarters.
    Example: If reference_date is Feb 2026, returns Q1-Q4 of 2025.
    """
    if reference_date is None:
        reference_date = date.today()
    
    # Determine current quarter
    current_month = reference_date.month
    current_year = reference_date.year
    current_quarter = (current_month - 1) // 3 + 1
    
    quarters = []
    # Start from the quarter before current
    q = current_quarter - 1
    y = current_year
    
    if q <= 0:
        q = 4
        y -= 1
    
    # Collect 4 quarters going backwards
    for _ in range(4):
        label = f"{y}-{q}"
        # Month ranges: Q1=1-3, Q2=4-6, Q3=7-9, Q4=10-12
        start_month = (q - 1) * 3 + 1
        end_month = q * 3
        start_date = date(y, start_month, 1)
        # End date is last day of end_month
        if end_month == 12:
            end_date = date(y, 12, 31)
        else:
            end_date = date(y, end_month + 1, 1).replace(day=1)
            end_date = end_date.replace(day=1) - pd.Timedelta(days=1)
            end_date = end_date.date() if hasattr(end_date, 'date') else end_date
        
        quarters.append((label, start_date, date(y, end_month, 28)))  # Simplified end
        
        q -= 1
        if q <= 0:
            q = 4
            y -= 1
    
    # Reverse to chronological order
    quarters.reverse()
    return quarters

def get_quarterly_data(cursor, product_ids, n1_id):
    """
    Fetches quarterly averages for a list of products.
    Returns dict: {product_id: {quarter_label: avg_qty}}
    """
    from src.database import get_connection
    
    if not product_ids:
        return {}
    
    # Determine schema type for this N1
    cursor.execute("SELECT TIPO_PROCESSAMENTO FROM PRODUTOS_NIVEL1 WHERE CODIGO = ?", (n1_id,))
    row = cursor.fetchone()
    schema_type = row[0] if row and row[0] else 'V'
    
    quarters = get_last_4_quarters()
    result = {pid: {} for pid in product_ids}
    
    for label, start_date, end_date in quarters:
        # Adjust end_date to be inclusive of the full month
        q_num = int(label.split('-')[1])
        q_year = int(label.split('-')[0])
        end_month = q_num * 3
        
        # Get last day of end_month
        import calendar
        last_day = calendar.monthrange(q_year, end_month)[1]
        end_date_str = f"{q_year}-{end_month:02d}-{last_day:02d}"
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # Query based on schema type
        if schema_type == 'P':
            query_template = """
                SELECT pi.PRODUTO, SUM(pi.QUANTIDADE)
                FROM PEDIDO_ITEM pi
                JOIN PEDIDO p ON p.CODIGO = pi.PEDIDO
                WHERE pi.PRODUTO IN ({}) 
                  AND p.DATA >= ? AND p.DATA <= ?
                  AND p.SITUACAO NOT IN (3)
                  AND pi.SITUACAO NOT IN (3)
                GROUP BY pi.PRODUTO
            """
        else:
            query_template = """
                SELECT vi.PRODUTO, SUM(vi.QUANTIDADE)
                FROM VENDA_ITEM vi
                JOIN VENDA v ON v.CODIGO = vi.VENDA
                WHERE vi.PRODUTO IN ({})
                  AND v.DATA >= ? AND v.DATA <= ?
                GROUP BY vi.PRODUTO
            """
        
        rows = execute_chunked_in_query(
            cursor, query_template, product_ids,
            extra_params=[start_date_str, end_date_str]
        )
        
        for prod_id, total_qty in rows:
            avg = round(float(total_qty) / 3, 1) if total_qty else 0
            result[prod_id][label] = avg
        
        # Fill zeros for products not in result
        for pid in product_ids:
            if label not in result[pid]:
                result[pid][label] = 0
    
    return result, [q[0] for q in quarters]


def save_suggestion(conn, n1, n2, n3, n4, abc_id, min_months, max_months, rule_id=None):
    """
    Saves or updates a stock suggestion rule.
    If rule_id is provided, performs UPDATE (with validation).
    If rule_id is None, performs INSERT.
    """
    cursor = conn.cursor()
    
    # 1. Validation: Check for duplicates
    # Construct WHERE clause for duplicate check
    dup_query = """
        SELECT CODIGO FROM SUGESTAO_NIVEL 
        WHERE NIVEL1 = ? AND 
              (NIVEL2 = ? OR (? IS NULL AND NIVEL2 IS NULL)) AND
              (NIVEL3 = ? OR (? IS NULL AND NIVEL3 IS NULL)) AND
              (NIVEL4 = ? OR (? IS NULL AND NIVEL4 IS NULL)) AND
              ABC = ?
    """
    params_chk = (n1, n2, n2, n3, n3, n4, n4, abc_id)
    
    # If Update, exclude self from check
    if rule_id:
        dup_query += " AND CODIGO <> ?"
        params_chk += (rule_id,)
        
    cursor.execute(dup_query, params_chk)
    row = cursor.fetchone()
    
    if row:
        return False, "Já existe uma regra cadastrada para esta combinação de Níveis e Classe ABC."
        
    if rule_id:
        # Update
        update_query = """
            UPDATE SUGESTAO_NIVEL 
            SET NIVEL1=?, NIVEL2=?, NIVEL3=?, NIVEL4=?, ABC=?, MINIMO=?, MAXIMO=?
            WHERE CODIGO = ?
        """
        cursor.execute(update_query, (n1, n2, n3, n4, abc_id, min_months, max_months, rule_id))
        msg = "Regra Atualizada com Sucesso!"
    else:
        # Insert
        cursor.execute("SELECT MAX(CODIGO) FROM SUGESTAO_NIVEL")
        max_id = cursor.fetchone()[0]
        new_id = (max_id if max_id is not None else 0) + 1
        
        insert_query = """
            INSERT INTO SUGESTAO_NIVEL (CODIGO, NIVEL1, NIVEL2, NIVEL3, NIVEL4, ABC, MINIMO, MAXIMO)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (new_id, n1, n2, n3, n4, abc_id, min_months, max_months))
        msg = "Regra Cadastrada com Sucesso!"
        
    conn.commit()
    return True, msg

def get_suggestions(conn):
    """
    Fetches all suggestion rules for display.
    Joins with level tables for descriptions.
    """
    query = """
    SELECT 
        S.CODIGO,
        S.NIVEL1,
        S.NIVEL2,
        S.NIVEL3,
        S.NIVEL4,
        S.ABC,
        N1.DESCRICAO as N1_DESC,
        N2.DESCRICAO as N2_DESC,
        N3.DESCRICAO as N3_DESC,
        N4.DESCRICAO as N4_DESC,
        A.DESCRICAO as CLASS_ABC,
        S.MINIMO,
        S.MAXIMO
    FROM 
        SUGESTAO_NIVEL S
    LEFT JOIN PRODUTOS_NIVEL1 N1 ON N1.CODIGO = S.NIVEL1
    LEFT JOIN PRODUTOS_NIVEL2 N2 ON N2.CODIGO = S.NIVEL2
    LEFT JOIN PRODUTOS_NIVEL3 N3 ON N3.CODIGO = S.NIVEL3
    LEFT JOIN PRODUTOS_NIVEL4 N4 ON N4.CODIGO = S.NIVEL4
    LEFT JOIN ABC A ON A.CODIGO = S.ABC
    ORDER BY N1.DESCRICAO, N2.DESCRICAO, N3.DESCRICAO, A.DESCRICAO
    """
    
    return pd.read_sql(query, conn)

def delete_suggestion(conn, suggestion_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM SUGESTAO_NIVEL WHERE CODIGO = ?", (suggestion_id,))
    conn.commit()

def update_suggestion_fields(conn, suggestion_id, changes):
    """
    Updates specific fields for a rule by ID.
    changes: dict of {field_name: new_value}
    """
    if not changes: return
    
    cursor = conn.cursor()
    
    # Allowed fields to prevent injection (though args are safe)
    valid_fields = {'MINIMO', 'MAXIMO', 'ABC'}
    
    set_clauses = []
    params = []
    
    for field, value in changes.items():
        if field in valid_fields:
            set_clauses.append(f"{field} = ?")
            params.append(value)
            
    if not set_clauses: return
    
    sql = f"UPDATE SUGESTAO_NIVEL SET {', '.join(set_clauses)} WHERE CODIGO = ?"
    params.append(suggestion_id)
    
    cursor.execute(sql, tuple(params))
    conn.commit()
