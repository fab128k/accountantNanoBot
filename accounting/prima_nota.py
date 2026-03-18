# accounting/prima_nota.py
# AccountantNanoBot v1.0.0 - Sistema Prima Nota (Partita Doppia)
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Tuple


class TipoRegistrazione(str, Enum):
    """Tipo di registrazione contabile."""
    FATTURA_ACQUISTO = "FATTURA_ACQUISTO"
    FATTURA_VENDITA = "FATTURA_VENDITA"
    NOTA_CREDITO_ACQUISTO = "NOTA_CREDITO_ACQUISTO"
    NOTA_CREDITO_VENDITA = "NOTA_CREDITO_VENDITA"
    PAGAMENTO_FORNITORE = "PAGAMENTO_FORNITORE"
    INCASSO_CLIENTE = "INCASSO_CLIENTE"
    STIPENDIO = "STIPENDIO"
    VERSAMENTO_IVA = "VERSAMENTO_IVA"
    F24 = "F24"
    AMMORTAMENTO = "AMMORTAMENTO"
    GENERICO = "GENERICO"

    @property
    def descrizione(self) -> str:
        descrizioni = {
            "FATTURA_ACQUISTO": "Fattura di acquisto",
            "FATTURA_VENDITA": "Fattura di vendita",
            "NOTA_CREDITO_ACQUISTO": "Nota di credito da fornitore",
            "NOTA_CREDITO_VENDITA": "Nota di credito a cliente",
            "PAGAMENTO_FORNITORE": "Pagamento fornitore",
            "INCASSO_CLIENTE": "Incasso da cliente",
            "STIPENDIO": "Pagamento stipendi",
            "VERSAMENTO_IVA": "Versamento IVA periodica",
            "F24": "Pagamento F24",
            "AMMORTAMENTO": "Quota ammortamento",
            "GENERICO": "Registrazione generica",
        }
        return descrizioni.get(self.value, self.value)


@dataclass
class RigaPrimaNota:
    """
    Singola riga di una registrazione in prima nota.

    In partita doppia ogni riga ha DARE (addebito) o AVERE (accredito).
    Una delle due deve essere 0.
    """
    conto_codice: str
    conto_nome: str
    dare: Decimal = Decimal("0")
    avere: Decimal = Decimal("0")
    descrizione: str = ""

    def __post_init__(self):
        # Conversione da float/int se necessario
        if not isinstance(self.dare, Decimal):
            self.dare = Decimal(str(self.dare))
        if not isinstance(self.avere, Decimal):
            self.avere = Decimal(str(self.avere))

    @property
    def is_dare(self) -> bool:
        return self.dare > 0

    @property
    def importo(self) -> Decimal:
        return self.dare if self.is_dare else self.avere

    def valida(self) -> Tuple[bool, str]:
        """Valida la singola riga."""
        if self.dare > 0 and self.avere > 0:
            return False, f"Riga '{self.conto_codice}': dare e avere non possono essere entrambi > 0"
        if self.dare == 0 and self.avere == 0:
            return False, f"Riga '{self.conto_codice}': almeno uno tra dare e avere deve essere > 0"
        if not self.conto_codice:
            return False, "Codice conto mancante"
        return True, "OK"


