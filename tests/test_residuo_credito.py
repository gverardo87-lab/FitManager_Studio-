"""G9.0c/QW1 (ADR-022) — SSoT unico `contract_state.residuo_credito` per i 2 DTO finora duplicati.

Prima: `CreditoTerminazioneResponse.residuo` e `CreditoClienteResponse.residuo` avevano la stessa formula
inline copiata (`round(max(importo − consumato, 0), 2)`). Ora delegano entrambi all'helper puro: un cambio
dell'helper si propaga a entrambi (meta-test via monkeypatch).
"""

from datetime import date

import pytest

from api.schemas.financial import CreditoClienteResponse, CreditoTerminazioneResponse
from api.services.contract_state import residuo_credito


@pytest.mark.parametrize("importo,consumato,atteso", [
    (300.0, 100.0, 200.0),
    (100.0, 100.0, 0.0),
    (100.0, 150.0, 0.0),    # clamp: mai negativo
    (0.0, 0.0, 0.0),
    (None, None, 0.0),      # null-safe
    (300.0, None, 300.0),
])
def test_residuo_credito_correttezza(importo, consumato, atteso):
    assert residuo_credito(importo, consumato) == atteso


def _receivable(**kw):
    base = dict(id=1, id_contratto=1, id_cliente=1, importo=300.0, importo_incassato=100.0,
                stato="APERTO", data_creazione=date.today())
    base.update(kw)
    return CreditoTerminazioneResponse(**base)


def _wallet(**kw):
    base = dict(id=1, trainer_id=1, id_cliente=1, importo=300.0, importo_erogato=100.0, stato="APERTO",
                causale="RIMBORSO_DIFFERITO", id_contratto_origine=1, data_creazione=date.today())
    base.update(kw)
    return CreditoClienteResponse(**base)


def test_dto_residuo_coerenti_con_helper():
    """Entrambi i DTO espongono lo stesso residuo del helper per (importo, consumato) uguali."""
    assert _receivable().residuo == residuo_credito(300.0, 100.0) == 200.0
    assert _wallet().residuo == residuo_credito(300.0, 100.0) == 200.0


def test_dto_residuo_delegano_al_helper(monkeypatch):
    """Meta-test: cambiare l'helper cambia ENTRAMBI i DTO (prova la delega, non la coincidenza)."""
    monkeypatch.setattr("api.services.contract_state.residuo_credito", lambda importo, consumato: 999.0)
    assert _receivable().residuo == 999.0
    assert _wallet().residuo == 999.0
