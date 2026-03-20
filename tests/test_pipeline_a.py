# tests/test_pipeline_a.py
# TDD tests for Pipeline A: PIPE-01 (invoice processing) and PIPE-02 (deduplication)
# DB schema tests for PIPE-04 (IBAN-CoA mapping + movimenti_bancari table)
# ============================================================================

import sqlite3
import pytest
from pathlib import Path
from decimal import Decimal


# ---------------------------------------------------------------------------
# Minimal valid FatturaPA XML bytes for use in tests
# ---------------------------------------------------------------------------

MINIMAL_FATTURA_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<FatturaElettronica versione="FPR12" xmlns="urn:www.agenziaentrate.gov.it:specificheTecniche:sdi:fatturapa:v1.2">
  <FatturaElettronicaHeader>
    <DatiTrasmissione>
      <ProgressivoInvio>00001</ProgressivoInvio>
      <FormatoTrasmissione>FPR12</FormatoTrasmissione>
    </DatiTrasmissione>
    <CedentePrestatore>
      <DatiAnagrafici>
        <IdFiscaleIVA>
          <IdPaese>IT</IdPaese>
          <IdCodice>12345678901</IdCodice>
        </IdFiscaleIVA>
        <Anagrafica>
          <Denominazione>Fornitore SRL</Denominazione>
        </Anagrafica>
        <RegimeFiscale>RF01</RegimeFiscale>
      </DatiAnagrafici>
      <Sede>
        <Indirizzo>Via Roma 1</Indirizzo>
        <CAP>00100</CAP>
        <Comune>Roma</Comune>
        <Provincia>RM</Provincia>
        <Nazione>IT</Nazione>
      </Sede>
    </CedentePrestatore>
    <CessionarioCommittente>
      <DatiAnagrafici>
        <IdFiscaleIVA>
          <IdPaese>IT</IdPaese>
          <IdCodice>09876543210</IdCodice>
        </IdFiscaleIVA>
        <Anagrafica>
          <Denominazione>Cliente SRL</Denominazione>
        </Anagrafica>
      </DatiAnagrafici>
      <Sede>
        <Indirizzo>Via Milano 2</Indirizzo>
        <CAP>20100</CAP>
        <Comune>Milano</Comune>
        <Provincia>MI</Provincia>
        <Nazione>IT</Nazione>
      </Sede>
    </CessionarioCommittente>
  </FatturaElettronicaHeader>
  <FatturaElettronicaBody>
    <DatiGenerali>
      <DatiGeneraliDocumento>
        <TipoDocumento>TD01</TipoDocumento>
        <Divisa>EUR</Divisa>
        <Data>2026-01-15</Data>
        <Numero>FT/2026/001</Numero>
        <ImportoTotaleDocumento>122.00</ImportoTotaleDocumento>
      </DatiGeneraliDocumento>
    </DatiGenerali>
    <DatiBeniServizi>
      <DettaglioLinee>
        <NumeroLinea>1</NumeroLinea>
        <Descrizione>Servizio consulenza</Descrizione>
        <Quantita>1.00</Quantita>
        <PrezzoUnitario>100.00</PrezzoUnitario>
        <PrezzoTotale>100.00</PrezzoTotale>
        <AliquotaIVA>22.00</AliquotaIVA>
      </DettaglioLinee>
      <DatiRiepilogo>
        <AliquotaIVA>22.00</AliquotaIVA>
        <ImponibileImporto>100.00</ImponibileImporto>
        <Imposta>22.00</Imposta>
        <EsigibilitaIVA>I</EsigibilitaIVA>
      </DatiRiepilogo>
    </DatiBeniServizi>
  </FatturaElettronicaBody>
