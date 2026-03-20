# ui/pages/scanner.py
# Scanner page renderer — displays classified file counts and file lists.
# Shows Pipeline A results (invoice review cards + bank movement review table)
# for human confirmation before persisting to SQLite.
# Zero scanner/ imports at module level — ScanResult accessed via session_state duck typing.
# ============================================================================

import streamlit as st


def render_scanner():
    """Render the Scanner page showing scan results from session_state."""
    st.title("Scanner Cartella Cliente")

    scan_result = st.session_state.get("scan_results")
    if scan_result is None:
        st.info("Nessuna scansione eseguita. Seleziona una cartella dalla barra laterale.")
        return

    # Summary metric cards — one per non-empty category
    categories_with_files = [
        (cat, scan_result.count(cat))
        for cat in ["FatturaXML", "PDF", "CSV", "DOCX", "TXT", "Altro"]
        if scan_result.count(cat) > 0
    ]
    if not categories_with_files:
        st.warning("Nessun file trovato nella cartella selezionata.")
        return

    cols = st.columns(len(categories_with_files))
    for col, (cat, count) in zip(cols, categories_with_files):
        col.metric(cat, count)

    st.caption(f"Totale: {scan_result.total()} file -- {scan_result.client_folder}")

    # -----------------------------------------------------------------------
    # CTA button for Pipeline A (invoices + CSV bank statements)
    # -----------------------------------------------------------------------
    n_fatture = scan_result.count("FatturaXML")
    n_csv = scan_result.count("CSV")
    n_processabili = n_fatture + n_csv

    if n_processabili > 0:
        label_parts = []
        if n_fatture > 0:
            label_parts.append(f"{n_fatture} fatture")
        if n_csv > 0:
            label_parts.append(f"{n_csv} estratti conto")
        label = f"Avvia elaborazione ({', '.join(label_parts)})"

        if st.button(label, type="primary", use_container_width=True):
            from pipeline.pipeline_a import PipelineA
            from config.settings import get_company_piva
            with st.spinner("Elaborazione in corso..."):
                pipeline = PipelineA()
                result = pipeline.process_folder(scan_result, get_company_piva())
                st.session_state["pipeline_a_results"] = result
            st.rerun()
    else:
        st.info("Nessun file elaborabile trovato (FatturaXML o CSV).")

    # -----------------------------------------------------------------------
    # Pipeline A results: invoice review cards + bank movement review table
    # -----------------------------------------------------------------------
    if st.session_state.get("pipeline_a_results") is not None:
        pipeline_result = st.session_state["pipeline_a_results"]

        st.subheader("Risultati Elaborazione")

        # -------------------------------------------------------------------
        # INVOICE REVIEW SECTION
        # -------------------------------------------------------------------
        invoice_results = pipeline_result.invoice_results

        if invoice_results:
            st.markdown(f"### Fatture ({len(invoice_results)})")

            n_new = sum(1 for r in invoice_results if r.status == "new")
            n_dup = sum(1 for r in invoice_results if r.status == "gia_importata")
            n_err = sum(1 for r in invoice_results if r.status == "parse_error")
            n_confirmed = sum(1 for r in invoice_results if r.status == "confermata")

            cols = st.columns(4)
            cols[0].metric("Nuove", n_new)
            cols[1].metric("Gia importate", n_dup)
            cols[2].metric("Errori", n_err)
            cols[3].metric("Confermate", n_confirmed)

            for i, r in enumerate(invoice_results):
                if r.status == "gia_importata":
                    st.caption(f"Gia importata: {r.path.name}")

                elif r.status == "parse_error":
                    with st.expander(f"Errore: {r.path.name}", expanded=False):
                        st.error(r.error_message or "Errore di parsing sconosciuto")

                elif r.status == "confermata":
                    st.caption(f"Confermata: {r.path.name}")

                elif r.status == "scartata":
                    st.caption(f"Scartata: {r.path.name}")

                elif r.status == "new" and r.fattura is not None and r.registrazione is not None:
                    header = (
                        f"{r.fattura.cedente.nome_completo} -- "
                        f"Fatt. {r.fattura.numero} -- "
                        f"{r.fattura.data} -- "
                        f"EUR {r.fattura.importo_totale:.2f}"
                    )
                    with st.expander(header, expanded=True):
                        if r.registrazione.righe:
                            import pandas as pd
                            df = pd.DataFrame([
                                {
                                    "Conto": riga.conto_codice,
                                    "Nome": riga.conto_nome,
                                    "Dare": float(riga.dare),
                                    "Avere": float(riga.avere),
                                }
                                for riga in r.registrazione.righe
                            ])
                            st.dataframe(df, use_container_width=True, hide_index=True)

                        st.metric("Bilanciata", "Si" if r.registrazione.is_bilanciata else "No")

                        if r.error_message:
                            st.warning(r.error_message)

                        col1, col2 = st.columns(2)
                        if col1.button(
                            "Conferma e Salva",
                            key=f"confirm_inv_{i}",
                            type="primary",
                            disabled=not r.registrazione.is_bilanciata,
                        ):
                            from accounting.db import salva_fattura_importata, salva_registrazione
                            r.registrazione.confermata = True
                            salva_fattura_importata(r.fattura, r.xml_bytes, str(r.path))
                            salva_registrazione(r.registrazione)
                            r.status = "confermata"
                            st.rerun()

                        if col2.button("Scarta", key=f"discard_inv_{i}"):
                            r.status = "scartata"
                            st.rerun()

            # Batch confirm button
            if n_new > 0:
                if st.button("Conferma tutto (solo bilanciate)", key="confirm_all_inv"):
                    from accounting.db import salva_fattura_importata, salva_registrazione
                    for r in invoice_results:
                        if r.status == "new" and r.registrazione is not None and r.registrazione.is_bilanciata:
                            r.registrazione.confermata = True
                            salva_fattura_importata(r.fattura, r.xml_bytes, str(r.path))
                            salva_registrazione(r.registrazione)
                            r.status = "confermata"
                    st.rerun()

        # -------------------------------------------------------------------
        # BANK MOVEMENT REVIEW SECTION
        # -------------------------------------------------------------------
        if pipeline_result.bank_results:
            bank_results = pipeline_result.bank_results

            st.markdown(f"### Movimenti Bancari ({len(bank_results)})")

            from decimal import Decimal
            total_income = sum(
                r.movement.importo for r in bank_results
                if r.movement.importo > 0
            )
            total_expense = sum(
                r.movement.importo for r in bank_results
                if r.movement.importo < 0
            )
            n_bank_confirmed = sum(
                1 for r in bank_results
                if getattr(r, "_confirmed", False)
            )

            cols = st.columns(3)
            cols[0].metric("Entrate", f"EUR {float(total_income):.2f}")
            cols[1].metric("Uscite", f"EUR {abs(float(total_expense)):.2f}")
            cols[2].metric("Netto", f"EUR {float(total_income + total_expense):.2f}")

            for i, r in enumerate(bank_results):
                if getattr(r, "_confirmed", False):
                    st.caption(
                        f"Confermato: {r.movement.data} | "
                        f"{r.movement.descrizione[:40]} | "
                        f"EUR {float(r.movement.importo):.2f}"
                    )
                    continue

                label = (
                    f"{r.movement.data} | "
                    f"{r.movement.descrizione[:50]} | "
                    f"EUR {float(r.movement.importo):.2f}"
                )
                with st.expander(label, expanded=False):
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**Data:** {r.movement.data}")
                    if r.movement.data_valuta:
                        col1.markdown(f"**Data valuta:** {r.movement.data_valuta}")
                    col1.markdown(f"**Importo:** EUR {float(r.movement.importo):.2f}")
                    if r.movement.saldo is not None:
                        col1.markdown(f"**Saldo:** EUR {float(r.movement.saldo):.2f}")
                    col2.markdown(f"**IBAN:** {r.movement.iban or 'N/D'}")
                    col2.markdown(f"**Fonte CSV:** {r.csv_source}")
                    col2.markdown(f"**Descrizione:** {r.movement.descrizione}")

                    if r.suggested_registrazione and r.suggested_registrazione.righe:
                        import pandas as pd
                        df_bank = pd.DataFrame([
                            {
                                "Conto": riga.conto_codice,
                                "Nome": riga.conto_nome,
                                "Dare": float(riga.dare),
                                "Avere": float(riga.avere),
                            }
                            for riga in r.suggested_registrazione.righe
                        ])
                        st.dataframe(df_bank, use_container_width=True, hide_index=True)

                    # CoA correction selectbox
                    from accounting.piano_dei_conti import get_conti_comuni
                    conti_comuni = get_conti_comuni()
                    coa_options = []
                    for cat_conti in conti_comuni.values():
                        for c in cat_conti:
                            if c is not None:
                                coa_options.append(f"{c['codice']} - {c['nome']}")

                    current_codice = r.coa_mapping.get("conto_codice", "C.IV.1")
                    current_nome = r.coa_mapping.get("conto_nome", "Depositi bancari e postali")
                    current_label = f"{current_codice} - {current_nome}"
                    default_idx = 0
                    if current_label in coa_options:
                        default_idx = coa_options.index(current_label)

                    st.selectbox(
                        "Conto CoA suggerito",
                        options=coa_options,
                        index=default_idx,
                        key=f"coa_select_{i}",
                    )

                    btn_col1, btn_col2 = st.columns(2)
                    if btn_col1.button("Conferma", key=f"confirm_bank_{i}", type="primary"):
                        from accounting.db import salva_registrazione, salva_movimento_bancario
                        if r.suggested_registrazione:
                            r.suggested_registrazione.confermata = True
                            salva_registrazione(r.suggested_registrazione)
                        salva_movimento_bancario({
                            "data": r.movement.data.isoformat(),
                            "data_valuta": (
                                r.movement.data_valuta.isoformat()
                                if r.movement.data_valuta else None
                            ),
                            "descrizione": r.movement.descrizione,
                            "importo": float(r.movement.importo),
                            "saldo": (
                                float(r.movement.saldo)
                                if r.movement.saldo is not None else None
                            ),
                            "iban": r.movement.iban,
                            "confermato": True,
                        })
                        r._confirmed = True
                        st.rerun()

                    if btn_col2.button("Salta", key=f"skip_bank_{i}"):
                        r._skipped = True
                        st.rerun()

            # Batch confirm for bank movements
            unconfirmed_bank = [
                r for r in bank_results
                if not getattr(r, "_confirmed", False)
                and not getattr(r, "_skipped", False)
            ]
            if unconfirmed_bank:
                if st.button("Conferma tutti i movimenti", key="confirm_all_bank"):
                    from accounting.db import salva_registrazione, salva_movimento_bancario
                    for r in unconfirmed_bank:
                        if r.suggested_registrazione:
                            r.suggested_registrazione.confermata = True
                            salva_registrazione(r.suggested_registrazione)
                        salva_movimento_bancario({
                            "data": r.movement.data.isoformat(),
                            "data_valuta": (
                                r.movement.data_valuta.isoformat()
                                if r.movement.data_valuta else None
                            ),
                            "descrizione": r.movement.descrizione,
                            "importo": float(r.movement.importo),
                            "saldo": (
                                float(r.movement.saldo)
                                if r.movement.saldo is not None else None
                            ),
                            "iban": r.movement.iban,
                            "confermato": True,
                        })
                        r._confirmed = True
                    st.rerun()

    st.divider()

    # -----------------------------------------------------------------------
    # File list expanders — FatturaXML opens by default, others collapsed
    # -----------------------------------------------------------------------
    for cat in ["FatturaXML", "PDF", "CSV", "DOCX", "TXT", "Altro"]:
        files = scan_result.files.get(cat, [])
        if not files:
            continue
        with st.expander(f"{cat} ({len(files)})", expanded=(cat == "FatturaXML")):
            for f in files:
                try:
                    size_kb = f.stat().st_size / 1024
                except OSError:
                    size_kb = 0.0
                try:
                    rel = f.relative_to(scan_result.client_folder)
                except ValueError:
                    rel = f
                st.text(f"{f.name}  |  {size_kb:.1f} KB  |  {rel.parent}")
