from .custom_query import QUERY_ABC_BY_LEVEL
from .abc_analysis import process_abc_curve
import pandas as pd
from datetime import datetime

def execute_abc_update(conn, level_id, start_date, end_date, metric_type='VALOR_TOTAL'):
    """
    Executes the full ABC process for a specific level:
    ...
    metric_type: 'VALOR_TOTAL' (Value) or 'QUANTIDADE_TOTAL' (Quantity)
    """
    cursor = conn.cursor()
    
    # ... (params preparation same as before) ...
    params = (
        start_date, end_date,
        start_date, end_date,
        start_date, end_date,
        start_date, end_date,
        level_id
    )
    
    cursor.execute(QUERY_ABC_BY_LEVEL, params)
    rows = cursor.fetchall()
    
    if not rows:
        return pd.DataFrame()
        
    # Manual Mapping based on SQL: descricao, codigo, venda, valor
    # Indices: 0=Desc, 1=Cod, 2=Venda(Qtd), 3=Valor
    data = []
    for r in rows:
        data.append({
            'DESCRICAO': r[0],
            'CODIGO': r[1],
            'QUANTIDADE_TOTAL': r[2],
            'VALOR_TOTAL': r[3]
        })
        
    df = pd.DataFrame(data)
    
    # 2. Calculate ABC
    df_abc = process_abc_curve(df, metric_column=metric_type)
    
    # Parse dates to calculate months duration
    d1 = datetime.strptime(start_date, '%Y-%m-%d')
    d2 = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate months roughly (inclusive of start/end months)
    months_diff = (d2.year - d1.year) * 12 + (d2.month - d1.month) + 1
    months_diff = max(1, months_diff) # avoid zero division
    
    # 3. Update Database
    # 3.1 Calculate MEDIA (Sales / months_diff)
    # Ensure QUANTIDADE_TOTAL is numeric
    # Round to 1 decimal place
    df_abc['MEDIA'] = df_abc['QUANTIDADE_TOTAL'].apply(lambda x: round(float(x)/float(months_diff), 1) if x else 0.0)

    # Map 'A'->1, 'B'->2, 'C'->3
    class_map = {'A': 1, 'B': 2, 'C': 3}
    
    # Prepare batch update
    update_sql = "UPDATE PRODUTOS SET ABC = ?, MEDIA = ? WHERE CODIGO = ?"
    
    # We can iterate and update. For performance, executemany is better but requires list of tuples.
    update_data = []
    for index, row in df_abc.iterrows():
        abc_code = class_map.get(row['CLASSE'])
        prod_id = row['CODIGO']
        media_val = row['MEDIA']
        
        if abc_code and prod_id:
            update_data.append((abc_code, media_val, prod_id))
            
    if update_data:
        cursor.executemany(update_sql, update_data)
        
        # Update Last Processing Time for this Level 1
        cursor.execute("UPDATE PRODUTOS_NIVEL1 SET DATA_PROCESSAMENTO = CURRENT_TIMESTAMP WHERE CODIGO = ?", (level_id,))
        
        conn.commit()
        
    return df_abc
