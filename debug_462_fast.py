from firebird.driver import connect, driver_config
import os
from dotenv import load_dotenv
from src.config import Config
from src.custom_query import QUERY_ABC_BY_LEVEL

# Load env variables
load_dotenv(r'D:\Estudos\Python\curva_abc\.env')

# Configure Firebird Driver
driver_config.server_defaults.host.value = 'localhost'
fb_lib_path = r"C:\Program Files\Firebird\Firebird_3_0\fbclient.dll"
if os.path.exists(fb_lib_path):
    driver_config.fb_client_library.value = fb_lib_path

def debug_product_462_fast():
    try:
        cfg = Config()
        conn = connect(
            database=cfg.dsn, 
            user=cfg.DB_USER, 
            password=cfg.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # 1. Get N1 Level
        cursor.execute("SELECT CLASSIFICACAO_N1 FROM PRODUTOS WHERE CODIGO = 462")
        row = cursor.fetchone()
        if not row:
            print("Product 462 not found.")
            return
        n1_level = row[0]
        
        # 2. Modified Query
        query = QUERY_ABC_BY_LEVEL.replace("--and p.codigo = 762", "AND p.codigo = 462")
        
        start_date = '2023-01-01'
        end_date = '2024-12-31'
        print(f"Running FAST Query for Product 462, 2023-2024")

        params = (
            start_date, end_date,
            start_date, end_date,
            start_date, end_date,
            start_date, end_date,
            n1_level
        )
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for r in rows:
            print(f"Desc: {r[0]}")
            print(f"Codigo: {r[1]}")
            qty = r[2] if r[2] is not None else 0
            val = r[3] if r[3] is not None else 0
            print(f"QUANTIDADE (r[2]): {qty}")
            print(f"VALOR (r[3]): {val}")
            
            # Show calculation
            media = round(float(qty) / 24.0, 1)
            print(f"CALCULATED MEDIA (Qty/24): {media}")
            
            if qty > 0:
                print(f"Implied Price (Val/Qty): {float(val)/float(qty)}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    debug_product_462_fast()
