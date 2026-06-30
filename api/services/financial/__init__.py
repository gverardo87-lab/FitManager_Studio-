"""Financial command layer (G9, ADR-022).

Lo strato di SCRITTURA gemello del SSoT di lettura `contract_state.py`: rende il ledger
`CashMovement` load-bearing. G9.0 introduce qui `invariant_gate` (sensore osservabile degli
invarianti). I gate successivi aggiungono la penna unica di posting (G9.1) e il transition
executor (G9.3). Vedi `docs/technical/SPEC_G9_FINANCIAL_COMMAND_LAYER.md`.
"""
