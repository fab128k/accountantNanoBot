# ui/pages/scanner.py
# Scanner page renderer — displays classified file counts and file lists.
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

    # CTA button for Pipeline A
    n_fatture = scan_result.count("FatturaXML")
    if n_fatture > 0:
        if st.button(
            f"Avvia elaborazione ({n_fatture} fatture)",
            type="primary",
            use_container_width=True,
        ):
            from pipeline.pipeline_a import PipelineA
            try:
                PipelineA().process_folder(scan_result.client_folder)
            except NotImplementedError as e:
                st.warning(f"Pipeline A non ancora implementata (Phase 4). {e}")
    else:
        st.info("Nessun file FatturaXML trovato. Pipeline A non disponibile.")

    st.divider()

    # Expanders per category — FatturaXML opens by default, others collapsed
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
