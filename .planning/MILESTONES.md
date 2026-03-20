# Milestones

## v1.0 MVP (Shipped: 2026-03-20)

**Phases completed:** 4 phases, 8 plans, 0 tasks

**Key accomplishments:**
- Rimossi LangChain, SQLAlchemy, PyPDF2 — stack pulito con openai SDK nativo e sqlite3 nativo
- ChromaDB configurato con multilingual MiniLM (paraphrase-multilingual-MiniLM-L12-v2) per embedding italiani
- ProcessingContext dataclass + BaseSwarmAgent ABC — fondamenta architettura swarm
- Agenti esistenti migrati a BaseSwarmAgent; route_with_context() aggiunto all'Orchestrator
- ClientFolderScanner con classificazione 6 categorie (FatturaXML, PDF, CSV, DOCX, TXT, Altro)
- Scanner UI integrata in Streamlit: sidebar folder selector, pagina Scanner, metriche file
- PipelineA.process_folder() — ingestion fatture XML + estratti conto CSV con 47 test
- Invoice review cards + bank movement table con human-in-the-loop confirmation in Scanner UI

---

