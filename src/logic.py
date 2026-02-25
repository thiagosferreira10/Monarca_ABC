from .custom_query import QUERY_ABC_BY_LEVEL, QUERY_ABC_BY_LEVEL_ORDER
from .abc_analysis import process_abc_curve
import pandas as pd
from datetime import datetime, timedelta

def execute_abc_update(conn, level_id, metric_type='VALOR_TOTAL'):
    """
    Executes the full ABC process for a specific level:
    ...
    metric_type: 'VALOR_TOTAL' (Value) or 'QUANTIDADE_TOTAL' (Quantity)
    """
    cursor = conn.cursor()
    
    # Check Processing Type and Months (MESES) for this Level
    cursor.execute("SELECT TIPO_PROCESSAMENTO, MESES FROM PRODUTOS_NIVEL1 WHERE CODIGO = ?", (level_id,))
    row = cursor.fetchone()
    tipo_proc = row[0] if row and row[0] else 'V' # Default to Venda
    meses_config = row[1] if row and row[1] else 24
    
    selected_query = QUERY_ABC_BY_LEVEL
    if tipo_proc == 'P':
        selected_query = QUERY_ABC_BY_LEVEL_ORDER
        # print(f"Executing Order-Based ABC for Level {level_id}")
    
    # Calculate Dates
    end_date_obj = datetime.now()
    # Approx months to days: 30.44 days/month or simpler approach
    # logic: subtract months from current date
    # We can use relativedelta if available, otherwise manual calc
    # Using timedelta(days=30 * months) is rough but usually acceptable for this scope
    # Better: Use simple month subtraction logic
    
    # For day precision is less critical for "last X months", usually
    start_date_obj = end_date_obj - timedelta(days=int(meses_config * 30.4167))
    
    start_date = start_date_obj.strftime('%Y-%m-%d')
    end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # ... (params preparation same as before) ...
    params = (
        start_date, end_date, # Vendas/Pedidos
        start_date, end_date, # Assistencia
        level_id
    )
    
    cursor.execute(selected_query, params)
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
    
    # Ensure numeric columns are clean
    cols_to_clean = ['QUANTIDADE_TOTAL', 'VALOR_TOTAL']
    for c in cols_to_clean:
        if c in df.columns:
             df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

    # 2. Calculate ABC
    df_abc = process_abc_curve(df, metric_column=metric_type)
    
    # Use Fixed Months for Calculation
    months_diff = max(1, meses_config)
    
    # 3. Update Database
    # 3.1 Calculate MEDIA (Sales / months_diff)
    # Ensure QUANTIDADE_TOTAL is numeric
    df_abc['QUANTIDADE_TOTAL'] = pd.to_numeric(df_abc['QUANTIDADE_TOTAL'], errors='coerce').fillna(0)
    
    # Round to 1 decimal place
    df_abc['MEDIA'] = df_abc['QUANTIDADE_TOTAL'].apply(lambda x: round(x/float(months_diff), 1) if months_diff > 0 else 0.0)

    # Map 'A'->1, 'B'->2, 'C'->3
    class_map = {'A': 1, 'B': 2, 'C': 3}
    
    # Prepare batch update
    update_sql = "UPDATE PRODUTOS SET ABC = ?, MEDIA = ?, PERCENTUAL = ? WHERE CODIGO = ?"
    
    # We can iterate and update. For performance, executemany is better but requires list of tuples.
    update_data = []
    for index, row in df_abc.iterrows():
        abc_code = class_map.get(row['CLASSE'])
        prod_id = row['CODIGO']
        media_val = row['MEDIA']
        percentual = row['PERCENTUAL']
        
        if abc_code and prod_id:
            update_data.append((abc_code, media_val, percentual, prod_id))
            
    if update_data:
        cursor.executemany(update_sql, update_data)
        
        # Update Last Processing Time for this Level 1
        cursor.execute("UPDATE PRODUTOS_NIVEL1 SET DATA_PROCESSAMENTO = CURRENT_TIMESTAMP WHERE CODIGO = ?", (level_id,))
        
        conn.commit()
        
    return df_abc
