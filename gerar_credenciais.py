"""
Gerador de Credenciais Criptografadas para config.ini
=====================================================
Use este script para criptografar User e Password
antes de colocar no config.ini de produção.

Uso:
    python gerar_credenciais.py
"""
import sys
sys.path.insert(0, '.')
from src.crypto_utils import encrypt

print("=" * 50)
print("🔐 Gerador de Credenciais Criptografadas")
print("=" * 50)
print()

user = input("Digite o usuário do banco: ").strip()
password = input("Digite a senha do banco:   ").strip()

enc_user = encrypt(user)
enc_pass = encrypt(password)

print()
print("=" * 50)
print("Cole estas linhas no config.ini:")
print("=" * 50)
print()
print(f"User = ENC:{enc_user}")
print(f"Password = ENC:{enc_pass}")
print()
print("=" * 50)
print()
input("Pressione Enter para sair...")
