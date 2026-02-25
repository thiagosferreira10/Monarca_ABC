import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import src_loader; src_loader.register()
from src.database import get_connection, get_n1_levels, get_levels, get_last_processed, get_fornecedores_ativos, get_sugestao_fornecedores, save_sugestao_fornecedor, delete_sugestao_fornecedor, get_produtos_ativos, get_sugestao_dolar, save_sugestao_dolar, delete_sugestao_dolar
from src.logic import execute_abc_update
from src.suggestion_logic import save_suggestion, get_suggestions, delete_suggestion, update_suggestion_fields
from src.schema_manager import check_and_update_schema
import time

# --- Schema Migration ---
# Ensure DB has required columns/tables before starting UI
try:
    _conn = get_connection()
    check_and_update_schema(_conn)
    _conn.close()
except Exception as e:
    st.error(f"Failed to update database schema: {e}")
    st.stop()
# ------------------------

st.set_page_config(page_title="Monarca Curva ABC", page_icon="Icone.ico", layout="wide", initial_sidebar_state="expanded")

from src.ui_utils import apply_sidebar_style, force_sidebar_expansion, render_bottom_logout
from src.auth_logic import check_permission
apply_sidebar_style()
force_sidebar_expansion()

# Auth Guard
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Faça login para acessar esta página.")
    st.stop()

user_id = st.session_state.get('user_id')

render_bottom_logout()

