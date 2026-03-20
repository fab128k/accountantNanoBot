# pipeline/pipeline_a.py
# Pipeline A — processes FatturaXML invoices and CSV bank statements.
# Consumes ScanResult from scanner/ and produces InvoiceResult + BankMovementResult
# objects for human review in the UI.
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from scanner.client_folder_scanner import ScanResult
    from parsers.fattura_pa import FatturaPA
    from accounting.prima_nota import RegistrazionePrimaNota
    from pipeline.csv_bank_parser import BankMovement


# ============================================================================
# RESULT DATACLASSES
# ============================================================================

@dataclass
class InvoiceResult:
    """Result of processing a single FatturaPA XML file."""
    path: Path
    xml_bytes: bytes = b""
    hash: str = ""
    status: str = ""       # "new" | "gia_importata" | "parse_error"
    fattura: Optional["FatturaPA"] = None
    registrazione: Optional["RegistrazionePrimaNota"] = None
    error_message: str = ""


@dataclass
class BankMovementResult:
    """Result of processing a single bank movement with CoA suggestion."""
    movement: Optional["BankMovement"] = None
    suggested_registrazione: Optional["RegistrazionePrimaNota"] = None
    coa_mapping: Dict[str, str] = field(default_factory=dict)
    csv_source: str = ""


@dataclass
class PipelineResult:
    """Aggregated results from PipelineA.process_folder()."""
    invoice_results: List[InvoiceResult] = field(default_factory=list)
    bank_results: List[BankMovementResult] = field(default_factory=list)


# ============================================================================
# PIPELINE A
# ============================================================================

