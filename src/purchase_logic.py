import pandas as pd
import math
from .purchase_query import QUERY_PURCHASE_SUGGESTION
from .suggestion_logic import get_suggestions

def calculate_purchases(conn, n1_id, n2_id=None, n3_id=None, n4_id=None, abc_ids_filter=None):
    """
    Calculates purchase suggestions for products in the given hierarchy.
    abc_ids_filter: List of ABC IDs to include. If None/Empty, includes all.
    """
    cursor = conn.cursor()
    
    # 1. Fetch Product Data
    # ... (same)
    cursor.execute(QUERY_PURCHASE_SUGGESTION, (n1_id,))
    rows = cursor.fetchall()
    
    if not rows:
        return pd.DataFrame()
        
    products = []
    for r in rows:
        # Filter by Hierarchy
        if n2_id and r[8] != n2_id: continue
        if n3_id and r[9] != n3_id: continue
        if n4_id and r[10] != n4_id: continue
        
        # Filter by ABC (if provided)
        # r[15] is abc_id
        if abc_ids_filter and r[15] not in abc_ids_filter: continue
        
        media_val = float(r[3]) if r[3] is not None else 0.0
        # Use stored percentual from DB or 0.0 if null
        pct_share = float(r[16]) if len(r) > 16 and r[16] is not None else 0.0
        nom_fornecedor = r[17] if len(r) > 17 else None
        compra_val = float(r[18]) if len(r) > 18 and r[18] is not None else 0.0
        
        products.append({
            'DESCRICAO': r[0],
            'CODIGO': r[1],
            'FORNECEDOR': nom_fornecedor,
            'COMPRA': compra_val,
            # ...
            'CURVA': r[2],
            'PERCENTUAL': pct_share,
            'MEDIA': media_val,
            'ESTOQUE': float(r[4]) if r[4] is not None else 0.0,
            'RESERVADO': float(r[5]) if r[5] is not None else 0.0,
            'TRANSITO': float(r[6]) if r[6] is not None else 0.0,
            'N1_ID': r[7],
            'N2_ID': r[8],
            'N3_ID': r[9],
            'N4_ID': r[10],
            'N1_DESC': r[11],
            'N2_DESC': r[12],
            'N3_DESC': r[13],
            'N4_DESC': r[14],
            'ABC_ID': r[15]
        })
        
    df_prod = pd.DataFrame(products)
    if df_prod.empty:
        return df_prod
        
    # ... rule logic ...
    
    df_rules = get_suggestions(conn)
    
    results = []
    
    for _, prod in df_prod.iterrows():
        # ... matching logic (kept mostly same, just updating inside loop) ...
        # Can we rely on unchanged code handling if we don't replace the whole block?
        # The tool requires StartLine/EndLine. 
        # I need to be careful not to delete the matching logic in between.
        # I will replace the function signature and the loop filtering part.
        # And separately update the calculation part? Or do one big replace if needed?
        # Let's do signature + filtering first.
        pass # Placeholder for thought logic, actual action below.
        
    df_prod = pd.DataFrame(products)
    if df_prod.empty:
        return df_prod
        
    # 2. Fetch Rules
    df_rules = get_suggestions(conn)
    # df_rules cols: CODIGO, NIVEL1, NIVEL2, NIVEL3, NIVEL4, ABC, MINIMO, MAXIMO
    
    # helper to find rule
    # Priority: N4 > N3 > N2 > N1
    # Match ID and ABC
    
    # Pre-process rules for faster lookup? 
    # Or just iterate since rules count is probably low? 
    # Let's iterate for safety and exact matching.
    
    results = []
    
    results = []
    
    # Iterate with index for Ranking (1-based)
    for i, (_, prod) in enumerate(df_prod.iterrows(), start=1):
        # Find Strategy
        matched_rule = None
        
        # Filter rules by ABC first
        rules_abc = df_rules[df_rules['ABC'] == prod['ABC_ID']]
        # ... existing matching logic ...
        
        if rules_abc.empty:
            matched_rule = None
        else:
             # Try to find N4 match
            r4 = rules_abc[
                (rules_abc['NIVEL1'] == prod['N1_ID']) &
                (rules_abc['NIVEL2'] == prod['N2_ID']) &
                (rules_abc['NIVEL3'] == prod['N3_ID']) &
                (rules_abc['NIVEL4'] == prod['N4_ID'])
            ]
            if not r4.empty:
                matched_rule = r4.iloc[0]
            else:
                # N3 Match (N4 is None)
                r3 = rules_abc[
                    (rules_abc['NIVEL1'] == prod['N1_ID']) &
                    (rules_abc['NIVEL2'] == prod['N2_ID']) &
                    (rules_abc['NIVEL3'] == prod['N3_ID']) &
                    ((rules_abc['NIVEL4'].isnull()) | (rules_abc['NIVEL4'] == 0))
                ]
                if not r3.empty:
                    matched_rule = r3.iloc[0]
                else:
                    # N2 Match
                    r2 = rules_abc[
                        (rules_abc['NIVEL1'] == prod['N1_ID']) &
                        (rules_abc['NIVEL2'] == prod['N2_ID']) &
                        ((rules_abc['NIVEL3'].isnull()) | (rules_abc['NIVEL3'] == 0)) &
                        ((rules_abc['NIVEL4'].isnull()) | (rules_abc['NIVEL4'] == 0))
                    ]
                    if not r2.empty:
                        matched_rule = r2.iloc[0]
                    else:
                        # N1 Match
                        r1 = rules_abc[
                            (rules_abc['NIVEL1'] == prod['N1_ID']) &
                            ((rules_abc['NIVEL2'].isnull()) | (rules_abc['NIVEL2'] == 0)) &
                            ((rules_abc['NIVEL3'].isnull()) | (rules_abc['NIVEL3'] == 0)) &
                            ((rules_abc['NIVEL4'].isnull()) | (rules_abc['NIVEL4'] == 0))
                        ]
                        if not r1.empty:
                            matched_rule = r1.iloc[0]

        # Calculations
        media = prod['MEDIA']
        estoque = prod['ESTOQUE']
        reservado = prod['RESERVADO']
        transito = prod['TRANSITO']
        
        if media > 0:
            # Corrected Formula: (Stock - Reserved + Transit) / Media
            net_stock_duracao = estoque - reservado + transito
            duracao = round(net_stock_duracao / media, 1)
        else:
            duracao = 999 
            
        min_meses = 0
        max_meses = 0
        sugestao = 0
        
        if matched_rule is not None:
            min_meses = int(matched_rule['MINIMO'])
            max_meses = int(matched_rule['MAXIMO'])
            
            net_stock = estoque - reservado + transito
            
            # Target Stock = Max months of coverage
            target_stock = media * max_meses
            
            if net_stock < target_stock:
                # Calculate suggestion to top up to Max coverage
                raw_sug = target_stock - net_stock
                # Custom rounding: >= 0.3 decimal rounds up, < 0.3 rounds down
                sugestao = math.ceil(raw_sug) if (raw_sug % 1) >= 0.3 else math.floor(raw_sug)
                if sugestao < 0: sugestao = 0
            else:
                # Stock covers Max months, no purchase needed
                sugestao = 0
        
        # Alert levels based on duration vs min/max thresholds
        # Orange: critical - duration below minimum
        # Yellow: warning - duration below maximum but above minimum
        if sugestao > 0 and duracao < min_meses and min_meses > 0:
            alert_level = 'orange'
        elif sugestao > 0 and duracao < max_meses and max_meses > 0:
            alert_level = 'yellow'
        else:
            alert_level = None
        
        results.append({
            'RK': i,
            'Código': prod['CODIGO'],
            'Fornecedor': prod['FORNECEDOR'],
            'Produto': prod['DESCRICAO'],
            'Nível 1': prod['N1_ID'],
            'Curva': prod['CURVA'],
            'Percentual': prod['PERCENTUAL'],
            'Média': media,
            'Estoque': estoque,
            'Reservado': reservado,
            'Trânsito': transito,
            'Duração': duracao,
            'Mínimo': min_meses,
            'Máximo': max_meses,
            'Sugestão': sugestao,
            'Compra R$': prod['COMPRA'],
            'Cotação': None,
            'Variação': None,
            'Total': None,
            'N1_DESC': prod['N1_DESC'],
            'N2_DESC': prod['N2_DESC'],
            'N3_DESC': prod['N3_DESC'],
            'N4_DESC': prod['N4_DESC'],
            'Alert': alert_level
        })
        
    return pd.DataFrame(results)
