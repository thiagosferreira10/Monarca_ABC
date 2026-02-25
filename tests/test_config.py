"""
tests/test_config.py
====================
Testa a leitura do config.ini e fallback para .env.
Usa arquivos temporários — sem tocar nos arquivos reais.
"""
import pytest
import os
import configparser
import tempfile


# ── Helper ────────────────────────────────────────────────────────────────────

def _find_config_ini(search_dir: str) -> str:
    """Réplica da função de busca do config.py."""
    candidates = [
        os.path.join(search_dir, 'config.ini'),
        os.path.join(os.path.dirname(search_dir), 'config.ini'),
        os.path.join(search_dir, 'Instalacao', 'config.ini'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ''


# ── Testes de busca do config.ini ────────────────────────────────────────────

def test_encontra_config_ini_na_raiz(tmp_path):
    """Deve encontrar config.ini na pasta raiz."""
    ini = tmp_path / "config.ini"
    ini.write_text("[DATABASE]\nServer = 1.2.3.4\n")
    resultado = _find_config_ini(str(tmp_path))
    assert resultado == str(ini)

def test_encontra_config_ini_em_instalacao(tmp_path):
    """Deve encontrar config.ini em Instalacao/ se não houver na raiz."""
    instalacao = tmp_path / "Instalacao"
    instalacao.mkdir()
    ini = instalacao / "config.ini"
    ini.write_text("[DATABASE]\nServer = 1.2.3.4\n")
    resultado = _find_config_ini(str(tmp_path))
    assert resultado == str(ini)

def test_retorna_vazio_sem_config(tmp_path):
    """Deve retornar string vazia se não encontrar."""
    resultado = _find_config_ini(str(tmp_path))
    assert resultado == ''


# ── Testes de leitura do config.ini ──────────────────────────────────────────

def test_le_server_do_config_ini(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[DATABASE]\nServer = 192.168.1.10\nPort = 3050\nPath = C:\\DB.fdb\n")
    cfg = configparser.ConfigParser()
    cfg.read(str(ini))
    assert cfg['DATABASE'].get('server') == '192.168.1.10'

def test_le_port_do_config_ini(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[DATABASE]\nServer = localhost\nPort = 3050\nPath = C:\\DB.fdb\n")
    cfg = configparser.ConfigParser()
    cfg.read(str(ini))
    assert cfg['DATABASE'].get('port') == '3050'

def test_configparser_e_case_insensitive(tmp_path):
    """ConfigParser converte chaves para minúsculas."""
    ini = tmp_path / "config.ini"
    ini.write_text("[DATABASE]\nServer = 10.0.0.1\n")
    cfg = configparser.ConfigParser()
    cfg.read(str(ini))
    db = cfg['DATABASE']
    # Ambas as formas devem funcionar
    assert db.get('Server') == '10.0.0.1'
    assert db.get('server') == '10.0.0.1'

def test_sem_secao_database_retorna_vazio(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[OUTRA_SECAO]\nChave = valor\n")
    cfg = configparser.ConfigParser()
    cfg.read(str(ini))
    assert 'DATABASE' not in cfg

def test_config_ini_com_enc_prefix(tmp_path):
    """Valores com ENC: devem ser preservados no config.ini."""
    ini = tmp_path / "config.ini"
    ini.write_text("[DATABASE]\nUser = ENC:abc123==\nPassword = ENC:xyz456==\n")
    cfg = configparser.ConfigParser()
    cfg.read(str(ini))
    assert cfg['DATABASE'].get('user').startswith('ENC:')
    assert cfg['DATABASE'].get('password').startswith('ENC:')


# ── Testes de prioridade: config.ini > .env ───────────────────────────────────

def test_config_ini_tem_prioridade_sobre_env(tmp_path, monkeypatch):
    """Se config.ini tem Server, deve prevalecer sobre DB_HOST do .env."""
    monkeypatch.setenv('DB_HOST', 'env_servidor')

    ini = tmp_path / "config.ini"
    ini.write_text("[DATABASE]\nServer = ini_servidor\nPort = 3050\nPath = C:\\DB.fdb\n")
    cfg = configparser.ConfigParser()
    cfg.read(str(ini))
    db = cfg['DATABASE']

    db_host = db.get('server', None) or os.getenv('DB_HOST', 'localhost')
    assert db_host == 'ini_servidor'  # config.ini vence

def test_env_e_usado_se_sem_config_ini(monkeypatch):
    """Se não há config.ini, deve usar variável de ambiente."""
    monkeypatch.setenv('DB_HOST', 'env_servidor')

    db = {}  # sem config.ini
    db_host = db.get('server', None) or os.getenv('DB_HOST', 'localhost')
    assert db_host == 'env_servidor'

def test_default_se_sem_config_e_sem_env(monkeypatch):
    """Sem config.ini e sem .env, deve usar valor padrão."""
    monkeypatch.delenv('DB_HOST', raising=False)

    db = {}
    db_host = db.get('server', None) or os.getenv('DB_HOST', 'localhost')
    assert db_host == 'localhost'
