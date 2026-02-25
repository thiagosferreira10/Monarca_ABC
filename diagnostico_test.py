import sys
import os
import traceback

sys.path.insert(0, '.')

print("Python:", sys.version)
print("cwd:", os.getcwd())
print()

# Teste 1: src_loader
try:
    import src_loader
    src_loader.register()
    print("src_loader: OK")
except Exception as e:
    print("src_loader ERRO:", e)
    traceback.print_exc()

print()

# Teste 2: src.ui_utils
try:
    from src.ui_utils import apply_sidebar_style
    print("src.ui_utils: OK")
except Exception as e:
    print("src.ui_utils ERRO:", e)
    traceback.print_exc()

print()

# Teste 3: src.config
try:
    from src.config import Config
    print("src.config: OK")
    print("  DB_HOST:", Config.DB_HOST)
    print("  DB_PATH:", Config.DB_PATH)
    print("  DB_USER:", Config.DB_USER)
except Exception as e:
    print("src.config ERRO:", e)
    traceback.print_exc()

print()

# Teste 4: src.database
try:
    from src.database import get_connection
    print("src.database: OK (modulo importado)")
except Exception as e:
    print("src.database ERRO:", e)
    traceback.print_exc()

print()
print("=== FIM DO TESTE ===")
input("Pressione Enter para sair...")
