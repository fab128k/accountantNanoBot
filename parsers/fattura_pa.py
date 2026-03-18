# parsers/fattura_pa.py
# AccountantNanoBot v1.0.0 - Parser XML FatturaPA
# ============================================================================
# Supporta formato FatturaPA v1.2 (FPR12 - privati, FPA12 - PA)
# Namespace: urn:www.agenziaentrate.gov.it:specificheTecniche:sdi:fatturapa:v1.2
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class Soggetto:
    """Dati anagrafici di un soggetto (cedente o cessionario)."""
    denominazione: str = ""
    nome: str = ""
    cognome: str = ""
    partita_iva: str = ""
    codice_fiscale: str = ""
    indirizzo: str = ""
    cap: str = ""
    comune: str = ""
    provincia: str = ""
    nazione: str = "IT"

    @property
    def nome_completo(self) -> str:
        if self.denominazione:
            return self.denominazione
        return f"{self.nome} {self.cognome}".strip()

    @property
    def identificativo(self) -> str:
        return self.partita_iva or self.codice_fiscale


@dataclass
class DettaglioLinea:
    """Singola riga del corpo fattura."""
    numero: int = 0
    descrizione: str = ""
    quantita: Decimal = Decimal("1")
    unita_misura: str = ""
    prezzo_unitario: Decimal = Decimal("0")
    aliquota_iva: Decimal = Decimal("0")
    importo: Decimal = Decimal("0")
    natura: str = ""  # N1-N7 per operazioni senza IVA


@dataclass
class RiepilogoIVA:
    """Riepilogo IVA per aliquota."""
    aliquota: Decimal = Decimal("0")
    imponibile: Decimal = Decimal("0")
    imposta: Decimal = Decimal("0")
    natura: str = ""
    esigibilita_iva: str = "I"  # I=immediata, D=differita, S=scissione


@dataclass
class DatiPagamento:
    """Dati di pagamento della fattura."""
    condizioni: str = ""        # TP01=rate, TP02=completo, TP03=anticipo
    modalita: str = ""          # MP01=contanti, MP05=bonifico, ecc.
    data_scadenza: Optional[date] = None
    importo_pagamento: Decimal = Decimal("0")
    iban: str = ""


@dataclass
class FatturaPA:
    """
    Rappresentazione strutturata di una FatturaPA.

    Una singola fattura può contenere più corpi (FatturaElettronicaBody)
    ma per semplicità gestiamo il caso standard di 1 body.
    """
    # Header
    progressivo_invio: str = ""
    formato: str = "FPR12"          # FPR12=privati, FPA12=PA

    # Soggetti
    cedente: Soggetto = field(default_factory=Soggetto)
    cessionario: Soggetto = field(default_factory=Soggetto)

    # Dati documento
    tipo_documento: str = "TD01"    # TD01=fattura, TD04=nota credito, ecc.
    data: Optional[date] = None
    numero: str = ""
    divisa: str = "EUR"

    # Importi
    importo_totale: Decimal = Decimal("0")

    # Righe e riepiloghi
    linee: List[DettaglioLinea] = field(default_factory=list)
    riepilogo_iva: List[RiepilogoIVA] = field(default_factory=list)
    pagamenti: List[DatiPagamento] = field(default_factory=list)

    # Metadati
    xml_path: Optional[str] = None

    @property
    def imponibile_totale(self) -> Decimal:
        return sum(r.imponibile for r in self.riepilogo_iva)

    @property
    def iva_totale(self) -> Decimal:
        return sum(r.imposta for r in self.riepilogo_iva)

    @property
    def is_nota_credito(self) -> bool:
        return self.tipo_documento in ("TD04",)

    @property
    def descrizione_tipo(self) -> str:
        from config.constants import TIPI_DOCUMENTO_FATTURA
        return TIPI_DOCUMENTO_FATTURA.get(self.tipo_documento, self.tipo_documento)


# ============================================================================
# PARSER
# ============================================================================

