import pandas as pd

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
