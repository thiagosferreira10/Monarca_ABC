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
    
    # We split DDLs because execute usually runs one statement at a time
    commands = [
        """
        CREATE TABLE SUGESTAO_NIVEL (
            CODIGO INTEGER NOT NULL PRIMARY KEY,
            NIVEL1 INTEGER,
            NIVEL2 INTEGER,
            NIVEL3 INTEGER,
            NIVEL4 INTEGER,
            ABC INTEGER,
            MINIMO INTEGER,
            MAXIMO INTEGER
        )
        """,
        "ALTER TABLE SUGESTAO_NIVEL ADD CONSTRAINT FK_SUGESTAO_NIVEL_TheN1 FOREIGN KEY (NIVEL1) REFERENCES PRODUTOS_NIVEL1 (CODIGO)",
        "ALTER TABLE SUGESTAO_NIVEL ADD CONSTRAINT FK_SUGESTAO_NIVEL_TheN2 FOREIGN KEY (NIVEL2) REFERENCES PRODUTOS_NIVEL2 (CODIGO)",
        "ALTER TABLE SUGESTAO_NIVEL ADD CONSTRAINT FK_SUGESTAO_NIVEL_TheN3 FOREIGN KEY (NIVEL3) REFERENCES PRODUTOS_NIVEL3 (CODIGO)",
        "ALTER TABLE SUGESTAO_NIVEL ADD CONSTRAINT FK_SUGESTAO_NIVEL_TheN4 FOREIGN KEY (NIVEL4) REFERENCES PRODUTOS_NIVEL4 (CODIGO)",
        "ALTER TABLE SUGESTAO_NIVEL ADD CONSTRAINT FK_SUGESTAO_NIVEL_TheABC FOREIGN KEY (ABC) REFERENCES ABC (CODIGO)"
    ]
    
    try:
        for cmd in commands:
            print(f"Executing: {cmd.strip()[:50]}...")
            try:
                cursor.execute(cmd)
                conn.commit()
                print("Success.")
            except Exception as e:
                print(f"Error executing command: {e}")
                # Don't halt completely, maybe table exists but keys don't, etc.
                conn.rollback()

    except Exception as e:
        print(f"General Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_ddl()