@dataclass
class RegistrazionePrimaNota:
    """
    Registrazione completa in prima nota (partita doppia).

    Una registrazione è bilanciata quando:
        ∑ DARE == ∑ AVERE
    """
    data: date
    tipo: TipoRegistrazione
    descrizione: str
    righe: List[RigaPrimaNota] = field(default_factory=list)
    fattura_riferimento: str = ""
    numero_progressivo: Optional[int] = None
    creata_da_agente: bool = False
    confermata: bool = False  # True solo dopo review umana

    @property
    def totale_dare(self) -> Decimal:
        return sum(r.dare for r in self.righe)

    @property
    def totale_avere(self) -> Decimal:
        return sum(r.avere for r in self.righe)

    @property
    def differenza(self) -> Decimal:
        return abs(self.totale_dare - self.totale_avere)

    @property
    def is_bilanciata(self) -> bool:
        """True se ∑DARE == ∑AVERE (tolleranza 1 centesimo)."""
        return self.differenza < Decimal("0.01")

    def valida(self) -> Tuple[bool, List[str]]:
        """
        Valida la registrazione completa.

        Returns:
            Tupla (valida, lista_errori)
        """
        errori = []

        if not self.righe:
            errori.append("La registrazione deve avere almeno una riga")
            return False, errori

        if len(self.righe) < 2:
            errori.append("La partita doppia richiede almeno 2 righe")

        # Valida singole righe
        for riga in self.righe:
            ok, msg = riga.valida()
            if not ok:
                errori.append(msg)

        # Controlla bilanciamento
        if not self.is_bilanciata:
            errori.append(
                f"Registrazione non bilanciata: "
                f"DARE={self.totale_dare:.2f} ≠ AVERE={self.totale_avere:.2f} "
                f"(differenza: {self.differenza:.2f})"
            )

        return len(errori) == 0, errori

    def to_dict(self) -> dict:
        """Serializza per salvataggio DB."""
        return {
            "data": self.data.isoformat(),
            "tipo": self.tipo.value,
            "descrizione": self.descrizione,
            "fattura_riferimento": self.fattura_riferimento,
            "numero_progressivo": self.numero_progressivo,
            "creata_da_agente": self.creata_da_agente,
            "confermata": self.confermata,
            "righe": [
                {
                    "conto_codice": r.conto_codice,
                    "conto_nome": r.conto_nome,
                    "dare": float(r.dare),
                    "avere": float(r.avere),
                    "descrizione": r.descrizione,
                }
                for r in self.righe
            ],
        }

    @classmethod
    def from_suggestion(cls, suggestion: dict) -> "RegistrazionePrimaNota":
        """
        Crea registrazione da suggerimento del FatturazioneAgent.

        Args:
            suggestion: Dict ritornato da FatturaPAParser.to_prima_nota_suggestion()
        """
        from datetime import date as date_type

        data_str = suggestion.get("data", "")
        try:
            data = date_type.fromisoformat(data_str)
        except (ValueError, TypeError):
            data = date_type.today()

        tipo_str = suggestion.get("tipo", "GENERICO")
        try:
            tipo = TipoRegistrazione(tipo_str)
        except ValueError:
            tipo = TipoRegistrazione.GENERICO

        righe = []
        for r in suggestion.get("righe", []):
            righe.append(RigaPrimaNota(
                conto_codice=r["conto_codice"],
                conto_nome=r["conto_nome"],
                dare=Decimal(str(r.get("dare", 0))),
                avere=Decimal(str(r.get("avere", 0))),
                descrizione=r.get("descrizione", ""),
            ))

        return cls(
            data=data,
            tipo=tipo,
            descrizione=suggestion.get("descrizione", ""),
            fattura_riferimento=suggestion.get("fattura_riferimento", ""),
            righe=righe,
            creata_da_agente=True,
            confermata=False,
        )

    def __str__(self) -> str:
        lines = [
            f"Registrazione {self.numero_progressivo or 'N/A'} - {self.data}",
            f"Tipo: {self.tipo.descrizione}",
            f"Descrizione: {self.descrizione}",
            f"",
        ]
        for riga in self.righe:
            dare_str = f"D: €{riga.dare:.2f}" if riga.dare > 0 else ""
            avere_str = f"A: €{riga.avere:.2f}" if riga.avere > 0 else ""
            lines.append(f"  {riga.conto_codice} {riga.conto_nome}: {dare_str}{avere_str}")

        lines.append(f"")
        lines.append(f"  TOTALI: DARE €{self.totale_dare:.2f} | AVERE €{self.totale_avere:.2f}")
        lines.append(f"  {'✅ BILANCIATA' if self.is_bilanciata else '❌ NON BILANCIATA'}")

        return "\n".join(lines)
