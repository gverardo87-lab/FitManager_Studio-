"""Test schema_sync — verifica che colonne mancanti vengano aggiunte."""


import inspect

import pytest
from sqlalchemy import text

from api.services import schema_sync as schema_sync_service
from api.services.schema_sync import sync_schema


@pytest.fixture
def test_engine():
    """Engine di test con DB in-memory."""
    from sqlmodel import SQLModel, create_engine

    engine = create_engine("sqlite://", echo=False)
    # Crea tutte le tabelle con schema completo
    SQLModel.metadata.create_all(engine)
    return engine


def test_sync_schema_noop_on_complete_db(test_engine):
    """Su un DB con schema completo, sync_schema non fa nulla."""
    messages = sync_schema(test_engine)
    assert messages == []


def test_sync_schema_adds_missing_column(test_engine):
    """Rimuove una colonna e verifica che sync_schema la riaggiunga."""
    # Simula DB vecchio: rimuovi colonna 'indirizzo' da clienti
    # SQLite non supporta DROP COLUMN nativamente, quindi ricreiamo la tabella senza la colonna
    with test_engine.connect() as conn:
        # Leggi colonne attuali
        cols = conn.execute(text("PRAGMA table_info(clienti)")).fetchall()
        col_names = [c[1] for c in cols]
        assert "indirizzo" in col_names, "La colonna indirizzo deve esistere nel modello"

        # Crea tabella temp senza 'indirizzo'
        cols_without = [c for c in col_names if c != "indirizzo"]
        cols_csv = ", ".join(cols_without)
        conn.execute(text(f"CREATE TABLE clienti_old AS SELECT {cols_csv} FROM clienti"))
        conn.execute(text("DROP TABLE clienti"))
        conn.execute(text(f"ALTER TABLE clienti_old RENAME TO clienti"))
        conn.commit()

        # Verifica che 'indirizzo' sia sparita
        cols_after = conn.execute(text("PRAGMA table_info(clienti)")).fetchall()
        col_names_after = [c[1] for c in cols_after]
        assert "indirizzo" not in col_names_after

    # Esegui sync
    messages = sync_schema(test_engine)

    # Verifica che 'indirizzo' sia stata ri-aggiunta
    assert len(messages) > 0
    assert any("indirizzo" in m for m in messages)

    with test_engine.connect() as conn:
        cols_final = conn.execute(text("PRAGMA table_info(clienti)")).fetchall()
        col_names_final = [c[1] for c in cols_final]
        assert "indirizzo" in col_names_final


def test_sync_schema_idempotent(test_engine):
    """Chiamare sync_schema due volte non cambia nulla la seconda volta."""
    # Prima chiamata su DB completo
    messages1 = sync_schema(test_engine)
    assert messages1 == []

    # Seconda chiamata
    messages2 = sync_schema(test_engine)
    assert messages2 == []


def test_sync_schema_skips_catalog_tables(test_engine):
    """Le tabelle catalog (muscoli, articolazioni, ecc.) non vengono toccate."""
    with test_engine.connect() as conn:
        # Verifica che muscoli esista
        cols = conn.execute(text("PRAGMA table_info(muscoli)")).fetchall()
        if not cols:
            pytest.skip("Tabella muscoli non presente nel metadata di test")

    messages = sync_schema(test_engine)
    assert not any("muscoli" in m for m in messages)


def test_fix_cross_db_fk_removes_metriche_fk(test_engine):
    """FK locale residua valori_misurazione→metriche viene rimossa, righe preservate.

    Simula il DDL vecchio (FK locale) che i crm.db deployati hanno ancora.
    Il modello l'ha rimossa (cross-DB), schema_sync allinea il DB esistente.
    """
    with test_engine.connect() as conn:
        # Ricrea valori_misurazione con il vecchio DDL (FK locale a metriche)
        conn.execute(text("DROP TABLE valori_misurazione"))
        conn.execute(text("""
            CREATE TABLE valori_misurazione (
                id INTEGER NOT NULL PRIMARY KEY,
                id_misurazione INTEGER NOT NULL,
                id_metrica INTEGER NOT NULL,
                valore FLOAT NOT NULL,
                FOREIGN KEY(id_misurazione) REFERENCES misurazioni_cliente (id),
                FOREIGN KEY(id_metrica) REFERENCES metriche (id)
            )
        """))
        # Una metrica + una sessione + un valore che usa la FK
        conn.execute(text(
            "INSERT INTO metriche (id, nome, nome_en, unita_misura, categoria, ordinamento) "
            "VALUES (1, 'Peso', 'Weight', 'kg', 'composizione', 0)"
        ))
        conn.execute(text("INSERT INTO valori_misurazione (id, id_misurazione, id_metrica, valore) "
                          "VALUES (1, 1, 1, 75.0)"))
        conn.commit()
        fks = conn.execute(text("PRAGMA foreign_key_list(valori_misurazione)")).fetchall()
        assert any(r[2] == "metriche" for r in fks), "setup: la FK a metriche deve esserci"

    messages = sync_schema(test_engine)
    assert any("valori_misurazione" in m and "metriche" in m for m in messages)

    with test_engine.connect() as conn:
        fks = conn.execute(text("PRAGMA foreign_key_list(valori_misurazione)")).fetchall()
        assert not any(r[2] == "metriche" for r in fks), "FK a metriche deve essere rimossa"
        # riga preservata
        assert conn.execute(text("SELECT COUNT(*) FROM valori_misurazione")).scalar() == 1
        # FK legittima (misurazioni_cliente) preservata
        assert any(r[2] == "misurazioni_cliente" for r in fks)


