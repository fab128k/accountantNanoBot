# ui/pages/prima_nota.py
# AccountantNanoBot v1.0.0 - Pagina Prima Nota
# ============================================================================

import streamlit as st
from datetime import date, timedelta
from decimal import Decimal


def render_prima_nota():
    """Renderizza la pagina Prima Nota."""
    st.title("📒 Prima Nota")

    tab_lista, tab_fatture, tab_manuale = st.tabs([
        "📋 Registrazioni",
        "📄 Fatture da Processare",
        "✏️ Registrazione Manuale",
    ])

    with tab_lista:
        _render_lista_registrazioni()

    with tab_fatture:
        _render_fatture_da_processare()

    with tab_manuale:
        _render_registrazione_manuale()


def _render_lista_registrazioni():
    """Mostra tabella registrazioni con filtri."""
    from accounting.db import get_prima_nota, init_db, marca_registrazione_confermata
    from accounting.prima_nota import TipoRegistrazione

    init_db()

    st.subheader("Registrazioni di Prima Nota")

    # Filtri
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        data_da = st.date_input(
            "Da",
            value=date.today() - timedelta(days=90),
            key="pn_data_da",
        )
    with col2:
        data_a = st.date_input(
            "A",
            value=date.today(),
            key="pn_data_a",
        )
    with col3:
        tipo_filter = st.selectbox(
            "Tipo",
            options=["Tutti"] + [t.value for t in TipoRegistrazione],
            key="pn_tipo",
        )
    with col4:
        solo_confermate = st.checkbox("Solo confermate", key="pn_solo_conf")

    # Carica dati
    registrazioni = get_prima_nota(
        data_da=data_da,
        data_a=data_a,
        tipo=tipo_filter if tipo_filter != "Tutti" else None,
        solo_confermate=solo_confermate,
    )

    if not registrazioni:
        st.info("Nessuna registrazione trovata per i filtri selezionati.")
        return

    # Costruisci dataframe per visualizzazione
    import pandas as pd

    rows = []
    for reg in registrazioni:
        rows.append({
            "ID": reg["id"],
            "Data": reg["data"],
            "Tipo": reg["tipo"],
            "Descrizione": reg["descrizione"],
            "Fattura": reg.get("fattura_riferimento", ""),
            "Bilanciata": "✅" if reg["bilanciata"] else "❌",
            "Confermata": "✅" if reg["confermata"] else "⏳",
            "Da Agente": "🤖" if reg["creata_da_agente"] else "👤",
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Bilanciata": st.column_config.TextColumn(width="small"),
            "Confermata": st.column_config.TextColumn(width="small"),
            "Da Agente": st.column_config.TextColumn("Origine", width="small"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"Totale: {len(registrazioni)} registrazioni")

    # Dettaglio registrazione selezionata
    if registrazioni:
        st.divider()
        st.subheader("Dettaglio Registrazione")

        reg_ids = [r["id"] for r in registrazioni]
        selected_id = st.selectbox(
            "Seleziona registrazione",
            options=reg_ids,
            format_func=lambda x: next(
                (f"#{x} - {r['data']} - {r['descrizione'][:50]}"
                 for r in registrazioni if r["id"] == x), str(x)
            ),
            key="pn_selected_id",
        )

        selected_reg = next((r for r in registrazioni if r["id"] == selected_id), None)

        if selected_reg:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Data:** {selected_reg['data']}")
                st.markdown(f"**Tipo:** {selected_reg['tipo']}")
                st.markdown(f"**Descrizione:** {selected_reg['descrizione']}")
                if selected_reg.get("fattura_riferimento"):
                    st.markdown(f"**Fattura rif.:** {selected_reg['fattura_riferimento']}")
            with col2:
                st.markdown(f"**Bilanciata:** {'✅ Sì' if selected_reg['bilanciata'] else '❌ No'}")
                st.markdown(f"**Confermata:** {'✅ Sì' if selected_reg['confermata'] else '⏳ In attesa'}")
                st.markdown(f"**Origine:** {'🤖 Agente' if selected_reg['creata_da_agente'] else '👤 Manuale'}")

            # Righe dare/avere
            if selected_reg.get("righe"):
                righe_data = []
                for riga in selected_reg["righe"]:
                    righe_data.append({
                        "Conto": riga["conto_codice"],
                        "Nome Conto": riga["conto_nome"],
                        "Dare (€)": float(riga["dare"]) if riga["dare"] else 0,
                        "Avere (€)": float(riga["avere"]) if riga["avere"] else 0,
                        "Descrizione": riga.get("descrizione", ""),
                    })

                import pandas as pd
                df_righe = pd.DataFrame(righe_data)

                st.dataframe(
                    df_righe,
                    column_config={
                        "Dare (€)": st.column_config.NumberColumn(format="€%.2f"),
                        "Avere (€)": st.column_config.NumberColumn(format="€%.2f"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                totale_dare = sum(r["Dare (€)"] for r in righe_data)
                totale_avere = sum(r["Avere (€)"] for r in righe_data)

                col1, col2, col3 = st.columns(3)
                col1.metric("Totale Dare", f"€{totale_dare:.2f}")
                col2.metric("Totale Avere", f"€{totale_avere:.2f}")
                differenza = abs(totale_dare - totale_avere)
                col3.metric("Differenza", f"€{differenza:.2f}",
                           delta_color="inverse" if differenza > 0.01 else "normal")

            # Pulsante conferma
            if not selected_reg["confermata"]:
                if st.button("✅ Conferma Registrazione", type="primary", key=f"conf_{selected_id}"):
                    if marca_registrazione_confermata(selected_id):
                        st.success("✅ Registrazione confermata!")
                        st.rerun()
                    else:
                        st.error("❌ Errore nella conferma")

            # Export PDF (placeholder)
            if st.button("📥 Esporta PDF", key=f"pdf_{selected_id}"):
                st.info("Export PDF in sviluppo")


def _render_fatture_da_processare():
    """Mostra fatture importate non ancora registrate."""
    from accounting.db import get_fatture_importate, init_db

    init_db()

    st.subheader("Fatture da Processare")
    st.markdown("Fatture XML importate che non hanno ancora una registrazione contabile.")

    fatture = get_fatture_importate(processata=False)

    if not fatture:
        st.success("✅ Tutte le fatture sono state processate!")
        return

    import pandas as pd

    rows = []
    for f in fatture:
        rows.append({
            "ID": f["id"],
            "Numero": f["numero"],
            "Data": f["data"],
            "Fornitore": f["cedente_nome"],
            "Cliente": f["cessionario_nome"],
            "Tipo": f["tipo_documento"],
            "Totale (€)": float(f["importo_totale"]),
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        column_config={
            "Totale (€)": st.column_config.NumberColumn(format="€%.2f"),
            "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.warning(f"⚠️ {len(fatture)} fattura/e da processare. Vai alla sezione **Fatture** per registrarle.")


def _render_registrazione_manuale():
    """Form per inserimento manuale di una registrazione."""
    from accounting.prima_nota import TipoRegistrazione, RigaPrimaNota, RegistrazionePrimaNota
    from accounting.piano_dei_conti import cerca_conto
    from accounting.db import salva_registrazione, init_db

    init_db()

    st.subheader("Nuova Registrazione Manuale")
    st.markdown("Inserisci manualmente una registrazione in partita doppia.")

    with st.form("registrazione_manuale"):
        col1, col2 = st.columns(2)

        with col1:
            data_reg = st.date_input("Data *", value=date.today())
            tipo = st.selectbox(
                "Tipo *",
                options=[t.value for t in TipoRegistrazione],
                format_func=lambda x: TipoRegistrazione(x).descrizione,
            )
        with col2:
            descrizione = st.text_input("Descrizione *", placeholder="Es. Acquisto materiale ufficio")
            fattura_rif = st.text_input("Fattura riferimento", placeholder="Es. FT-2024-001")

        st.markdown("**Righe contabili** (almeno 2, dare = avere)")

        # Righe statiche (per semplicità - 4 righe)
        righe_data = []

        for i in range(4):
            cols = st.columns([2, 3, 2, 2, 3])
            with cols[0]:
                conto_cod = st.text_input(f"Conto {i+1}", key=f"conto_{i}", placeholder="Es. C.II.1")
            with cols[1]:
                conto_nome = st.text_input(f"Nome {i+1}", key=f"nome_{i}", placeholder="Es. Crediti vs clienti")
            with cols[2]:
                dare = st.number_input(f"Dare {i+1}", key=f"dare_{i}", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            with cols[3]:
                avere = st.number_input(f"Avere {i+1}", key=f"avere_{i}", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            with cols[4]:
                desc_riga = st.text_input(f"Desc. {i+1}", key=f"desc_{i}", placeholder="Descrizione riga")

            if conto_cod or dare > 0 or avere > 0:
                righe_data.append({
                    "conto_codice": conto_cod,
                    "conto_nome": conto_nome,
                    "dare": Decimal(str(dare)),
                    "avere": Decimal(str(avere)),
                    "descrizione": desc_riga,
                })

        submitted = st.form_submit_button("💾 Salva Registrazione", type="primary")

        if submitted:
            if not descrizione:
                st.error("❌ La descrizione è obbligatoria")
            elif len(righe_data) < 2:
                st.error("❌ Inserisci almeno 2 righe contabili")
            else:
                righe = [
                    RigaPrimaNota(
                        conto_codice=r["conto_codice"],
                        conto_nome=r["conto_nome"],
                        dare=r["dare"],
                        avere=r["avere"],
                        descrizione=r["descrizione"],
                    )
                    for r in righe_data
                ]

                reg = RegistrazionePrimaNota(
                    data=data_reg,
                    tipo=TipoRegistrazione(tipo),
                    descrizione=descrizione,
                    fattura_riferimento=fattura_rif,
                    righe=righe,
                    creata_da_agente=False,
                    confermata=True,  # Manuale = già confermata
                )

                valida, errori = reg.valida()

                if not valida:
                    for err in errori:
                        st.error(f"❌ {err}")
                else:
                    try:
                        reg_id = salva_registrazione(reg)
                        st.success(f"✅ Registrazione #{reg_id} salvata!")
                    except Exception as e:
                        st.error(f"❌ Errore salvataggio: {e}")

    # Helper ricerca conti
    st.divider()
    st.subheader("🔍 Ricerca Piano dei Conti")

    query_conto = st.text_input("Cerca conto", placeholder="Es. crediti clienti")
    if query_conto:
        results = cerca_conto(query_conto)
        if results:
            import pandas as pd
            df = pd.DataFrame([
                {"Codice": r["codice"], "Nome": r["nome"], "Sezione": r["sezione"], "D/A": r["dare_avere"]}
                for r in results
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun conto trovato")
