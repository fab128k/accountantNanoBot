# ui/pages/onboarding.py
# AccountantNanoBot v1.0.0 - Pagina Onboarding
# ============================================================================

import streamlit as st
from pathlib import Path


def render_onboarding():
    """Renderizza la pagina di onboarding (configurazione azienda + upload documenti)."""
    st.title("📋 Onboarding")
    st.markdown("Configura la tua azienda e carica i documenti per la knowledge base.")

    tab_azienda, tab_documenti = st.tabs(["🏢 Dati Azienda", "📄 Documenti RAG"])

    with tab_azienda:
        _render_company_form()

    with tab_documenti:
        _render_document_upload()


def _render_company_form():
    """Form per configurazione dati azienda."""
    from config.settings import load_company_config, save_company_config

    st.subheader("Dati Azienda")
    st.markdown("Inserisci i dati della tua azienda. Vengono usati per identificare automaticamente acquisti e vendite nelle fatture.")

    config = load_company_config()

    with st.form("company_form"):
        col1, col2 = st.columns(2)

        with col1:
            ragione_sociale = st.text_input(
                "Ragione Sociale *",
                value=config.get("ragione_sociale", ""),
                placeholder="Es. Mario Rossi S.r.l."
            )
            partita_iva = st.text_input(
                "Partita IVA *",
                value=config.get("partita_iva", ""),
                placeholder="Es. 12345678901",
                max_chars=11,
            )
            codice_fiscale = st.text_input(
                "Codice Fiscale",
                value=config.get("codice_fiscale", ""),
                placeholder="Es. RSSMRA80A01H501Z",
            )
            codice_sdi = st.text_input(
                "Codice SDI / PEC",
                value=config.get("codice_sdi", ""),
                placeholder="Es. ABCDEFG oppure pec@example.it",
            )

        with col2:
            indirizzo = st.text_input(
                "Indirizzo",
                value=config.get("indirizzo", ""),
                placeholder="Es. Via Roma 1",
            )
            col_cap, col_comune, col_prov = st.columns([2, 4, 1])
            with col_cap:
                cap = st.text_input("CAP", value=config.get("cap", ""), max_chars=5)
            with col_comune:
                comune = st.text_input("Comune", value=config.get("comune", ""))
            with col_prov:
                provincia = st.text_input("Prov.", value=config.get("provincia", ""), max_chars=2)

            regime_fiscale = st.selectbox(
                "Regime Fiscale",
                options=["RF01", "RF02", "RF04", "RF05", "RF10", "RF18", "RF19"],
                format_func=lambda x: {
                    "RF01": "RF01 - Ordinario",
                    "RF02": "RF02 - Contribuenti minimi (art.1 c.96-117 L.244/07)",
                    "RF04": "RF04 - Agricoltura e attività connesse",
                    "RF05": "RF05 - Vendita sali e tabacchi",
                    "RF10": "RF10 - Agriturismo",
                    "RF18": "RF18 - Altro",
                    "RF19": "RF19 - Regime forfettario",
                }.get(x, x),
                index=["RF01", "RF02", "RF04", "RF05", "RF10", "RF18", "RF19"].index(
                    config.get("regime_fiscale", "RF01")
                ) if config.get("regime_fiscale", "RF01") in ["RF01", "RF02", "RF04", "RF05", "RF10", "RF18", "RF19"] else 0,
            )

            settore = st.selectbox(
                "Settore",
                options=["commercio", "servizi", "produzione", "costruzioni", "professionisti", "altro"],
                index=["commercio", "servizi", "produzione", "costruzioni", "professionisti", "altro"].index(
                    config.get("settore", "commercio")
                ) if config.get("settore", "commercio") in ["commercio", "servizi", "produzione", "costruzioni", "professionisti", "altro"] else 0,
            )

        submitted = st.form_submit_button("💾 Salva Configurazione", type="primary")

        if submitted:
            if not ragione_sociale or not partita_iva:
                st.error("❌ Ragione sociale e Partita IVA sono obbligatori")
            else:
                new_config = {
                    **config,
                    "ragione_sociale": ragione_sociale,
                    "partita_iva": partita_iva,
                    "codice_fiscale": codice_fiscale,
                    "codice_sdi": codice_sdi,
                    "indirizzo": indirizzo,
                    "cap": cap,
                    "comune": comune,
                    "provincia": provincia,
                    "regime_fiscale": regime_fiscale,
                    "settore": settore,
                }
                if save_company_config(new_config):
                    st.success("✅ Configurazione salvata!")
                    st.rerun()
                else:
                    st.error("❌ Errore nel salvataggio. Verifica i permessi.")

    # Mostra stato attuale
    if config.get("ragione_sociale"):
        st.info(f"📊 Configurazione attuale: **{config['ragione_sociale']}** (P.IVA: {config.get('partita_iva', 'N/D')})")


