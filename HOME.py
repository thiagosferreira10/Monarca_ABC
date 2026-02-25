import streamlit as st
import os
import time
import src_loader; src_loader.register()  # carrega src.* de __pycache__/ em producao
from src.ui_utils import apply_sidebar_style, force_sidebar_expansion, render_bottom_logout
from src.auth_logic import check_login

# Page Config
st.set_page_config(
    page_title="Monarca ERP - Suíte de Ferramentas",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Theme Overrides
apply_sidebar_style()
force_sidebar_expansion()

# --- Authentication State ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def login():
    st.session_state['authenticated'] = True
    st.rerun()

def logout():
    st.session_state['authenticated'] = False
    st.rerun()

# --- Login Logic ---
if not st.session_state['authenticated']:
    # Show Login Screen
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # Display Monarca Text (Reverted from Logo)
        # Remove extra break lines to save vertical space
        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <div style="background-color: #000080; padding: 20px; border-radius: 10px; margin-bottom: 5px; text-align: center;">
                <h1 style="color: white; margin: 0; padding: 0;">Monarca</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Inject CSS for Blue Button + Hide form instructions
        st.markdown(
            """
            <style>
            div[data-testid="stFormSubmitButton"] > button {
                background-color: #000080 !important;
                color: white !important;
                border: none !important;
            }
            div[data-testid="stFormSubmitButton"] > button:hover {
                background-color: #0000A0 !important;
                color: white !important;
            }
            /* Hide 'Press Enter to submit form' message */
            .stForm [data-testid="InputInstructions"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if submitted:
                user_id = check_login(username, password)
                if user_id is not None:
                    st.session_state['user_id'] = user_id
                    login()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
else:
    # --- Main Application (Logged In) ---
    
    # Sidebar Logout Button
    render_bottom_logout()

    # Display Logo centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("Logo.jpg", use_container_width=True)
