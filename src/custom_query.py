QUERY_ABC_BY_LEVEL = """
select
  p.descricao,
  p.codigo,
  /*
  n1.descricao as nivel1,
  n2.descricao as nivel2,
  n3.descricao as nivel3,
  n4.descricao as nivel4,
  coalesce((select sum(e.quantidade) from estoque e where e.produto = p.codigo group by e.produto),0) as estoque,
  coalesce((select sum(pi.quantidade - coalesce(pv.quantidade,0))
    from pedido_item pi left join pedido d on (d.codigo = pi.pedido) left join pedido_venda pv on (pv.pedido = pi.pedido and pv.venda_produto = pi.produto)
    where 1=1 and pi.produto = p.codigo and d.situacao not in (3,4,5) and pi.situacao not in (3,4,5)
    group by pi.produto),0)
  as reservado,
  --Pedido de Compra
  coalesce((select sum(coalesce(pci.quantidade,0) - coalesce(pce.quantidade,0))
    from pedido_compra_item pci left join pedido_compra pc on (pc.codigo = pci.pedido) left join pedido_compra_entrega pce on (pci.pedido = pce.pedido and pci.produto = pce.produto)
    where 1=1 and pci.produto = p.codigo and pc.situacao not in (3,4,5) and pc.sugestao = 'N'
    group by pci.produto),0)
  as transito,
  */
  coalesce((select sum (i.quantidade) from venda_item i 
            join venda v on v.codigo = i.venda 
            where i.produto = p.codigo 
            and v.data >= ? and v.data <= ? -- Date Filter Added
            group by i.produto),0) +
  coalesce((select sum(s.quantidade)
    from assist a left join assist_item i on (i.assistencia = a.codigo) left join assist_item_produto s on (s.item = i.codigo)
    where 1=1 and s.baixa_estoque = 'S' and s.produto = p.codigo
    and a.data >= ? and a.data <= ? -- Date Filter Added
    group by s.produto),0)
  as venda,
  coalesce((select sum (i.quantidade * i.valor_unitario) from venda_item i 
            join venda v on v.codigo = i.venda 
            where i.produto = p.codigo 
            and v.data >= ? and v.data <= ? -- Date Filter Added
            group by i.produto),0) +
  coalesce((select sum(s.quantidade * s.preco_unitario)
    from assist a left join assist_item i on (i.assistencia = a.codigo) left join assist_item_produto s on (s.item = i.codigo)
    where 1=1 and s.baixa_estoque = 'S' and s.produto = p.codigo
    and a.data >= ? and a.data <= ? -- Date Filter Added
    group by s.produto),0)
  as valor
from
  produtos p
  --left join produtos_nivel1 n1 on (n1.codigo = p.classificacao_n1)
  --left join produtos_nivel2 n2 on (n2.codigo = p.classificacao_n2)
  --left join produtos_nivel3 n3 on (n3.codigo = p.classificacao_n3)
  --left join produtos_nivel4 n4 on (n4.codigo = p.classificacao_n4)
where
  1=1
  and p.ativo = 'S'
  and p.classificacao_n1 = ? -- Level Parameter
  --and p.codigo = 762
order by 3 desc
"""