def test_drop_stale_catalog_tables_on_file_db(tmp_path):
    """Su un crm.db FILE, le tabelle catalog stale (popolate) vengono droppate;
    su DB in-memory NO (guard, coperto da test_sync_schema_skips_catalog_tables)."""
    from sqlmodel import SQLModel, create_engine

    db_path = tmp_path / "crm_test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)  # crea anche le catalog tables (test metadata unico)

    # Popola una catalog table (metriche) per simulare il detrito monolite
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO metriche (id, nome, nome_en, unita_misura, categoria, ordinamento) "
            "VALUES (1, 'Peso', 'Weight', 'kg', 'composizione', 0)"
        ))
        conn.commit()
        assert conn.execute(text("SELECT 1 FROM sqlite_master WHERE name='metriche'")).fetchone()

    messages = sync_schema(engine)
    assert any("stale catalog table 'metriche'" in m for m in messages)

    with engine.connect() as conn:
        # catalog tables rimosse
        assert conn.execute(text("SELECT 1 FROM sqlite_master WHERE name='metriche'")).fetchone() is None
        assert conn.execute(text("SELECT 1 FROM sqlite_master WHERE name='esercizi'")).fetchone() is None
        # business intatta
        assert conn.execute(text("SELECT 1 FROM sqlite_master WHERE name='clienti'")).fetchone() is not None
    engine.dispose()


def test_sync_schema_adds_termination_columns_and_index(test_engine):
    """AC-7.0-2 (SPEC_G7.0): le 4 colonne di terminazione + l'indice ix_contratti_motivo_chiusura
    vengono aggiunti su un crm.db deployato che ne è privo; ZERO FK sulle nuove colonne (pitfall #15);
    idempotente al secondo boot."""
    NEW = ("totale_rimborsato", "quota_stornata", "data_chiusura", "motivo_chiusura")
    with test_engine.connect() as conn:
        cols = [c[1] for c in conn.execute(text("PRAGMA table_info(contratti)")).fetchall()]
        for c in NEW:
            assert c in cols, f"setup: {c} deve esistere nel modello"
        # Simula DB pre-G7: ricrea contratti senza le 4 colonne
        cols_without = [c for c in cols if c not in NEW]
        conn.execute(text(f"CREATE TABLE contratti_old AS SELECT {', '.join(cols_without)} FROM contratti"))
        conn.execute(text("DROP TABLE contratti"))
        conn.execute(text("ALTER TABLE contratti_old RENAME TO contratti"))
        conn.commit()
        cols_after = [c[1] for c in conn.execute(text("PRAGMA table_info(contratti)")).fetchall()]
        assert not any(c in cols_after for c in NEW)

    messages = sync_schema(test_engine)
    assert any("totale_rimborsato" in m for m in messages)

    with test_engine.connect() as conn:
        cols_final = [c[1] for c in conn.execute(text("PRAGMA table_info(contratti)")).fetchall()]
        for c in NEW:
            assert c in cols_final, f"{c} non aggiunta"
        idx = [r[1] for r in conn.execute(text("PRAGMA index_list(contratti)")).fetchall()]
        assert "ix_contratti_motivo_chiusura" in idx, idx
        fks = conn.execute(text("PRAGMA foreign_key_list(contratti)")).fetchall()
        fk_cols = {f[3] for f in fks}
        assert not (fk_cols & set(NEW)), f"FK su colonne nuove (vietato, pitfall #15)! {fks}"

    # idempotente: secondo boot non ritocca le colonne di contratti
    messages2 = sync_schema(test_engine)
    assert not any("contratti" in m and "column" in m for m in messages2)


