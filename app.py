# app.py
# AccountantNanoBot v1.0.0 - Router multipagina
# ============================================================================
# Sistema multi-agente per contabilità italiana
# ============================================================================

import streamlit as st

# ============================================================================
# PAGE CONFIG (deve essere prima di tutto)
# ============================================================================

st.set_page_config(
    page_title="AccountantNanoBot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# IMPORTS
# ============================================================================

from config import (
    APP_TITLE,
    APP_ICON,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K_RESULTS,
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
)
from core.llm_client import get_local_ollama_models
from ui.style import inject_style

# ============================================================================
# TEMA
# ============================================================================

inject_style()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Inizializza tutte le variabili di sessione necessarie."""
    from rag import KnowledgeBaseManager

    defaults = {
        # Core
        "current_page": "dashboard",
        "current_model": DEFAULT_MODEL,
        "models_local": [],
        # RAG
        "kb_manager": KnowledgeBaseManager(),
        "use_knowledge_base": False,
        "kb_folder_path": "",
        "kb_extensions": [".md", ".txt", ".pdf", ".xml"],
        "kb_recursive": True,
        "kb_chunk_size": DEFAULT_CHUNK_SIZE,
        "kb_chunk_overlap": DEFAULT_CHUNK_OVERLAP,
        "rag_top_k": DEFAULT_TOP_K_RESULTS,
        # Agenti
        "orchestrator": None,
        "ollama_base_url": OLLAMA_BASE_URL,
        # UI state
        "dashboard_messages": [],
        # Scanner
        "scan_results": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize client_folder_path once per session from persisted config.
    # client_folder_path is used directly as the widget key — single source of truth.
    if "client_folder_path" not in st.session_state:
        from config.settings import load_company_config
        cfg = load_company_config()
        st.session_state["client_folder_path"] = cfg.get("client_folder_path", "")


initialize_session_state()


# ============================================================================
# INIZIALIZZAZIONE AGENTI (lazy, solo quando necessario)
# ============================================================================

def ensure_orchestrator():
    """Inizializza l'orchestratore agenti se non già fatto."""
    if st.session_state.get("orchestrator") is None:
        try:
            from agents.orchestrator import build_default_orchestrator
            from config.settings import load_company_config

            config = load_company_config()
            model = st.session_state.get("current_model", DEFAULT_MODEL)
            base_url = st.session_state.get("ollama_base_url", OLLAMA_BASE_URL)

            orchestrator = build_default_orchestrator(
                models={agent_id: model for agent_id in
                       ["fatturazione", "iva", "bilancio", "compliance", "prima_nota", "memoria"]},
                base_url=base_url,
            )

            # Inietta RAG manager
            kb_manager = st.session_state.get("kb_manager")
            if kb_manager:
                orchestrator.set_rag_manager(kb_manager)

            st.session_state["orchestrator"] = orchestrator
        except Exception as e:
            pass  # Agenti non disponibili - OK, verranno richiesti più tardi


# ============================================================================
# PAGINA FATTURE
# ============================================================================

def _render_fatture_page():
    """Pagina Fatture - upload e analisi XML FatturaPA."""
    from config.settings import load_company_config
    from accounting.db import (
        init_db, salva_fattura_importata, fattura_gia_importata,
        salva_registrazione, get_fatture_importate
    )

    init_db()

    st.title("📄 Fatture")

    tab_import, tab_lista = st.tabs(["📤 Importa Fattura", "📋 Fatture Importate"])

    with tab_import:
        st.subheader("Importa FatturaPA XML")

        config = load_company_config()
        company_piva = config.get("partita_iva", "")

        if not company_piva:
            st.warning("⚠️ P.IVA azienda non configurata. Vai alla sezione **Configurazione** prima.")

        uploaded_xml = st.file_uploader(
            "Carica file XML FatturaPA",
            type=["xml"],
            key="fattura_upload",
            help="Formato FatturaPA v1.2 (FPR12 o FPA12)",
        )

        if uploaded_xml:
            xml_bytes = uploaded_xml.read()

            # Controlla duplicato
            if fattura_gia_importata(xml_bytes):
                st.warning("⚠️ Questa fattura è già stata importata in precedenza.")
            else:
                st.success(f"✅ File caricato: `{uploaded_xml.name}` ({len(xml_bytes):,} bytes)")

                # Preview rapida
                try:
                    from parsers.fattura_pa import FatturaPAParser
                    parser = FatturaPAParser()
                    fatture = parser.parse_bytes(xml_bytes)

                    if fatture:
                        fattura = fatture[0]

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Numero", fattura.numero)
                        col2.metric("Data", str(fattura.data))
                        col3.metric("Totale", f"€{fattura.importo_totale:.2f}")

                        st.markdown(f"**Fornitore:** {fattura.cedente.nome_completo} (P.IVA: {fattura.cedente.partita_iva})")
                        st.markdown(f"**Cliente:** {fattura.cessionario.nome_completo} (P.IVA: {fattura.cessionario.partita_iva})")
                        st.markdown(f"**Tipo:** {fattura.descrizione_tipo} ({fattura.tipo_documento})")

                        st.divider()

                        # Analisi agente
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button("🤖 Genera Registrazione", type="primary"):
                                orchestrator = st.session_state.get("orchestrator")
                                if orchestrator:
                                    agent = orchestrator.get_agent("fatturazione")
                                    if agent:
                                        # Operazione deterministica — veloce, niente LLM
                                        ft, reg, _ = agent.analizza_xml_bytes(
                                            xml_bytes, company_piva
                                        )
                                        if reg:
                                            st.session_state["_current_fattura"] = fattura
                                            st.session_state["_current_registrazione"] = reg
                                            st.session_state["_current_xml_bytes"] = xml_bytes
                                            st.session_state["_current_xml_name"] = uploaded_xml.name
                                            st.session_state.pop("_llm_analysis", None)
                                            st.rerun()
                                    else:
                                        st.error("❌ Agente fatturazione non disponibile")
                                else:
                                    st.error("❌ Agenti non inizializzati")

                        with col2:
                            if st.button("💾 Importa senza analisi"):
                                from config.constants import FATTURE_DIR
                                FATTURE_DIR.mkdir(parents=True, exist_ok=True)
                                xml_path = FATTURE_DIR / uploaded_xml.name
                                with open(xml_path, "wb") as f:
                                    f.write(xml_bytes)

                                salva_fattura_importata(fattura, xml_bytes, str(xml_path))
                                st.success(f"✅ Fattura importata. Analizzala dalla Prima Nota.")

                except Exception as e:
                    st.error(f"❌ Errore parsing: {e}")

        # Mostra risultato analisi se presente
        if st.session_state.get("_current_registrazione"):
            st.divider()
            st.subheader("Suggerimento Registrazione")

            reg = st.session_state["_current_registrazione"]

            # Riepilogo registrazione
            st.markdown(f"**{reg.tipo.descrizione}** — {reg.data} — {reg.descrizione}")

            if reg.righe:
                import pandas as pd
                df_righe = pd.DataFrame([
                    {
                        "Conto": r.conto_codice,
                        "Nome": r.conto_nome,
                        "Dare (€)": float(r.dare),
                        "Avere (€)": float(r.avere),
                    }
                    for r in reg.righe
                ])
                st.dataframe(df_righe, use_container_width=True, hide_index=True)

                col1, col2, col3 = st.columns(3)
                col1.metric("Totale Dare", f"€{reg.totale_dare:.2f}")
                col2.metric("Totale Avere", f"€{reg.totale_avere:.2f}")
                col3.metric(
                    "Stato",
                    "✅ Bilanciata" if reg.is_bilanciata else f"❌ Diff: €{reg.differenza:.2f}"
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Conferma e Salva", type="primary", disabled=not reg.is_bilanciata):
                    from config.constants import FATTURE_DIR
                    fattura = st.session_state.get("_current_fattura")
                    xml_bytes_saved = st.session_state.get("_current_xml_bytes", b"")
                    xml_name = st.session_state.get("_current_xml_name", "fattura.xml")

                    # Salva fattura
                    FATTURE_DIR.mkdir(parents=True, exist_ok=True)
                    xml_path = FATTURE_DIR / xml_name
                    with open(xml_path, "wb") as f:
                        f.write(xml_bytes_saved)

                    if fattura:
                        salva_fattura_importata(fattura, xml_bytes_saved, str(xml_path))

                    # Salva registrazione confermata
                    reg.confermata = True
                    reg_id = salva_registrazione(reg)

                    # Pulisci session state
                    for key in ["_current_fattura", "_current_registrazione",
                                "_current_xml_bytes", "_current_xml_name", "_llm_analysis"]:
                        st.session_state.pop(key, None)

                    st.success(f"✅ Registrazione #{reg_id} salvata e confermata!")
                    st.rerun()

            with col2:
                if st.button("🔄 Rigenera"):
                    orchestrator = st.session_state.get("orchestrator")
                    if orchestrator:
                        agent = orchestrator.get_agent("fatturazione")
                        if agent:
                            xml_bytes_regen = st.session_state.get("_current_xml_bytes", b"")
                            ft, new_reg, _ = agent.analizza_xml_bytes(
                                xml_bytes_regen, company_piva
                            )
                            if new_reg:
                                st.session_state["_current_registrazione"] = new_reg
                                st.session_state.pop("_llm_analysis", None)
                                st.rerun()

            with col3:
                if st.button("❌ Scarta"):
                    for key in ["_current_fattura", "_current_registrazione",
                                "_current_xml_bytes", "_current_xml_name", "_llm_analysis"]:
                        st.session_state.pop(key, None)
                    st.rerun()

            # Commento LLM in streaming — opzionale, on-demand
            st.divider()
            with st.expander("💬 Commento dell'Agente (LLM)", expanded=False):
                llm_msg = st.session_state.get("_llm_analysis", "")
                if llm_msg:
                    st.markdown(llm_msg)
                else:
                    st.caption("Il commento LLM viene generato on-demand e non blocca l'interfaccia.")
                    if st.button("🤖 Chiedi all'Agente", key="btn_llm_commento"):
                        orchestrator = st.session_state.get("orchestrator")
                        if orchestrator:
                            agent = orchestrator.get_agent("fatturazione")
                            if agent:
                                xml_bytes_for_llm = st.session_state.get("_current_xml_bytes", b"")
                                response_placeholder = st.empty()
                                full_response = ""
                                try:
                                    for chunk in agent.stream_commento_fattura(xml_bytes_for_llm, company_piva):
                                        chunk_text = getattr(chunk, "text", str(chunk))
                                        if chunk_text:
                                            full_response = chunk_text
                                            response_placeholder.markdown(full_response + "▌")
                                    response_placeholder.markdown(full_response)
                                    st.session_state["_llm_analysis"] = full_response
                                except Exception as e:
                                    st.error(f"❌ Errore LLM: {e}")
                            else:
                                st.error("❌ Agente fatturazione non disponibile")
                        else:
                            st.warning("⚠️ Agenti non inizializzati")

    with tab_lista:
        import pandas as pd

        fatture = get_fatture_importate()

        if not fatture:
            st.info("Nessuna fattura importata ancora.")
        else:
            df = pd.DataFrame([
                {
                    "ID": f["id"],
                    "Numero": f["numero"],
                    "Data": f["data"],
                    "Fornitore": f["cedente_nome"],
                    "P.IVA Fornitore": f["cedente_piva"],
                    "Tipo": f["tipo_documento"],
                    "Totale (€)": float(f["importo_totale"]),
                    "Processata": "✅" if f["processata"] else "⏳",
                }
                for f in fatture
            ])

            st.dataframe(
                df,
                column_config={
                    "Totale (€)": st.column_config.NumberColumn(format="€%.2f"),
                    "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                },
                use_container_width=True,
                hide_index=True,
            )


# ============================================================================
# SIDEBAR - NAVIGAZIONE E CONFIGURAZIONE
# ============================================================================

with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.markdown("---")

    # Navigazione
    st.markdown("### Navigazione")

    pages = {
        "dashboard": ("🏠", "Dashboard"),
        "onboarding": ("⚙️", "Configurazione"),
        "scanner": ("📁", "Scanner"),
        "fatture": ("📄", "Fatture"),
        "prima_nota": ("📒", "Prima Nota"),
        "bilancio": ("📊", "Bilancio"),
    }

    for page_id, (icon, label) in pages.items():
        if st.button(
            f"{icon} {label}",
            key=f"nav_{page_id}",
            use_container_width=True,
            type="primary" if st.session_state.get("current_page") == page_id else "secondary",
        ):
            st.session_state["current_page"] = page_id
            st.rerun()

    st.markdown("---")
    st.markdown("### Cartella Cliente")
    folder_input = st.text_input(
        "Percorso cartella",
        placeholder="/home/user/clienti/rossi_srl",
        key="client_folder_path",
        label_visibility="collapsed",
    )
    if st.button("Scansiona", use_container_width=True, type="primary"):
        from pathlib import Path
        from config.settings import load_company_config, save_company_config
        from scanner.client_folder_scanner import ClientFolderScanner

        # Persist to config.yaml (widget already updated session_state["client_folder_path"])
        cfg = load_company_config()
        cfg["client_folder_path"] = folder_input
        save_company_config(cfg)
        # Run scan
        scanner = ClientFolderScanner()
        result = scanner.scan(Path(folder_input))
        st.session_state["scan_results"] = result
        st.session_state["current_page"] = "scanner"
        st.rerun()

    st.markdown("---")

    # Configurazione Ollama
    with st.expander("🔧 Configurazione LLM", expanded=False):
        # Refresh modelli
        if st.button("🔄 Aggiorna modelli", use_container_width=True):
            with st.spinner("Caricamento..."):
                models = get_local_ollama_models()
                st.session_state["models_local"] = models
                st.session_state["orchestrator"] = None  # Reset per reinizializzare

        models_list = st.session_state.get("models_local", [])

        if models_list:
            current_model = st.selectbox(
                "Modello",
                options=models_list,
                index=models_list.index(st.session_state.get("current_model", models_list[0]))
                if st.session_state.get("current_model") in models_list else 0,
                key="model_selector",
            )
            if current_model != st.session_state.get("current_model"):
                st.session_state["current_model"] = current_model
                st.session_state["orchestrator"] = None  # Reset per nuovo modello
        else:
            st.text_input(
                "Modello (manuale)",
                value=st.session_state.get("current_model", DEFAULT_MODEL),
                key="model_manual",
            )
            if st.session_state.get("model_manual"):
                st.session_state["current_model"] = st.session_state["model_manual"]

        ollama_url = st.text_input(
            "URL Ollama",
            value=st.session_state.get("ollama_base_url", OLLAMA_BASE_URL),
            key="ollama_url_input",
        )
        if ollama_url != st.session_state.get("ollama_base_url"):
            st.session_state["ollama_base_url"] = ollama_url
            st.session_state["orchestrator"] = None

    # Status connessione
    st.markdown("---")
    models_available = bool(st.session_state.get("models_local"))
    if models_available:
        st.success(f"✅ Ollama connesso ({len(st.session_state['models_local'])} modelli)")
    else:
        st.warning("⚠️ Ollama non rilevato")
        if st.button("Connetti", use_container_width=True):
            with st.spinner("Connessione..."):
                models = get_local_ollama_models()
                if models:
                    st.session_state["models_local"] = models
                    st.rerun()
                else:
                    st.error("❌ Ollama non raggiungibile su localhost:11434")

    # Stato KB
    kb_manager = st.session_state.get("kb_manager")
    if kb_manager and kb_manager.is_indexed():
        stats = kb_manager.get_stats()
        st.info(f"📚 KB: {stats.get('document_count', 0)} doc, {stats.get('chunk_count', 0)} chunk")

    st.markdown("---")
    st.caption("AccountantNanoBot v1.0.0")
    st.caption("🔒 100% locale - Privacy garantita")


# ============================================================================
# ASSICURA ORCHESTRATORE
# ============================================================================

ensure_orchestrator()

# ============================================================================
# ROUTING PAGINE
# ============================================================================

current_page = st.session_state.get("current_page", "dashboard")

if current_page == "dashboard":
    from ui.pages.dashboard import render_dashboard
    render_dashboard()

elif current_page == "onboarding":
    from ui.pages.onboarding import render_onboarding
    render_onboarding()

elif current_page == "scanner":
    from ui.pages.scanner import render_scanner
    render_scanner()

elif current_page == "fatture":
    _render_fatture_page()

elif current_page == "prima_nota":
    from ui.pages.prima_nota import render_prima_nota
    render_prima_nota()

elif current_page == "bilancio":
    st.title("📊 Bilancio")
    st.info("🚧 Sezione in sviluppo. Sarà disponibile nella prossima versione.")

else:
    from ui.pages.dashboard import render_dashboard
    render_dashboard()