</FatturaElettronica>
"""

MALFORMED_XML = b"<this is not valid xml>"


# ---------------------------------------------------------------------------
# TestDBSchema — verifies new tables created by init_db()
# ---------------------------------------------------------------------------

class TestDBSchema:
    """Verifies that init_db() creates iban_coa_mapping and movimenti_bancari tables."""

    def test_iban_coa_mapping_table_created(self, tmp_path):
        from accounting.db import init_db
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='iban_coa_mapping'"
        )
        assert cursor.fetchone() is not None, "Table iban_coa_mapping should exist"
        conn.close()

    def test_iban_coa_mapping_columns(self, tmp_path):
        from accounting.db import init_db
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA table_info(iban_coa_mapping)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected = {"id", "iban", "conto_codice", "conto_nome", "note", "created_at"}
        assert expected == columns

    def test_movimenti_bancari_table_created(self, tmp_path):
        from accounting.db import init_db
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='movimenti_bancari'"
        )
        assert cursor.fetchone() is not None, "Table movimenti_bancari should exist"
        conn.close()

    def test_movimenti_bancari_columns(self, tmp_path):
        from accounting.db import init_db
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA table_info(movimenti_bancari)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "id", "data", "data_valuta", "descrizione", "importo", "saldo",
            "iban", "hash_file", "confermato", "registrazione_id", "created_at"
        }
        assert expected == columns


# ---------------------------------------------------------------------------
# TestIBANMapping — tests get_iban_coa_mapping and save_iban_coa_mapping
# ---------------------------------------------------------------------------

class TestIBANMapping:
    """Tests for IBAN-to-CoA mapping CRUD."""

    def test_get_returns_default_when_no_mapping(self, tmp_path):
        from accounting.db import get_iban_coa_mapping
        db_path = tmp_path / "test.db"
        result = get_iban_coa_mapping("IT60X0542811101000000123456", db_path=db_path)
        assert result["conto_codice"] == "C.IV.1"
        assert result["conto_nome"] == "Depositi bancari e postali"

    def test_get_returns_default_for_empty_iban(self, tmp_path):
        from accounting.db import get_iban_coa_mapping
        db_path = tmp_path / "test.db"
        result = get_iban_coa_mapping("", db_path=db_path)
        assert result["conto_codice"] == "C.IV.1"

    def test_save_then_get_returns_saved_mapping(self, tmp_path):
        from accounting.db import get_iban_coa_mapping, save_iban_coa_mapping
        db_path = tmp_path / "test.db"
        iban = "IT60X0542811101000000123456"

        row_id = save_iban_coa_mapping(iban, "C.IV.3", "Denaro e valori in cassa", db_path=db_path)
        assert row_id is not None and row_id > 0

        result = get_iban_coa_mapping(iban, db_path=db_path)
        assert result["conto_codice"] == "C.IV.3"
        assert result["conto_nome"] == "Denaro e valori in cassa"

    def test_save_upsert_updates_existing_mapping(self, tmp_path):
        from accounting.db import get_iban_coa_mapping, save_iban_coa_mapping
        db_path = tmp_path / "test.db"
        iban = "IT60X0542811101000000999999"

        save_iban_coa_mapping(iban, "C.IV.1", "Depositi bancari e postali", db_path=db_path)
        save_iban_coa_mapping(iban, "C.IV.3", "Denaro e valori in cassa", db_path=db_path)

        result = get_iban_coa_mapping(iban, db_path=db_path)
        assert result["conto_codice"] == "C.IV.3"


# ---------------------------------------------------------------------------
# TestBankMovementSave — tests salva_movimento_bancario
# ---------------------------------------------------------------------------

class TestBankMovementSave:
    """Tests for salva_movimento_bancario."""

    def test_save_returns_positive_id(self, tmp_path):
        from accounting.db import salva_movimento_bancario
        db_path = tmp_path / "test.db"
        movement = {
            "data": "2026-01-15",
            "data_valuta": "2026-01-15",
            "descrizione": "Pagamento fornitore XYZ",
            "importo": -500.00,
            "saldo": 10000.00,
            "iban": "IT60X0542811101000000123456",
            "hash_file": "abc123",
            "confermato": False,
        }
        row_id = salva_movimento_bancario(movement, db_path=db_path)
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_save_persists_data(self, tmp_path):
        from accounting.db import salva_movimento_bancario, init_db
        import sqlite3
        db_path = tmp_path / "test.db"
        movement = {
            "data": "2026-02-20",
            "descrizione": "Incasso cliente ABC",
            "importo": 1220.00,
            "saldo": 15000.00,
            "iban": "IT60X0542811101000000123456",
            "hash_file": "def456",
        }
        salva_movimento_bancario(movement, db_path=db_path)

        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT * FROM movimenti_bancari WHERE hash_file = 'def456'"
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[3] == "Incasso cliente ABC"  # descrizione column

    def test_save_handles_none_saldo(self, tmp_path):
        from accounting.db import salva_movimento_bancario
        db_path = tmp_path / "test.db"
        movement = {
            "data": "2026-03-01",
            "descrizione": "Test saldo None",
            "importo": -100.00,
        }
        row_id = salva_movimento_bancario(movement, db_path=db_path)
        assert row_id > 0


# ---------------------------------------------------------------------------
# TestInvoicePipeline — tests PipelineA.process_folder invoice processing (PIPE-01)
# These initially FAIL (RED) — will pass after Task 3 implements PipelineA.
# ---------------------------------------------------------------------------

class TestInvoicePipeline:
    """Tests for PipelineA.process_folder invoice processing (PIPE-01)."""

    def _make_scan_result(self, tmp_path, xml_files=None, csv_files=None):
        from scanner.client_folder_scanner import ScanResult
        from pathlib import Path
        result = ScanResult(client_folder=tmp_path)
        if xml_files:
            result.files["FatturaXML"] = xml_files
        if csv_files:
            result.files["CSV"] = csv_files
        return result

    def test_process_folder_returns_pipeline_result(self, tmp_path):
        from pipeline.pipeline_a import PipelineA, PipelineResult

        xml_file = tmp_path / "fattura.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="09876543210")

        assert isinstance(result, PipelineResult)

    def test_process_folder_returns_invoice_result_per_xml_file(self, tmp_path):
        from pipeline.pipeline_a import PipelineA, InvoiceResult

        xml_file = tmp_path / "fattura.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="09876543210")

        assert len(result.invoice_results) == 1
        assert isinstance(result.invoice_results[0], InvoiceResult)

    def test_new_invoice_has_status_new(self, tmp_path):
        from pipeline.pipeline_a import PipelineA

        xml_file = tmp_path / "fattura.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="09876543210")

        invoice = result.invoice_results[0]
        assert invoice.status == "new"

    def test_new_invoice_has_fattura_and_registrazione(self, tmp_path):
        from pipeline.pipeline_a import PipelineA

        xml_file = tmp_path / "fattura.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="09876543210")

        invoice = result.invoice_results[0]
        assert invoice.fattura is not None
        assert invoice.registrazione is not None

    def test_new_invoice_registrazione_is_bilanciata(self, tmp_path):
        from pipeline.pipeline_a import PipelineA

        xml_file = tmp_path / "fattura.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="09876543210")

        invoice = result.invoice_results[0]
        assert invoice.registrazione.is_bilanciata is True

    def test_parse_error_has_status_parse_error(self, tmp_path):
        from pipeline.pipeline_a import PipelineA

        xml_file = tmp_path / "malformed.xml"
        xml_file.write_bytes(MALFORMED_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="")

        invoice = result.invoice_results[0]
        assert invoice.status == "parse_error"
        assert invoice.error_message != ""

    def test_empty_scan_result_returns_empty_pipeline_result(self, tmp_path):
        from pipeline.pipeline_a import PipelineA

        scan_result = self._make_scan_result(tmp_path)
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="")

        assert result.invoice_results == []
        assert result.bank_results == []

    def test_process_folder_returns_bank_results_for_csv_files(self, tmp_path):
        from pipeline.pipeline_a import PipelineA, BankMovementResult

        csv_file = tmp_path / "estratto.csv"
        # Minimal Italian bank CSV with semicolons
        csv_content = (
            "Data;Data valuta;Descrizione;Accrediti;Addebiti;Saldo\n"
            "15/01/2026;15/01/2026;Incasso cliente;1220,00;;15000,00\n"
            "20/01/2026;20/01/2026;Pagamento fornitore;;500,00;14500,00\n"
        )
        csv_file.write_text(csv_content, encoding="utf-8")

        scan_result = self._make_scan_result(tmp_path, csv_files=[csv_file])
        pipeline = PipelineA()
        result = pipeline.process_folder(scan_result, company_piva="")

        assert len(result.bank_results) == 2
        assert all(isinstance(r, BankMovementResult) for r in result.bank_results)


# ---------------------------------------------------------------------------
# TestDeduplication — tests dedup logic returns status="gia_importata" (PIPE-02)
# These initially FAIL (RED) — will pass after Task 3.
# ---------------------------------------------------------------------------

class TestDeduplication:
    """Tests for PipelineA deduplication via fattura_gia_importata (PIPE-02)."""

    def _make_scan_result(self, tmp_path, xml_files=None):
        from scanner.client_folder_scanner import ScanResult
        result = ScanResult(client_folder=tmp_path)
        if xml_files:
            result.files["FatturaXML"] = xml_files
        return result

    def test_already_imported_returns_gia_importata(self, tmp_path):
        from pipeline.pipeline_a import PipelineA
        from accounting.db import salva_fattura_importata, init_db
        from parsers.fattura_pa import FatturaPAParser

        # Pre-import the fattura into the test DB
        db_path = tmp_path / "test_dedup.db"
        init_db(db_path)

        parser = FatturaPAParser()
        fatture = parser.parse_bytes(MINIMAL_FATTURA_XML)
        salva_fattura_importata(fatture[0], MINIMAL_FATTURA_XML, db_path=db_path)

        xml_file = tmp_path / "fattura.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()
        # Pass the test DB path via process_folder to avoid touching production DB
        result = pipeline.process_folder(scan_result, company_piva="", db_path=db_path)

        invoice = result.invoice_results[0]
        assert invoice.status == "gia_importata"
        assert invoice.fattura is None
        assert invoice.registrazione is None

    def test_already_imported_does_not_raise(self, tmp_path):
        from pipeline.pipeline_a import PipelineA
        from accounting.db import salva_fattura_importata, init_db
        from parsers.fattura_pa import FatturaPAParser

        db_path = tmp_path / "test_dedup2.db"
        init_db(db_path)

        parser = FatturaPAParser()
        fatture = parser.parse_bytes(MINIMAL_FATTURA_XML)
        salva_fattura_importata(fatture[0], MINIMAL_FATTURA_XML, db_path=db_path)

        xml_file = tmp_path / "fattura_dup.xml"
        xml_file.write_bytes(MINIMAL_FATTURA_XML)

        scan_result = self._make_scan_result(tmp_path, xml_files=[xml_file])
        pipeline = PipelineA()

        # Must not raise any exception
        result = pipeline.process_folder(scan_result, company_piva="", db_path=db_path)
        assert len(result.invoice_results) == 1
