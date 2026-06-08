"""
DuckDB connection helper - infrastructure for both bounded contexts.

Each bounded context gets its own parquet file (separate databases), modelling
real-world data isolation between contexts. The file paths are defined here and
are the only place these paths live.
"""
from pathlib import Path

# Resolve paths relative to project root so the app works from any CWD.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

CATALOG_DB_PATH = str(DATA_DIR / "catalog.parquet")
BORROWING_DB_PATH = str(DATA_DIR / "borrowing.parquet")
