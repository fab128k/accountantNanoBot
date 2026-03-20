# accounting/db.py
# AccountantNanoBot v1.0.0 - Gestione database SQLite
# ============================================================================

from __future__ import annotations

import hashlib
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from config.constants import DB_PATH


# ============================================================================
# INIT DATABASE
# ============================================================================

def init_db(db_path: Path = DB_PATH) -> None:
    """
    Inizializza il database SQLite creando le tabelle se non esistono.

    Args:
        db_path: Path al file SQLite
    """
    import sqlite3

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript("""
            -- Registrazioni di prima nota
            CREATE TABLE IF NOT EXISTS registrazioni_prima_nota (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                numero_progressivo INTEGER,
                tipo TEXT NOT NULL,
                descrizione TEXT NOT NULL,
                fattura_riferimento TEXT DEFAULT '',
                bilanciata BOOLEAN DEFAULT 1,
                creata_da_agente BOOLEAN DEFAULT 0,
                confermata BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Righe delle registrazioni (dare/avere)
            CREATE TABLE IF NOT EXISTS righe_prima_nota (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registrazione_id INTEGER NOT NULL
                    REFERENCES registrazioni_prima_nota(id) ON DELETE CASCADE,
                conto_codice TEXT NOT NULL,
                conto_nome TEXT NOT NULL,
                dare DECIMAL(15,2) DEFAULT 0,
                avere DECIMAL(15,2) DEFAULT 0,
                descrizione TEXT DEFAULT ''
            );

            -- Fatture importate (con deduplicazione via hash)
            CREATE TABLE IF NOT EXISTS fatture_importate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_file TEXT UNIQUE NOT NULL,
                numero TEXT NOT NULL,
                data DATE,
                cedente_piva TEXT DEFAULT '',
                cedente_nome TEXT DEFAULT '',
                cessionario_piva TEXT DEFAULT '',
                cessionario_nome TEXT DEFAULT '',
                tipo_documento TEXT DEFAULT 'TD01',
                importo_totale DECIMAL(15,2) DEFAULT 0,
                xml_path TEXT DEFAULT '',
                processata BOOLEAN DEFAULT 0,
                registrazione_id INTEGER
                    REFERENCES registrazioni_prima_nota(id),
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Indici per performance
            CREATE INDEX IF NOT EXISTS idx_registrazioni_data
                ON registrazioni_prima_nota(data);
            CREATE INDEX IF NOT EXISTS idx_registrazioni_tipo
                ON registrazioni_prima_nota(tipo);
            CREATE INDEX IF NOT EXISTS idx_righe_registrazione
                ON righe_prima_nota(registrazione_id);
            CREATE INDEX IF NOT EXISTS idx_righe_conto
                ON righe_prima_nota(conto_codice);
            CREATE INDEX IF NOT EXISTS idx_fatture_data
                ON fatture_importate(data);
            CREATE INDEX IF NOT EXISTS idx_fatture_cedente
                ON fatture_importate(cedente_piva);

            -- IBAN to CoA account mapping (per-client)
            CREATE TABLE IF NOT EXISTS iban_coa_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iban TEXT NOT NULL UNIQUE,
                conto_codice TEXT NOT NULL,
                conto_nome TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Confirmed bank movements
            CREATE TABLE IF NOT EXISTS movimenti_bancari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                data_valuta DATE,
                descrizione TEXT NOT NULL,
                importo DECIMAL(15,2) NOT NULL,
                saldo DECIMAL(15,2),
                iban TEXT DEFAULT '',
                hash_file TEXT DEFAULT '',
                confermato BOOLEAN DEFAULT 0,
                registrazione_id INTEGER REFERENCES registrazioni_prima_nota(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_movimenti_data ON movimenti_bancari(data);
            CREATE INDEX IF NOT EXISTS idx_iban_mapping ON iban_coa_mapping(iban);
        """)
        conn.commit()


def _get_connection(db_path: Path = DB_PATH):
    """Ritorna connessione SQLite con row_factory."""
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# PRIMA NOTA - SALVATAGGIO
# ============================================================================

