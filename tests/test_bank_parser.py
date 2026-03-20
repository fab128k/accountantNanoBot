# tests/test_bank_parser.py
# TDD tests for BankStatementParser: PIPE-03 (CSV parsing) and PIPE-04 (CoA mapping)
# ============================================================================

import pytest
from pathlib import Path
from decimal import Decimal


# ---------------------------------------------------------------------------
# Sample CSV content for tests
# ---------------------------------------------------------------------------

SAMPLE_ITALIAN_CSV = """\
Conto corrente: IT60X0542811101000000123456
Periodo: 01/01/2026 - 31/01/2026

Data;Data valuta;Descrizione;Accrediti;Addebiti;Saldo
15/01/2026;15/01/2026;Incasso da ALFA SRL;1220,00;;15220,00
20/01/2026;20/01/2026;Bonifico a BETA SRL;;500,00;14720,00
31/01/2026;31/01/2026;Interessi attivi;18,63;;14738,63
"""

SAMPLE_ITALIAN_CSV_NO_IBAN = """\
Data;Data valuta;Descrizione;Accrediti;Addebiti;Saldo
10/02/2026;10/02/2026;Pagamento fattura;850,00;;20000,00
15/02/2026;15/02/2026;Addebito utenze;;300,00;19700,00
"""

SAMPLE_CANONICAL_CSV = """\
data,descrizione,importo,saldo
15/01/2026,Incasso cliente,1220.00,15000.00
20/01/2026,Pagamento fornitore,-500.00,14500.00
"""

SAMPLE_CSV_SPACE_THOUSANDS = """\
Data;Data valuta;Descrizione;Accrediti;Addebiti;Saldo
31/01/2026;31/01/2026;Saldo finale;18 668,63;;18668,63
"""

SAMPLE_CSV_DOT_THOUSANDS = """\
Data;Data valuta;Descrizione;Importo;Saldo
31/01/2026;31/01/2026;Totale;18.668,63;18668,63
"""


# ---------------------------------------------------------------------------
# TestItalianDecimalParsing — parametrized tests for _parse_italian_decimal
# ---------------------------------------------------------------------------

class TestItalianDecimalParsing:
    """Parametrized tests for the _parse_italian_decimal helper."""

    @pytest.mark.parametrize("input_str,expected", [
        ("25,10", Decimal("25.10")),
        ("-300,22", Decimal("-300.22")),
        ("18 668,63", Decimal("18668.63")),
        ("18.668,63", Decimal("18668.63")),
        ("", Decimal("0")),
        ("-", Decimal("0")),
        ("0,00", Decimal("0.00")),
        ("1.000,00", Decimal("1000.00")),
        ("  100,50  ", Decimal("100.50")),
        ("1220,00", Decimal("1220.00")),
    ])
    def test_parse_italian_decimal(self, input_str, expected):
        from pipeline.csv_bank_parser import _parse_italian_decimal
        result = _parse_italian_decimal(input_str)
        assert result == expected, f"_parse_italian_decimal({input_str!r}) = {result}, expected {expected}"


# ---------------------------------------------------------------------------
# TestFormatDetection — tests _detect_header_row
# ---------------------------------------------------------------------------

class TestFormatDetection:
    """Tests that _detect_header_row finds the correct row index."""

    def test_detects_header_at_row_zero(self):
        from pipeline.csv_bank_parser import BankStatementParser
        rows = [
            ["Data", "Data valuta", "Descrizione", "Accrediti", "Addebiti", "Saldo"],
            ["15/01/2026", "15/01/2026", "Incasso", "1220,00", "", "15000,00"],
        ]
        parser = BankStatementParser()
        idx = parser._detect_header_row(rows)
        assert idx == 0

    def test_detects_header_after_metadata_rows(self):
        from pipeline.csv_bank_parser import BankStatementParser
        rows = [
            ["Banca Italiana SPA"],
            ["Estratto conto: 01/01/2026-31/01/2026"],
            [""],
            ["Data", "Data valuta", "Descrizione", "Accrediti", "Addebiti", "Saldo"],
            ["15/01/2026", "15/01/2026", "Incasso", "1220,00", "", "15000,00"],
        ]
        parser = BankStatementParser()
        idx = parser._detect_header_row(rows)
        assert idx == 3

    def test_returns_zero_when_no_header_found(self):
        from pipeline.csv_bank_parser import BankStatementParser
        rows = [
            ["totally", "unrelated", "data"],
            ["no date here", "col2", "col3"],
        ]
        parser = BankStatementParser()
        idx = parser._detect_header_row(rows)
        assert idx == 0


