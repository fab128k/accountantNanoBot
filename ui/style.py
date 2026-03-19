# ui/style.py
# AccountantNanoBot v1.0.0 - Tema professionale per commercialisti
# ============================================================================


def inject_style() -> None:
    """Inietta il tema professionale nell'app Streamlit."""
    _inject_css()


inject_matrix_style = inject_style


def _inject_css() -> None:
    import streamlit as st

    st.markdown("""<style>

    /* =====================================================================
       TESTO PRINCIPALE — forza colore scuro su tutto il body principale
    ===================================================================== */
    .stApp, .stApp p, .stApp span, .stApp div,
    .stApp label, .stApp li, .stApp td, .stApp th,
    [data-testid="stMarkdown"], [data-testid="stMarkdown"] *,
    [data-testid="stText"], [data-testid="stCaption"],
    .stMarkdown, .stMarkdown p, .stMarkdown span {
      color: #0d1b2a !important;
    }

    /* Titoli */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
      color: #0d2137 !important;
      font-weight: 700 !important;
    }
    h1 { border-bottom: 3px solid #1a5fa8; padding-bottom: 0.4rem; }

    /* Sfondo app */
    .stApp { background: #f0f4f8 !important; }
    .block-container { padding-top: 1.5rem !important; max-width: 1200px !important; }

    /* =====================================================================
       SIDEBAR — sfondo bianco, testo scuro
    ===================================================================== */
    [data-testid="stSidebar"] {
      background: #1e3a5f !important;
      border-right: 2px solid #0d2137 !important;
    }

    /* Tutto il testo nella sidebar: bianco ad alta leggibilità */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown * {
      color: #ffffff !important;
    }

    /* Caption/muted nella sidebar */
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
      color: #c0d4ea !important;
    }

    /* Bottoni nella sidebar: outline bianco */
    [data-testid="stSidebar"] .stButton > button {
      border: 1px solid rgba(255,255,255,0.5) !important;
      color: #ffffff !important;
      background: rgba(255,255,255,0.08) !important;
      font-weight: 500 !important;
      border-radius: 6px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
      background: rgba(255,255,255,0.18) !important;
      border-color: rgba(255,255,255,0.8) !important;
    }
    /* Bottone primario nella sidebar: bianco pieno */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
      background: rgba(255,255,255,0.22) !important;
      border: 2px solid #ffffff !important;
      font-weight: 700 !important;
    }

    /* Input nella sidebar — sfondo chiaro per massimo contrasto con il testo */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] select {
      background: rgba(255,255,255,0.92) !important;
      color: #0d1b2a !important;
      border-color: rgba(255,255,255,0.6) !important;
      border-radius: 4px !important;
    }
    /* Placeholder del text_input nella sidebar */
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
      color: #5a7a9a !important;
      opacity: 1 !important;
    }

    /* Success/info/warning nella sidebar */
    [data-testid="stSidebar"] .stAlert {
      color: #0d1b2a !important;
    }

    /* =====================================================================
       BOTTONI PRINCIPALI (area contenuto)
    ===================================================================== */
    .stButton > button {
      border: 1px solid #1a5fa8 !important;
      color: #1a5fa8 !important;
      background: #ffffff !important;
      border-radius: 6px !important;
      font-weight: 500 !important;
      transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
      background: #e8f0fb !important;
      border-color: #0d2137 !important;
      color: #0d2137 !important;
    }
    .stButton > button[kind="primary"] {
      background: #1a5fa8 !important;
      color: #ffffff !important;
      border: none !important;
      font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
      background: #0d2137 !important;
    }

    /* =====================================================================
       INPUT / FORM
    ===================================================================== */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
      background: #ffffff !important;
      color: #0d1b2a !important;
      border: 1px solid #9ab3cc !important;
      border-radius: 6px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
      border-color: #1a5fa8 !important;
      box-shadow: 0 0 0 3px rgba(26,95,168,0.15) !important;
    }
    /* Label dei form */
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stNumberInput label, .stDateInput label, .stCheckbox label,
    .stRadio label {
      color: #0d1b2a !important;
      font-weight: 600 !important;
    }

    /* =====================================================================
       METRICHE
    ===================================================================== */
    [data-testid="stMetric"] {
      background: #ffffff !important;
      border: 1px solid #c8d8e8 !important;
      border-radius: 8px !important;
      padding: 1rem !important;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
    }
    [data-testid="stMetricLabel"] p { color: #3a5a78 !important; font-size: 0.85rem !important; }
    [data-testid="stMetricValue"]  { color: #0d2137 !important; font-weight: 800 !important; font-size: 1.8rem !important; }

    /* =====================================================================
       TABELLE / DATAFRAME
    ===================================================================== */
    [data-testid="stDataFrame"] { border: 1px solid #c8d8e8 !important; border-radius: 8px !important; }
    [data-testid="stDataFrame"] th { background: #1e3a5f !important; color: #ffffff !important; }
    [data-testid="stDataFrame"] td { color: #0d1b2a !important; }

    /* =====================================================================
       CHAT
    ===================================================================== */
    [data-testid="stChatMessage"] {
      background: #ffffff !important;
      border: 1px solid #c8d8e8 !important;
      border-radius: 8px !important;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span {
      color: #0d1b2a !important;
    }

    /* =====================================================================
       TAB
    ===================================================================== */
    [data-testid="stTabs"] [data-baseweb="tab"] {
      color: #3a5a78 !important;
      font-weight: 500 !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
      color: #0d2137 !important;
      font-weight: 700 !important;
      border-bottom: 2px solid #1a5fa8 !important;
    }

    /* =====================================================================
       ALERT / BANNER
    ===================================================================== */
    .stAlert p, .stAlert span, .stAlert div { color: inherit !important; }
    [data-testid="stNotification"] { color: #0d1b2a !important; }

    /* =====================================================================
       EXPANDER
    ===================================================================== */
    [data-testid="stExpander"] summary,
    .streamlit-expanderHeader { color: #0d2137 !important; font-weight: 600 !important; }

    /* =====================================================================
       RADIO BUTTON
    ===================================================================== */
    .stRadio > div {
      background: transparent !important;
    }
    .stRadio label, .stRadio span, .stRadio p,
    [data-testid="stWidgetLabel"] {
      color: #0d1b2a !important;
    }
    /* Nella sidebar: testo bianco */
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stRadio span,
    [data-testid="stSidebar"] .stRadio p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
      color: #ffffff !important;
    }
    /* Cerchio radio selezionato */
    [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] div {
      border-color: #ffffff !important;
    }

    /* =====================================================================
       SELECTBOX / DROPDOWN
    ===================================================================== */
    /* Contenitore selectbox */
    [data-baseweb="select"] {
      background: #ffffff !important;
    }
    [data-baseweb="select"] > div {
      background: #ffffff !important;
      border: 1px solid #9ab3cc !important;
      border-radius: 6px !important;
    }
    /* Testo valore selezionato */
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
      color: #0d1b2a !important;
      background: transparent !important;
    }
    /* Icona freccia */
    [data-baseweb="select"] svg { fill: #1a5fa8 !important; }

    /* Dropdown aperto (lista opzioni) */
    [data-baseweb="popover"] {
      background: #ffffff !important;
    }
    [data-baseweb="menu"] {
      background: #ffffff !important;
      border: 1px solid #c8d8e8 !important;
      border-radius: 6px !important;
    }
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] ul,
    [data-baseweb="option"] {
      background: #ffffff !important;
      color: #0d1b2a !important;
    }
    [data-baseweb="option"]:hover {
      background: #e8f0fb !important;
      color: #0d2137 !important;
    }

    /* Selectbox nella sidebar */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
      background: rgba(255,255,255,0.12) !important;
      border-color: rgba(255,255,255,0.3) !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div {
      color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #ffffff !important; }

    /* =====================================================================
       FILE UPLOADER
    ===================================================================== */
    [data-testid="stFileUploader"] {
      background: #ffffff !important;
      border: 2px dashed #9ab3cc !important;
      border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] section {
      background: #ffffff !important;
    }
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] div,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] label {
      color: #0d1b2a !important;
      background: transparent !important;
    }
    [data-testid="stFileUploader"] button {
      background: #ffffff !important;
      color: #1a5fa8 !important;
      border: 1px solid #1a5fa8 !important;
      border-radius: 6px !important;
    }
    [data-testid="stFileUploaderDropzone"] {
      background: #f0f4f8 !important;
      border-color: #9ab3cc !important;
    }
    [data-testid="stFileUploaderDropzone"] p,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] div {
      color: #0d1b2a !important;
    }
    /* File già caricati — badge */
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
      background: #e8f0fb !important;
      border: 1px solid #c8d8e8 !important;
      border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] * {
      color: #0d1b2a !important;
    }

    /* =====================================================================
       SCROLLBAR
    ===================================================================== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #e8f0f8; }
    ::-webkit-scrollbar-thumb { background: #1a5fa8; border-radius: 3px; }

    </style>""", unsafe_allow_html=True)
