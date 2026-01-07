"""
Database module for Prison Roll Call Server.

Provides SQLite database connection management, initialization,
and migration utilities.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Create and configure a SQLite database connection.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        Configured SQLite connection

    Configuration:
        - Row factory for dict-like access
        - Foreign key constraints enabled
        - Auto-creates database file if it doesn't exist
    """
    # Create parent directories if they don't exist
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    # check_same_thread=False allows connection to be used across threads
    # This is safe since we manage connections properly with context managers
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # Configure Row factory for dict-like access
    conn.row_factory = sqlite3.Row

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def get_migration_path() -> Path:
    """
    Get the path to the migrations directory.

    Returns:
        Path to the migrations directory
    """
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    migrations_dir = current_dir / "migrations"
    return migrations_dir


def load_migration_sql(filename: str) -> str:
    """
    Load SQL from a migration file.

    Args:
        filename: Name of the migration file (e.g., "001_initial.sql")

    Returns:
        SQL content as string

    Raises:
        FileNotFoundError: If migration file doesn't exist
    """
    migration_path = get_migration_path() / filename
    
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    
    return migration_path.read_text()


def init_db(conn: sqlite3.Connection) -> None:
    """
    Initialize the database schema.

    Loads and executes all migration SQL files to create tables,
    indexes, and insert default data.

    Args:
        conn: SQLite database connection

    Note:
        This function is idempotent - safe to call multiple times.
        Uses IF NOT EXISTS clauses to avoid errors on repeated calls.
    """
    # Load and execute migrations in order
    migrations = [
        "001_initial.sql",
        "002_multiple_embeddings.sql",
    ]
    
    for migration_file in migrations:
        sql = load_migration_sql(migration_file)
        conn.executescript(sql)
    
    # Commit changes
    conn.commit()


@contextmanager
def get_db_context(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections with transaction handling.

    Automatically commits on successful completion and rolls back on exceptions.

    Args:
        db_path: Path to the SQLite database file

    Yields:
        SQLite database connection

    Example:
        >>> with get_db_context("prison_rollcall.db") as conn:
        ...     conn.execute("INSERT INTO inmates ...")
        ...     # Automatically commits on exit
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency for database connections.
    
    Yields:
        SQLite database connection
    """
    from app.config import Settings
    
    settings = Settings()
    db_path = settings.db_path
    
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
