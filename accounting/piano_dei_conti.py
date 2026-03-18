# accounting/piano_dei_conti.py
# AccountantNanoBot v1.0.0 - Piano dei Conti OIC
# ============================================================================
# Struttura basata su OIC (Organismo Italiano di Contabilità)
# Riferimento: art. 2424-2426 Codice Civile
# ============================================================================

from typing import Dict, List, Optional, Tuple


# ============================================================================
# PIANO DEI CONTI OIC
# ============================================================================

PIANO_DEI_CONTI: Dict[str, Dict] = {
    # =====================================================================
    # STATO PATRIMONIALE - ATTIVO
    # =====================================================================

    # A) CREDITI VS SOCI
    "A": {
        "codice": "A",
        "nome": "Crediti verso soci per versamenti ancora dovuti",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },

    # B) IMMOBILIZZAZIONI
    "B": {
        "codice": "B",
        "nome": "Immobilizzazioni",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.I": {
        "codice": "B.I",
        "nome": "Immobilizzazioni immateriali",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.I.1": {
        "codice": "B.I.1",
        "nome": "Costi di impianto e ampliamento",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.I.2": {
        "codice": "B.I.2",
        "nome": "Costi di sviluppo",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.I.3": {
        "codice": "B.I.3",
        "nome": "Diritti di brevetto industriale e diritti di utilizzazione delle opere dell'ingegno",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.I.4": {
        "codice": "B.I.4",
        "nome": "Concessioni, licenze, marchi e diritti simili",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.I.5": {
        "codice": "B.I.5",
        "nome": "Avviamento",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.II": {
        "codice": "B.II",
        "nome": "Immobilizzazioni materiali",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.II.1": {
        "codice": "B.II.1",
        "nome": "Terreni e fabbricati",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.II.2": {
        "codice": "B.II.2",
        "nome": "Impianti e macchinari",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.II.3": {
        "codice": "B.II.3",
        "nome": "Attrezzature industriali e commerciali",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.II.4": {
        "codice": "B.II.4",
        "nome": "Altri beni",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "B.II.5": {
        "codice": "B.II.5",
        "nome": "Immobilizzazioni in corso e acconti",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },

    # C) ATTIVO CIRCOLANTE
    "C": {
        "codice": "C",
        "nome": "Attivo circolante",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.I": {
        "codice": "C.I",
        "nome": "Rimanenze",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.I.1": {
        "codice": "C.I.1",
        "nome": "Materie prime, sussidiarie e di consumo",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.I.2": {
        "codice": "C.I.2",
        "nome": "Prodotti in corso di lavorazione e semilavorati",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.I.4": {
        "codice": "C.I.4",
        "nome": "Prodotti finiti e merci",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.II": {
        "codice": "C.II",
        "nome": "Crediti",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.II.1": {
        "codice": "C.II.1",
        "nome": "Crediti verso clienti",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.II.4-bis": {
        "codice": "C.II.4-bis",
        "nome": "IVA a credito",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.II.5": {
        "codice": "C.II.5",
        "nome": "Crediti verso altri",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.IV": {
        "codice": "C.IV",
        "nome": "Disponibilità liquide",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.IV.1": {
        "codice": "C.IV.1",
        "nome": "Depositi bancari e postali",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.IV.2": {
        "codice": "C.IV.2",
        "nome": "Assegni",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },
    "C.IV.3": {
        "codice": "C.IV.3",
        "nome": "Denaro e valori in cassa",
        "sezione": "ATTIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "D",
    },

    # =====================================================================
    # STATO PATRIMONIALE - PASSIVO
    # =====================================================================

    # A) PATRIMONIO NETTO
    "PN.A": {
        "codice": "PN.A",
        "nome": "Patrimonio netto",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "PN.A.I": {
        "codice": "PN.A.I",
        "nome": "Capitale sociale",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "PN.A.IV": {
        "codice": "PN.A.IV",
        "nome": "Riserva legale",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "PN.A.IX": {
        "codice": "PN.A.IX",
        "nome": "Utile (perdita) dell'esercizio",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },

    # B) FONDI RISCHI E ONERI
    "B": {
        "codice": "B",
        "nome": "Fondi per rischi e oneri",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },

    # C) TFR
    "C.TFR": {
        "codice": "C.TFR",
        "nome": "Trattamento di fine rapporto di lavoro subordinato",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },

    # D) DEBITI
    "D": {
        "codice": "D",
        "nome": "Debiti",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "D.4": {
        "codice": "D.4",
        "nome": "Debiti verso banche",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "D.7": {
        "codice": "D.7",
        "nome": "Debiti verso fornitori",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "D.12": {
        "codice": "D.12",
        "nome": "IVA a debito",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "D.13": {
        "codice": "D.13",
        "nome": "Debiti tributari",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },
    "D.14": {
        "codice": "D.14",
        "nome": "Debiti verso istituti previdenziali e di sicurezza sociale",
        "sezione": "PASSIVO",
        "tipo": "PATRIMONIALE",
        "dare_avere": "A",
    },

    # =====================================================================
    # CONTO ECONOMICO
    # =====================================================================

    # A) VALORE DELLA PRODUZIONE
    "A.1": {
        "codice": "A.1",
        "nome": "Ricavi delle vendite e delle prestazioni",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },
    "A.2": {
        "codice": "A.2",
        "nome": "Variazioni delle rimanenze di prodotti in lavorazione, semilavorati e finiti",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },
    "A.5": {
        "codice": "A.5",
        "nome": "Altri ricavi e proventi",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },

    # B) COSTI DELLA PRODUZIONE
    "B.6": {
        "codice": "B.6",
        "nome": "Per materie prime, sussidiarie, di consumo e di merci",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.7": {
        "codice": "B.7",
        "nome": "Per servizi",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.8": {
        "codice": "B.8",
        "nome": "Per godimento di beni di terzi",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.9": {
        "codice": "B.9",
        "nome": "Per il personale",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.9.a": {
        "codice": "B.9.a",
        "nome": "Salari e stipendi",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.9.b": {
        "codice": "B.9.b",
        "nome": "Oneri sociali",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.9.c": {
        "codice": "B.9.c",
        "nome": "Trattamento di fine rapporto",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.10": {
        "codice": "B.10",
        "nome": "Ammortamenti e svalutazioni",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.10.a": {
        "codice": "B.10.a",
        "nome": "Ammortamento delle immobilizzazioni immateriali",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.10.b": {
        "codice": "B.10.b",
        "nome": "Ammortamento delle immobilizzazioni materiali",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
    "B.14": {
        "codice": "B.14",
        "nome": "Oneri diversi di gestione",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },

    # C) PROVENTI E ONERI FINANZIARI
    "C.15": {
        "codice": "C.15",
        "nome": "Proventi da partecipazioni",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },
    "C.16": {
        "codice": "C.16",
        "nome": "Altri proventi finanziari",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },
    "C.17": {
        "codice": "C.17",
        "nome": "Interessi e altri oneri finanziari",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },

    # D) RETTIFICHE DI VALORE
    "D.18": {
        "codice": "D.18",
        "nome": "Rivalutazioni",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },
    "D.19": {
        "codice": "D.19",
        "nome": "Svalutazioni",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },

    # E) PROVENTI E ONERI STRAORDINARI (abrogato ma ancora usato)
    "E.20": {
        "codice": "E.20",
        "nome": "Proventi straordinari",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "A",
    },
    "E.21": {
        "codice": "E.21",
        "nome": "Oneri straordinari",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },

    # IMPOSTE
    "CE.22": {
        "codice": "CE.22",
        "nome": "Imposte sul reddito dell'esercizio (IRES/IRAP)",
        "sezione": "CONTO_ECONOMICO",
        "tipo": "ECONOMICO",
        "dare_avere": "D",
    },
}


# ============================================================================
# FUNZIONI DI RICERCA E NAVIGAZIONE
# ============================================================================

def cerca_conto(query: str) -> List[Dict]:
    """
    Cerca conti nel piano dei conti per codice o nome (case-insensitive).

    Args:
        query: Stringa di ricerca

    Returns:
        Lista di conti corrispondenti (max 20)
    """
    query_lower = query.lower().strip()
    results = []

    for codice, conto in PIANO_DEI_CONTI.items():
        if (
            query_lower in codice.lower() or
            query_lower in conto["nome"].lower()
        ):
            results.append(conto)

        if len(results) >= 20:
            break

    return results


def get_conto(codice: str) -> Optional[Dict]:
    """
    Ritorna dati di un conto specifico per codice.

    Args:
        codice: Codice conto (es. "C.II.1")

    Returns:
        Dict conto o None se non trovato
    """
    return PIANO_DEI_CONTI.get(codice)


def get_conti_by_sezione(sezione: str) -> List[Dict]:
    """
    Ritorna tutti i conti di una sezione.

    Args:
        sezione: "ATTIVO" | "PASSIVO" | "CONTO_ECONOMICO"

    Returns:
        Lista di conti nella sezione
    """
    return [
        conto for conto in PIANO_DEI_CONTI.values()
        if conto["sezione"] == sezione
    ]


def validate_conto(codice: str) -> Tuple[bool, str]:
    """
    Verifica se un codice conto è valido nel piano dei conti.

    Args:
        codice: Codice conto da validare

    Returns:
        Tupla (valido, messaggio)
    """
    conto = get_conto(codice)
    if conto:
        return True, f"Conto valido: {conto['nome']}"
    return False, f"Conto non trovato nel piano dei conti OIC: {codice}"


def get_conti_comuni() -> Dict[str, List[Dict]]:
    """
    Ritorna i conti più comunemente usati, raggruppati per categoria.

    Returns:
        Dict con categorie e relativi conti
    """
    return {
        "Crediti vs clienti": [PIANO_DEI_CONTI.get("C.II.1")],
        "Debiti vs fornitori": [PIANO_DEI_CONTI.get("D.7")],
        "IVA a credito": [PIANO_DEI_CONTI.get("C.II.4-bis")],
        "IVA a debito": [PIANO_DEI_CONTI.get("D.12")],
        "Cassa": [PIANO_DEI_CONTI.get("C.IV.3")],
        "Banca": [PIANO_DEI_CONTI.get("C.IV.1")],
        "Ricavi": [PIANO_DEI_CONTI.get("A.1"), PIANO_DEI_CONTI.get("A.5")],
        "Acquisti": [PIANO_DEI_CONTI.get("B.6"), PIANO_DEI_CONTI.get("B.7")],
        "Personale": [PIANO_DEI_CONTI.get("B.9.a"), PIANO_DEI_CONTI.get("B.9.b")],
    }
