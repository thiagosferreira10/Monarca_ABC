import streamlit as st
import pandas as pd
import time
import src_loader; src_loader.register()
from src.database import get_connection
from src.ui_utils import apply_sidebar_style, force_sidebar_expansion, render_bottom_logout
from src.schema_manager import check_and_update_schema
from src.auth_logic import check_permission

# --- Schema Migration ---
try:
    _conn = get_connection()
    check_and_update_schema(_conn)
    _conn.close()
except Exception as e:
    print(f"Schema check error: {e}")

# Apply Theme
apply_sidebar_style()
force_sidebar_expansion()

# Auth Guard
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Faça login para acessar esta página.")
    st.stop()

# Permission Guard: Administração (FERRAMENTAS ID=1)
user_id = st.session_state.get('user_id')
if not user_id or not check_permission(user_id, 1):
    st.error("⛔ Você não tem permissão para acessar o módulo Administrador.")
    st.stop()

render_bottom_logout()

# Custom CSS (same style as Sugestão de Compra)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .stApp {
        background-color: #ffffff;
    }
    
    h1, h2, h3 {
        color: #1d1d1f;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    .stButton > button {
        background-color: #000080;
        color: white;
        border-radius: 980px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #0000A0;
        transform: scale(1.02);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e5e5ea;
    }
    .stDataFrame th {
        color: #000080 !important;
    }
</style>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div style="background-color: #000080; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0; font-family: 'Inter', sans-serif; font-size: 2rem;">Sistema Monarca - Administrador</h1>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2 = st.tabs(["Ferramentas", "Permissões"])

