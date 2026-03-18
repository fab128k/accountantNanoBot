# tests/test_scanner.py
# TDD tests for scanner module: ClientFolderScanner + ScanResult + PipelineA stub
# ============================================================================

import pytest
from pathlib import Path


class TestClientFolderScanner:
    """ClientFolderScanner core scan() behavior tests."""

    def test_scan_returns_scan_result(self, tmp_path):
        from scanner.client_folder_scanner import ClientFolderScanner, ScanResult

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        assert isinstance(result, ScanResult)

    def test_scan_result_has_all_categories(self, tmp_path):
        from scanner.client_folder_scanner import ClientFolderScanner, CATEGORIES

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        for cat in CATEGORIES:
            assert cat in result.files, f"Category '{cat}' missing from ScanResult.files"

    def test_recursive(self, tmp_path):
        """Files in subdirectories are found."""
        from scanner.client_folder_scanner import ClientFolderScanner

        subdir = tmp_path / "fatture"
        subdir.mkdir()
        xml_file = subdir / "invoice.xml"
        xml_file.write_bytes(b'<?xml version="1.0"?><FatturaElettronica versione="FPR12">')

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        # The file is in a subdirectory — must be found
        assert result.total() >= 1
        assert xml_file in result.files["FatturaXML"]

    def test_total_count(self, tmp_path):
        """ScanResult.total() returns correct sum of all classified files."""
        from scanner.client_folder_scanner import ClientFolderScanner

        (tmp_path / "a.pdf").write_bytes(b"%PDF-fake")
        (tmp_path / "b.pdf").write_bytes(b"%PDF-fake")
        (tmp_path / "notes.txt").write_bytes(b"hello")

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        assert result.total() == 3


class TestClassification:
    """File classification logic tests."""

    def test_fattura_xml_classified(self, tmp_path):
        """XML file with b'FatturaElettronica' in first 512 bytes -> FatturaXML."""
        from scanner.client_folder_scanner import ClientFolderScanner

        fattura = tmp_path / "invoice.xml"
        fattura.write_bytes(b'<?xml version="1.0"?><FatturaElettronica versione="FPR12">')

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        assert fattura in result.files["FatturaXML"]
        assert len(result.files["FatturaXML"]) == 1

    def test_generic_xml_to_altro(self, tmp_path):
        """XML file without FatturaElettronica -> Altro."""
        from scanner.client_folder_scanner import ClientFolderScanner

        generic = tmp_path / "generic.xml"
        generic.write_bytes(b'<?xml version="1.0"?><root><item/></root>')

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        assert generic in result.files["Altro"]
        assert len(result.files["FatturaXML"]) == 0

    def test_extension_dispatch(self, tmp_path):
        """.pdf -> PDF, .csv -> CSV, .docx -> DOCX, .txt -> TXT."""
        from scanner.client_folder_scanner import ClientFolderScanner

        pdf = tmp_path / "contract.pdf"
        pdf.write_bytes(b"%PDF-fake")
        csv = tmp_path / "data.csv"
        csv.write_bytes(b"col1,col2\n1,2")
        docx = tmp_path / "report.docx"
        docx.write_bytes(b"PK\x03\x04")
        txt = tmp_path / "notes.txt"
        txt.write_bytes(b"hello world")

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)

        assert pdf in result.files["PDF"]
        assert csv in result.files["CSV"]
        assert docx in result.files["DOCX"]
        assert txt in result.files["TXT"]

    def test_unknown_extension_to_altro(self, tmp_path):
        """.zip extension -> Altro."""
        from scanner.client_folder_scanner import ClientFolderScanner

        archive = tmp_path / "archive.zip"
        archive.write_bytes(b"PK\x03\x04")

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)
        assert archive in result.files["Altro"]


class TestScannerEdgeCases:
    """Edge case behavior tests."""

    def test_missing_folder(self):
        """scan(Path('/nonexistent')) returns empty ScanResult, no exception raised."""
        from scanner.client_folder_scanner import ClientFolderScanner

        scanner = ClientFolderScanner()
        result = scanner.scan(Path("/nonexistent_folder_that_does_not_exist_12345"))
        assert result.total() == 0

    def test_hidden_files_skipped(self, tmp_path):
        """Dot-prefixed files (.gitignore) are not included in scan results."""
        from scanner.client_folder_scanner import ClientFolderScanner

        hidden = tmp_path / ".gitignore"
        hidden.write_bytes(b"*.pyc\n")
        visible = tmp_path / "readme.txt"
        visible.write_bytes(b"project readme")

        scanner = ClientFolderScanner()
        result = scanner.scan(tmp_path)

        # Hidden file must NOT appear anywhere in results
        all_files = [f for files in result.files.values() for f in files]
        assert hidden not in all_files
        # Visible file must be found
        assert visible in result.files["TXT"]


class TestPipelineAStub:
    """PipelineA stub contract tests."""

    def test_import(self):
        """from pipeline.pipeline_a import PipelineA succeeds."""
        from pipeline.pipeline_a import PipelineA
        assert PipelineA is not None

    def test_process_folder_raises_not_implemented(self, tmp_path):
        """PipelineA().process_folder(Path('/tmp')) raises NotImplementedError."""
        from pipeline.pipeline_a import PipelineA

        pipeline = PipelineA()
        with pytest.raises(NotImplementedError):
            pipeline.process_folder(tmp_path)
