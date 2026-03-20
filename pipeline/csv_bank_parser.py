# pipeline/csv_bank_parser.py
# CSV/OFX bank statement parser — Italian format support.
# ============================================================================

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class BankMovement:
    """Single bank movement parsed from a statement."""
    data: date
    data_valuta: Optional[date] = None
    descrizione: str = ""
    importo: Decimal = Decimal("0")     # positive = income, negative = expense
    saldo: Optional[Decimal] = None
    iban: str = ""
    raw_row: Dict = field(default_factory=dict)


def _parse_italian_decimal(s: str) -> Decimal:
    """Parse Italian decimal format: '25,10', '-300,22', '18 668,63', '18.668,63'."""
    s = s.strip()
    if not s or s == "-":
        return Decimal("0")
    # Remove thousands separators: dots or spaces before exactly 3 digits
    # (e.g. "18.668,63" -> "18668,63", "18 668,63" -> "18668,63")
    s = re.sub(r'[.\s](?=\d{3}(?:[,.]|$))', '', s)
    # Replace comma decimal separator with dot
    s = s.replace(',', '.')
    # Remove any remaining spaces
    s = s.replace(' ', '')
    try:
        return Decimal(s)
    except (InvalidOperation, Exception):
        return Decimal("0")


def _parse_date(s: str) -> Optional[date]:
    """Parse date from DD/MM/YYYY or YYYY-MM-DD format."""
    s = s.strip()
    if not s:
        return None
    # Try DD/MM/YYYY or DD.MM.YYYY
    m = re.match(r'(\d{2})[./](\d{2})[./](\d{4})', s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    # Try YYYY-MM-DD
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


class BankStatementParser:
    """
    Parser for CSV and OFX bank statements, with Italian format support.

    Handles:
    - Italian semicolon-separated CSVs with multi-row metadata headers
    - Separate Accrediti (credit) / Addebiti (debit) columns
    - Single Importo column (signed or unsigned)
    - IBAN extraction from metadata header rows
    - Canonical comma-separated format (data,descrizione,importo,saldo)
    """

    def parse_csv(self, path: Path) -> List[BankMovement]:
        """
        Parse a bank statement CSV file with auto-detection of Italian format.

        Reads the file detecting encoding (utf-8 first, fallback to latin-1),
        finds the data header row via _detect_header_row(), extracts IBAN from
        metadata rows, and parses all data rows into BankMovement objects.

        Args:
            path: Path to the CSV file

        Returns:
            List[BankMovement] with parsed movements
        """
        # Read file content with encoding detection
        content = None
        for encoding in ("utf-8", "latin-1", "utf-8-sig"):
            try:
                content = path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, Exception):
                continue
        if content is None:
            return []

        # Parse all rows using semicolon delimiter
        rows: List[List[str]] = []
        reader = csv.reader(io.StringIO(content), delimiter=";")
        for row in reader:
            rows.append(row)

        if not rows:
            return []

        # Find header row index
        header_idx = self._detect_header_row(rows)

        # Extract IBAN from metadata rows before the header
        iban = self._extract_iban_from_header(rows[:header_idx])

        # Parse header columns
        if header_idx >= len(rows):
            return []
        header_row = [cell.strip().lower() for cell in rows[header_idx]]

        # Map column names to indices (case-insensitive)
        col_map: Dict[str, int] = {}
        for i, col in enumerate(header_row):
            col_map[col] = i

        # Detect column layout
        # Italian format: "accrediti" + "addebiti" columns
        # Single importo format: "importo" column
        has_accrediti = any("accrediti" in c for c in header_row)
        has_addebiti = any("addebiti" in c for c in header_row)
        has_importo = any(c == "importo" for c in header_row)

        def get_col(names: List[str]) -> Optional[int]:
            """Return index of first matching column name."""
            for name in names:
                for col_name, idx in col_map.items():
                    if name in col_name:
                        return idx
            return None

        idx_data = get_col(["data contabile", "data"])
        idx_data_valuta = get_col(["data valuta"])
        idx_descrizione = get_col(["descrizione estesa", "descrizione"])
        idx_accrediti = get_col(["accrediti"])
        idx_addebiti = get_col(["addebiti"])
        idx_importo = get_col(["importo"])
        idx_saldo = get_col(["saldo"])

        # Parse data rows
        movements: List[BankMovement] = []
        for row in rows[header_idx + 1:]:
            if not row or all(cell.strip() == "" for cell in row):
                continue

            # Data column
            data_str = row[idx_data].strip() if idx_data is not None and idx_data < len(row) else ""
            parsed_data = _parse_date(data_str)
            if parsed_data is None:
                # Skip rows that don't start with a date (footer rows, etc.)
                continue

            # Data valuta
            data_valuta_str = (
                row[idx_data_valuta].strip()
                if idx_data_valuta is not None and idx_data_valuta < len(row)
                else ""
            )
            parsed_data_valuta = _parse_date(data_valuta_str)

            # Descrizione
            descrizione = (
                row[idx_descrizione].strip()
                if idx_descrizione is not None and idx_descrizione < len(row)
                else ""
            )

            # Importo: Accrediti/Addebiti or single Importo column
            if has_accrediti and has_addebiti:
                accrediti_str = (
                    row[idx_accrediti].strip()
                    if idx_accrediti is not None and idx_accrediti < len(row)
                    else ""
                )
                addebiti_str = (
                    row[idx_addebiti].strip()
                    if idx_addebiti is not None and idx_addebiti < len(row)
                    else ""
                )
                accrediti = _parse_italian_decimal(accrediti_str)
                addebiti = _parse_italian_decimal(addebiti_str)
                # Accrediti -> positive, Addebiti -> negative
                importo = accrediti - abs(addebiti)
            elif has_importo and idx_importo is not None:
                importo_str = (
                    row[idx_importo].strip()
                    if idx_importo < len(row)
                    else ""
                )
                importo = _parse_italian_decimal(importo_str)
            else:
                importo = Decimal("0")

            # Saldo
            saldo_str = (
                row[idx_saldo].strip()
                if idx_saldo is not None and idx_saldo < len(row)
                else ""
            )
            saldo = _parse_italian_decimal(saldo_str) if saldo_str else None

            # Build raw_row dict
            raw_row = {header_row[i]: row[i] for i in range(min(len(header_row), len(row)))}

            movements.append(BankMovement(
                data=parsed_data,
                data_valuta=parsed_data_valuta,
                descrizione=descrizione,
                importo=importo,
                saldo=saldo,
                iban=iban,
                raw_row=raw_row,
            ))

        return movements

    def parse_canonical_csv(self, path: Path) -> List[BankMovement]:
        """
        Parse a simple canonical CSV with header: data,descrizione,importo,saldo.

        Uses comma as separator and DictReader for straightforward parsing.

        Args:
            path: Path to the CSV file

        Returns:
            List[BankMovement] with parsed movements
        """
        content = None
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                content = path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, Exception):
                continue
        if content is None:
            return []

        movements: List[BankMovement] = []
        reader = csv.DictReader(io.StringIO(content))

        for row in reader:
            data_str = (row.get("data") or "").strip()
            parsed_data = _parse_date(data_str)
            if parsed_data is None:
                continue

            descrizione = (row.get("descrizione") or "").strip()
            importo_str = (row.get("importo") or "0").strip()
            saldo_str = (row.get("saldo") or "").strip()

            importo = _parse_italian_decimal(importo_str)
            saldo = _parse_italian_decimal(saldo_str) if saldo_str else None

            movements.append(BankMovement(
                data=parsed_data,
                descrizione=descrizione,
                importo=importo,
                saldo=saldo,
                raw_row=dict(row),
            ))

        return movements

    def _detect_header_row(self, rows: List[List[str]]) -> int:
        """
        Detect the index of the data header row.

        Strategy: scan first 30 rows looking for a row where at least one cell
        (case-insensitive) contains "data" or "data valuta" or "data contabile"
        AND the NEXT row's first cell matches a date pattern DD/MM/YYYY.

        Returns the index of the header row. Falls back to 0 if not found.

        Args:
            rows: All rows parsed from the CSV

        Returns:
            Index of the header row
        """
        date_pattern = re.compile(r'\d{2}[./]\d{2}[./]\d{4}')
        date_keywords = {"data", "data valuta", "data contabile"}

        for i, row in enumerate(rows[:30]):
            row_lower = [cell.strip().lower() for cell in row]
            # Check if any cell in this row matches date column keywords
            has_date_col = any(cell in date_keywords for cell in row_lower)
            if not has_date_col:
                continue
            # Check if next row's first non-empty cell looks like a date
            if i + 1 < len(rows):
                next_row = rows[i + 1]
                first_cell = next_row[0].strip() if next_row else ""
                if date_pattern.match(first_cell):
                    return i

        return 0

    def _extract_iban_from_header(self, header_rows: List[List[str]]) -> str:
        """
        Scan metadata header rows for an IBAN pattern.

        IBAN pattern: 2 uppercase letters + 2 digits + 11-30 alphanumeric chars.

        Args:
            header_rows: Rows before the data header row

        Returns:
            First IBAN found, or empty string
        """
        iban_pattern = re.compile(r'[A-Z]{2}\d{2}[A-Z0-9]{11,30}')
        for row in header_rows:
            for cell in row:
                match = iban_pattern.search(cell.strip())
                if match:
                    return match.group(0)
        return ""

    def parse_ofx(self, path: Path) -> List[BankMovement]:
        """
        Parse an OFX/QIF bank statement file.

        Not yet implemented — future extension point.

        Args:
            path: Path to the OFX file

        Raises:
            NotImplementedError: Always — OFX parsing is not yet implemented
        """
        raise NotImplementedError("OFX parsing not yet implemented")
