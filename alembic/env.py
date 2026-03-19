"""
Alembic env.py — migrazioni per crm.db (SOLO tabelle business).

ESCLUDE tabelle catalog (catalog.db) e nutrition (nutrition.db).
Quei DB non sono gestiti da Alembic: catalog.db e' costruito da
build_catalog.py + seed ORM, nutrition.db ha il suo alembic_nutrition.ini.

DATABASE_URL priority:
  1. Variabile d'ambiente DATABASE_URL (per dual-DB dev/prod)
  2. alembic.ini sqlalchemy.url (default: crm.db)

Uso:
  alembic upgrade head                                    → crm.db (default)
  DATABASE_URL=sqlite:///data/crm_dev.db alembic upgrade head  → crm_dev.db
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Root del progetto nel path per importare api.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.models import *  # noqa: F401, F403
from sqlmodel import SQLModel
from api.database import CATALOG_TABLE_NAMES, NUTRITION_TABLE_NAMES

# Alembic Config object
config = context.config

# Override sqlalchemy.url da env se presente
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData per autogenerate — filtrato alle sole tabelle business
target_metadata = SQLModel.metadata

# Tabelle da escludere: catalog.db + nutrition.db
_EXCLUDED_TABLE_NAMES = CATALOG_TABLE_NAMES | NUTRITION_TABLE_NAMES


def include_name(name, type_, parent_names):
    """Filtra: includi SOLO tabelle business (escludi catalog + nutrition)."""
    if type_ == "table":
        return name not in _EXCLUDED_TABLE_NAMES
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite non supporta ALTER TABLE complessi
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
