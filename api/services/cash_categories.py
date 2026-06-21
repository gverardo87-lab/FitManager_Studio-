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
CATEGORIA_RIMBORSO_CONTRATTO = "RIMBORSO_CONTRATTO"  # OUT: rimborso da terminazione anticipata (G7)

# ── Categoria di rettifica (NON-ricavo, id_contratto NULL) ──────────
CATEGORIA_STORNO_SPESA_FISSA = "STORNO_SPESA_FISSA"  # rettifica di un'uscita fissa (legata a spesa ricorrente)

# ── Set di classificazione (predicato contrattuale bidirezionale, §2) ──
CONTRACT_CASH_IN = frozenset({CATEGORIA_ACCONTO_CONTRATTO, CATEGORIA_PAGAMENTO_RATA})
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
