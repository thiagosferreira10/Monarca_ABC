import time
import streamlit as st
import streamlit.components.v1 as components

def force_sidebar_expansion():
    """
    Forces the sidebar to expand using JavaScript.
    Uses a unique key to ensure the script re-runs on every page load/navigation.
    """
    js = """
    <script>
        function expandSidebar() {
            try {
                // Nuclear Option: Clear Local Storage to remove "collapsed" preference
                // This forces Streamlit to read 'initial_sidebar_state="expanded"' from config
                window.localStorage.clear();
                
                const doc = window.parent.document;
                const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                
                if (sidebar && sidebar.getAttribute("aria-expanded") === "false") {
                    const btn = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button') ||
                                doc.querySelector('[data-testid="stSidebarCollapsedControl"]');
                    
                    if (btn) {
                        btn.click();
                    }
                }
            } catch (e) {
                console.log("Sidebar expansion error:", e);
            }
        }

        // Delay slightly to let Streamlit load preference, then Nuke it.
        setTimeout(expandSidebar, 500);
        setTimeout(expandSidebar, 1000);
        setTimeout(expandSidebar, 2000);
    </script>
    """
    # Embed timestamp in comments to force re-render (since 'key' arg is not supported in this version)
    components.html(js + f"<!-- force_reload_{time.time()} -->", height=0, width=0)