def generate_excel_buffer(df_sug, p_n1):
    from datetime import date, datetime
    from src.suggestion_logic import get_quarterly_data, execute_chunked_in_query
    from src.database import get_connection as get_conn
    import io
    
    buffer = io.BytesIO()
    
    # Load SUGESTAO_DOLAR product IDs for Moeda lookup
    conn_d = get_conn()
    cursor_d = conn_d.cursor()
    cursor_d.execute("SELECT PRODUTO FROM SUGESTAO_DOLAR")
    dolar_product_ids = set(r[0] for r in cursor_d.fetchall())
    conn_d.close()
    
    # Add Moeda column to dataframe
    df_sug_copy = df_sug.copy()
    df_sug_copy['Moeda'] = df_sug_copy['Código'].apply(lambda x: 'Dolar' if x in dolar_product_ids else 'Real')
    
    # Columns for export (Moeda before Compra, renamed from Compra R$)
    cols_export = [
        'RK', 'Código', 'Produto', 'Fornecedor', 'Curva', 'Média', 
        'Estoque', 'Reservado', 'Trânsito', 'Duração', 'Sugestão',
        'Moeda', 'Compra R$', 'Cotação', 'Variação', 'Total'
    ]
    
    df_export = df_sug_copy[cols_export].copy()
    df_export = df_export.rename(columns={'Compra R$': 'Compra'})
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Sugestão')
        worksheet = writer.sheets['Sugestão']
        workbook = writer.book
        
        # Freeze Panes
        worksheet.freeze_panes(1, 3)
        
        # Formats
        fmt_header = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#000080', 'font_color': 'white', 'border': 1, 'locked': False})
        fmt_header_center = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#000080', 'font_color': 'white', 'border': 1, 'locked': False})
        
        common = {'border': 1, 'locked': False}
        common_locked = {'border': 1, 'locked': False}
        
        fmt_std = workbook.add_format({**common, 'bg_color': '#FFFFFF'})
        fmt_alert_orange = workbook.add_format({**common, 'bg_color': '#FF99CC'})
        fmt_alert_yellow = workbook.add_format({**common, 'bg_color': '#FFFF99'})
        fmt_yellow = workbook.add_format({'bg_color': '#FFFFCC', 'border': 1})
        
        # BRL formats
        fmt_currency = workbook.add_format({**common, 'bg_color': '#FFFFFF', 'num_format': 'R$ #,##0.00'})
        fmt_currency_orange = workbook.add_format({**common, 'bg_color': '#FF99CC', 'num_format': 'R$ #,##0.00'})
        fmt_currency_yellow = workbook.add_format({**common, 'bg_color': '#FFFF99', 'num_format': 'R$ #,##0.00'})
        
        fmt_currency_lk = workbook.add_format({**common_locked, 'bg_color': '#FFFFFF', 'num_format': 'R$ #,##0.00'})
        fmt_currency_orange_lk = workbook.add_format({**common_locked, 'bg_color': '#FF99CC', 'num_format': 'R$ #,##0.00'})
        fmt_currency_yellow_lk = workbook.add_format({**common_locked, 'bg_color': '#FFFF99', 'num_format': 'R$ #,##0.00'})
        
        # USD formats
        fmt_usd = workbook.add_format({**common, 'bg_color': '#FFFFFF', 'num_format': '$ #,##0.00'})
        fmt_usd_orange = workbook.add_format({**common, 'bg_color': '#FF99CC', 'num_format': '$ #,##0.00'})
        fmt_usd_yellow = workbook.add_format({**common, 'bg_color': '#FFFF99', 'num_format': '$ #,##0.00'})
        
        fmt_usd_lk = workbook.add_format({**common_locked, 'bg_color': '#FFFFFF', 'num_format': '$ #,##0.00'})
        fmt_usd_orange_lk = workbook.add_format({**common_locked, 'bg_color': '#FF99CC', 'num_format': '$ #,##0.00'})
        fmt_usd_yellow_lk = workbook.add_format({**common_locked, 'bg_color': '#FFFF99', 'num_format': '$ #,##0.00'})
        
        var_fmt_str = '[Red]▲ 0.0%;[Color10]▼ 0.0%;0.0%'
        fmt_var_lk = workbook.add_format({**common_locked, 'bg_color': '#FFFFFF', 'num_format': var_fmt_str})
        fmt_var_orange_lk = workbook.add_format({**common_locked, 'bg_color': '#FF99CC', 'num_format': var_fmt_str})
        fmt_var_yellow_lk = workbook.add_format({**common_locked, 'bg_color': '#FFFF99', 'num_format': var_fmt_str})

        # Apply Header Format
        for col_num, value in enumerate(df_export.columns.values):
            fmt = fmt_header_center if value == 'Total' else fmt_header
            worksheet.write(0, col_num, value, fmt)
        
        # Column layout (0-indexed):
        # 0:RK 1:Código 2:Produto 3:Fornecedor 4:Curva 5:Média 6:Estoque 7:Reservado
        # 8:Trânsito 9:Duração 10:Sugestão 11:Moeda 12:Compra 13:Cotação 14:Variação 15:Total
        # Excel letters: K=Sugestão L=Moeda M=Compra N=Cotação O=Variação P=Total
        
        # Apply Row Formats
        for row_num in range(len(df_export)):
            xl_row = row_num + 2
            
            # Base Style based on Alert level
            alert_val = df_sug.iloc[row_num]['Alert']
            if pd.isna(alert_val) or alert_val is None:
                alert_level = None
            else:
                alert_level = alert_val
            
            # Check if product is Dolar
            prod_id = df_sug.iloc[row_num]['Código']
            is_dolar = prod_id in dolar_product_ids
            
            if alert_level == 'orange':
                f_std = fmt_alert_orange; f_curr = fmt_currency_orange; f_curr_lk = fmt_currency_orange_lk; f_var = fmt_var_orange_lk
                f_usd = fmt_usd_orange; f_usd_lk = fmt_usd_orange_lk
            elif alert_level == 'yellow':
                f_std = fmt_alert_yellow; f_curr = fmt_currency_yellow; f_curr_lk = fmt_currency_yellow_lk; f_var = fmt_var_yellow_lk
                f_usd = fmt_usd_yellow; f_usd_lk = fmt_usd_yellow_lk
            else:
                f_std = fmt_std; f_curr = fmt_currency; f_curr_lk = fmt_currency_lk; f_var = fmt_var_lk
                f_usd = fmt_usd; f_usd_lk = fmt_usd_lk
                
            for col_num, value in enumerate(df_export.iloc[row_num]):
                col_name = df_export.columns[col_num]
                
                if col_name == 'Variação':
                    formula = f'=IFERROR(((N{xl_row}/M{xl_row})-1), 0)'
                    worksheet.write_formula(row_num + 1, col_num, formula, f_var)
                elif col_name == 'Total':
                    formula = f'=N{xl_row}*K{xl_row}'
                    fmt_total = f_usd_lk if is_dolar else f_curr_lk
                    worksheet.write_formula(row_num + 1, col_num, formula, fmt_total)
                elif col_name == 'Cotação':
                    fmt_cot = f_usd if is_dolar else f_curr
                    worksheet.write(row_num + 1, col_num, "", fmt_cot)
                elif col_name == 'Compra':
                    fmt_compra = f_usd if is_dolar else f_curr
                    worksheet.write(row_num + 1, col_num, value, fmt_compra)
                else:
                    val = value if pd.notna(value) else ""
                    worksheet.write(row_num + 1, col_num, val, f_std)
        
        # Auto-adjust column widths
        min_widths = {'Total': 18, 'Variação': 12, 'Compra': 15, 'Cotação': 15, 'Fornecedor': 30, 'Produto': 40, 'Moeda': 10}
        fixed_widths = {'Estoque': 13, 'Reservado': 13}
        
        for i, col in enumerate(df_export.columns):
            max_data_len = df_export[col].astype(str).map(len).max()
            if pd.isna(max_data_len): max_data_len = 0
            column_len = max(max_data_len, len(col)) + 3
            if col in min_widths: column_len = max(column_len, min_widths[col])
            if col in fixed_widths: column_len = fixed_widths[col]
            worksheet.set_column(i, i, column_len)

        worksheet.autofilter(0, 0, len(df_export), len(df_export.columns) - 1)
        
        # ================== ANALISE SHEET ==================
        product_ids = df_sug['Código'].tolist()
        
        conn_q = get_conn()
        cursor_q = conn_q.cursor()
        quarterly_data, quarter_labels = get_quarterly_data(cursor_q, product_ids, p_n1)
        
        prazo_query_template = """
            SELECT PF.PRODUTO, SF.PRAZO
            FROM PRODUTOS_FORNECEDOR PF
            JOIN PRODUTOS P ON P.CODIGO = PF.PRODUTO
            JOIN SUGESTAO_FORNECEDOR SF ON SF.FORNECEDOR = PF.FORNECEDOR AND SF.TIPO = P.CLASSIFICACAO_N1
            WHERE PF.PRINCIPAL = 'S' AND PF.PRODUTO IN ({})
        """
        prazo_rows = execute_chunked_in_query(cursor_q, prazo_query_template, product_ids)
        prazo_map = {r[0]: float(r[1]) if r[1] else 0 for r in prazo_rows}
        conn_q.close()
        
        current_month = date.today().month
        
        def get_arrival_quarter(prazo_months):
             arrival_month = ((current_month - 1 + prazo_months) % 12) + 1
             return (arrival_month - 1) // 3 + 1
        
        def get_matching_quarter_label(quarter_num, quarter_labels):
             for label in quarter_labels:
                 if label.endswith(f"-{quarter_num}"): return label
             return quarter_labels[-1] if quarter_labels else None
        
        analise_cols = ['Rk', 'Código', 'Produto', 'Fornecedor', 'Curva', 'Media'] + quarter_labels + ['Prazo', 'Variação', 'Trimestre', 'Estoque', 'Reservado', 'Trânsito', 'Duração', 'Sugestão']
        analise_rows = []
        
        for idx, row in df_sug.iterrows():
            prod_id = row['Código']
            q_data = quarterly_data.get(prod_id, {})
            prazo = prazo_map.get(prod_id, 0)
            
            arrival_q = get_arrival_quarter(prazo) if prazo else 1
            matching_label = get_matching_quarter_label(arrival_q, quarter_labels)
            tri_ant = q_data.get(matching_label, 0) if matching_label else 0
            
            estoque = row['Estoque'] if 'Estoque' in df_sug.columns else 0
            reservado = row['Reservado'] if 'Reservado' in df_sug.columns else 0
            transito = row['Trânsito'] if 'Trânsito' in df_sug.columns else 0
            
            net_stock = estoque - reservado + transito
            duracao = round(net_stock / tri_ant, 1) if tri_ant > 0 else 0
            
            min_meses = row['Mínimo'] if 'Mínimo' in df_sug.columns else 0
            max_meses = row['Máximo'] if 'Máximo' in df_sug.columns else 0
            
            target_stock = tri_ant * max_meses
            if net_stock < target_stock:
                import math
                raw_sug = target_stock - net_stock
                sug_tri = math.ceil(raw_sug) if (raw_sug % 1) >= 0.3 else math.floor(raw_sug)
                if sug_tri < 0: sug_tri = 0
            else:
                sug_tri = 0
            
            analise_row = [row['RK'], prod_id, row['Produto'], row['Fornecedor'] if 'Fornecedor' in df_sug.columns else '', row['Curva'], row['Média']]
            for ql in quarter_labels: analise_row.append(q_data.get(ql, 0))
            analise_row.append(prazo)
            
            media_val = row['Média'] if 'Média' in df_sug.columns else 0
            if media_val > 0 and tri_ant is not None:
                var_val = (tri_ant / media_val) - 1
                var_pct = round(var_val * 100, 1)
                var_display = f"▼ {var_pct}%" if var_val < 0 else (f"▲ {var_pct}%" if var_val > 0 else "0%")
            else:
                 var_display = "0%"
            analise_row.append(var_display)
            analise_row.append(tri_ant); analise_row.append(estoque); analise_row.append(reservado); analise_row.append(transito); analise_row.append(duracao); analise_row.append(sug_tri)
            analise_rows.append(analise_row)
        
        df_analise = pd.DataFrame(analise_rows, columns=analise_cols)
        df_analise.to_excel(writer, index=False, sheet_name='Analise')
        
        ws_analise = writer.sheets['Analise']
        ws_analise.freeze_panes(1, 3)
        for col_num, value in enumerate(df_analise.columns.values):
             ws_analise.write(0, col_num, value, fmt_header)
        
        var_col_idx = list(df_analise.columns).index('Variação') if 'Variação' in df_analise.columns else -1
        sug_col_idx = list(df_analise.columns).index('Sugestão') if 'Sugestão' in df_analise.columns else -1
        
        for row_num in range(len(df_analise)):
             sug_val = df_analise.iloc[row_num, sug_col_idx] if sug_col_idx >= 0 else 0
             try: has_suggestion = float(sug_val) > 0
             except: has_suggestion = False
             
             if has_suggestion: base_fmt = fmt_yellow; bg_color = '#FFFFCC'
             else: base_fmt = fmt_std; bg_color = '#FFFFFF'
             
             for col_num in range(len(df_analise.columns)):
                 val = df_analise.iloc[row_num, col_num]
                 if col_num == var_col_idx and isinstance(val, str):
                     if '▼' in val: ws_analise.write(row_num + 1, col_num, val, workbook.add_format({'font_color': 'red', 'bg_color': bg_color, 'border': 1}))
                     elif '▲' in val: ws_analise.write(row_num + 1, col_num, val, workbook.add_format({'font_color': 'green', 'bg_color': bg_color, 'border': 1}))
                     else: ws_analise.write(row_num + 1, col_num, val, base_fmt)
                 else:
                     ws_analise.write(row_num + 1, col_num, val, base_fmt)
        
        for i, col in enumerate(df_analise.columns):
             max_len = max(df_analise[col].astype(str).apply(len).max(), len(str(col))) + 2
             ws_analise.set_column(i, i, max_len)
        ws_analise.autofilter(0, 0, len(df_analise), len(df_analise.columns) - 1)
        
    return buffer