class FatturaPAParser:
    """
    Parser per file XML FatturaPA v1.2.

    Gestisce sia il namespace esplicito che assente.
    Supporta file con più corpi fattura (multipla).
    """

    NAMESPACE = "urn:www.agenziaentrate.gov.it:specificheTecniche:sdi:fatturapa:v1.2"

    def parse_file(self, xml_path: str | Path) -> List[FatturaPA]:
        """
        Parsa un file XML FatturaPA dal disco.

        Args:
            xml_path: Path al file XML

        Returns:
            Lista di FatturaPA (una per ogni body nel file)
        """
        xml_path = Path(xml_path)
        with open(xml_path, "rb") as f:
            xml_bytes = f.read()

        fatture = self.parse_bytes(xml_bytes)
        for f in fatture:
            f.xml_path = str(xml_path)
        return fatture

    def parse_bytes(self, xml_bytes: bytes) -> List[FatturaPA]:
        """
        Parsa bytes XML FatturaPA.

        Args:
            xml_bytes: Contenuto XML in bytes

        Returns:
            Lista di FatturaPA
        """
        try:
            from lxml import etree
            root = etree.fromstring(xml_bytes)
        except ImportError:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            raise ValueError(f"XML non valido: {e}")

        return self._parse_root(root)

    def _ns(self, tag: str) -> str:
        """Ritorna tag con namespace."""
        return f"{{{self.NAMESPACE}}}{tag}"

    def _find(self, element, path: str):
        """
        Cerca elemento con o senza namespace.
        Prova prima con namespace, poi senza.
        """
        # Con namespace
        ns_path = "/".join(f"{{{self.NAMESPACE}}}{p}" for p in path.split("/"))
        result = element.find(ns_path)
        if result is not None:
            return result
        # Senza namespace
        return element.find(path)

    def _findall(self, element, path: str) -> list:
        """Cerca tutti gli elementi con o senza namespace."""
        ns_path = "/".join(f"{{{self.NAMESPACE}}}{p}" for p in path.split("/"))
        results = element.findall(ns_path)
        if results:
            return results
        return element.findall(path)

    def _text(self, element, path: str, default: str = "") -> str:
        """Estrae testo da un elemento figlio."""
        el = self._find(element, path)
        if el is not None and el.text:
            return el.text.strip()
        return default

    def _decimal(self, element, path: str, default: Decimal = Decimal("0")) -> Decimal:
        """Estrae valore decimale da un elemento figlio."""
        text = self._text(element, path)
        if not text:
            return default
        try:
            # FatturaPA usa virgola o punto come separatore
            return Decimal(text.replace(",", "."))
        except InvalidOperation:
            return default

    def _date(self, element, path: str) -> Optional[date]:
        """Estrae data da un elemento figlio (formato YYYY-MM-DD)."""
        text = self._text(element, path)
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except (ValueError, AttributeError):
            return None

    def _parse_root(self, root) -> List[FatturaPA]:
        """Parsa il root element FatturaElettronica."""
        # Header comune
        header = self._find(root, "FatturaElettronicaHeader")
        if header is None:
            return []

        cedente = self._parse_cedente(header)
        cessionario = self._parse_cessionario(header)
        progressivo = self._text(header, "DatiTrasmissione/ProgressivoInvio")
        formato = self._text(header, "DatiTrasmissione/FormatoTrasmissione", "FPR12")

        # Uno o più body
        bodies = self._findall(root, "FatturaElettronicaBody")
        fatture = []

        for body in bodies:
            fattura = FatturaPA(
                progressivo_invio=progressivo,
                formato=formato,
                cedente=cedente,
                cessionario=cessionario,
            )
            self._parse_body(body, fattura)
            fatture.append(fattura)

        return fatture

    def _parse_cedente(self, header) -> Soggetto:
        """Parsa dati cedente/prestatore."""
        cedente_el = self._find(header, "CedentePrestatore")
        if cedente_el is None:
            return Soggetto()

        return Soggetto(
            denominazione=self._text(cedente_el, "DatiAnagrafici/Anagrafica/Denominazione"),
            nome=self._text(cedente_el, "DatiAnagrafici/Anagrafica/Nome"),
            cognome=self._text(cedente_el, "DatiAnagrafici/Anagrafica/Cognome"),
            partita_iva=self._text(cedente_el, "DatiAnagrafici/IdFiscaleIVA/IdCodice"),
            codice_fiscale=self._text(cedente_el, "DatiAnagrafici/CodiceFiscale"),
            indirizzo=self._text(cedente_el, "Sede/Indirizzo"),
            cap=self._text(cedente_el, "Sede/CAP"),
            comune=self._text(cedente_el, "Sede/Comune"),
            provincia=self._text(cedente_el, "Sede/Provincia"),
            nazione=self._text(cedente_el, "Sede/Nazione", "IT"),
        )

    def _parse_cessionario(self, header) -> Soggetto:
        """Parsa dati cessionario/committente."""
        cessionario_el = self._find(header, "CessionarioCommittente")
        if cessionario_el is None:
            return Soggetto()

        return Soggetto(
            denominazione=self._text(cessionario_el, "DatiAnagrafici/Anagrafica/Denominazione"),
            nome=self._text(cessionario_el, "DatiAnagrafici/Anagrafica/Nome"),
            cognome=self._text(cessionario_el, "DatiAnagrafici/Anagrafica/Cognome"),
            partita_iva=self._text(cessionario_el, "DatiAnagrafici/IdFiscaleIVA/IdCodice"),
            codice_fiscale=self._text(cessionario_el, "DatiAnagrafici/CodiceFiscale"),
            indirizzo=self._text(cessionario_el, "Sede/Indirizzo"),
            cap=self._text(cessionario_el, "Sede/CAP"),
            comune=self._text(cessionario_el, "Sede/Comune"),
            provincia=self._text(cessionario_el, "Sede/Provincia"),
            nazione=self._text(cessionario_el, "Sede/Nazione", "IT"),
        )

    def _parse_body(self, body, fattura: FatturaPA) -> None:
        """Parsa un FatturaElettronicaBody."""
        dati_gen = self._find(body, "DatiGenerali/DatiGeneraliDocumento")
        if dati_gen is not None:
            fattura.tipo_documento = self._text(dati_gen, "TipoDocumento", "TD01")
            fattura.data = self._date(dati_gen, "Data")
            fattura.numero = self._text(dati_gen, "Numero")
            fattura.divisa = self._text(dati_gen, "Divisa", "EUR")
            fattura.importo_totale = self._decimal(dati_gen, "ImportoTotaleDocumento")

        # Righe
        linee_els = self._findall(body, "DatiBeniServizi/DettaglioLinee")
        for linea_el in linee_els:
            linea = DettaglioLinea(
                numero=int(self._text(linea_el, "NumeroLinea", "0")),
                descrizione=self._text(linea_el, "Descrizione"),
                quantita=self._decimal(linea_el, "Quantita", Decimal("1")),
                unita_misura=self._text(linea_el, "UnitaMisura"),
                prezzo_unitario=self._decimal(linea_el, "PrezzoUnitario"),
                aliquota_iva=self._decimal(linea_el, "AliquotaIVA"),
                importo=self._decimal(linea_el, "PrezzoTotale"),
                natura=self._text(linea_el, "Natura"),
            )
            fattura.linee.append(linea)

        # Riepilogo IVA
        riep_els = self._findall(body, "DatiBeniServizi/DatiRiepilogo")
        for riep_el in riep_els:
            riep = RiepilogoIVA(
                aliquota=self._decimal(riep_el, "AliquotaIVA"),
                imponibile=self._decimal(riep_el, "ImponibileImporto"),
                imposta=self._decimal(riep_el, "Imposta"),
                natura=self._text(riep_el, "Natura"),
                esigibilita_iva=self._text(riep_el, "EsigibilitaIVA", "I"),
            )
            fattura.riepilogo_iva.append(riep)

        # Pagamenti
        pag_els = self._findall(body, "DatiPagamento")
        for pag_el in pag_els:
            condizioni = self._text(pag_el, "CondizioniPagamento")
            det_els = self._findall(pag_el, "DettaglioPagamento")
            for det_el in det_els:
                pag = DatiPagamento(
                    condizioni=condizioni,
                    modalita=self._text(det_el, "ModalitaPagamento"),
                    data_scadenza=self._date(det_el, "DataScadenzaPagamento"),
                    importo_pagamento=self._decimal(det_el, "ImportoPagamento"),
                    iban=self._text(det_el, "IBAN"),
                )
                fattura.pagamenti.append(pag)

    def to_text_summary(self, fattura: FatturaPA) -> str:
        """
        Genera testo leggibile della fattura per indicizzazione RAG.

        Args:
            fattura: FatturaPA già parsata

        Returns:
            Testo strutturato della fattura
        """
        lines = [
            f"=== FATTURA {fattura.numero} ===",
            f"Tipo: {fattura.descrizione_tipo} ({fattura.tipo_documento})",
            f"Data: {fattura.data.isoformat() if fattura.data else 'N/D'}",
            f"",
            f"FORNITORE (Cedente):",
            f"  Nome: {fattura.cedente.nome_completo}",
            f"  P.IVA: {fattura.cedente.partita_iva or 'N/D'}",
            f"  Indirizzo: {fattura.cedente.indirizzo}, {fattura.cedente.cap} {fattura.cedente.comune} ({fattura.cedente.provincia})",
            f"",
            f"CLIENTE (Cessionario):",
            f"  Nome: {fattura.cessionario.nome_completo}",
            f"  P.IVA: {fattura.cessionario.partita_iva or 'N/D'}",
            f"",
            f"IMPORTI:",
            f"  Imponibile: €{fattura.imponibile_totale:.2f}",
            f"  IVA: €{fattura.iva_totale:.2f}",
            f"  Totale: €{fattura.importo_totale:.2f}",
            f"  Divisa: {fattura.divisa}",
        ]

        if fattura.linee:
            lines.append("")
            lines.append("DETTAGLIO RIGHE:")
            for linea in fattura.linee:
                lines.append(
                    f"  {linea.numero}. {linea.descrizione} | "
                    f"Qtà: {linea.quantita} | "
                    f"Prezzo: €{linea.prezzo_unitario:.2f} | "
                    f"IVA: {linea.aliquota_iva}% | "
                    f"Totale: €{linea.importo:.2f}"
                )

        if fattura.riepilogo_iva:
            lines.append("")
            lines.append("RIEPILOGO IVA:")
            for riep in fattura.riepilogo_iva:
                if riep.natura:
                    lines.append(f"  Natura {riep.natura}: Imponibile €{riep.imponibile:.2f}")
                else:
                    lines.append(
                        f"  Aliquota {riep.aliquota}%: "
                        f"Imponibile €{riep.imponibile:.2f} | "
                        f"Imposta €{riep.imposta:.2f}"
                    )

        if fattura.pagamenti:
            lines.append("")
            lines.append("PAGAMENTI:")
            for pag in fattura.pagamenti:
                scad = pag.data_scadenza.isoformat() if pag.data_scadenza else "N/D"
                lines.append(
                    f"  Modalità: {pag.modalita} | "
                    f"Scadenza: {scad} | "
                    f"Importo: €{pag.importo_pagamento:.2f}"
                )
                if pag.iban:
                    lines.append(f"  IBAN: {pag.iban}")

        return "\n".join(lines)

    def to_prima_nota_suggestion(
        self,
        fattura: FatturaPA,
        is_acquisto: bool,
        company_piva: str = ""
    ) -> dict:
        """
        Suggerisce la registrazione di prima nota per la fattura.

        La logica segue il principio della partita doppia:
        - Fattura di ACQUISTO:
            Dare: Costo (classe B CE) + IVA a credito
            Avere: Debito vs fornitore
        - Fattura di VENDITA:
            Dare: Credito vs cliente
            Avere: Ricavo (classe A CE) + IVA a debito

        Args:
            fattura: FatturaPA parsata
            is_acquisto: True se è una fattura di acquisto, False se vendita
            company_piva: P.IVA dell'azienda (per determinare automaticamente)

        Returns:
            Dict con struttura suggerita per RegistrazionePrimaNota
        """
        # Determina automaticamente se acquisto o vendita
        if company_piva:
            is_acquisto = fattura.cedente.partita_iva != company_piva

        righe = []

        if is_acquisto:
            # Acquisto da fornitore
            for riep in fattura.riepilogo_iva:
                if riep.imponibile > 0:
                    righe.append({
                        "conto_codice": "B.6",  # Costi per materie prime / merci
                        "conto_nome": f"Acquisti da {fattura.cedente.nome_completo}",
                        "dare": float(riep.imponibile),
                        "avere": 0.0,
                        "descrizione": f"Imponibile acquisto - {fattura.numero}",
                    })
                if riep.imposta > 0:
                    righe.append({
                        "conto_codice": "C.II.4-bis",  # IVA a credito
                        "conto_nome": "IVA a credito",
                        "dare": float(riep.imposta),
                        "avere": 0.0,
                        "descrizione": f"IVA {riep.aliquota}% - {fattura.numero}",
                    })
            righe.append({
                "conto_codice": "D.7",   # Debiti vs fornitori
                "conto_nome": f"Debiti v/{fattura.cedente.nome_completo}",
                "dare": 0.0,
                "avere": float(fattura.importo_totale),
                "descrizione": f"Fattura fornitore {fattura.numero} del {fattura.data}",
            })
        else:
            # Vendita a cliente
            righe.append({
                "conto_codice": "C.II.1",  # Crediti vs clienti
                "conto_nome": f"Crediti v/{fattura.cessionario.nome_completo}",
                "dare": float(fattura.importo_totale),
                "avere": 0.0,
                "descrizione": f"Fattura cliente {fattura.numero} del {fattura.data}",
            })
            for riep in fattura.riepilogo_iva:
                if riep.imponibile > 0:
                    righe.append({
                        "conto_codice": "A.1",  # Ricavi vendite
                        "conto_nome": f"Ricavi da {fattura.cessionario.nome_completo}",
                        "dare": 0.0,
                        "avere": float(riep.imponibile),
                        "descrizione": f"Ricavo - {fattura.numero}",
                    })
                if riep.imposta > 0:
                    righe.append({
                        "conto_codice": "D.12",  # IVA a debito
                        "conto_nome": "IVA a debito",
                        "dare": 0.0,
                        "avere": float(riep.imposta),
                        "descrizione": f"IVA {riep.aliquota}% - {fattura.numero}",
                    })

        return {
            "data": fattura.data.isoformat() if fattura.data else "",
            "tipo": "FATTURA_ACQUISTO" if is_acquisto else "FATTURA_VENDITA",
            "descrizione": (
                f"{'Acquisto da' if is_acquisto else 'Vendita a'} "
                f"{fattura.cedente.nome_completo if is_acquisto else fattura.cessionario.nome_completo} - "
                f"Ft. {fattura.numero}"
            ),
            "fattura_riferimento": fattura.numero,
            "righe": righe,
            "totale_dare": sum(r["dare"] for r in righe),
            "totale_avere": sum(r["avere"] for r in righe),
            "bilanciata": abs(
                sum(r["dare"] for r in righe) - sum(r["avere"] for r in righe)
            ) < 0.01,
        }


# ============================================================================
# CLI HELPER
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python -m parsers.fattura_pa <file.xml>")
        sys.exit(1)

    parser = FatturaPAParser()
    try:
        fatture = parser.parse_file(sys.argv[1])
        for f in fatture:
            print(parser.to_text_summary(f))
            print()
            suggestion = parser.to_prima_nota_suggestion(f, is_acquisto=True)
            print("=== SUGGERIMENTO PRIMA NOTA ===")
            for riga in suggestion["righe"]:
                print(f"  {riga['conto_codice']} {riga['conto_nome']}: D={riga['dare']:.2f} A={riga['avere']:.2f}")
            print(f"  Bilanciata: {suggestion['bilanciata']}")
    except Exception as e:
        print(f"Errore: {e}")
        sys.exit(1)
