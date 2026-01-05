"""
Test suite for database module.

Tests database connection, initialization, and schema creation.
"""
import sqlite3
from pathlib import Path

import pytest


class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_get_connection(self, tmp_path):
        """Should create and return a database connection."""
        from app.db.database import get_connection

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_connection_creates_database_file(self, tmp_path):
        """Should create database file if it doesn't exist."""
        from app.db.database import get_connection

        db_path = tmp_path / "test.db"
        assert not db_path.exists()

        conn = get_connection(str(db_path))
        conn.close()

        assert db_path.exists()

    def test_connection_row_factory(self, tmp_path):
        """Should configure connection with Row factory for dict-like access."""
        from app.db.database import get_connection

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))

        # Execute a simple query
        cursor = conn.execute("SELECT 1 as value, 'test' as name")
        row = cursor.fetchone()

        # Should be able to access by column name
        assert row["value"] == 1
        assert row["name"] == "test"
        conn.close()

    def test_connection_foreign_keys_enabled(self, tmp_path):
        """Should enable foreign key constraints."""
        from app.db.database import get_connection

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))

        # Check if foreign keys are enabled
        cursor = conn.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()

        assert result[0] == 1  # 1 means enabled
        conn.close()


class TestDatabaseInitialization:
    """Test database schema initialization."""

    def test_init_db_creates_all_tables(self, tmp_path):
        """Should create all required tables."""
        from app.db.database import get_connection, init_db

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))
        init_db(conn)

        # Check that all tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]

        expected_tables = [
            "audit_log",
            "embeddings",
            "inmates",
            "locations",
            "policy",
            "roll_calls",
            "verifications",
        ]

        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found"

        conn.close()

    def test_init_db_creates_inmates_table(self, tmp_path):
        """Should create inmates table with correct schema."""
        from app.db.database import get_connection, init_db

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))
        init_db(conn)

        # Check inmates table structure
        cursor = conn.execute("PRAGMA table_info(inmates)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}

        assert "id" in columns
        assert "inmate_number" in columns
        assert "first_name" in columns
        assert "last_name" in columns
        assert "date_of_birth" in columns
        assert "cell_block" in columns
        assert "cell_number" in columns
        assert "is_enrolled" in columns
        assert "created_at" in columns

        conn.close()

    def test_init_db_creates_indexes(self, tmp_path):
        """Should create indexes for performance."""
        from app.db.database import get_connection, init_db

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))
        init_db(conn)

        # Check that indexes were created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
        indexes = [row["name"] for row in cursor.fetchall()]

        expected_indexes = [
            "idx_inmates_block",
            "idx_inmates_enrolled",
            "idx_inmates_number",
            "idx_locations_type",
            "idx_locations_building",
            "idx_rollcalls_status",
            "idx_rollcalls_scheduled",
            "idx_verifications_rollcall",
            "idx_verifications_inmate",
            "idx_verifications_timestamp",
            "idx_audit_timestamp",
            "idx_audit_action",
        ]

        for index in expected_indexes:
            assert index in indexes, f"Index '{index}' not found"

        conn.close()

    def test_init_db_idempotent(self, tmp_path):
        """Should be safe to call init_db multiple times."""
        from app.db.database import get_connection, init_db

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))

        # Initialize twice
        init_db(conn)
        init_db(conn)  # Should not raise error

        # Tables should still exist
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
        )
        count = cursor.fetchone()["count"]
        assert count > 0

        conn.close()

    def test_init_db_inserts_default_policy(self, tmp_path):
        """Should insert default policy row."""
        from app.db.database import get_connection, init_db

        db_path = tmp_path / "test.db"
        conn = get_connection(str(db_path))
        init_db(conn)

        # Check policy table has default row
        cursor = conn.execute("SELECT * FROM policy WHERE id='default'")
        policy = cursor.fetchone()

        assert policy is not None
        assert policy["verification_threshold"] == 0.75
        assert policy["enrollment_quality_threshold"] == 0.80
        assert policy["auto_accept_threshold"] == 0.92
        assert policy["manual_review_threshold"] == 0.60

        conn.close()


class TestDatabaseContextManager:
    """Test database context manager for transaction handling."""

    def test_get_db_context_manager(self, tmp_path):
        """Should provide context manager for database connections."""
        from app.db.database import get_db_context, init_db

        db_path = tmp_path / "test.db"

        # Initialize database first
        with get_db_context(str(db_path)) as conn:
            init_db(conn)

        # Use context manager
        with get_db_context(str(db_path)) as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

    def test_context_manager_commits_on_success(self, tmp_path):
        """Should commit changes when context exits normally."""
        from app.db.database import get_db_context, init_db

        db_path = tmp_path / "test.db"

        # Initialize and insert data
        with get_db_context(str(db_path)) as conn:
            init_db(conn)
            conn.execute(
                """
                INSERT INTO inmates 
                (id, inmate_number, first_name, last_name, date_of_birth, 
                 cell_block, cell_number, created_at, updated_at)
                VALUES ('test-id', 'A12345', 'John', 'Doe', '1990-01-01',
                        'A', '101', datetime('now'), datetime('now'))
                """
            )

        # Verify data persisted
        with get_db_context(str(db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM inmates")
            count = cursor.fetchone()["count"]
            assert count == 1

    def test_context_manager_rollback_on_exception(self, tmp_path):
        """Should rollback changes when exception occurs."""
        from app.db.database import get_db_context, init_db

        db_path = tmp_path / "test.db"

        # Initialize database
        with get_db_context(str(db_path)) as conn:
            init_db(conn)

        # Try to insert data but raise exception
        try:
            with get_db_context(str(db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO inmates 
                    (id, inmate_number, first_name, last_name, date_of_birth, 
                     cell_block, cell_number, created_at, updated_at)
                    VALUES ('test-id', 'A12345', 'John', 'Doe', '1990-01-01',
                            'A', '101', datetime('now'), datetime('now'))
                    """
                )
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # Verify data was rolled back
        with get_db_context(str(db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM inmates")
            count = cursor.fetchone()["count"]
            assert count == 0


class TestDatabaseUtilities:
    """Test database utility functions."""

    def test_get_migration_path(self):
        """Should return path to migrations directory."""
        from app.db.database import get_migration_path

        migration_path = get_migration_path()

        assert isinstance(migration_path, Path)
        assert "migrations" in str(migration_path)

    def test_load_migration_sql(self):
        """Should load SQL from migration file."""
        from app.db.database import load_migration_sql

        sql = load_migration_sql("001_initial.sql")

        assert isinstance(sql, str)
        assert len(sql) > 0
        assert "CREATE TABLE" in sql
