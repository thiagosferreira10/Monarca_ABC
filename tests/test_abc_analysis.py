"""
tests/test_abc_analysis.py
==========================
Testa a lógica de classificação ABC (Pareto 80/95/100).
Não precisa de banco de dados — testa pura lógica.
"""
import pytest
import pandas as pd
from src.abc_analysis import process_abc_curve


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def df_simples():
    """5 produtos com valores bem distribuídos."""
    return pd.DataFrame({
        'CODIGO':           [1, 2, 3, 4, 5],
        'DESCRICAO':        ['A', 'B', 'C', 'D', 'E'],
        'QUANTIDADE_TOTAL': [100, 80, 60, 40, 20],
        'VALOR_TOTAL':      [500.0, 250.0, 150.0, 75.0, 25.0],
    })

@pytest.fixture
def df_vazio():
    return pd.DataFrame(columns=['CODIGO', 'DESCRICAO', 'QUANTIDADE_TOTAL', 'VALOR_TOTAL'])

@pytest.fixture
def df_valor_zero():
    return pd.DataFrame({
        'CODIGO': [1, 2],
        'DESCRICAO': ['X', 'Y'],
        'QUANTIDADE_TOTAL': [0, 0],
        'VALOR_TOTAL': [0.0, 0.0],
    })


# ── Testes básicos ────────────────────────────────────────────────────────────

def test_retorna_dataframe(df_simples):
    resultado = process_abc_curve(df_simples)
    assert isinstance(resultado, pd.DataFrame)

def test_df_vazio_retorna_vazio(df_vazio):
    resultado = process_abc_curve(df_vazio)
    assert resultado.empty

def test_valor_zero_classifica_como_c(df_valor_zero):
    resultado = process_abc_curve(df_valor_zero)
    assert (resultado['CLASSE'] == 'C').all()

def test_colunas_criadas(df_simples):
    resultado = process_abc_curve(df_simples)
    assert 'VALOR_ACUMULADO' in resultado.columns
    assert 'PERCENTUAL_ACUMULADO' in resultado.columns
    assert 'PERCENTUAL' in resultado.columns
    assert 'CLASSE' in resultado.columns


# ── Testes de classificação A/B/C ────────────────────────────────────────────

def test_classes_validas(df_simples):
    """Só podem existir classes A, B ou C."""
    resultado = process_abc_curve(df_simples)
    assert set(resultado['CLASSE']).issubset({'A', 'B', 'C'})

def test_ordenacao_decrescente(df_simples):
    """O item de maior valor deve ser o primeiro (Pareto)."""
    resultado = process_abc_curve(df_simples)
    assert resultado.iloc[0]['VALOR_TOTAL'] == df_simples['VALOR_TOTAL'].max()

def test_percentual_acumulado_termina_em_100(df_simples):
    resultado = process_abc_curve(df_simples)
    assert abs(resultado['PERCENTUAL_ACUMULADO'].iloc[-1] - 100.0) < 0.01

def test_soma_percentuais_igual_100(df_simples):
    resultado = process_abc_curve(df_simples)
    assert abs(resultado['PERCENTUAL'].sum() - 100.0) < 0.01

def test_classificacao_a_ate_80_pct():
    """Item que representa 80% do valor acumulado deve ser classe A."""
    df = pd.DataFrame({
        'CODIGO':           [1, 2],
        'DESCRICAO':        ['Dominante', 'Secundario'],
        'QUANTIDADE_TOTAL': [1, 1],
        'VALOR_TOTAL':      [800.0, 200.0],  # 80% / 20%
    })
    resultado = process_abc_curve(df)
    assert resultado.iloc[0]['CLASSE'] == 'A'   # 80% acumulado → A
    assert resultado.iloc[1]['CLASSE'] == 'C'   # 100% acumulado → C (>95)

def test_classificacao_b_entre_80_e_95():
    """Item que leva o acumulado de 80% a 95% deve ser classe B."""
    df = pd.DataFrame({
        'CODIGO':           [1, 2, 3],
        'DESCRICAO':        ['X', 'Y', 'Z'],
        'QUANTIDADE_TOTAL': [1, 1, 1],
        'VALOR_TOTAL':      [800.0, 150.0, 50.0],  # 80% | 95% | 100%
    })
    resultado = process_abc_curve(df)
    assert resultado.iloc[0]['CLASSE'] == 'A'
    assert resultado.iloc[1]['CLASSE'] == 'B'
    assert resultado.iloc[2]['CLASSE'] == 'C'


# ── Teste com coluna alternativa ──────────────────────────────────────────────

def test_metrica_por_quantidade(df_simples):
    """Deve funcionar com QUANTIDADE_TOTAL como métrica."""
    resultado = process_abc_curve(df_simples, metric_column='QUANTIDADE_TOTAL')
    assert 'CLASSE' in resultado.columns
    assert resultado.iloc[0]['QUANTIDADE_TOTAL'] == df_simples['QUANTIDADE_TOTAL'].max()


# ── Teste de valores negativos / edge cases ───────────────────────────────────

def test_produto_unico():
    """Um único produto deve ser classe A (100% = A ≤ 80%? Não — 100% > 95 = C)."""
    df = pd.DataFrame({
        'CODIGO': [1], 'DESCRICAO': ['Único'],
        'QUANTIDADE_TOTAL': [10], 'VALOR_TOTAL': [1000.0],
    })
    resultado = process_abc_curve(df)
    # 100% acumulado → classified as C (>95)
    assert resultado.iloc[0]['CLASSE'] == 'C'