def _render_document_upload():
    """Upload documenti per knowledge base RAG."""
    st.subheader("Carica Documenti")
    st.markdown("""
    Carica i documenti aziendali per la knowledge base RAG.
    L'agente Memoria potrà usarli per rispondere a domande specifiche.

    **Formati supportati:** PDF, DOCX, TXT, MD, XML (FatturaPA)
    """)

    kb_manager = st.session_state.get("kb_manager")

    # Upload widget
    uploaded_files = st.file_uploader(
        "Seleziona documenti",
        type=["pdf", "docx", "txt", "md", "xml"],
        accept_multiple_files=True,
        key="onboarding_upload",
        help="Puoi caricare più file contemporaneamente",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file selezionati:**")
        for f in uploaded_files:
            size_kb = len(f.read()) / 1024
            f.seek(0)
            st.markdown(f"- `{f.name}` ({size_kb:.1f} KB)")

        col1, col2 = st.columns(2)

        with col1:
            dest_dir = st.selectbox(
                "Cartella destinazione",
                options=["documenti", "fatture_xml"],
                format_func=lambda x: "📁 Documenti generali" if x == "documenti" else "📄 Fatture XML",
            )

        with col2:
            indicizza = st.checkbox("Indicizza subito nella KB", value=True)

        if st.button("📤 Carica File", type="primary"):
            from config.constants import DATA_DIR

            dest_path = DATA_DIR / dest_dir
            dest_path.mkdir(parents=True, exist_ok=True)

            saved = []
            for f in uploaded_files:
                file_path = dest_path / f.name
                with open(file_path, "wb") as out:
                    out.write(f.read())
                saved.append(str(file_path))

            st.success(f"✅ {len(saved)} file salvati in `data/{dest_dir}/`")

            if indicizza and kb_manager:
                with st.spinner("🔍 Indicizzazione in corso..."):
                    try:
                        kb_manager.index_documents(
                            folder_path=str(dest_path),
                            extensions=[".pdf", ".docx", ".txt", ".md", ".xml"],
                            recursive=False,
                        )
                        stats = kb_manager.get_stats()
                        st.success(
                            f"✅ Knowledge Base aggiornata: "
                            f"{stats.get('document_count', 0)} documenti, "
                            f"{stats.get('chunk_count', 0)} chunk"
                        )
                    except Exception as e:
                        st.error(f"❌ Errore indicizzazione: {e}")

    # Stato KB attuale
    st.divider()
    st.subheader("Stato Knowledge Base")

    if kb_manager and kb_manager.is_indexed():
        stats = kb_manager.get_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Documenti", stats.get("document_count", 0))
        col2.metric("Chunk", stats.get("chunk_count", 0))
        col3.metric("Dimensione", f"{stats.get('total_chars', 0):,} chars")

        if st.button("🔄 Reindicizza tutto"):
            from config.constants import DOCUMENTI_DIR, FATTURE_DIR
            with st.spinner("Reindicizzazione..."):
                try:
                    for folder in [DOCUMENTI_DIR, FATTURE_DIR]:
                        if folder.exists():
                            kb_manager.index_documents(
                                folder_path=str(folder),
                                extensions=[".pdf", ".docx", ".txt", ".md", ".xml"],
                                recursive=True,
                            )
                    st.success("✅ Reindicizzazione completata!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Errore: {e}")
    else:
        st.info("📚 Knowledge Base non ancora indicizzata. Carica dei documenti per iniziare.")
