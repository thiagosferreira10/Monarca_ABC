import pandas as pd
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
        
        products.append({
            'DESCRICAO': r[0],
            'CODIGO': r[1],
            # ...
            'CURVA': r[2],
            'MEDIA': float(r[3]) if r[3] is not None else 0.0,
            'ESTOQUE': float(r[4]) if r[4] is not None else 0.0,
            'RESERVADO': float(r[5]) if r[5] is not None else 0.0,
            'TRANSITO': float(r[6]) if r[6] is not None else 0.0,
            'N1_ID': r[7],
            'N2_ID': r[8],
            'N3_ID': r[9],
            'N4_ID': r[10],
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
    
    for _, prod in df_prod.iterrows():
        # Find Strategy
        matched_rule = None
        
        # Filter rules by ABC first
        rules_abc = df_rules[df_rules['ABC'] == prod['ABC_ID']]
        
        if rules_abc.empty:
            # Fallback or Skip? 
            # If no rule for this ABC class, maybe no suggestion.
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
                # N3 Match (N4 is None in Rule OR we ignore N4 column in rule if we want strict hierarchy?)
                # User requirement: "Localizar na tabela Sugestao_Nivel de acordo com o produto"
                # Implies specific levels. usually rules are defined like:
                # Rule A: N1=1, N2=Null... (Generic for N1)
                # Rule B: N1=1, N2=5... (Specific for N2)
                # So we look for Exact Matches of existing levels.
                # But a rule might have Nulls for lower levels.
                
                # Try N3 (Rule has N1, N2, N3 matches, N4 is Null/0)
                # Assuming 0 or None for unused levels in DB? 
                # Our Create Table/Insert logic likely puts None or Integer.
                # Let's assume matching None/0/NaN is the way for "Any".
                # BUT user said "select between 4 levels... ".
                # Let's stick to explicit match attempts.
                
                r3 = rules_abc[
                    (rules_abc['NIVEL1'] == prod['N1_ID']) &
                    (rules_abc['NIVEL2'] == prod['N2_ID']) &
                    (rules_abc['NIVEL3'] == prod['N3_ID']) &
                    ((rules_abc['NIVEL4'].isnull()) | (rules_abc['NIVEL4'] == 0))
                ]
                if not r3.empty:
                    matched_rule = r3.iloc[0]
                else:
                    r2 = rules_abc[
                        (rules_abc['NIVEL1'] == prod['N1_ID']) &
                        (rules_abc['NIVEL2'] == prod['N2_ID']) &
                        ((rules_abc['NIVEL3'].isnull()) | (rules_abc['NIVEL3'] == 0)) &
                        ((rules_abc['NIVEL4'].isnull()) | (rules_abc['NIVEL4'] == 0))
                    ]
                    if not r2.empty:
                        matched_rule = r2.iloc[0]
                    else:
                        r1 = rules_abc[
                            (rules_abc['NIVEL1'] == prod['N1_ID']) &
                            ((rules_abc['NIVEL2'].isnull()) | (rules_abc['NIVEL2'] == 0)) &
                            ((rules_abc['NIVEL3'].isnull()) | (rules_abc['NIVEL3'] == 0)) &
                            ((rules_abc['NIVEL4'].isnull()) | (rules_abc['NIVEL4'] == 0))
                        ]
                        if not r1.empty:
                            matched_rule = r1.iloc[0]
                            
        # Calculations
        # Duracao = Estoque / Media (Int)
        media = prod['MEDIA']
        estoque = prod['ESTOQUE']
        reservado = prod['RESERVADO']
        transito = prod['TRANSITO']
        
        if media > 0:
            duracao = int(estoque / media)
        else:
            duracao = 999 # Infinite duration logic? Or 0? 
            # If media is 0, duration is infinite technically. 
            
        min_meses = 0
        max_meses = 0
        sugestao = 0
        
        if matched_rule is not None:
            min_meses = matched_rule['MINIMO']
            max_meses = matched_rule['MAXIMO']
            
            # Sugestao = (Media * Max) - (Estoque - Reservado + Transito)
            # Logic Check: (Estoque - Reservado + Transito) represents "Net Available Stock"
            net_stock = estoque - reservado + transito
            target_stock = media * max_meses
            
            sugestao = int(target_stock - net_stock)
            if sugestao < 0: sugestao = 0
        
        results.append({
            'Código': prod['CODIGO'],
            'Produto': prod['DESCRICAO'],
            'Nível 1': prod['N1_ID'], # Or desc
            'Curva': prod['CURVA'],
            'Média': media,
            'Estoque': estoque,
            'Reservado': reservado,
            'Trânsito': transito,
            'Duração (Meses)': duracao,
            'Mínimo': min_meses,
            'Máximo': max_meses,
            'Sugestão': sugestao,
            'Alert': duracao < min_meses and min_meses > 0 # Flag for UI highlighting
        })
        
    return pd.DataFrame(results)