def salva_registrazione(
    registrazione,  # RegistrazionePrimaNota
    db_path: Path = DB_PATH
) -> int:
    """
    Salva una registrazione di prima nota nel DB.

    Args:
        registrazione: Istanza di RegistrazionePrimaNota
        db_path: Path al DB

    Returns:
        ID della registrazione salvata
    """
    init_db(db_path)

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO registrazioni_prima_nota
                (data, numero_progressivo, tipo, descrizione,
                 fattura_riferimento, bilanciata, creata_da_agente, confermata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            registrazione.data.isoformat(),
            registrazione.numero_progressivo,
            registrazione.tipo.value,
            registrazione.descrizione,
            registrazione.fattura_riferimento,
            registrazione.is_bilanciata,
            registrazione.creata_da_agente,
            registrazione.confermata,
        ))

        reg_id = cursor.lastrowid

        for riga in registrazione.righe:
            cursor.execute("""
                INSERT INTO righe_prima_nota
                    (registrazione_id, conto_codice, conto_nome, dare, avere, descrizione)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reg_id,
                riga.conto_codice,
                riga.conto_nome,
                float(riga.dare),
                float(riga.avere),
                riga.descrizione,
            ))

        conn.commit()
        return reg_id


# ============================================================================
# FATTURE IMPORTATE
# ============================================================================

def calcola_hash_fattura(xml_bytes: bytes) -> str:
    """Calcola SHA256 del contenuto XML per deduplicazione."""
    return hashlib.sha256(xml_bytes).hexdigest()


def fattura_gia_importata(xml_bytes: bytes, db_path: Path = DB_PATH) -> bool:
    """
    Verifica se una fattura è già stata importata (controllo hash).

    Args:
        xml_bytes: Contenuto XML della fattura
        db_path: Path al DB

    Returns:
        True se già presente
    """
    hash_file = calcola_hash_fattura(xml_bytes)

    init_db(db_path)
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM fatture_importate WHERE hash_file = ?",
            (hash_file,)
        ).fetchone()
        return row is not None


def salva_fattura_importata(
    fattura,  # FatturaPA
    xml_bytes: bytes,
    xml_path: str = "",
    db_path: Path = DB_PATH
) -> Optional[int]:
    """
    Salva una fattura importata nel DB.

    Args:
        fattura: Istanza di FatturaPA
        xml_bytes: Contenuto XML originale (per hash)
        xml_path: Path al file XML
        db_path: Path al DB

    Returns:
        ID del record inserito, o None se già presente
    """
    hash_file = calcola_hash_fattura(xml_bytes)

    init_db(db_path)

    with _get_connection(db_path) as conn:
        # Controlla duplicato
        existing = conn.execute(
            "SELECT id FROM fatture_importate WHERE hash_file = ?",
            (hash_file,)
        ).fetchone()

        if existing:
            return None  # Già importata

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fatture_importate
                (hash_file, numero, data, cedente_piva, cedente_nome,
                 cessionario_piva, cessionario_nome, tipo_documento,
                 importo_totale, xml_path, processata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hash_file,
            fattura.numero,
            fattura.data.isoformat() if fattura.data else None,
            fattura.cedente.partita_iva,
            fattura.cedente.nome_completo,
            fattura.cessionario.partita_iva,
            fattura.cessionario.nome_completo,
            fattura.tipo_documento,
            float(fattura.importo_totale),
            xml_path,
            False,
        ))

        conn.commit()
        return cursor.lastrowid


# ============================================================================
# QUERY
# ============================================================================

def get_prima_nota(
    data_da: Optional[date] = None,
    data_a: Optional[date] = None,
    tipo: Optional[str] = None,
    solo_confermate: bool = False,
    db_path: Path = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Recupera registrazioni di prima nota con filtri opzionali.

    Args:
        data_da: Data inizio (inclusa)
        data_a: Data fine (inclusa)
        tipo: Tipo registrazione (TipoRegistrazione.value)
        solo_confermate: Se True, ritorna solo quelle confermate
        db_path: Path al DB

    Returns:
        Lista di dict con registrazione + righe
    """
    init_db(db_path)

    with _get_connection(db_path) as conn:
        where_clauses = []
        params = []

        if data_da:
            where_clauses.append("r.data >= ?")
            params.append(data_da.isoformat())
        if data_a:
            where_clauses.append("r.data <= ?")
            params.append(data_a.isoformat())
        if tipo:
            where_clauses.append("r.tipo = ?")
            params.append(tipo)
        if solo_confermate:
            where_clauses.append("r.confermata = 1")

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        rows = conn.execute(f"""
            SELECT r.*, GROUP_CONCAT(
                rn.conto_codice || '|' || rn.conto_nome || '|' ||
                rn.dare || '|' || rn.avere || '|' || rn.descrizione, ';;'
            ) as righe_concat
            FROM registrazioni_prima_nota r
            LEFT JOIN righe_prima_nota rn ON rn.registrazione_id = r.id
            {where_sql}
            GROUP BY r.id
            ORDER BY r.data DESC, r.id DESC
        """, params).fetchall()

        result = []
        for row in rows:
            reg = dict(row)
            righe = []
            if reg.get("righe_concat"):
                for riga_str in reg["righe_concat"].split(";;"):
                    parts = riga_str.split("|")
                    if len(parts) >= 4:
                        righe.append({
                            "conto_codice": parts[0],
                            "conto_nome": parts[1],
                            "dare": Decimal(parts[2]),
                            "avere": Decimal(parts[3]),
                            "descrizione": parts[4] if len(parts) > 4 else "",
                        })
            reg["righe"] = righe
            del reg["righe_concat"]
            result.append(reg)

        return result


def get_fatture_importate(
    processata: Optional[bool] = None,
    db_path: Path = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Recupera fatture importate.

    Args:
        processata: Filtra per stato elaborazione (None = tutte)
        db_path: Path al DB

    Returns:
        Lista di dict con dati fattura
    """
    init_db(db_path)

    with _get_connection(db_path) as conn:
        if processata is None:
            rows = conn.execute(
                "SELECT * FROM fatture_importate ORDER BY data DESC, imported_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM fatture_importate WHERE processata = ? ORDER BY data DESC",
                (int(processata),)
            ).fetchall()

        return [dict(row) for row in rows]


def get_statistiche(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """
    Ritorna statistiche generali del database.

    Returns:
        Dict con conteggi e totali
    """
    init_db(db_path)

    with _get_connection(db_path) as conn:
        n_registrazioni = conn.execute(
            "SELECT COUNT(*) FROM registrazioni_prima_nota"
        ).fetchone()[0]

        n_fatture = conn.execute(
            "SELECT COUNT(*) FROM fatture_importate"
        ).fetchone()[0]

        n_da_processare = conn.execute(
            "SELECT COUNT(*) FROM fatture_importate WHERE processata = 0"
        ).fetchone()[0]

        n_non_confermate = conn.execute(
            "SELECT COUNT(*) FROM registrazioni_prima_nota WHERE confermata = 0"
        ).fetchone()[0]

        totale_crediti = conn.execute("""
            SELECT COALESCE(SUM(dare - avere), 0)
            FROM righe_prima_nota
            WHERE conto_codice = 'C.II.1'
        """).fetchone()[0]

        totale_debiti = conn.execute("""
            SELECT COALESCE(SUM(avere - dare), 0)
            FROM righe_prima_nota
            WHERE conto_codice = 'D.7'
        """).fetchone()[0]

    return {
        "n_registrazioni": n_registrazioni,
        "n_fatture_importate": n_fatture,
        "n_fatture_da_processare": n_da_processare,
        "n_registrazioni_non_confermate": n_non_confermate,
        "totale_crediti_clienti": Decimal(str(totale_crediti)),
        "totale_debiti_fornitori": Decimal(str(totale_debiti)),
    }


def marca_registrazione_confermata(reg_id: int, db_path: Path = DB_PATH) -> bool:
    """
    Marca una registrazione come confermata dall'utente.

    Args:
        reg_id: ID della registrazione
        db_path: Path al DB

    Returns:
        True se aggiornata con successo
    """
    init_db(db_path)

    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE registrazioni_prima_nota SET confermata = 1 WHERE id = ?",
            (reg_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# IBAN-CoA MAPPING
# ============================================================================

def get_iban_coa_mapping(iban: str, db_path: Path = DB_PATH) -> Dict[str, str]:
    """
    Look up CoA account for an IBAN. Returns default C.IV.1 if no mapping found.

    Args:
        iban: IBAN string
        db_path: Path al DB

    Returns:
        Dict with conto_codice and conto_nome
    """
    init_db(db_path)
    default = {"conto_codice": "C.IV.1", "conto_nome": "Depositi bancari e postali"}
    if not iban:
        return default
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT conto_codice, conto_nome FROM iban_coa_mapping WHERE iban = ?",
            (iban,)
        ).fetchone()
        if row:
            return {"conto_codice": row["conto_codice"], "conto_nome": row["conto_nome"]}
        return default


def save_iban_coa_mapping(
    iban: str,
    conto_codice: str,
    conto_nome: str,
    note: str = "",
    db_path: Path = DB_PATH
) -> int:
    """
    Save or update an IBAN-to-CoA mapping.

    Args:
        iban: IBAN string
        conto_codice: CoA code (e.g. "C.IV.1")
        conto_nome: CoA name
        note: Optional note
        db_path: Path al DB

    Returns:
        Row ID of the inserted/updated mapping
    """
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO iban_coa_mapping (iban, conto_codice, conto_nome, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(iban) DO UPDATE SET
                conto_codice = excluded.conto_codice,
                conto_nome = excluded.conto_nome,
                note = excluded.note
        """, (iban, conto_codice, conto_nome, note))
        conn.commit()
        return cursor.lastrowid


# ============================================================================
# MOVIMENTI BANCARI
# ============================================================================

def salva_movimento_bancario(
    movement: Dict[str, Any],
    db_path: Path = DB_PATH
) -> int:
    """
    Save a confirmed bank movement to DB.

    Args:
        movement: Dict with keys: data, data_valuta, descrizione, importo, saldo, iban, hash_file
        db_path: Path al DB

    Returns:
        Row ID of the inserted movement
    """
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO movimenti_bancari
                (data, data_valuta, descrizione, importo, saldo, iban, hash_file, confermato)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movement.get("data", ""),
            movement.get("data_valuta"),
            movement.get("descrizione", ""),
            float(movement.get("importo", 0)),
            float(movement["saldo"]) if movement.get("saldo") is not None else None,
            movement.get("iban", ""),
            movement.get("hash_file", ""),
            movement.get("confermato", False),
        ))
        conn.commit()
        return cursor.lastrowid