# Custom CSS for Apple-like Minimalism
st.markdown("""
<style>
    /* Global Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .stApp {
        background-color: #ffffff; /* Reverted to White as requested */
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1d1d1f;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #000080; /* Navy Blue */
        color: white;
        border-radius: 980px; /* Pill shape */
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #0000A0; /* Slightly lighter Navy */
        transform: scale(1.02);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Blue Download Button (Custom) */
    .stDownloadButton > button {
        background-color: #000080 !important; /* Force Navy Blue */
        color: white !important;
        border: none !important;
        border-radius: 980px; /* Pill shape */
        font-weight: 500;
        padding: 0.5rem 1.5rem; /* Match stButton */
    }
    .stDownloadButton > button:hover {
        background-color: #0000A0 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white !important;
    }

    /* Cards/Containers */
    .css-1r6slb0, .css-1keycJ, .stForm {
        background-color: #f9f9f9; /* Slight gray for cards to contrast against white bg */
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); /* Lighter shadow */
        border: 1px solid rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    
    /* Force Navy Blue Button for Form Submit specifically (overriding default red if any) */
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #000080 !important;
        color: white !important;
        border: none;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #0000A0 !important;
        color: white !important;
    }
    
    /* Meters / Progress */
    .stProgress > div > div > div > div {
        background-color: #000080;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
        color: #1d1d1f;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #86868b;
        font-weight: 500;
    }

    /* Inputs */
    .stSelectbox label, .stDateInput label, .stRadio label, .stTextInput label, .stNumberInput label {
        font-size: 13px;
        color: #424245;
        font-weight: 500;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px;
        color: #86868b;
        font-weight: 500;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        color: #0071e3;
        border-bottom: 2px solid #0071e3;
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e5e5ea;
    }
    .stDataFrame th {
        color: #000080 !important; /* Navy Blue Headers */
    }
    
    /* Multiselect Tags - Black Background */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #000000 !important;
        color: white !important;
    }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #000080; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0; font-family: 'Inter', sans-serif; font-size: 2rem;">Sistema Monarca - Sugestão de Compra</h1>
</div>
""", unsafe_allow_html=True)

# Reordered Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Sugestão de Compra", "Configuração", "Fornecedores", "Produtos Dolar"])