def test_sync_schema_multiple_missing_columns(test_engine):
    """Verifica sync con piu' colonne mancanti sulla stessa tabella."""
    with test_engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(clienti)")).fetchall()
        col_names = [c[1] for c in cols]

        # Rimuovi indirizzo e codice_fiscale
        cols_without = [c for c in col_names if c not in ("indirizzo", "codice_fiscale")]
        cols_csv = ", ".join(cols_without)
        conn.execute(text(f"CREATE TABLE clienti_old AS SELECT {cols_csv} FROM clienti"))
        conn.execute(text("DROP TABLE clienti"))
        conn.execute(text(f"ALTER TABLE clienti_old RENAME TO clienti"))
        conn.commit()

    messages = sync_schema(test_engine)
    added_cols = [m for m in messages if "added column" in m]
    assert len(added_cols) >= 2
    assert any("indirizzo" in m for m in added_cols)
    assert any("codice_fiscale" in m for m in added_cols)


# ── G9.2b (ADR-022 Addendum I): backfill quota_stornata legacy → rettifiche_contratto ──

def test_backfill_causale_consumata_dalla_ssot():
    """R1.4: il raw SQL boot usa un bind dalla costante, mai una seconda causale literal."""
    source = inspect.getsource(schema_sync_service._backfill_quota_stornata_rettifiche)
    assert ":causale" in source
    assert '"causale": CAUSALE_BACKFILL_LEGACY' in source
    assert "'BACKFILL_LEGACY'" not in source


def _seed_contract_con_quota(engine, *, quota, data_chiusura="2026-05-10"):
    """Contratto legacy con quota_stornata scritta a mano (pre-terza-penna), zero rettifiche."""
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO trainers (email, nome, cognome, hashed_password, is_active, created_at, saldo_iniziale_cassa) "
            "VALUES ('t@t.it', 'T', 'T', 'x', 1, '2026-01-01', 0)"
        ))
        conn.execute(text(
            "INSERT INTO clienti (trainer_id, nome, cognome, stato) VALUES (1, 'C', 'C', 'Attivo')"
        ))
        conn.execute(text(
            "INSERT INTO contratti (trainer_id, id_cliente, prezzo_totale, totale_versato, quota_stornata, "
            "chiuso, data_chiusura, motivo_chiusura, crediti_usati, acconto, totale_rimborsato, stato_pagamento) "
            "VALUES (1, 1, 1000, 750, :quota, 1, :dc, 'TERMINAZIONE_RIMBORSO', 0, 0, 0, 'SALDATO')"
        ), {"quota": quota, "dc": data_chiusura})
        conn.commit()


def test_backfill_quota_stornata_crea_riga_legacy(test_engine):
    """Legacy quota>0 senza rettifiche → 1 riga BACKFILL_LEGACY di pari importo; colonna intatta."""
    _seed_contract_con_quota(test_engine, quota=250.0)
    messages = sync_schema(test_engine)
    assert any("BACKFILL_LEGACY" in m for m in messages)
    with test_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id_contratto, importo, causale, data_effettiva, trainer_id FROM rettifiche_contratto"
        )).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1 and rows[0][1] == 250.0 and rows[0][2] == "BACKFILL_LEGACY"
        assert rows[0][3] == "2026-05-10"      # data_effettiva = data_chiusura del contratto
        assert rows[0][4] == 1                 # trainer_id dal contratto (tenant-isolation)
        # Additivo: la colonna non si tocca — l'ancora quota == Σ rettifiche vale da subito
        quota = conn.execute(text("SELECT quota_stornata FROM contratti WHERE id=1")).fetchone()[0]
        assert quota == 250.0


def test_backfill_idempotente_rerun_noop(test_engine):
    """Secondo boot: il guard zero-rettifiche rende il backfill un no-op (mai doppia riga)."""
    _seed_contract_con_quota(test_engine, quota=250.0)
    sync_schema(test_engine)
    messages2 = sync_schema(test_engine)
    assert not any("BACKFILL_LEGACY" in m for m in messages2)
    with test_engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM rettifiche_contratto")).fetchone()[0]
        assert n == 1


def test_backfill_skip_contratto_gia_con_rettifiche(test_engine):
    """Un contratto che HA già rettifiche non viene backfillato (la sua quota deriva dai posting)."""
    _seed_contract_con_quota(test_engine, quota=300.0)
    with test_engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO rettifiche_contratto (trainer_id, id_contratto, importo, causale, data_effettiva) "
            "VALUES (1, 1, 300.0, 'STORNO_TERMINAZIONE', '2026-05-10')"
        ))
        conn.commit()
    messages = sync_schema(test_engine)
    assert not any("BACKFILL_LEGACY" in m for m in messages)
    with test_engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM rettifiche_contratto")).fetchone()[0]
        assert n == 1


def test_backfill_skip_quota_zero(test_engine):
    """quota_stornata == 0 → nessuna riga (il backfill copre solo il legacy con storno reale)."""
    _seed_contract_con_quota(test_engine, quota=0.0)
    messages = sync_schema(test_engine)
    assert not any("BACKFILL_LEGACY" in m for m in messages)
    with test_engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM rettifiche_contratto")).fetchone()[0]
        assert n == 0
