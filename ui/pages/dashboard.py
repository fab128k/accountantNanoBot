# ui/pages/dashboard.py
# AccountantNanoBot v1.0.0 - Pagina Dashboard principale
# ============================================================================

import streamlit as st
from datetime import datetime


def render_dashboard():
    """Renderizza la dashboard principale con statistiche e chat agenti."""
    from config.settings import load_company_config

    config = load_company_config()
    company_name = config.get("ragione_sociale", "Azienda")

    st.title(f"📊 Dashboard — {company_name}")

    _render_stats()

    st.divider()

    _render_agent_chat()


def _render_stats():
    """Mostra statistiche rapide dal database."""
    try:
        from accounting.db import get_statistiche, init_db
        init_db()
        stats = get_statistiche()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Fatture Importate",
            stats["n_fatture_importate"],
            help="Totale fatture XML importate nel sistema"
        )
        col2.metric(
            "Da Processare",
            stats["n_fatture_da_processare"],
            delta=f"-{stats['n_fatture_da_processare']}" if stats["n_fatture_da_processare"] > 0 else None,
            delta_color="inverse",
            help="Fatture importate ma non ancora registrate"
        )
        col3.metric(
            "Registrazioni",
            stats["n_registrazioni"],
            help="Totale registrazioni in prima nota"
        )
        col4.metric(
            "Da Confermare",
            stats["n_registrazioni_non_confermate"],
            delta=f"-{stats['n_registrazioni_non_confermate']}" if stats["n_registrazioni_non_confermate"] > 0 else None,
            delta_color="inverse",
            help="Registrazioni generate dagli agenti in attesa di review"
        )

        if stats["n_fatture_da_processare"] > 0:
            st.warning(
                f"⚠️ Hai {stats['n_fatture_da_processare']} fattura/e da processare. "
                f"Vai alla sezione **Fatture** per registrarle."
            )

        if stats["n_registrazioni_non_confermate"] > 0:
            st.info(
                f"📝 {stats['n_registrazioni_non_confermate']} registrazione/i in attesa di conferma. "
                f"Vai alla **Prima Nota** per reviewarle."
            )

    except Exception as e:
        st.warning(f"Statistiche non disponibili: {e}")


def _render_agent_chat():
    """Area chat con gli agenti."""
    st.subheader("🤖 Chat con gli Agenti")

    # Selector agente
    orchestrator = st.session_state.get("orchestrator")

    if orchestrator is None:
        st.warning("⚠️ Agenti non inizializzati. Verifica la connessione Ollama.")
        return

    agents_list = orchestrator.list_agents()

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_agent_id = st.selectbox(
            "Seleziona agente",
            options=list(agents_list.keys()),
            format_func=lambda x: f"🤖 {agents_list[x]}",
            key="dashboard_agent_select",
        )
    with col2:
        routing_mode = st.checkbox("Auto-routing", value=True, key="auto_routing",
                                    help="Seleziona automaticamente l'agente più adatto")

    # Chat history
    if "dashboard_messages" not in st.session_state:
        st.session_state.dashboard_messages = []

    # Display messages
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.dashboard_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("agent"):
                    st.caption(f"🤖 {msg['agent']}")

    # Input
    user_input = st.chat_input("Scrivi un messaggio all'agente...")

    if user_input:
        # Aggiungi messaggio utente
        st.session_state.dashboard_messages.append({
            "role": "user",
            "content": user_input,
        })

        # Determina agente
        if routing_mode:
            agent_id, agent = orchestrator.route(user_input)
        else:
            agent_id = selected_agent_id
            agent = orchestrator.get_agent(agent_id)

        if agent:
            # Genera risposta con streaming
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""

                try:
                    for chunk in agent.stream_ask(user_input):
                        chunk_text = getattr(chunk, "text", str(chunk))
                        if chunk_text:
                            # chunk.text è cumulativo — mostra solo il nuovo testo
                            full_response = chunk_text
                            response_placeholder.markdown(full_response + "▌")

                    response_placeholder.markdown(full_response)
                    st.caption(f"🤖 {agents_list.get(agent_id, agent.name)}")

                except Exception as e:
                    full_response = f"❌ Errore: {e}"
                    response_placeholder.error(full_response)

            # Salva risposta
            st.session_state.dashboard_messages.append({
                "role": "assistant",
                "content": full_response,
                "agent": agents_list.get(agent_id, agent.name),
            })

        st.rerun()

    # Pulsante cancella chat
    if st.session_state.dashboard_messages:
        if st.button("🗑️ Cancella chat", key="clear_dashboard_chat"):
            st.session_state.dashboard_messages = []
            st.rerun()
