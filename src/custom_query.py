QUERY_ABC_BY_LEVEL = """
WITH VENDAS AS (
    SELECT 
        i.produto, 
        SUM(i.quantidade) as qtd, 
        SUM(i.quantidade * i.valor_unitario) as valor
    FROM venda_item i 
    JOIN venda v ON v.codigo = i.venda 
    WHERE v.data >= ? AND v.data <= ?
    GROUP BY i.produto
),
ASSIST AS (
    SELECT 
        s.produto, 
        SUM(s.quantidade) as qtd, 
        SUM(s.quantidade * s.preco_unitario) as valor
    FROM assist_item_produto s
    JOIN assist_item i ON i.codigo = s.item
    JOIN assist a ON a.codigo = i.assistencia
    WHERE s.baixa_estoque = 'S' 
    AND a.data >= ? AND a.data <= ?
    GROUP BY s.produto
),
FORNECEDORES AS (
    SELECT 
        pf.PRODUTO, 
        MAX(c.NOME) as NOM_FORNECEDOR
    FROM PRODUTOS_FORNECEDOR pf
    JOIN CLIENTES c ON c.CODIGO = pf.FORNECEDOR
    WHERE pf.PRINCIPAL = 'S'
    GROUP BY pf.PRODUTO
)
SELECT
    p.descricao,
    p.codigo,
    COALESCE(v.qtd, 0) + COALESCE(a.qtd, 0) as venda,
    COALESCE(v.valor, 0) + COALESCE(a.valor, 0) as valor,
    f.NOM_FORNECEDOR
FROM produtos p
LEFT JOIN VENDAS v ON v.produto = p.codigo
LEFT JOIN ASSIST a ON a.produto = p.codigo
LEFT JOIN FORNECEDORES f ON f.produto = p.codigo
LEFT JOIN PRODUTOS_NIVEL2 n2 ON n2.codigo = p.classificacao_n2
WHERE
    p.ativo = 'S'
    AND p.classificacao_n1 = ?
    AND (n2.abc = 'S' OR n2.codigo IS NULL)
ORDER BY 3 DESC
"""

QUERY_ABC_BY_LEVEL_ORDER = """
WITH PEDIDOS AS (
    SELECT 
        i.produto, 
        SUM(i.quantidade) as qtd, 
        SUM(i.quantidade * i.valor_unitario) as valor
    FROM pedido_item i 
    JOIN pedido p ON p.codigo = i.pedido 
    WHERE p.data >= ? AND p.data <= ?
      AND p.situacao NOT IN (3)
      AND i.situacao NOT IN (3)
    GROUP BY i.produto
),
ASSIST AS (
    SELECT 
        s.produto, 
        SUM(s.quantidade) as qtd, 
        SUM(s.quantidade * s.preco_unitario) as valor
    FROM assist_item_produto s
    JOIN assist_item i ON i.codigo = s.item
    JOIN assist a ON a.codigo = i.assistencia
    WHERE s.baixa_estoque = 'S' 
    AND a.data >= ? AND a.data <= ?
    GROUP BY s.produto
),
FORNECEDORES AS (
    SELECT 
        pf.PRODUTO, 
        MAX(c.NOME) as NOM_FORNECEDOR
    FROM PRODUTOS_FORNECEDOR pf
    JOIN CLIENTES c ON c.CODIGO = pf.FORNECEDOR
    WHERE pf.PRINCIPAL = 'S'
    GROUP BY pf.PRODUTO
)
SELECT
    p.descricao,
    p.codigo,
    COALESCE(v.qtd, 0) + COALESCE(a.qtd, 0) as venda,
    COALESCE(v.valor, 0) + COALESCE(a.valor, 0) as valor,
    f.NOM_FORNECEDOR
FROM produtos p
LEFT JOIN PEDIDOS v ON v.produto = p.codigo
LEFT JOIN ASSIST a ON a.produto = p.codigo
LEFT JOIN FORNECEDORES f ON f.produto = p.codigo
LEFT JOIN PRODUTOS_NIVEL2 n2 ON n2.codigo = p.classificacao_n2
WHERE
    p.ativo = 'S'
    AND p.classificacao_n1 = ?
    AND (n2.abc = 'S' OR n2.codigo IS NULL)
ORDER BY 3 DESC
"""