# ==============================================================================
# TAB 1: SUGESTÃO DE COMPRA (Previously Tab 3)
# ==============================================================================
with tab1:
    if not user_id or not check_permission(user_id, 4):
        st.error("⛔ Você não tem permissão para acessar a aba Sugestão de Compra.")
    else:
      with st.container():
        st.markdown("### Sugestão de Compra")
        
        # Hierarchy Filter for Execution
        c_f1, c_f2, c_f3, c_f4 = st.columns(4)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # N1
        l_n1 = get_n1_levels(cursor) # Fetches ABC='S' only
        l_n1_sorted = sorted([(l[1], l[0]) for l in l_n1], key=lambda x: x[0])
        opts_n1 = {f"{desc} ({code})": code for desc, code in l_n1_sorted}
        
        sel_n1_lbl = c_f1.selectbox("Nível 1 (Obrigatório)", options=["Selecione"] + list(opts_n1.keys()), key="p_n1")
        p_n1 = opts_n1.get(sel_n1_lbl) if sel_n1_lbl != "Selecione" else None
        
        # N2
        p_n2 = None
        if p_n1:
            l_n2 = get_levels(cursor, "PRODUTOS_NIVEL2", p_n1, abc_only=True)
            if l_n2:
                # l_n2 = [(CODE, DESC)]
                l_n2_sorted = sorted([(l[1], l[0]) for l in l_n2], key=lambda x: x[0])
                opts_n2 = {f"{desc} ({code})": code for desc, code in l_n2_sorted}
                sel_n2_lbl = c_f2.selectbox("Nível 2", options=["(Todos)"] + list(opts_n2.keys()), key="p_n2")
                p_n2 = opts_n2.get(sel_n2_lbl) if sel_n2_lbl != "(Todos)" else None
                
        # N3
        p_n3 = None
        if p_n2:
            l_n3 = get_levels(cursor, "PRODUTOS_NIVEL3", p_n2)
            if l_n3:
                l_n3_sorted = sorted([(l[1], l[0]) for l in l_n3], key=lambda x: x[0])
                opts_n3 = {f"{desc} ({code})": code for desc, code in l_n3_sorted}
                sel_n3_lbl = c_f3.selectbox("Nível 3", options=["(Todos)"] + list(opts_n3.keys()), key="p_n3")
                p_n3 = opts_n3.get(sel_n3_lbl) if sel_n3_lbl != "(Todos)" else None
                
        # N4
        p_n4 = None
        if p_n3:
            l_n4 = get_levels(cursor, "PRODUTOS_NIVEL4", p_n3)
            if l_n4:
                l_n4_sorted = sorted([(l[1], l[0]) for l in l_n4], key=lambda x: x[0])
                opts_n4 = {f"{desc} ({code})": code for desc, code in l_n4_sorted}
                sel_n4_lbl = c_f4.selectbox("Nível 4", options=["(Todos)"] + list(opts_n4.keys()), key="p_n4")
                p_n4 = opts_n4.get(sel_n4_lbl) if sel_n4_lbl != "(Todos)" else None
                
        # ABC Filter + Critério (aligned with N1/N2 columns)
        col_abc, col_metric, _col_r2_3, _col_r2_4 = st.columns(4)
        
        abc_df = pd.read_sql("SELECT CODIGO, DESCRICAO FROM ABC ORDER BY CODIGO", conn)
        abc_opts = { row['DESCRICAO']: row['CODIGO'] for i, row in abc_df.iterrows() }
        
        with col_abc:
            selected_abc_labels = st.multiselect(
                "Filtrar Curva ABC (Opcional)",
                options=list(abc_opts.keys()),
                default=list(abc_opts.keys()) 
            )
        selected_abc_ids = [abc_opts[l] for l in selected_abc_labels] if selected_abc_labels else None

        with col_metric:
            metric_option = st.radio(
                "**Critério de Cálculo**",
                ("Quantidade (Qtd)", "Valor Financeiro (R$)"), 
                horizontal=True
            )
        metric_col = 'VALOR_TOTAL' if metric_option == "Valor Financeiro (R$)" else 'QUANTIDADE_TOTAL'

        conn.close() 

        # Buttons aligned with N1/N2 columns
        col_b1, col_b2, _col_b3, _col_b4 = st.columns(4)
        
        # Initialize session state for results if not present
        if 'abc_sug_data' not in st.session_state:
            st.session_state['abc_sug_data'] = None
        if 'abc_sug_buffer' not in st.session_state:
            st.session_state['abc_sug_buffer'] = None
        if 'abc_sug_filename' not in st.session_state:
            st.session_state['abc_sug_filename'] = None

        with col_b1:
            if st.button("🔎 Gerar Sugestão", type="primary", use_container_width=True):
                if not p_n1:
                    st.error("Selecione o Nível 1.")
                else:
                    try:
                        from src.purchase_logic import calculate_purchases
                        
                        # Step 1: Process ABC Curve
                        with st.spinner("Processando Curva ABC..."):
                            conn = get_connection()
                            df_abc = execute_abc_update(conn, p_n1, metric_type=metric_col)
                            conn.close()
                        
                        if df_abc.empty:
                            st.warning("Nenhum dado encontrado para Curva ABC.")
                        
                        # Step 2: Calculate Purchase Suggestions
                        with st.spinner("Calculando Sugestões..."):
                            conn = get_connection()
                            df_sug = calculate_purchases(conn, p_n1, p_n2, p_n3, p_n4, abc_ids_filter=selected_abc_ids)
                            conn.close()
                            
                        if df_sug.empty:
                            st.warning("Nenhum produto encontrado.")
                            st.session_state['abc_sug_data'] = None
                            st.session_state['abc_sug_buffer'] = None
                        else:
                            st.session_state['abc_sug_data'] = df_sug
                            
                            # Generate Excel Buffer immediately to have it ready for download
                            # (We'll call the generation logic here or reuse the one below?)
                            # Better to encapsulate Excel generation in a function, 
                            # but for now I will trigger a rerun or valid state to let the rest of script run.
                            # Actually, to put the button HERE, I need the buffer NOW.
                            # So I will move the Excel generation logic to a helper function or duplicate it inside this block.
                            # Let's defer Excel generation to a function or just do it here.
                            
                            # ... (Logic to generate buffer - I'll need to move the code from below to here or a function)
                            # Since the user wants the button *next* to Gerar, I have to generate it *before* rendering the button or on the *next* rerun.
                            # If I generate it now, I can display it.
                            
                            # Generate Excel Buffer immediately
                            buffer = generate_excel_buffer(df_sug, p_n1)
                            st.session_state['abc_sug_buffer'] = buffer.getvalue()
                            st.session_state['abc_sug_filename'] = f"Sugestao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

                    except Exception as e:
                        st.error(f"Erro: {e}")

        # Logic to Generate Excel if needed (from session state data)
        if st.session_state.get('abc_sug_data') is not None:
             df_sug = st.session_state['abc_sug_data']
             
             # Check if we need to regenerate buffer (e.g. new search)
             # For simplicity, let's generate if it's missing or if we just searched.
             # To avoid code duplication, I should ideally refactor, but for this edit:
             # I will assume the code below (lines 323+) handles generation. 
             # I need to pull that code UP or reference it.
             pass

        # Placeholder for Download Button (will be populated if buffer exists)
        with col_b2:
            if st.session_state.get('abc_sug_buffer'):
                 st.download_button(
                    label="📥 Baixar Excel",
                    data=st.session_state['abc_sug_buffer'],
                    file_name=st.session_state['abc_sug_filename'],
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                 )

        # Check if we have data to display
        if st.session_state.get('abc_sug_data') is not None:
             df_sug = st.session_state['abc_sug_data']
             # Allow flow to continue to display table...
        else:
             # If no data, stop execution to avoid errors below
             # But we need to be careful about not breaking the page layout.
             # If df_sug is not defined, the original code would crash loop/if.
             # So we define df_sug as empty?
             df_sug = pd.DataFrame() 

        if not df_sug.empty:
             # Continue to table render...
                        
                        # Formatting and Styling
                        # Highlight logic
                        # Styler is great for this using Styler.apply
                        
                        def highlight_alert(row):
                            if row.get('Alert'):
                                return ['background-color: #ffeba1; color: black'] * len(row)
                            else:
                                return [''] * len(row)
                                
                        # Drop 'Alert' column for display, but use it for style? 
                        # Pandas Styler is a bit tricky with hidden columns.
                        # Let's keep Alert visible or iterate index.
                        
                        # Simplified display:
                        # Let's drop ID columns to clean up
                        cols_show = ['RK', 'Código', 'Produto', 'Curva', 'Percentual', 'Média', 'Estoque', 'Reservado', 'Trânsito', 'Duração', 'Mínimo', 'Máximo', 'Sugestão']
                        df_show = df_sug[cols_show].copy()
                        
                        # Apply Style (Alert Colors)
                        def highlight_rows(row):
                            # Default white
                            color = '#FFFFFF'
                            # Alert overrides
                            alert_val = df_sug.loc[row.name, 'Alert']
                            if alert_val == 'orange':
                                color = '#FF99CC'
                            elif alert_val == 'yellow':
                                color = '#FFFF99'
                            return [f'background-color: {color}; color: black'] * len(row)

                        # Build column configs with right-alignment injected
                        _num_right_cols = {
                            "RK": st.column_config.NumberColumn(format="%d"),
                            "Percentual": st.column_config.NumberColumn(format="%.1f%%"),
                            "Média": st.column_config.NumberColumn(format="%.1f"),
                            "Estoque": st.column_config.NumberColumn(format="%.0f"),
                            "Reservado": st.column_config.NumberColumn(format="%.0f"),
                            "Trânsito": st.column_config.NumberColumn(format="%.0f"),
                            "Duração": st.column_config.NumberColumn(format="%.1f"),
                            "Mínimo": st.column_config.NumberColumn(format="%d"),
                            "Máximo": st.column_config.NumberColumn(format="%d"),
                            "Sugestão": st.column_config.NumberColumn(format="%d"),
                        }
                        for _cfg in _num_right_cols.values():
                            _cfg["alignment"] = "right"
                        _codigo_cfg = st.column_config.NumberColumn(format="%d")
                        _codigo_cfg["alignment"] = "left"
                        _num_right_cols["Código"] = _codigo_cfg

                        st.dataframe(
                            df_show.style.apply(highlight_rows, axis=1),
                            column_config=_num_right_cols,
                            use_container_width=True,
                            hide_index=True
                        )
                        

