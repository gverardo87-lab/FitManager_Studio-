"""
cash_categories — SSoT delle categorie di movimento cassa e del predicato "movimento contrattuale".

Implementa il predicato **bidirezionale** di TASSONOMIA_FINANZIARIA.md §2/§7: un CashMovement è
contrattuale se la sua categoria è una di queste — IN (entrata) o OUT (uscita). Serve perché le query
di cassa NON devono classificare un rimborso contrattuale (uscita) come costo operativo, né perdere un
incasso contrattuale (entrata).

Le categorie sono valori TEXT della colonna `CashMovement.categoria` (nessuna DDL). Modulo **neutro**:
zero DB, zero import di router → consumabile ovunque senza cicli. Unica fonte: chi scrive un movimento
contrattuale usa queste costanti; chi aggrega le usa via i predicati.
"""

from __future__ import annotations

# ── Categorie contrattuali (legate a un contratto via id_contratto) ──
CATEGORIA_ACCONTO_CONTRATTO = "ACCONTO_CONTRATTO"    # IN: acconto alla firma
CATEGORIA_PAGAMENTO_RATA = "PAGAMENTO_RATA"          # IN: pagamento rata / incasso residuo diretto (G6)
CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO = "INCASSO_CONGUAGLIO_CONTRATTO"  # IN: incasso del saldo a favore del trainer alla terminazione (G7.9, INCASSA_ORA) o del credito differito (G7.10)
CATEGORIA_RIMBORSO_CONTRATTO = "RIMBORSO_CONTRATTO"  # OUT: rimborso da terminazione anticipata (G7)

# ── Categoria di rettifica (NON-ricavo, id_contratto NULL) ──────────
CATEGORIA_STORNO_SPESA_FISSA = "STORNO_SPESA_FISSA"  # rettifica di un'uscita fissa (legata a spesa ricorrente)

# ── Set di classificazione (predicato contrattuale bidirezionale, §2) ──
# NB: gli aggregati cassa classificano l'inflow per `tipo == 'ENTRATA'` + presenza `id_contratto`
# (mai per allowlist di categoria) → il conguaglio entra come ricavo automaticamente. Questo set è
# la SSoT del predicato (`is_contract_inflow`) e del grep-guard: il conguaglio è un IN contrattuale.
CONTRACT_CASH_IN = frozenset({
    CATEGORIA_ACCONTO_CONTRATTO,
    CATEGORIA_PAGAMENTO_RATA,
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
})
CONTRACT_CASH_OUT = frozenset({CATEGORIA_RIMBORSO_CONTRATTO})
CONTRACT_CASH_CATEGORIES = CONTRACT_CASH_IN | CONTRACT_CASH_OUT


def is_contract_inflow(categoria: str | None) -> bool:
    """ENTRATA contrattuale (acconto/rata) → **+** incassi da contratti."""
    return categoria in CONTRACT_CASH_IN


def is_contract_outflow(categoria: str | None) -> bool:
    """USCITA contrattuale (rimborso) → **−** incassi da contratti (contra-ricavo, NON costo operativo)."""
    return categoria in CONTRACT_CASH_OUT


def is_contract_movement(categoria: str | None) -> bool:
    """Movimento contrattuale in qualsiasi direzione (IN o OUT)."""
    return categoria in CONTRACT_CASH_CATEGORIES


def signed_contractual_amount(categoria: str | None, importo: float) -> float:
    """
    Importo firmato per gli "incassi netti da contratti" (TASSONOMIA §1 Asse 1):
    `+importo` se IN, `-importo` se OUT, `0` se non contrattuale.
    """
    if categoria in CONTRACT_CASH_IN:
        return importo
    if categoria in CONTRACT_CASH_OUT:
        return -importo
    return 0.0


# ════════════════════════════════════════════════════════════════════════════
# G9.4-bis (ADR-022 Addendum II) — il PIANO DEI CONTI ha un nome: ClasseContabile
# ════════════════════════════════════════════════════════════════════════════

