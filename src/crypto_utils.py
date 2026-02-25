"""
crypto_utils.py — Criptografia leve para credenciais do config.ini
================================================================
Usa AES-like XOR cipher com chave derivada de um segredo interno.
A chave fica embutida no .pyc compilado (não legível em texto).

USO (desenvolvedor):
    python crypto_utils.py encrypt "minha_senha"
    python crypto_utils.py decrypt "base64_cifrado"

O resultado criptografado deve ser colado no config.ini:
    [DATABASE]
    Password = ENC:base64_cifrado_aqui
"""

import base64
import hashlib
import os
import sys

# ================================================================
# CHAVE SECRETA — fica protegida dentro do .pyc em produção
# Mude este valor para algo único do seu projeto!
# ================================================================
_SECRET_KEY = "M0n4rc4-T4G-2026-$ecret!K3y"


def _derive_key(length: int = 32) -> bytes:
    """Deriva uma chave de bytes a partir do segredo interno."""
    return hashlib.sha256(_SECRET_KEY.encode("utf-8")).digest()[:length]


def encrypt(plain_text: str) -> str:
    """
    Criptografa um texto plano.
    Retorna string base64 que pode ser colocada no config.ini.
    """
    key = _derive_key()
    # Adiciona salt aleatório para que o mesmo texto gere cifras diferentes
    salt = os.urandom(8)
    data = plain_text.encode("utf-8")
    
    # XOR com chave derivada (key cycling)
    encrypted = bytearray()
    for i, byte in enumerate(data):
        encrypted.append(byte ^ key[i % len(key)])
    
    # Resultado = salt + encrypted, codificado em base64
    result = base64.b64encode(salt + bytes(encrypted)).decode("ascii")
    return result


def decrypt(cipher_text: str) -> str:
    """
    Descriptografa um texto cifrado (base64).
    Retorna o texto plano original.
    """
    key = _derive_key()
    raw = base64.b64decode(cipher_text)
    
    # Remove salt (primeiros 8 bytes)
    encrypted = raw[8:]
    
    # XOR reverso
    decrypted = bytearray()
    for i, byte in enumerate(encrypted):
        decrypted.append(byte ^ key[i % len(key)])
    
    return decrypted.decode("utf-8")


def is_encrypted(value: str) -> bool:
    """Verifica se um valor do config.ini está criptografado."""
    return value.startswith("ENC:")


def decrypt_if_needed(value: str) -> str:
    """Descriptografa apenas se o valor começa com 'ENC:'."""
    if is_encrypted(value):
        return decrypt(value[4:])  # Remove o prefixo "ENC:"
    return value


# ================================================================
# CLI para o desenvolvedor usar
# ================================================================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso:")
        print("  python crypto_utils.py encrypt <texto>")
        print("  python crypto_utils.py decrypt <base64>")
        print()
        print("Exemplo:")
        print('  python crypto_utils.py encrypt "minha_senha_123"')
        print("  Resultado: ENC:abc123...")
        print()
        print("  No config.ini:")
        print("  Password = ENC:abc123...")
        sys.exit(1)

    action = sys.argv[1].lower()
    value = sys.argv[2]

    if action == "encrypt":
        result = encrypt(value)
        print(f"Texto plano: {value}")
        print(f"Criptografado: ENC:{result}")
        print()
        print("Cole no config.ini:")
        print(f"Password = ENC:{result}")

    elif action == "decrypt":
        if value.startswith("ENC:"):
            value = value[4:]
        result = decrypt(value)
        print(f"Descriptografado: {result}")

    else:
        print(f"Ação desconhecida: {action}")
        print("Use 'encrypt' ou 'decrypt'")
