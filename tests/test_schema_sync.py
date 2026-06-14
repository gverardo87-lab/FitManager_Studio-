"""Test schema_sync — verifica che colonne mancanti vengano aggiunte."""


import pytest
from sqlalchemy import text

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