from enum import Enum  # noqa: E402 — sezione G9.4-bis, modulo resta zero-DB/zero-ORM


class ClasseContabile(str, Enum):
    """Le 6 classi del piano dei conti de-facto (censimento AUDIT_CENSIMENTO_ASSI_SEMANTICI_CASSA §4).

    Prima di questo enum la mappa viveva inline, ripetuta e leggermente variata, in ~7 superfici di
    aggregazione (stats, burn, forecast, trend, monthly_revenue, recurring, balance) con default
    SILENZIOSO per esclusione — il gemello cattivo della penna fail-loud (INC-2026-07-03)."""

    RICAVO_CONTRATTUALE = "RICAVO_CONTRATTUALE"      # ENTRATA legata a contratto
    ALTRO_INCASSO = "ALTRO_INCASSO"                  # ENTRATA libera (no contratto, no spesa)
    RETTIFICA_COSTO_FISSO = "RETTIFICA_COSTO_FISSO"  # ENTRATA-storno di una spesa fissa
    CONTRA_RICAVO = "CONTRA_RICAVO"                  # USCITA rimborso contrattuale (anche wallet, id_contratto NULL)
    COSTO_FISSO = "COSTO_FISSO"                      # USCITA legata a spesa ricorrente
    COSTO_VARIABILE = "COSTO_VARIABILE"              # USCITA libera


def classify_cash_movement(
    tipo: str,
    categoria: str | None,
    id_contratto: int | None,
    id_spesa_ricorrente: int | None,
) -> ClasseContabile:
    """Classifica un movimento di cassa nel piano dei conti (D-CLASSIFY-SSOT, ADR-022 Add. II).

    **Firma SCALARE** (mai l'oggetto ORM): il modulo resta zero-DB. **Totale per costruzione** sulla
    partizione strutturale (tipo × FK-ness, TASSONOMIA §2 "esaustiva per costruzione") — ogni movimento
    possibile ha una classe. **Fail-loud sulle celle vincolate** (D-LETTURA-FAIL-LOUD, gemello della
    penna): dove la struttura VINCOLA la categoria (movimento agganciato a un contratto), una categoria
    fuori asse è un bug del writer → `ValueError`, mai una classificazione silenziosa per esclusione.
    L'asse A4 (categorie spese/incassi liberi, testo libero) resta APERTO by-design: lì la classe la dà
    la struttura, mai la stringa.
    """
    if tipo == "ENTRATA":
        if id_contratto is not None:
            if categoria not in CONTRACT_CASH_IN:
                raise ValueError(
                    f"classify_cash_movement: ENTRATA con id_contratto ma categoria {categoria!r} "
                    f"fuori da CONTRACT_CASH_IN — movimento scritto fuori dalla penna?"
                )
            return ClasseContabile.RICAVO_CONTRATTUALE
        if id_spesa_ricorrente is not None:
            if categoria != CATEGORIA_STORNO_SPESA_FISSA:
                raise ValueError(
                    f"classify_cash_movement: ENTRATA con id_spesa_ricorrente ma categoria "
                    f"{categoria!r} ≠ {CATEGORIA_STORNO_SPESA_FISSA} — rettifica scritta male?"
                )
            return ClasseContabile.RETTIFICA_COSTO_FISSO
        return ClasseContabile.ALTRO_INCASSO
    if tipo == "USCITA":
        if categoria in CONTRACT_CASH_OUT:
            # Con o senza id_contratto: include l'erogazione wallet (id_contratto NULL, ADR-020)
            return ClasseContabile.CONTRA_RICAVO
        if id_contratto is not None:
            raise ValueError(
                f"classify_cash_movement: USCITA con id_contratto ma categoria {categoria!r} "
                f"fuori da CONTRACT_CASH_OUT — movimento scritto fuori dalla penna?"
            )
        if id_spesa_ricorrente is not None:
            return ClasseContabile.COSTO_FISSO
        return ClasseContabile.COSTO_VARIABILE
    raise ValueError(f"classify_cash_movement: tipo {tipo!r} sconosciuto (atteso ENTRATA|USCITA)")
