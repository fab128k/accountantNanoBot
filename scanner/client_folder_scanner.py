# scanner/client_folder_scanner.py
# ClientFolderScanner: classifies files in a client folder into six categories.
# Zero Streamlit dependency — pure Python, fully testable with pytest.
# ============================================================================

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

CATEGORIES = ["FatturaXML", "PDF", "CSV", "DOCX", "TXT", "Altro"]


@dataclass
class ScanResult:
    """Holds classified file lists keyed by category, plus a reference to the scanned folder."""

    client_folder: Path
    files: Dict[str, List[Path]] = field(
        default_factory=lambda: {cat: [] for cat in CATEGORIES}
    )

    def total(self) -> int:
        """Return the total number of files across all categories."""
        return sum(len(v) for v in self.files.values())

    def count(self, category: str) -> int:
        """Return the number of files in a specific category."""
        return len(self.files.get(category, []))


def _is_fattura_xml(path: Path) -> bool:
    """
    Returns True if the file is a FatturaPA XML (FatturaElettronica).

    Reads only the first 512 bytes — avoids a full XML parse during scanning.
    This is consistent with the content-peek approach in core/file_processors.py
    but is cheaper: no lxml dependency required for classification.
    """
    try:
        with open(path, "rb") as f:
            header = f.read(512)
        return b"FatturaElettronica" in header
    except OSError:
        return False


_EXT_TO_CATEGORY: Dict[str, str] = {
    ".pdf": "PDF",
    ".csv": "CSV",
    ".docx": "DOCX",
    ".txt": "TXT",
    # .xml is handled separately via content peek (_is_fattura_xml)
}


def _classify(path: Path) -> str:
    """
    Return the category name for a given file path.

    For .xml files: uses a 512-byte content peek to distinguish FatturaPA from generic XML.
    For all other extensions: uses the _EXT_TO_CATEGORY dispatch table.
    Unknown extensions fall into 'Altro'.
    """
    ext = path.suffix.lower()
    if ext == ".xml":
        return "FatturaXML" if _is_fattura_xml(path) else "Altro"
    return _EXT_TO_CATEGORY.get(ext, "Altro")


class ClientFolderScanner:
    """
    Recursively scans a client folder and classifies each file into one of six categories:
    FatturaXML, PDF, CSV, DOCX, TXT, Altro.

    Usage:
        scanner = ClientFolderScanner()
        result = scanner.scan(Path("/path/to/client/folder"))
        print(result.total())           # total files found
        print(result.count("FatturaXML"))  # number of FatturaPA files
    """

    def scan(self, folder: Path) -> ScanResult:
        """
        Scan folder recursively and return a ScanResult.

        - Returns an empty ScanResult (total() == 0) for non-existent or non-directory paths.
        - Skips hidden files (dot-prefixed names such as .gitignore, .DS_Store).
        - Classification is done by extension dispatch + XML content peek.
        """
        result = ScanResult(client_folder=folder)
        if not folder.exists() or not folder.is_dir():
            return result
        for path in sorted(folder.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                category = _classify(path)
                result.files[category].append(path)
        return result
