from firebird.driver import connect, driver_config
import os
from dotenv import load_dotenv
from src.config import Config
from src.custom_query import QUERY_ABC_BY_LEVEL

# Load env variables
load_dotenv(r'D:\Estudos\Python\curva_abc\.env')

# Configure Firebird Driver
driver_config.server_defaults.host.value = 'localhost'
# Hardcoded path since it was not exported
fb_lib_path = r"C:\Program Files\Firebird\Firebird_3_0\fbclient.dll"
if os.path.exists(fb_lib_path):
    driver_config.fb_client_library.value = fb_lib_path

def debug_product_462():
    try:
        cfg = Config()
        dsn = cfg.dsn
        print(f"Connecting to: {dsn}")
        
        conn = connect(
            database=dsn, 
            user=cfg.DB_USER, 
            password=cfg.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # 1. Get N1 Level for product 462
        cursor.execute("SELECT CLASSIFICACAO_N1, DESCRICAO FROM PRODUTOS WHERE CODIGO = 462")
        row = cursor.fetchone()
        if not row:
            print("Product 462 not found.")
            return
            
        n1_level = row[0]
        desc = row[1]
        print(f"Product 462: {desc}, Level N1: {n1_level}")
        
        # 2. Run ABC Query for this level
        # Assuming last 24 months or whatever the user might be using.
        # User implies a 24 month divisor, so presumably they ran for 2 years?
        # Let's try to match the user's likely date range: '2023-01-01' to '2024-12-31' (2 years)
        # Or maybe they just ran it for a specific range. 
        # I'll just pick a wide range or ask the user. 
        # Actually, let's just use a wide range 2000-2030 to see everything, OR
        # Better: Print what the database has for a reasonable 2 year period (2023-2024)
        
        start_date = '2023-01-01'
        end_date = '2024-12-31'
        
        print(f"Running Query with dates: {start_date} to {end_date}")
        
        params = (
            start_date, end_date,
            start_date, end_date,
            start_date, end_date,
            start_date, end_date,
            n1_level
        )
        
        cursor.execute(QUERY_ABC_BY_LEVEL, params)
        rows = cursor.fetchall()
        
        found = False
        for r in rows:
            # r[0]=desc, r[1]=codigo, r[2]=venda(qty), r[3]=valor
            if r[1] == 462:
                print(f"FOUND 462 in Query Result!")
                print(f"  Desc: {r[0]}")
                print(f"  Codigo: {r[1]}")
                print(f"  QUANTIDADE (r[2]): {r[2]}")
                print(f"  VALOR (r[3]): {r[3]}")
                
                qty = r[2] if r[2] is not None else 0
                media = round(float(qty) / 24.0, 1)
                print(f"  CALCULATED MEDIA (Qty/24): {media}")
                found = True
                break
                
        if not found:
            print("Product 462 NOT found in query results for this date range/level.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    debug_product_462()