# ---------------------------------------------------------------------------
# TestBankStatementParser — tests parse_csv with inline CSV written to tmp_path
# ---------------------------------------------------------------------------

class TestBankStatementParser:
    """Tests BankStatementParser.parse_csv with semicolon Italian format."""

    def test_parse_csv_returns_list_of_bank_movements(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser, BankMovement

        csv_file = tmp_path / "estratto.csv"
        csv_file.write_text(SAMPLE_ITALIAN_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        assert isinstance(movements, list)
        assert len(movements) == 3
        assert all(isinstance(m, BankMovement) for m in movements)

    def test_parse_csv_dates_are_date_objects(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser
        from datetime import date

        csv_file = tmp_path / "estratto.csv"
        csv_file.write_text(SAMPLE_ITALIAN_CSV_NO_IBAN, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        assert len(movements) == 2
        assert isinstance(movements[0].data, date)
        assert movements[0].data == date(2026, 2, 10)

    def test_parse_csv_accrediti_are_positive(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "estratto.csv"
        csv_file.write_text(SAMPLE_ITALIAN_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        # First row: Accrediti=1220,00 -> positive importo
        assert movements[0].importo == Decimal("1220.00")
        assert movements[0].importo > 0

    def test_parse_csv_addebiti_are_negative(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "estratto.csv"
        csv_file.write_text(SAMPLE_ITALIAN_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        # Second row: Addebiti=500,00 -> negative importo
        assert movements[1].importo == Decimal("-500.00")
        assert movements[1].importo < 0

    def test_parse_csv_space_thousands(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "estratto_space.csv"
        csv_file.write_text(SAMPLE_CSV_SPACE_THOUSANDS, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        assert len(movements) == 1
        assert movements[0].importo == Decimal("18668.63")

    def test_parse_csv_dot_thousands(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "estratto_dot.csv"
        csv_file.write_text(SAMPLE_CSV_DOT_THOUSANDS, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        assert len(movements) == 1
        assert movements[0].importo == Decimal("18668.63")

    def test_parse_csv_extracts_iban_from_header(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "estratto_iban.csv"
        csv_file.write_text(SAMPLE_ITALIAN_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        # IBAN from header should propagate to all movements
        assert len(movements) > 0
        assert movements[0].iban == "IT60X0542811101000000123456"

    def test_parse_csv_importo_is_decimal(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "estratto.csv"
        csv_file.write_text(SAMPLE_ITALIAN_CSV_NO_IBAN, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_csv(csv_file)

        for m in movements:
            assert isinstance(m.importo, Decimal), f"importo should be Decimal, got {type(m.importo)}"


# ---------------------------------------------------------------------------
# TestCanonicalCSV — tests parse_canonical_csv with simple comma-separated format
# ---------------------------------------------------------------------------

class TestCanonicalCSV:
    """Tests parse_canonical_csv with simple comma-separated data,descrizione,importo,saldo."""

    def test_parse_canonical_csv_returns_movements(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser, BankMovement

        csv_file = tmp_path / "canonical.csv"
        csv_file.write_text(SAMPLE_CANONICAL_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_canonical_csv(csv_file)

        assert isinstance(movements, list)
        assert len(movements) == 2
        assert all(isinstance(m, BankMovement) for m in movements)

    def test_parse_canonical_csv_positive_importo(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        csv_file = tmp_path / "canonical.csv"
        csv_file.write_text(SAMPLE_CANONICAL_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_canonical_csv(csv_file)

        assert movements[0].importo == Decimal("1220.00")
        assert movements[1].importo == Decimal("-500.00")

    def test_parse_canonical_csv_date_parsed(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser
        from datetime import date

        csv_file = tmp_path / "canonical.csv"
        csv_file.write_text(SAMPLE_CANONICAL_CSV, encoding="utf-8")

        parser = BankStatementParser()
        movements = parser.parse_canonical_csv(csv_file)

        assert isinstance(movements[0].data, date)
        assert movements[0].data == date(2026, 1, 15)


# ---------------------------------------------------------------------------
# TestOFXStub — tests parse_ofx raises NotImplementedError
# ---------------------------------------------------------------------------

class TestOFXStub:
    """Tests that parse_ofx is a stub raising NotImplementedError."""

    def test_parse_ofx_raises_not_implemented(self, tmp_path):
        from pipeline.csv_bank_parser import BankStatementParser

        ofx_file = tmp_path / "bank.ofx"
        ofx_file.write_bytes(b"<OFX></OFX>")

        parser = BankStatementParser()
        with pytest.raises(NotImplementedError):
            parser.parse_ofx(ofx_file)
