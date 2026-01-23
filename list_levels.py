from firebird.driver import connect
from src.config import Config

def list_levels():
    print("Connecting to database...")
    conn = connect(
        database=Config().dsn,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset='WIN1252'
    )
    cursor = conn.cursor()
    
    query = "SELECT CODIGO, DESCRICAO, ABC FROM PRODUTOS_NIVEL1"
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("\n--- Níveis de Produto (N1) ---")
    print(f"{'ID':<5} | {'Descrição':<30} | {'ABC'}")
    print("-" * 50)
    for row in rows:
        abc_status = row[2] if row[2] else 'N'
        print(f"{row[0]:<5} | {row[1]:<30} | {abc_status}")

    conn.close()

if __name__ == "__main__":
    list_levels()