def apply_sidebar_style():
    """
    Injects CSS to force white text in the sidebar.
    This is necessary because we are mixing a Light Base theme with a Black Sidebar.
    """
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .stMarkdown, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] span {
            color: #FFFFFF !important;
        }
        /* Fix link colors in sidebar if any */
             color: #80bdff !important;
        }
        
        /* Force Input Fields to White Background & Black Text */
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"],
        input.st-bd,
        div[data-testid="stDateInput"] input,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input {
            background-color: #ffffff !important;
            color: #000000 !important;
            border-color: #d1d1d1;
        }
        
        /* Selectbox specific */
        div[data-baseweb="select"] > div {
             background-color: #ffffff !important;
             color: #000000 !important;
        }
        
        /* Dropdown options container */
        ul[data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Extra CSS specifically for Inputs
    st.markdown(
        """
        <style>
        /* Force ALL Inputs to White Background & Black Text (Aggressive) */
        /* Reduce Top Whitespace */
        .block-container {
             padding-top: 1rem !important; 
             padding-bottom: 1rem !important;
        }

        input, 
        input, 
        textarea, 
        select, 
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"],
        .stDateInput input,
        .stTextInput input,
        .stNumberInput input,
        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stNumberInput"] div[data-baseweb="input"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            caret-color: #000000 !important; 
        }
        
        /* Selectbox specific */
        div[data-baseweb="select"] > div {
             background-color: #ffffff !important;
             color: #000000 !important;
        }
        
        /* Calendar Popover */
        div[data-baseweb="calendar"] {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        
        /* Dropdown options container */
        ul[data-baseweb="menu"] {
            background-color: #ffffff !important;
        }

        /* Number Input Stepper Buttons (- +) */
        /* Target the spinbuttons inside NumberInput */
        div[data-testid="stNumberInput"] button {
            background-color: #000080 !important; /* Navy Blue */
            color: #ffffff !important;
            border-color: #000080 !important;
        }
        div[data-testid="stNumberInput"] button:hover {
            background-color: #0000A0 !important; /* Navigation hover color */
            color: #ffffff !important;
        }
        div[data-testid="stNumberInput"] button:active {
            color: #ffffff !important;
        }
        /* SVG Icon Fill */
        div[data-testid="stNumberInput"] button svg {
            fill: #ffffff !important;
        }
        
        /* Sidebar Navigation Items Background */
        [data-testid="stSidebarNav"] a {
            background-color: #000080 !important; /* Navy Blue */
            color: #FFFFFF !important; /* White Text */
            margin-bottom: 5px;
            border-radius: 5px;
            padding-left: 10px;
            font-weight: bold !important; /* Bold Text */
            transition: all 0.2s ease;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: #0000A0 !important; /* Lighter Navy on hover */
            color: #FFFFFF !important;
        }
        /* Active Item */
        [data-testid="stSidebarNav"] a[aria-current="page"] {
             background-color: #000060 !important; /* Darker Navy */
             border-left: 5px solid #FFFFFF !important; /* White Accent */
             color: #FFFFFF !important;
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
        [data-testid="stSidebar"] button:hover {
            background-color: #0000A0 !important;
            color: #FFFFFF !important;
        }
        
        /* Sidebar Buttons (Logout) */
        [data-testid="stSidebar"] button {
            background-color: #000080 !important; /* Navy Blue */
            color: #FFFFFF !important;
            border: none !important;
            width: 100%; /* Full width for consistency */
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #0000A0 !important;
            color: #FFFFFF !important;
        }
        
        /* HIDE DEFAULT STREAMLIT ELEMENTS - BUT KEEP SIDEBAR CONTROL VISIBLE */
        /* PERMANENTLY DISABLED To Ensure Sidebar Visibility */
        /* HIDE DEFAULT STREAMLIT ELEMENTS - BUT KEEP SIDEBAR CONTROL VISIBLE */
        /* PERMANENTLY DISABLED To Ensure Sidebar Visibility */
        .stDeployButton,
        .stAppDeployButton,
        [data-testid="stDeployButton"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
        }
        /* V8 FINAL: Additive Hiding Strategy */
        /* Do NOT hide the toolbar container or generic buttons, as that kills the arrow */
        
        [data-testid="stToolbar"] {
             opacity: 1 !important;
             pointer-events: auto !important;
             background-color: transparent !important;
             right: 0 !important;
        }
        
        /* Explicitly Hide Known Nuisances */
        
        /* 1. Deploy Button */
        [data-testid="stDeployButton"],
        .stDeployButton,
        .stAppDeployButton {
            display: none !important;
        }
        
        /* 2. Main Menu (Three Dots) */
        [data-testid="stMainMenu"],
        #MainMenu {
            display: none !important;
        }
        
        /* 3. Status Widget (Running Man) */
        [data-testid="stStatusWidget"] {
            display: none !important;
        }
        
        /* 4. Top Decoration (Rainbow Line) */
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* 5. Header Buttons (Generic fallback for 3 dots if ID fails) */
        button[kind="header"] {
             display: none !important;
        }
        
        /* 6. CRITICAL: Force Sidebar Toggle to be VISIBLE */
        /* This overrides rule #5 if the toggle uses kind="header" */
        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="stSidebarCollapsedControl"] {
             display: block !important;
             visibility: visible !important;
             z-index: 1000001 !important;
             opacity: 1 !important;
        }
        /* [data-testid="stToolbar"] {visibility: hidden;} */
        /* footer {visibility: hidden;} */
        /* #MainMenu {visibility: hidden;} */
        /* header[data-testid="stHeader"] {background-color: rgba(0,0,0,0);} */
        
        /* Force Sidebar Toggle Button to be Visible and Colored */
        [data-testid="stSidebarCollapsedControl"] {
            visibility: visible !important;
            display: block !important;
            color: #000080 !important; /* Navy Blue */
            background-color: transparent !important;
        }
        [data-testid="stSidebarCollapsedControl"] button {
             color: #000080 !important;
             background-color: transparent !important;
             border: none !important;
             box-shadow: none !important;
        }
        [data-testid="stSidebarCollapsedControl"] button:hover {
             background-color: #f0f2f6 !important;
             color: #000080 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_bottom_logout():
    """
    Renders the Logout button at the bottom of the sidebar.
    Handles authentication state and redirection.
    """
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        
    if st.session_state['authenticated']:
        with st.sidebar:
            # Spacer to push button to bottom (Adjusted to 50vh as per latest preference)
            st.markdown("<div style='height: 50vh;'></div>", unsafe_allow_html=True)
            if st.button("Sair", type="secondary"):
                st.session_state['authenticated'] = False
                st.rerun()
