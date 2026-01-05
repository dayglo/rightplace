"""
Pytest configuration and shared fixtures.

This file contains fixtures that are available to all test modules.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


# Add the server directory to the Python path
# This allows tests to import from the app package
@pytest.fixture(scope="session", autouse=True)
def setup_python_path():
    """Add server directory to Python path for imports."""
    server_path = Path(__file__).parent.parent.absolute()
    if str(server_path) not in sys.path:
        sys.path.insert(0, str(server_path))
    yield
    # Cleanup: remove from path after tests
    if str(server_path) in sys.path:
        sys.path.remove(str(server_path))


@pytest.fixture
def project_root():
    """Return the path to the project root directory."""
    return Path(__file__).parent.parent


# Additional fixtures will be added as needed for specific test modules
# For example:
# - Database fixtures
# - API client fixtures
# - Mock image fixtures
# - Mock ML model fixtures


@pytest.fixture
def test_db():
    """
    Create a test database with initialized schema.
    
    Returns:
        Path to test database file
    """
    from app.db.database import get_connection, init_db
    import tempfile
    import os
    
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    # Get connection and initialize schema
    conn = get_connection(db_path)
    init_db(conn)
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """
    Create a FastAPI TestClient for integration tests.
    
    Returns:
        TestClient instance for making HTTP requests to the API
    """
    from app.db.database import get_db, get_connection
    
    app = create_app()
    
    # Override the database dependency to use test database
    def override_get_db():
        conn = get_connection(test_db)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides
    app.dependency_overrides.clear()