class PipelineA:
    """
    Pipeline A — ingestion of FatturaXML invoices and CSV bank statements.

    process_folder() receives a ScanResult (from ClientFolderScanner) and:
    1. Processes each FatturaXML file into an InvoiceResult (new/gia_importata/parse_error)
    2. Processes each CSV file into BankMovementResult objects with CoA suggestions

    All results are returned for human review — nothing is persisted automatically.
    """

    def process_folder(
        self,
        scan_result: "ScanResult",
        company_piva: str = "",
        db_path: Optional[Path] = None,
    ) -> PipelineResult:
        """
        Process all FatturaXML and CSV files from a scanned client folder.

        Args:
            scan_result: ScanResult from ClientFolderScanner.scan()
            company_piva: P.IVA of the company (used to auto-determine acquisto/vendita).
                          Falls back to config/settings.py if empty.
            db_path: Optional path to SQLite DB. Uses default DB_PATH if None.
                     Useful for tests that need an isolated database.

        Returns:
            PipelineResult with invoice_results and bank_results lists.
        """
        # Local imports to avoid circular dependencies at module level
        from parsers.fattura_pa import FatturaPAParser
        from accounting.prima_nota import RegistrazionePrimaNota, RigaPrimaNota, TipoRegistrazione
        from pipeline.csv_bank_parser import BankStatementParser, BankMovement

        # DB imports — pass db_path through to support test isolation
        if db_path is not None:
            from accounting.db import calcola_hash_fattura
            def _fattura_gia_importata(xml_bytes: bytes) -> bool:
                from accounting.db import calcola_hash_fattura as _chf
                import sqlite3
                hash_val = _chf(xml_bytes)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                with sqlite3.connect(str(db_path)) as conn:
                    row = conn.execute(
                        "SELECT id FROM fatture_importate WHERE hash_file = ?", (hash_val,)
                    ).fetchone()
                    return row is not None

            def _get_iban_coa(iban: str) -> Dict[str, str]:
                from accounting.db import get_iban_coa_mapping as _gicm
                return _gicm(iban, db_path=db_path)
        else:
            from accounting.db import (
                calcola_hash_fattura,
                fattura_gia_importata as _fattura_gia_importata,
                get_iban_coa_mapping as _get_iban_coa,
            )

        from accounting.db import calcola_hash_fattura

        # Resolve company P.IVA — fallback to config if not provided
        if not company_piva:
            try:
                from config.settings import get_company_piva
                company_piva = get_company_piva()
            except Exception:
                company_piva = ""

        invoice_results: List[InvoiceResult] = []
        bank_results: List[BankMovementResult] = []

        # ------------------------------------------------------------------
        # 1. Process FatturaXML files
        # ------------------------------------------------------------------
        for path in scan_result.files.get("FatturaXML", []):
            try:
                xml_bytes = path.read_bytes()
                hash_val = calcola_hash_fattura(xml_bytes)

                # Deduplication check
                if _fattura_gia_importata(xml_bytes):
                    invoice_results.append(InvoiceResult(
                        path=path,
                        hash=hash_val,
                        status="gia_importata",
                    ))
                    continue

                # Parse XML
                parser = FatturaPAParser()
                fatture = parser.parse_bytes(xml_bytes)

                if not fatture:
                    invoice_results.append(InvoiceResult(
                        path=path,
                        xml_bytes=xml_bytes,
                        hash=hash_val,
                        status="parse_error",
                        error_message="Nessuna fattura trovata nel file",
                    ))
                    continue

                fattura = fatture[0]
                warning = (
                    f"Attenzione: file contiene {len(fatture)} fatture, elaborata solo la prima"
                    if len(fatture) > 1
                    else ""
                )

                suggestion = parser.to_prima_nota_suggestion(
                    fattura, is_acquisto=True, company_piva=company_piva
                )
                registrazione = RegistrazionePrimaNota.from_suggestion(suggestion)

                invoice_results.append(InvoiceResult(
                    path=path,
                    xml_bytes=xml_bytes,
                    hash=hash_val,
                    status="new",
                    fattura=fattura,
                    registrazione=registrazione,
                    error_message=warning,
                ))

            except Exception as e:
                hash_val = ""
                try:
                    xml_bytes = path.read_bytes()
                    hash_val = calcola_hash_fattura(xml_bytes)
                except Exception:
                    xml_bytes = b""
                invoice_results.append(InvoiceResult(
                    path=path,
                    xml_bytes=xml_bytes,
                    hash=hash_val,
                    status="parse_error",
                    error_message=str(e),
                ))

        # ------------------------------------------------------------------
        # 2. Process CSV bank statement files
        # ------------------------------------------------------------------
        for path in scan_result.files.get("CSV", []):
            try:
                bank_parser = BankStatementParser()
                movements = bank_parser.parse_csv(path)

                for movement in movements:
                    coa = _get_iban_coa(movement.iban)

                    # Build prima nota suggestion for bank movement
                    importo = movement.importo
                    if importo > 0:
                        # Income / receipt from customer
                        suggestion = {
                            "data": movement.data.isoformat(),
                            "tipo": TipoRegistrazione.INCASSO_CLIENTE.value,
                            "descrizione": f"Incasso: {movement.descrizione}",
                            "fattura_riferimento": "",
                            "righe": [
                                {
                                    "conto_codice": coa["conto_codice"],
                                    "conto_nome": coa["conto_nome"],
                                    "dare": float(importo),
                                    "avere": 0.0,
                                    "descrizione": movement.descrizione,
                                },
                                {
                                    "conto_codice": "C.II.1",
                                    "conto_nome": "Crediti verso clienti",
                                    "dare": 0.0,
                                    "avere": float(importo),
                                    "descrizione": movement.descrizione,
                                },
                            ],
                        }
                    elif importo < 0:
                        # Expense / payment to supplier
                        abs_importo = abs(importo)
                        suggestion = {
                            "data": movement.data.isoformat(),
                            "tipo": TipoRegistrazione.PAGAMENTO_FORNITORE.value,
                            "descrizione": f"Pagamento: {movement.descrizione}",
                            "fattura_riferimento": "",
                            "righe": [
                                {
                                    "conto_codice": "D.7",
                                    "conto_nome": "Debiti verso fornitori",
                                    "dare": float(abs_importo),
                                    "avere": 0.0,
                                    "descrizione": movement.descrizione,
                                },
                                {
                                    "conto_codice": coa["conto_codice"],
                                    "conto_nome": coa["conto_nome"],
                                    "dare": 0.0,
                                    "avere": float(abs_importo),
                                    "descrizione": movement.descrizione,
                                },
                            ],
                        }
                    else:
                        # Zero importo — generic entry
                        suggestion = {
                            "data": movement.data.isoformat(),
                            "tipo": TipoRegistrazione.GENERICO.value,
                            "descrizione": f"Movimento: {movement.descrizione}",
                            "fattura_riferimento": "",
                            "righe": [
                                {
                                    "conto_codice": coa["conto_codice"],
                                    "conto_nome": coa["conto_nome"],
                                    "dare": 0.0,
                                    "avere": 0.0,
                                    "descrizione": movement.descrizione,
                                },
                            ],
                        }

                    reg = RegistrazionePrimaNota.from_suggestion(suggestion)

                    bank_results.append(BankMovementResult(
                        movement=movement,
                        suggested_registrazione=reg,
                        coa_mapping=coa,
                        csv_source=path.name,
                    ))

            except Exception:
                # Skip malformed CSVs silently — pure library code, no logging
                continue

        return PipelineResult(
            invoice_results=invoice_results,
            bank_results=bank_results,
        )
