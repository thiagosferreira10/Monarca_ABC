from firebird.driver import connect
from src.config import Config

def run_ddl():
    print("Connecting to database...")
    conn = connect(
        database=Config().dsn,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset='WIN1252'
    )
    cursor = conn.cursor()
    
    commands = [
        "CREATE TABLE ABC (CODIGO INTEGER NOT NULL PRIMARY KEY, DESCRICAO CHAR(1))",
        "INSERT INTO ABC (CODIGO, DESCRICAO) VALUES (1, 'A')",
        "INSERT INTO ABC (CODIGO, DESCRICAO) VALUES (2, 'B')",
        "INSERT INTO ABC (CODIGO, DESCRICAO) VALUES (3, 'C')"
    ]
    
    try:
        for cmd in commands:
            print(f"Executing: {cmd}")
            try:
                cursor.execute(cmd)
                conn.commit()
                print("Success.")
            except Exception as e:
                print(f"Error executing command: {e}")
                conn.rollback()

    except Exception as e:
        print(f"General Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_ddl()
