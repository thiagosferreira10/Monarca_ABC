import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3050')
    DB_PATH = os.getenv('DB_PATH', r'D:\Bases\Penatec\SistemaMonarca.fdb')
    DB_USER = os.getenv('DB_USER', 'SYSDBA')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'masterkey')
    
    @property
    def dsn(self):
        return f"{self.DB_HOST}/{self.DB_PORT}:{self.DB_PATH}"

# Configure Firebird Library Path for the generic driver if needed
fb_lib_path = r"C:\Program Files\Firebird\Firebird_3_0\fbclient.dll"
if os.path.exists(fb_lib_path):
    os.environ['FIREBIRD_LIB'] = fb_lib_path