# Tab 2 (Calcular ABC) removed - ABC processing now integrated into Tab 1

# ==============================================================================
# TAB 3: CONFIGURAÇÃO (Previously Tab 2)
# ==============================================================================
# ==============================================================================
# TAB 3: CONFIGURAÇÃO (Previously Tab 2)
# ==============================================================================
# ==============================================================================
# TAB 3: CONFIGURAÇÃO (Previously Tab 2)
# ==============================================================================
with tab2:
    if not user_id or not check_permission(user_id, 5):
        st.error("⛔ Você não tem permissão para acessar a aba Configuração.")
    else:
      with st.container():
        st.markdown("### ⚙️ Parâmetros de Nível 1 (Processamento e Período)")
        
        from src.database import get_n1_configs, update_n1_config
        
        conn = get_connection()
        cursor = conn.cursor()
        data_n1 = get_n1_configs(cursor)
        conn.close()
        
        if data_n1:
            df_n1 = pd.DataFrame(data_n1)
            # Display Columns: Descricao (ReadOnly), Tipo (Selectbox), Meses (Number)
            
            edited_df = st.data_editor(
                df_n1,
                column_config={
                    "CODIGO": None, 
                    "DESCRICAO": st.column_config.TextColumn("Nível 1", disabled=True),
                    "TIPO_PROCESSAMENTO": st.column_config.SelectboxColumn(
                        "Processamento Base",
                        options=["V", "P"],
                        help="V=Venda, P=Pedido",
                        required=True
                    ),
                    "MESES": st.column_config.NumberColumn(
                        "Período (Meses)",
                        help="Quantidade de meses retroativos para análise",
                        min_value=1,
                        max_value=60,
                        step=1,
                        required=True
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="editor_n1"
            )
            
            # Check for changes
            # st.data_editor returns the current state of the dataframe.
            # We need to compare specific rows or just update everything on a button click?
            # Or use 'on_change' callback? 
            # Simple approach: Save Button.
            
            if st.button("💾 Salvar Configurações de Nível 1"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    changes_count = 0
                    for index, row in edited_df.iterrows():
                        # We could compare with original to optimize updates, but update all is safe enough here.
                        update_n1_config(cursor, row['CODIGO'], row['TIPO_PROCESSAMENTO'], int(row['MESES']))
                        changes_count += 1
                        
                    conn.commit()
                    conn.close()
                    st.success(f"Configurações atualizadas para {changes_count} níveis!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        st.write("---")
        st.markdown("### Regras de Sugestão de Estoque (Mínimo/Máximo)")
        st.write("")
        
        # State Management for Edit Mode
        if "edit_rule_id" not in st.session_state:
            st.session_state.edit_rule_id = None
        
        # 1. Fetch Rules First to Handle Selection Interaction
        # We need to know if user selected something in the grid BELOW (on previous run)
        # But Streamlit renders top-down. The grid is at bottom.
        # However, st.dataframe `on_select` updates session state and reruns. 
        # So we can read selection state at top.
        
        conn = get_connection()
        df_rules = get_suggestions(conn)
        conn.close()

        # Selection Logic - HANDLING FILTERS
        # The grid below might be filtered. If so, the `selection["rows"]` index refers to the FILTERED dataframe.
        # We must replicate the filters here to know which row was clicked.
        
        # Read Filters from Session State (defined below as f_n1, f_n2...)
        df_rules_filtered = df_rules.copy()
        
        if st.session_state.get("f_n1"):
            df_rules_filtered = df_rules_filtered[df_rules_filtered['N1_DESC'].isin(st.session_state["f_n1"])]
        if st.session_state.get("f_n2"):
            df_rules_filtered = df_rules_filtered[df_rules_filtered['N2_DESC'].isin(st.session_state["f_n2"])]
        if st.session_state.get("f_n3"):
            df_rules_filtered = df_rules_filtered[df_rules_filtered['N3_DESC'].isin(st.session_state["f_n3"])]
        if st.session_state.get("f_n4"):
            df_rules_filtered = df_rules_filtered[df_rules_filtered['N4_DESC'].isin(st.session_state["f_n4"])]
        if st.session_state.get("f_abc"):
            df_rules_filtered = df_rules_filtered[df_rules_filtered['CLASS_ABC'].isin(st.session_state["f_abc"])]
            
        selected_rule = None
        grid_state = st.session_state.get("rules_grid", {})
        if grid_state and grid_state.get("selection") and grid_state["selection"]["rows"]:
            # User selected a row
            idx = grid_state["selection"]["rows"][0]
            if idx < len(df_rules_filtered):
                 selected_rule = df_rules_filtered.iloc[idx]
        
        # If selection changed, update working vars?
        # Streamlit widgets hold their own state. We can use `value=` but it only works on initiation or key change.
        # We will use dynamic keys for widgets: key=f"n1_{selected_rule['CODIGO']}"? No, that resets state too much.
        # Strategy: Initialize default variables based on selection.
        
        defaults = {
            "n1": None, "n2": None, "n3": None, "n4": None,
            "abc": "A", "min": 1, "max": 3, "id": None
        }
        
        form_title = "Nova Regra"
        
        if selected_rule is not None:
            form_title = f"Editando Regra #{selected_rule['CODIGO']}"
            defaults["id"] = int(selected_rule['CODIGO'])
            defaults["n1"] = int(selected_rule['NIVEL1']) if pd.notna(selected_rule['NIVEL1']) else None
            defaults["n2"] = int(selected_rule['NIVEL2']) if pd.notna(selected_rule['NIVEL2']) else None
            defaults["n3"] = int(selected_rule['NIVEL3']) if pd.notna(selected_rule['NIVEL3']) else None
            defaults["n4"] = int(selected_rule['NIVEL4']) if pd.notna(selected_rule['NIVEL4']) else None
            # ABC in df is 'CLASS_ABC' (Desc) or 'ABC' (ID). df_rules has 'CLASS_ABC'.
            # DB has ID. UI Selectbox returns label or ID? 
            # Our selectbox below uses Description 'A', 'B'. 
            defaults["abc"] = selected_rule['CLASS_ABC'] 
            defaults["min"] = float(selected_rule['MINIMO'])
            defaults["max"] = float(selected_rule['MAXIMO'])
            
        
        # --- Form Area ---
        
        st.caption(f"**Status:** {form_title}")

        # Dynamic Hierarchy Selection
        
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # N1
        l_n1 = get_n1_levels(cursor) # [(CODE, DESC)]
        l_n1_sorted = sorted([(l[1], l[0]) for l in l_n1], key=lambda x: x[0])
        n1_opts = {f"{desc} ({code})": code for desc, code in l_n1_sorted}
        n1_vals = list(n1_opts.values())
        
        # Determine Index for Default
        idx_n1 = None
        if defaults["n1"] in n1_vals:
            idx_n1 = n1_vals.index(defaults["n1"])
            
        n1_sel = col_h1.selectbox("**Nível 1**", options=["Selecione"] + list(n1_opts.keys()), index=(idx_n1 + 1) if idx_n1 is not None else 0, key="cfg_n1_sel")
        n1_id = n1_opts.get(n1_sel) if n1_sel != "Selecione" else None
        
        # N2
        n2_id = None
        if n1_id:
            l_n2 = get_levels(cursor, "PRODUTOS_NIVEL2", n1_id, abc_only=True)
            if l_n2:
                l_n2_sorted = sorted([(l[1], l[0]) for l in l_n2], key=lambda x: x[0])
                n2_opts = {f"{desc} ({code})": code for desc, code in l_n2_sorted}
                n2_vals = list(n2_opts.values())
                
                idx_n2 = None
                if defaults["n2"] in n2_vals:
                    if n1_id == defaults["n1"]:
                         idx_n2 = n2_vals.index(defaults["n2"])
                
                n2_sel = col_h2.selectbox("**Nível 2**", options=["(Todos)"] + list(n2_opts.keys()), index=(idx_n2 + 1) if idx_n2 is not None else 0, key="cfg_n2_sel")
                n2_id = n2_opts.get(n2_sel) if n2_sel != "(Todos)" else None
                
        # N3
        n3_id = None
        if n2_id:
            l_n3 = get_levels(cursor, "PRODUTOS_NIVEL3", n2_id)
            if l_n3:
                l_n3_sorted = sorted([(l[1], l[0]) for l in l_n3], key=lambda x: x[0])
                n3_opts = {f"{desc} ({code})": code for desc, code in l_n3_sorted}
                n3_vals = list(n3_opts.values())
                
                idx_n3 = None
                if defaults["n3"] in n3_vals and n2_id == defaults["n2"]:
                     idx_n3 = n3_vals.index(defaults["n3"])
                     
                n3_sel = col_h3.selectbox("**Nível 3**", options=["(Todos)"] + list(n3_opts.keys()), index=(idx_n3 + 1) if idx_n3 is not None else 0, key="cfg_n3_sel")
                n3_id = n3_opts.get(n3_sel) if n3_sel != "(Todos)" else None
                
        # N4
        n4_id = None
        if n3_id:
            l_n4 = get_levels(cursor, "PRODUTOS_NIVEL4", n3_id)
            if l_n4:
                l_n4_sorted = sorted([(l[1], l[0]) for l in l_n4], key=lambda x: x[0])
                n4_opts = {f"{desc} ({code})": code for desc, code in l_n4_sorted}
                n4_vals = list(n4_opts.values())
                
                idx_n4 = None
                if defaults["n4"] in n4_vals and n3_id == defaults["n3"]:
                     idx_n4 = n4_vals.index(defaults["n4"])
                     
                n4_sel = col_h4.selectbox("**Nível 4**", options=["(Todos)"] + list(n4_opts.keys()), index=(idx_n4 + 1) if idx_n4 is not None else 0, key="cfg_n4_sel")
                n4_id = n4_opts.get(n4_sel) if n4_sel != "(Todos)" else None
                
        conn.close()
        
        st.write("---")
        
        # Input Rule Form
        with st.form("rule_form"):
            c_abc, c_min, c_max, c_submit = st.columns([2, 2, 2, 2])
            
            # ABC Selection
            conn = get_connection()
            abc_df = pd.read_sql("SELECT CODIGO, DESCRICAO FROM ABC ORDER BY CODIGO", conn)
            conn.close()
            abc_opts = { row['DESCRICAO']: row['CODIGO'] for i, row in abc_df.iterrows() }
            abc_vals = list(abc_opts.keys()) # ['A', 'B', 'C']
            
            idx_abc = 0
            if defaults["abc"] in abc_vals:
                idx_abc = abc_vals.index(defaults["abc"])
            
            abc_label = c_abc.selectbox("**ABC**", options=abc_vals, index=idx_abc)
            abc_id = abc_opts[abc_label]
            
            min_m = c_min.number_input("**Mínimo (Meses)**", min_value=0, value=int(defaults["min"]))
            max_m = c_max.number_input("**Máximo (Meses)**", min_value=0, value=int(defaults["max"]))
            
            # Alignment Spacer
            c_submit.markdown("<div style='height: 29px;'></div>", unsafe_allow_html=True) 
            
            save_label = "💾 Salvar Nova Regra" if defaults["id"] is None else "💾 Atualizar Regra"
            submitted = c_submit.form_submit_button(save_label, type="primary")
            
            if submitted:
                if not n1_id:
                    st.error("Selecione pelo menos o Nível 1.")
                else:
                    try:
                        conn = get_connection()
                        # Pass defaults['id'] (which is current selected ID) as rule_id
                        success, msg = save_suggestion(conn, n1_id, n2_id, n3_id, n4_id, abc_id, min_m, max_m, rule_id=defaults["id"])
                        conn.close()
                        
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                            
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        # Delete Action (Outside Form)
        if defaults["id"] is not None:
             col_del, col_info = st.columns([1, 5])
             if col_del.button("🗑️ Excluir Regra Selecionada", type="secondary"):
                 try:
                     conn = get_connection()
                     delete_suggestion(conn, defaults["id"])
                     conn.close()
                     st.success("Regra excluída!")
                     time.sleep(1)
                     st.rerun()
                 except Exception as e:
                     st.error(f"Erro ao excluir: {e}")
             col_info.info("Para DESMARCAR a seleção, clique no botão 'X' (Esc) que aparece ao passar o mouse na tabela abaixo ou clique em uma área vazia da tabela.")

        # Display Existing Rules (Selection Mode)
        st.write("### Regras Cadastradas")
        
        if not df_rules.empty:
            
            # Filters Area (aligned with grid columns: NIVEL_1, NIVEL_2, NIVEL_3, NIVEL_4, ABC, MINIMO, MAXIMO)
            st.markdown("**Filtros:**")
            _col_spacer, col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([0.1, 1, 1, 1, 1, 1])
            
            # Multiselects using Unique Values from Dataset
            # Using dropna() to avoid None
            # N1
            opts_f1 = sorted(df_rules['N1_DESC'].dropna().unique())
            f_n1 = col_f1.multiselect("Nível 1", opts_f1, key="f_n1", placeholder="Selecione...")
            
            # N2
            opts_f2 = sorted(df_rules['N2_DESC'].dropna().unique())
            f_n2 = col_f2.multiselect("Nível 2", opts_f2, key="f_n2", placeholder="Selecione...")
            
            # N3
            opts_f3 = sorted(df_rules['N3_DESC'].dropna().unique())
            f_n3 = col_f3.multiselect("Nível 3", opts_f3, key="f_n3", placeholder="Selecione...")
            
            # N4
            opts_f4 = sorted(df_rules['N4_DESC'].dropna().unique())
            f_n4 = col_f4.multiselect("Nível 4", opts_f4, key="f_n4", placeholder="Selecione...")
            
            # ABC
            opts_f5 = sorted(df_rules['CLASS_ABC'].dropna().unique())
            f_abc = col_f5.multiselect("ABC", opts_f5, key="f_abc", placeholder="Selecione...")
            
            # Apply Filters locally for display
            # Note: The EXACT SAME logic must be at the TOP (as implemented) for selection resolution.
            
            df_display_filtered = df_rules.copy()
            if f_n1:
                df_display_filtered = df_display_filtered[df_display_filtered['N1_DESC'].isin(f_n1)]
            if f_n2:
                df_display_filtered = df_display_filtered[df_display_filtered['N2_DESC'].isin(f_n2)]
            if f_n3:
                df_display_filtered = df_display_filtered[df_display_filtered['N3_DESC'].isin(f_n3)]
            if f_n4:
                df_display_filtered = df_display_filtered[df_display_filtered['N4_DESC'].isin(f_n4)]
            if f_abc:
                df_display_filtered = df_display_filtered[df_display_filtered['CLASS_ABC'].isin(f_abc)]
            
            
            # Reformat for Display
            rename_map = {
                'NIVEL1': 'N1', 'NIVEL2': 'N2', 'NIVEL3': 'N3', 'NIVEL4': 'N4', 'ABC': 'COD_ABC',
                'N1_DESC': 'NIVEL_1', 'N2_DESC': 'NIVEL_2', 'N3_DESC': 'NIVEL_3', 'N4_DESC': 'NIVEL_4',
                'CLASS_ABC': 'ABC'
            }
            df_fmt = df_display_filtered.rename(columns=rename_map)
            cols_to_show = ['NIVEL_1', 'NIVEL_2', 'NIVEL_3', 'NIVEL_4', 'ABC', 'MINIMO', 'MAXIMO']
            df_display = df_fmt[cols_to_show].copy()

            # Selection Enabled with Zebra Striping
            # Reset index for clean modulo
            df_display = df_display.reset_index(drop=True)
            
            def highlight_zebra(row):
                color = '#E6F0FF' if (row.name % 2 != 0) else '#FFFFFF'
                return [f'background-color: {color}; color: black'] * len(row)

            event = st.dataframe(
                df_display.style.apply(highlight_zebra, axis=1),
                column_config={
                    "NIVEL_1": st.column_config.TextColumn("NIVEL_1", width=190),
                    "NIVEL_2": st.column_config.TextColumn("NIVEL_2", width=190),
                    "NIVEL_3": st.column_config.TextColumn("NIVEL_3", width=190),
                    "NIVEL_4": st.column_config.TextColumn("NIVEL_4", width=190),
                    "ABC": st.column_config.TextColumn("ABC", width=130),
                    "MINIMO": st.column_config.NumberColumn(format="%d", width=130),
                    "MAXIMO": st.column_config.NumberColumn(format="%d", width=130),
                },
                use_container_width=True,
                hide_index=True,
                on_select="rerun", # Reruns script when selection changes
                selection_mode="single-row",
                key="rules_grid"
            )
        else:
            st.info("Nenhuma regra cadastrada.")

# ==============================================================================
# TAB 3: FORNECEDORES
# ==============================================================================
with tab3:
    if not user_id or not check_permission(user_id, 6):
        st.error("⛔ Você não tem permissão para acessar a aba Fornecedores.")
    else:
      with st.container():
        st.markdown("### 🚚 Cadastro de Fornecedores por Tipo")
        st.write("")
        
        # Load lookup data
        conn = get_connection()
        cursor = conn.cursor()
        fornecedores_list = get_fornecedores_ativos(cursor)
        n1_tipos = get_n1_levels(cursor)
        conn.close()
        
        # Build options for comboboxes
        fornecedor_options = {f"{r[1]} ({r[0]})": r[0] for r in fornecedores_list}
        tipo_options = {f"{r[1]} ({r[0]})": r[0] for r in n1_tipos}
        
        # --- Form ---
        st.markdown("**Novo Registro:**")
        col_f, col_t, col_p, col_btn = st.columns([3, 3, 1.5, 1.5])
        
        with col_f:
            sel_fornecedor = st.selectbox(
                "Fornecedor",
                options=list(fornecedor_options.keys()),
                placeholder="Selecione o fornecedor...",
                index=None,
                key="sf_fornecedor"
            )
        
        with col_t:
            sel_tipo = st.selectbox(
                "Tipo (Nível 1)",
                options=list(tipo_options.keys()),
                placeholder="Selecione o tipo...",
                index=None,
                key="sf_tipo"
            )
        
        with col_p:
            sel_prazo = st.number_input(
                "Prazo",
                min_value=0.0,
                max_value=999.0,
                value=0.0,
                step=0.1,
                format="%.1f",
                key="sf_prazo"
            )
        
        with col_btn:
            st.write("")  # Spacer for alignment
            st.write("")
            btn_salvar = st.button("💾 Salvar", key="sf_salvar", use_container_width=True)
        
        if btn_salvar:
            if sel_fornecedor and sel_tipo and sel_prazo > 0:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    forn_id = fornecedor_options[sel_fornecedor]
                    tipo_id = tipo_options[sel_tipo]
                    
                    # Check for duplicates (same FORNECEDOR + TIPO)
                    cursor.execute(
                        "SELECT COUNT(*) FROM SUGESTAO_FORNECEDOR WHERE FORNECEDOR = ? AND TIPO = ?",
                        (forn_id, tipo_id)
                    )
                    if cursor.fetchone()[0] > 0:
                        conn.close()
                        st.error("Já existe um registro com este Fornecedor e Tipo. Não é permitido duplicar.")
                    else:
                        save_sugestao_fornecedor(cursor, forn_id, tipo_id, sel_prazo)
                        conn.commit()
                        conn.close()
                        st.success("Registro salvo com sucesso!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha todos os campos (Fornecedor, Tipo e Prazo > 0).")
        
        st.write("---")
        
        # --- Grid ---
        st.markdown("### Registros Cadastrados")
        
        conn = get_connection()
        cursor = conn.cursor()
        data_sf = get_sugestao_fornecedores(cursor)
        conn.close()
        
        if data_sf:
            df_sf = pd.DataFrame(data_sf)
            
            # Delete button area
            col_del, col_info = st.columns([1, 4])
            with col_del:
                btn_excluir = st.button("🗑️ Excluir Selecionado", key="sf_excluir", use_container_width=True)
            
            # Display grid with selection
            df_display_sf = df_sf[['FORNECEDOR', 'TIPO', 'PRAZO']].copy()
            df_display_sf = df_display_sf.reset_index(drop=True)
            
            def highlight_zebra_sf(row):
                color = '#E6F0FF' if (row.name % 2 != 0) else '#FFFFFF'
                return [f'background-color: {color}; color: black'] * len(row)
            
            _sf_cols = {
                "FORNECEDOR": st.column_config.TextColumn("Fornecedor"),
                "TIPO": st.column_config.TextColumn("Tipo"),
                "PRAZO": st.column_config.NumberColumn("Prazo", format="%.1f"),
            }
            for _cfg in _sf_cols.values():
                _cfg["alignment"] = "left"

            event_sf = st.dataframe(
                df_display_sf.style.apply(highlight_zebra_sf, axis=1),
                column_config=_sf_cols,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="sf_grid"
            )
            
            # Handle deletion
            if btn_excluir:
                selected_rows = event_sf.selection.rows if event_sf and event_sf.selection else []
                if selected_rows:
                    row_idx = selected_rows[0]
                    codigo_del = df_sf.iloc[row_idx]['CODIGO']
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        delete_sugestao_fornecedor(cursor, codigo_del)
                        conn.commit()
                        conn.close()
                        st.success("Registro excluído!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                else:
                    st.warning("Selecione um registro na tabela para excluir.")
            
            col_info.info("Para DESMARCAR a seleção, clique no botão 'X' (Esc) que aparece ao passar o mouse na tabela ou clique em uma área vazia.")
        else:
            st.info("Nenhum registro cadastrado.")

# ==============================================================================
# TAB 4: PRODUTOS DOLAR
# ==============================================================================
with tab4:
    if not user_id or not check_permission(user_id, 7):
        st.error("⛔ Você não tem permissão para acessar a aba Produtos Dolar.")
    else:
      with st.container():
        st.markdown("### 💲 Cadastro de Produtos em Dólar")
        st.write("")
        
        # Load product list
        conn = get_connection()
        cursor = conn.cursor()
        produtos_list = get_produtos_ativos(cursor)
        conn.close()
        
        # Build options: "Code - Description" for easy search by code
        produto_options = {f"{r[0]} - {r[1]}": r[0] for r in produtos_list}
        
        # --- Form ---
        st.markdown("**Novo Registro:**")
        col_prod, col_dolar, col_btn = st.columns([4, 2, 1.5])
        
        with col_prod:
            sel_produto = st.selectbox(
                "Produto",
                options=list(produto_options.keys()),
                placeholder="Digite o código ou nome do produto...",
                index=None,
                key="sd_produto"
            )
        
        with col_dolar:
            sel_dolar = st.number_input(
                "Dolar $",
                min_value=0.00,
                max_value=999999.99,
                value=0.00,
                step=0.01,
                format="%.2f",
                key="sd_dolar"
            )
        
        with col_btn:
            st.write("")  # Spacer for alignment
            st.write("")
            btn_salvar_d = st.button("💾 Salvar", key="sd_salvar", use_container_width=True)
        
        if btn_salvar_d:
            if sel_produto and sel_dolar > 0:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    prod_id = produto_options[sel_produto]
                    save_sugestao_dolar(cursor, prod_id, sel_dolar)
                    conn.commit()
                    conn.close()
                    st.success("Registro salvo com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Selecione um produto e informe o valor em Dolar (> 0).")
        
        st.write("---")
        
        # --- Grid ---
        st.markdown("### Registros Cadastrados")
        
        conn = get_connection()
        cursor = conn.cursor()
        data_sd = get_sugestao_dolar(cursor)
        conn.close()
        
        if data_sd:
            df_sd = pd.DataFrame(data_sd)
            
            # Delete button area
            col_del, col_info = st.columns([1, 4])
            with col_del:
                btn_excluir_d = st.button("🗑️ Excluir Selecionado", key="sd_excluir", use_container_width=True)
            
            # Display grid with selection
            df_display_sd = df_sd[['PRODUTO_ID', 'PRODUTO', 'DOLAR']].copy()
            df_display_sd = df_display_sd.reset_index(drop=True)
            
            def highlight_zebra_sd(row):
                color = '#E6F0FF' if (row.name % 2 != 0) else '#FFFFFF'
                return [f'background-color: {color}; color: black'] * len(row)
            
            _sd_cols = {
                "PRODUTO_ID": st.column_config.NumberColumn("Código", format="%d"),
                "PRODUTO": st.column_config.TextColumn("Produto"),
                "DOLAR": st.column_config.NumberColumn("Dolar $", format="%.2f"),
            }
            for _cfg in _sd_cols.values():
                _cfg["alignment"] = "left"

            event_sd = st.dataframe(
                df_display_sd.style.apply(highlight_zebra_sd, axis=1),
                column_config=_sd_cols,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="sd_grid"
            )
            
            # Handle deletion
            if btn_excluir_d:
                selected_rows = event_sd.selection.rows if event_sd and event_sd.selection else []
                if selected_rows:
                    row_idx = selected_rows[0]
                    codigo_del = df_sd.iloc[row_idx]['CODIGO']
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        delete_sugestao_dolar(cursor, codigo_del)
                        conn.commit()
                        conn.close()
                        st.success("Registro excluído!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                else:
                    st.warning("Selecione um registro na tabela para excluir.")
            
            col_info.info("Para DESMARCAR a seleção, clique no botão 'X' (Esc) que aparece ao passar o mouse na tabela ou clique em uma área vazia.")
        else:
            st.info("Nenhum registro cadastrado.")


