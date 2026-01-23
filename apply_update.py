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
        "ALTER TABLE PRODUTOS_NIVEL1 ADD ABC CHAR(1) DEFAULT 'N'",
        # Optional: Set 'S' for a few categories to test, if they exist
        # "UPDATE PRODUTOS_NIVEL1 SET ABC = 'S'" 
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
                # Don't raise, maybe column already exists
                conn.rollback()

    except Exception as e:
        print(f"General Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_ddl()
