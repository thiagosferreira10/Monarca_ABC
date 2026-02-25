"""
tests/test_crypto_utils.py
==========================
Testa a criptografia/descriptografia de credenciais.
Não precisa de banco de dados.
"""
import pytest
from src.crypto_utils import encrypt, decrypt, decrypt_if_needed, is_encrypted


# ── Testes básicos ────────────────────────────────────────────────────────────

def test_encrypt_retorna_string():
    assert isinstance(encrypt("teste"), str)

def test_decrypt_retorna_original():
    original = "minha_senha"
    assert decrypt(encrypt(original)) == original

def test_round_trip_usuario():
    assert decrypt(encrypt("SYSDBA")) == "SYSDBA"

def test_round_trip_senha_complexa():
    senha = "P@$$w0rd!123#"
    assert decrypt(encrypt(senha)) == senha

def test_round_trip_string_vazia():
    assert decrypt(encrypt("")) == ""

def test_encrypt_gera_valores_diferentes():
    """Mesmo input deve gerar outputs diferentes (por causa do salt aleatório)."""
    enc1 = encrypt("senha")
    enc2 = encrypt("senha")
    assert enc1 != enc2  # salt diferente a cada chamada

def test_decrypt_both_encrypted_same_plaintext():
    """Dois valores criptografados diferentes devem descriptografar igual."""
    enc1 = encrypt("senha")
    enc2 = encrypt("senha")
    assert decrypt(enc1) == decrypt(enc2) == "senha"


# ── Testes de is_encrypted ────────────────────────────────────────────────────

def test_is_encrypted_com_prefixo():
    assert is_encrypted("ENC:abc123") is True

def test_is_encrypted_sem_prefixo():
    assert is_encrypted("senha_plana") is False

def test_is_encrypted_string_vazia():
    assert is_encrypted("") is False


# ── Testes de decrypt_if_needed ───────────────────────────────────────────────

def test_decrypt_if_needed_com_enc():
    enc = f"ENC:{encrypt('vpatvppm')}"
    assert decrypt_if_needed(enc) == "vpatvppm"

def test_decrypt_if_needed_sem_enc_passa_direto():
    """Valor sem ENC: deve retornar como está (retrocompatibilidade)."""
    assert decrypt_if_needed("SYSDBA") == "SYSDBA"

def test_decrypt_if_needed_masterkey():
    assert decrypt_if_needed("masterkey") == "masterkey"

def test_decrypt_if_needed_valor_vazio():
    assert decrypt_if_needed("") == ""


# ── Testes de caracteres especiais ────────────────────────────────────────────

@pytest.mark.parametrize("valor", [
    "senha123",
    "p@$$w0rd!",
    "üñíçödé",
    "senha com espaços",
    "123456",
    "abc!@#$%^&*()",
])
def test_round_trip_parametrizado(valor):
    assert decrypt(encrypt(valor)) == valor
