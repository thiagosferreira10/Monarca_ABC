import os
import configparser
from dotenv import load_dotenv
from src.crypto_utils import decrypt_if_needed

# ----------------------------------------------------------------
# Busca o config.ini em ordem de prioridade:
#   1. Pasta atual de execucao (cwd) — usado em producao
#   2. Pasta pai de cwd (caso o exe fique numa subpasta)
#   3. Pasta Instalacao/ relativa ao cwd
# ----------------------------------------------------------------
def _find_config_ini() -> str:
    """Retorna o caminho do config.ini encontrado, ou string vazia."""
    cwd = os.getcwd()
    candidates = [
        os.path.join(cwd, 'config.ini'),                       # raiz da producao
        os.path.join(os.path.dirname(cwd), 'config.ini'),      # pasta pai
        os.path.join(cwd, 'Instalacao', 'config.ini'),         # dev local
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ''

_ini_path = _find_config_ini()

# Carrega .env apenas como fallback (config.ini tem prioridade)
load_dotenv()

# Lê o config.ini
_config = configparser.ConfigParser()
if _ini_path:
    _config.read(_ini_path, encoding='utf-8')

class Config:
    _db = _config['DATABASE'] if 'DATABASE' in _config else {}

    # Prioridade: config.ini > .env > valor padrão
    DB_HOST     = _db.get('Server',   None) or os.getenv('DB_HOST',     'localhost')
    DB_PORT     = _db.get('Port',     None) or os.getenv('DB_PORT',     '3050')
    DB_PATH     = _db.get('Path',     None) or os.getenv('DB_PATH',     r'D:\Bases\SistemaMonarca.fdb')
    # User e Password suportam criptografia: ENC:base64_cifrado
    DB_USER     = decrypt_if_needed(_db.get('User',     None) or os.getenv('DB_USER',     'SYSDBA'))
    DB_PASSWORD = decrypt_if_needed(_db.get('Password', None) or os.getenv('DB_PASSWORD', 'masterkey'))

    @property
    def dsn(self):
        return f"{self.DB_HOST}/{self.DB_PORT}:{self.DB_PATH}"

# Configura biblioteca do Firebird (procura nos locais mais comuns)
for _fb_lib in [
    r"C:\Program Files\Firebird\Firebird_3_0\fbclient.dll",
    r"C:\Program Files\Firebird\Firebird_4_0\fbclient.dll",
    r"C:\Program Files (x86)\Firebird\Firebird_3_0\fbclient.dll",
]:
    if os.path.exists(_fb_lib):
        os.environ['FIREBIRD_LIB'] = _fb_lib
        break
