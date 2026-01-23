import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.database import get_connection, get_n1_levels, get_levels, get_last_processed
from src.logic import execute_abc_update
from src.suggestion_logic import save_suggestion, get_suggestions, delete_suggestion, update_suggestion_fields
import time

st.set_page_config(page_title="Monarca Curva ABC", page_icon="Icone.ico", layout="wide")

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
        border-radius: 12px;
        font-weight: 500;
        padding: 0.5rem 1rem;
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
    <h1 style="color: white; margin: 0; font-family: 'Inter', sans-serif; font-size: 2rem;">Sistema Monarca - Curva ABC</h1>
</div>
""", unsafe_allow_html=True)

# Reordered Tabs
tab1, tab2, tab3 = st.tabs(["Sugestão de Compra", "Calcular ABC", "Configuração"])



# ==============================================================================
# TAB 1: SUGESTÃO DE COMPRA (Previously Tab 3)
# ==============================================================================
with tab1:
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
            l_n2 = get_levels(cursor, "PRODUTOS_NIVEL2", p_n1)
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
                
        # ABC Filter
        st.write("---")
        abc_df = pd.read_sql("SELECT CODIGO, DESCRICAO FROM ABC ORDER BY CODIGO", conn)
        abc_opts = { row['DESCRICAO']: row['CODIGO'] for i, row in abc_df.iterrows() }
        
        selected_abc_labels = st.multiselect(
            "Filtrar Curva ABC (Opcional)",
            options=list(abc_opts.keys()),
            default=list(abc_opts.keys()) 
        )
        selected_abc_ids = [abc_opts[l] for l in selected_abc_labels] if selected_abc_labels else None

        conn.close() 

        st.write("")
        if st.button("🔎 Gerar Sugestão"):
            if not p_n1:
                st.error("Selecione o Nível 1.")
            else:
                try:
                    from src.purchase_logic import calculate_purchases
                    
                    with st.spinner("Calculando Sugestões..."):
                        conn = get_connection()
                        df_sug = calculate_purchases(conn, p_n1, p_n2, p_n3, p_n4, abc_ids_filter=selected_abc_ids)
                        conn.close()
                        
                    if df_sug.empty:
                        st.warning("Nenhum produto encontrado para estes filtros.")
                    else:
                        st.success(f"Encontrados {len(df_sug)} produtos.")
                        
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
                        cols_show = ['Código', 'Produto', 'Curva', 'Média', 'Estoque', 'Reservado', 'Trânsito', 'Duração (Meses)', 'Mínimo', 'Máximo', 'Sugestão']
                        df_show = df_sug[cols_show].copy()
                        
                        # Apply Style (Alerts + Zebra Striping)
                        # Helper for Zebra
                        def highlight_rows(row):
                            # Default cyclic color
                            color = '#E6F0FF' if (row.name % 2 != 0) else '#FFFFFF'
                            # Alert overrides
                            if df_sug.loc[row.name, 'Alert']:
                                color = '#ffeba1'
                            return [f'background-color: {color}; color: black'] * len(row)

                        st.dataframe(
                            df_show.style.apply(highlight_rows, axis=1),
                            column_config={
                                "Média": st.column_config.NumberColumn(format="%.1f"),
                                "Estoque": st.column_config.NumberColumn(format="%.0f"),
                                "Reservado": st.column_config.NumberColumn(format="%.0f"),
                                "Trânsito": st.column_config.NumberColumn(format="%.0f"),
                                "Sugestão": st.column_config.NumberColumn(format="%d"),
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Excel Export
                        import io
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_show.to_excel(writer, index=False, sheet_name='Sugestoes')
                            # Auto-adjust columns & Apply Zebra Striping
                            worksheet = writer.sheets['Sugestoes']
                            workbook = writer.book
                            
                            # Formats
                            fmt_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#DDEBF7', 'border': 1})
                            fmt_blue = workbook.add_format({'bg_color': '#E6F0FF', 'border': 1})
                            fmt_white = workbook.add_format({'bg_color': '#FFFFFF', 'border': 1})
                            fmt_alert = workbook.add_format({'bg_color': '#ffeba1', 'border': 1})
                            
                            # Apply Header Format
                            for col_num, value in enumerate(df_show.columns.values):
                                worksheet.write(0, col_num, value, fmt_header)
                            
                            # Apply Row Formats
                            for row_num in range(len(df_show)):
                                # Determine Base Format
                                if pd.isna(df_sug.iloc[row_num]['Alert']): is_alert = False
                                else: is_alert = df_sug.iloc[row_num]['Alert']
                                
                                if is_alert:
                                    fmt = fmt_alert
                                elif row_num % 2 != 0:
                                    fmt = fmt_blue
                                else:
                                    fmt = fmt_white
                                    
                                for col_num, value in enumerate(df_show.iloc[row_num]):
                                    # Handle NaN
                                    val = value if pd.notna(value) else ""
                                    worksheet.write(row_num + 1, col_num, val, fmt)
                            
                            # Adjust Widths
                            for i, col in enumerate(df_show.columns):
                                column_len = max(df_show[col].astype(str).map(len).max(), len(col)) + 2
                                worksheet.set_column(i, i, column_len)
                        
                        file_label = f"Sugestao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
                        st.download_button(
                            label="📥 Baixar Excel",
                            data=buffer.getvalue(),
                            file_name=file_label,
                            mime="application/vnd.ms-excel"
                        )
                        
                except Exception as e:
                    st.error(f"Erro ao calcular: {e}")

# ==============================================================================
# TAB 2: CALCULAR ABC (Previously Tab 1)
# ==============================================================================
with tab2:
    with st.container():
        # Renamed Title
        st.markdown("### Classificação de produtos") 
        st.write("") # Spacer

        # Filters
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            today = datetime.now()
            start_default = today - timedelta(days=730)
            end_default = today
            # Changed Date Format and Bold Label
            start_date = st.date_input("**Data Inicial**", start_default, format="DD/MM/YYYY") 
        with col_filter2:
            # Changed Date Format and Bold Label
            end_date = st.date_input("**Data Final**", end_default, format="DD/MM/YYYY")
        
        st.write("")
        # Changed Option Order and Bold Label
        metric_option = st.radio(
            "**Critério de Cálculo**",
            ("Quantidade (Qtd)", "Valor Financeiro (R$)"), 
            horizontal=True
        )
        metric_col = 'VALOR_TOTAL' if metric_option == "Valor Financeiro (R$)" else 'QUANTIDADE_TOTAL'

        st.write("---")
        
        # Level Selection
        try:
            conn = get_connection()
            cursor = conn.cursor()
            levels_n1 = get_n1_levels(cursor)
            conn.close()
            
            # Format: Desc (Code), Sorted Alphabetically
            # levels_n1 is list of tuples (code, desc)
            # Create list of tuples for sorting: (desc, code)
            levels_sorted = sorted([(l[1], l[0]) for l in levels_n1], key=lambda x: x[0])
            
            # Map for Display -> ID
            level_options = {f"{desc} ({code})": code for desc, code in levels_sorted}
            
            # Changed Label to Bold, No default selection
            selected_level_label = st.selectbox(
                "**Selecione o Nível de Produto**",
                options=list(level_options.keys()),
                index=None,
                placeholder="Selecione..."
            )
            selected_level_id = level_options[selected_level_label] if selected_level_label else None
            
            # Show Last Processed Date
            if selected_level_id:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    last_run = get_last_processed(cursor, selected_level_id)
                    conn.close()
                    
                    if last_run:
                        st.caption(f"🕒 **Último processamento:** {last_run.strftime('%d/%m/%Y %H:%M:%S')}")
                    else:
                        st.caption("🕒 **Último processamento:** Nunca processado")
                except Exception as e:
                    st.caption(f"Erro ao carregar data: {e}")
            
        except Exception as e:
            st.error(f"Erro ao carregar níveis: {e}")
            selected_level_id = None
            
        st.write("")
        if st.button("🚀 Processar Curva ABC", type="primary", disabled=not selected_level_id):
            if not selected_level_id:
                st.warning("Selecione um nível válido.")
            else:
                status_text = st.empty()
                progress_bar = st.progress(0)
                
                try:
                    status_text.text("Conectando ao banco de dados...")
                    conn = get_connection()
                    
                    status_text.text(f"Processando para Nível {selected_level_id}...")
                    progress_bar.progress(30)
                    
                    s_date_str = start_date.strftime('%Y-%m-%d')
                    e_date_str = end_date.strftime('%Y-%m-%d')
                    
                    df_result = execute_abc_update(conn, selected_level_id, s_date_str, e_date_str, metric_type=metric_col)
                    progress_bar.progress(80)
                    
                    conn.close()
                    progress_bar.progress(100)
                    
                    if df_result.empty:
                        status_text.warning("Nenhum dado encontrado.")
                    else:
                        status_text.success(f"Sucesso! {len(df_result)} produtos atualizados.")
                        
                        # Metrics
                        c1, c2 = st.columns(2)
                        c1.metric("Total Produtos", len(df_result))
                        c1.metric("Total Analisado", f"{df_result[metric_col].sum():,.2f}")
                        
                        # Summary
                        summary = df_result.groupby('CLASSE').agg({
                            'CODIGO': 'count',
                            metric_col: 'sum'
                        }).rename(columns={'CODIGO': 'Qtd', metric_col: 'Total'})
                        
                        st.dataframe(summary)
                        
                        # Download
                        csv = df_result.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Baixar CSV", csv, "abc_result.csv", "text/csv")
                        
                except Exception as e:
                    st.error(f"Erro: {e}")

# ==============================================================================
# TAB 3: CONFIGURAÇÃO (Previously Tab 2)
# ==============================================================================
# ==============================================================================
# TAB 3: CONFIGURAÇÃO (Previously Tab 2)
# ==============================================================================
# ==============================================================================
# TAB 3: CONFIGURAÇÃO (Previously Tab 2)
# ==============================================================================
with tab3:
    with st.container():
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
            l_n2 = get_levels(cursor, "PRODUTOS_NIVEL2", n1_id)
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
            
            # Filters Area
            st.markdown("**Filtros:**")
            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
            
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
                use_container_width=True,
                hide_index=True,
                on_select="rerun", # Reruns script when selection changes
                selection_mode="single-row",
                key="rules_grid"
            )
        else:
            st.info("Nenhuma regra cadastrada.")
