from src.database import get_connection

def add_column():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("Adding DATA_PROCESSAMENTO to PRODUTOS_NIVEL1...")
        # Firebird 3.0 syntax
        cursor.execute("ALTER TABLE PRODUTOS_NIVEL1 ADD DATA_PROCESSAMENTO TIMESTAMP")
        conn.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error (might already exist): {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    add_column()
