import pandas as pd
from .database import get_connection

def check_login(username, password):
    """
    Verifies if the username and password match a record in the Usuario table.
    Returns the user's ID_USUARIO if valid, None otherwise.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT ID_USUARIO FROM Usuario WHERE Nome_Usuario = ? AND senha = ?"
        cursor.execute(query, (username, password))
        row = cursor.fetchone()
        
        if row:
            return row[0]  # ID_USUARIO
        return None
    except Exception as e:
        print(f"Login Error: {e}")
        return None
    finally:
        conn.close()

def check_permission(user_id, ferramenta_id):
    """
    Checks if a user has permission for a specific tool/module.
    Returns True if the user has the permission, False otherwise.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM FERRAMENTAS_PERMISSAO WHERE FERRAMENTAS = ? AND USUARIO = ?",
            (ferramenta_id, user_id)
        )
        row = cursor.fetchone()
        return row[0] > 0 if row else False
    except Exception as e:
        print(f"Permission Check Error: {e}")
        return False
    finally:
        conn.close()
