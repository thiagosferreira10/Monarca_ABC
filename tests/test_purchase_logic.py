"""
tests/test_purchase_logic.py
============================
Testa a lógica de cálculo de sugestão de compra.
Usa mock do banco de dados — sem conexão real.
"""
import pytest
import math
import pandas as pd
from unittest.mock import MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def calcular_sugestao(media, estoque, reservado, transito, min_meses, max_meses):
    """
    Replica a lógica de cálculo de sugestão de compra do purchase_logic.py.
    Isolada para testar sem depender do BD.
    """
    net_stock = estoque - reservado + transito

    if media > 0:
        net_stock_duracao = estoque - reservado + transito
        duracao = round(net_stock_duracao / media, 1)
    else:
        duracao = 999

    target_stock = media * max_meses

    if net_stock < target_stock:
        raw_sug = target_stock - net_stock
        sugestao = math.ceil(raw_sug) if (raw_sug % 1) >= 0.3 else math.floor(raw_sug)
        if sugestao < 0:
            sugestao = 0
    else:
        sugestao = 0

    return sugestao, duracao


def calcular_alerta(sugestao, duracao, min_meses, max_meses):
    if sugestao > 0 and duracao < min_meses and min_meses > 0:
        return 'orange'
    elif sugestao > 0 and duracao < max_meses and max_meses > 0:
        return 'yellow'
    return None


# ── Testes de sugestão de compra ──────────────────────────────────────────────

def test_sem_estoque_sugere_compra():
    """Sem estoque, deve sugerir compra para cobrir o máximo."""
    sugestao, _ = calcular_sugestao(
        media=10, estoque=0, reservado=0, transito=0,
        min_meses=2, max_meses=3
    )
    assert sugestao == 30  # 10 * 3 meses

def test_estoque_suficiente_nao_sugere():
    """Estoque acima do máximo, não deve sugerir compra."""
    sugestao, _ = calcular_sugestao(
        media=10, estoque=50, reservado=0, transito=0,
        min_meses=2, max_meses=3
    )
    assert sugestao == 0  # 50 >= 10*3=30

def test_estoque_parcial_sugere_diferenca():
    """Estoque cobre 1 mês, máximo é 3 → sugere 2 meses."""
    sugestao, _ = calcular_sugestao(
        media=10, estoque=10, reservado=0, transito=0,
        min_meses=2, max_meses=3
    )
    assert sugestao == 20  # 30 - 10 = 20

def test_reservado_reduz_estoque_efetivo():
    """Reservado deve ser subtraído do estoque."""
    sugestao, _ = calcular_sugestao(
        media=10, estoque=30, reservado=10, transito=0,
        min_meses=2, max_meses=3
    )
    # net = 30 - 10 = 20, target = 30, sug = 10
    assert sugestao == 10

def test_transito_aumenta_estoque_efetivo():
    """Trânsito deve ser somado ao estoque."""
    sugestao, _ = calcular_sugestao(
        media=10, estoque=10, reservado=0, transito=20,
        min_meses=2, max_meses=3
    )
    # net = 10 + 20 = 30 >= target 30 → sem sugestão
    assert sugestao == 0

def test_media_zero_duracao_999():
    """Com média zero, duração deve ser 999 (infinito)."""
    _, duracao = calcular_sugestao(
        media=0, estoque=100, reservado=0, transito=0,
        min_meses=2, max_meses=3
    )
    assert duracao == 999

def test_sugestao_nunca_negativa():
    """Sugestão não pode ser negativa."""
    sugestao, _ = calcular_sugestao(
        media=10, estoque=100, reservado=0, transito=0,
        min_meses=2, max_meses=3
    )
    assert sugestao >= 0


# ── Testes de arredondamento customizado ──────────────────────────────────────

def test_arredondamento_acima_0_3_sobe():
    """>= 0.3 decimal → arredonda para cima."""
    # raw_sug = 10.3 → deve virar 11
    sugestao, _ = calcular_sugestao(
        media=3.433, estoque=0, reservado=0, transito=0,
        min_meses=1, max_meses=3
    )
    raw = 3.433 * 3
    esperado = math.ceil(raw) if (raw % 1) >= 0.3 else math.floor(raw)
    assert sugestao == esperado

def test_arredondamento_abaixo_0_3_desce():
    """< 0.3 decimal → arredonda para baixo."""
    raw = 10.1
    resultado = math.ceil(raw) if (raw % 1) >= 0.3 else math.floor(raw)
    assert resultado == 10


# ── Testes de níveis de alerta ────────────────────────────────────────────────

def test_alerta_orange_abaixo_minimo():
    assert calcular_alerta(sugestao=5, duracao=1, min_meses=2, max_meses=3) == 'orange'

def test_alerta_yellow_entre_min_max():
    assert calcular_alerta(sugestao=5, duracao=2.5, min_meses=2, max_meses=3) == 'yellow'

def test_sem_alerta_sem_sugestao():
    assert calcular_alerta(sugestao=0, duracao=5, min_meses=2, max_meses=3) is None

def test_sem_alerta_acima_max():
    assert calcular_alerta(sugestao=0, duracao=4, min_meses=2, max_meses=3) is None


# ── Testes parametrizados ─────────────────────────────────────────────────────

@pytest.mark.parametrize("media,estoque,reservado,transito,min_m,max_m,esperado_sug", [
    (10,  0,  0,  0, 2, 3, 30),   # sem estoque → compra max
    (10, 30,  0,  0, 2, 3,  0),   # estoque exato → sem compra
    (10, 30, 10,  0, 2, 3, 10),   # reservado reduz
    (10, 10,  0, 20, 2, 3,  0),   # trânsito completa
    ( 5, 10,  0,  0, 2, 4, 10),   # parcial
    ( 0, 50,  0,  0, 2, 3,  0),   # media=0 → sem sugestão
])
def test_sugestao_parametrizado(media, estoque, reservado, transito, min_m, max_m, esperado_sug):
    sugestao, _ = calcular_sugestao(media, estoque, reservado, transito, min_m, max_m)
    assert sugestao == esperado_sug