# ==============================================================================
# TAB 1: FERRAMENTAS
# ==============================================================================
with tab1:
    st.markdown("### 🔧 Módulos e Ferramentas")
    
    conn = get_connection()
    df_ferramentas = pd.read_sql("SELECT ID, MODULO, DESCRICAO, OPCAO FROM FERRAMENTAS ORDER BY MODULO, OPCAO", conn)
    conn.close()
    
    if not df_ferramentas.empty:
        st.dataframe(
            df_ferramentas,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "MODULO": st.column_config.NumberColumn("Módulo", format="%d"),
                "DESCRICAO": st.column_config.TextColumn("Descrição"),
                "OPCAO": st.column_config.NumberColumn("Opção", format="%d"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma ferramenta cadastrada.")

# ==============================================================================
# TAB 2: PERMISSÕES
# ==============================================================================
with tab2:
    st.markdown("### 🔐 Permissões de Acesso")
    
    # --- Fetch lookup data ---
    conn = get_connection()
    
    # Ferramentas (for combobox)
    df_fer = pd.read_sql("SELECT ID, DESCRICAO FROM FERRAMENTAS ORDER BY DESCRICAO", conn)
    fer_opts = {row['DESCRICAO']: row['ID'] for _, row in df_fer.iterrows()}
    
    # Usuários (for combobox)
    df_usr = pd.read_sql("SELECT ID_USUARIO, NOME_USUARIO FROM USUARIO ORDER BY NOME_USUARIO", conn)
    usr_opts = {row['NOME_USUARIO']: row['ID_USUARIO'] for _, row in df_usr.iterrows()}
    
    conn.close()
    
    # --- Add Permission Form ---
    st.markdown("#### Adicionar Permissão")
    col_fer, col_usr, col_btn = st.columns([2, 2, 1])
    
    with col_fer:
        sel_fer_label = st.selectbox(
            "Módulo/Opção",
            options=["Selecione"] + list(fer_opts.keys()),
            key="perm_fer_sel"
        )
    
    with col_usr:
        sel_usr_label = st.selectbox(
            "Usuário",
            options=["Selecione"] + list(usr_opts.keys()),
            key="perm_usr_sel"
        )
    
    with col_btn:
        st.markdown("<div style='height: 29px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Adicionar", type="primary", use_container_width=True):
            if sel_fer_label == "Selecione" or sel_usr_label == "Selecione":
                st.error("Selecione Módulo/Opção e Usuário.")
            else:
                fer_id = fer_opts[sel_fer_label]
                usr_id = usr_opts[sel_usr_label]
                
                # Check if already exists
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM FERRAMENTAS_PERMISSAO WHERE FERRAMENTAS = ? AND USUARIO = ?",
                    (fer_id, usr_id)
                )
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    conn.close()
                    st.warning("Esta permissão já existe.")
                else:
                    cursor.execute(
                        "INSERT INTO FERRAMENTAS_PERMISSAO (FERRAMENTAS, USUARIO) VALUES (?, ?)",
                        (fer_id, usr_id)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Permissão adicionada!")
                    time.sleep(0.5)
                    st.rerun()
    
    st.markdown("---")
    
    # --- Filters ---
    st.markdown("#### Permissões Cadastradas")
    col_f_spacer, col_f1, col_f2 = st.columns([0.5, 4, 4])
    
    with col_f1:
        filter_fer = st.multiselect(
            "Filtrar Módulo/Opção",
            options=list(fer_opts.keys()),
            key="perm_filter_fer",
            placeholder="Todos"
        )
    
    with col_f2:
        filter_usr = st.multiselect(
            "Filtrar Usuário",
            options=list(usr_opts.keys()),
            key="perm_filter_usr",
            placeholder="Todos"
        )
    
    # --- Load Grid Data ---
    conn = get_connection()
    
    query = """
    SELECT 
        FP.FERRAMENTAS,
        F.DESCRICAO AS FERRAMENTA_DESC,
        FP.USUARIO,
        U.NOME_USUARIO
    FROM FERRAMENTAS_PERMISSAO FP
    LEFT JOIN FERRAMENTAS F ON F.ID = FP.FERRAMENTAS
    LEFT JOIN USUARIO U ON U.ID_USUARIO = FP.USUARIO
    ORDER BY U.NOME_USUARIO, F.DESCRICAO
    """
    
    try:
        df_perms = pd.read_sql(query, conn)
    except Exception:
        df_perms = pd.DataFrame()
    
    conn.close()
    
    # Apply filters
    if filter_fer:
        df_perms = df_perms[df_perms['FERRAMENTA_DESC'].isin(filter_fer)]
    if filter_usr:
        df_perms = df_perms[df_perms['NOME_USUARIO'].isin(filter_usr)]
    
    if not df_perms.empty:
        # CSS for compact grid rows
        st.markdown("""
        <style>
        /* Reduce vertical space between grid rows */
        [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
            margin-top: -1.2rem !important;
            margin-bottom: 0 !important;
            padding: 0 !important;
        }
        /* Compact checkbox containers */
        [data-testid="stCheckbox"] {
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stCheckbox"] > label {
            padding: 0 !important;
            min-height: 0 !important;
        }
        /* Compact markdown containers */
        [data-testid="column"] [data-testid="stMarkdown"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="column"] .stMarkdown p {
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Reduce element container padding */
        [data-testid="stElementContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Column headers
        hdr_chk, hdr_desc, hdr_user = st.columns([0.5, 4, 4])
        hdr_chk.markdown(" ")
        hdr_desc.markdown("**Módulo/Opção**")
        hdr_user.markdown("**Usuário**")
        st.markdown("<hr style='margin: 0 0 2px 0; border-color: #e5e5ea;'>", unsafe_allow_html=True)
        
        # Display with checkboxes and zebra striping
        selected = []
        for i, (idx, row) in enumerate(df_perms.iterrows()):
            bg = "#f0f2f6" if i % 2 == 0 else "#ffffff"
            col_chk, col_desc, col_user = st.columns([0.5, 4, 4])
            checked = col_chk.checkbox(" ", key=f"chk_perm_{row['FERRAMENTAS']}_{row['USUARIO']}", label_visibility="collapsed")
            if checked:
                selected.append((int(row['FERRAMENTAS']), int(row['USUARIO'])))
            col_desc.markdown(f"<div style='background-color:{bg}; padding: 4px 8px; border-radius: 4px;'>{row['FERRAMENTA_DESC']}</div>", unsafe_allow_html=True)
            col_user.markdown(f"<div style='background-color:{bg}; padding: 4px 8px; border-radius: 4px;'>{row['NOME_USUARIO']}</div>", unsafe_allow_html=True)
        
        # Delete selected button
        st.write("")
        if st.button(f"🗑️ Excluir Selecionados ({len(selected)})", disabled=len(selected) == 0):
            conn = get_connection()
            cursor = conn.cursor()
            for fer_id, usr_id in selected:
                cursor.execute(
                    "DELETE FROM FERRAMENTAS_PERMISSAO WHERE FERRAMENTAS = ? AND USUARIO = ?",
                    (fer_id, usr_id)
                )
            conn.commit()
            conn.close()
            st.success(f"{len(selected)} permissão(ões) removida(s)!")
            time.sleep(0.5)
            st.rerun()
    else:
        st.info("Nenhuma permissão cadastrada.")

