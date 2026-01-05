"""
Test suite for project setup validation.

These tests verify that the project structure is correctly set up
according to the design document specifications.
"""
import sys
from pathlib import Path

import pytest


class TestProjectStructure:
    """Test that all required directories exist."""

    def test_server_directory_exists(self):
        """Should have server directory."""
        assert Path(".").exists()

    def test_app_directory_exists(self):
        """Should have app directory."""
        assert Path("app").exists()

    def test_api_directory_exists(self):
        """Should have app/api directory."""
        assert Path("app/api").exists()

    def test_routes_directory_exists(self):
        """Should have app/api/routes directory."""
        assert Path("app/api/routes").exists()

    def test_middleware_directory_exists(self):
        """Should have app/api/middleware directory."""
        assert Path("app/api/middleware").exists()

    def test_services_directory_exists(self):
        """Should have app/services directory."""
        assert Path("app/services").exists()

    def test_models_directory_exists(self):
        """Should have app/models directory."""
        assert Path("app/models").exists()

    def test_db_directory_exists(self):
        """Should have app/db directory."""
        assert Path("app/db").exists()

    def test_repositories_directory_exists(self):
        """Should have app/db/repositories directory."""
        assert Path("app/db/repositories").exists()

    def test_migrations_directory_exists(self):
        """Should have app/db/migrations directory."""
        assert Path("app/db/migrations").exists()

    def test_ml_directory_exists(self):
        """Should have app/ml directory."""
        assert Path("app/ml").exists()

    def test_ml_models_directory_exists(self):
        """Should have app/ml/models directory."""
        assert Path("app/ml/models").exists()

    def test_tests_directory_exists(self):
        """Should have tests directory."""
        assert Path("tests").exists()

    def test_unit_tests_directory_exists(self):
        """Should have tests/unit directory."""
        assert Path("tests/unit").exists()

    def test_integration_tests_directory_exists(self):
        """Should have tests/integration directory."""
        assert Path("tests/integration").exists()

    def test_fixtures_directory_exists(self):
        """Should have tests/fixtures directory."""
        assert Path("tests/fixtures").exists()

    def test_scripts_directory_exists(self):
        """Should have scripts directory."""
        assert Path("scripts").exists()


class TestPythonPackages:
    """Test that all packages have __init__.py files."""

    def test_app_is_package(self):
        """Should have __init__.py in app directory."""
        assert Path("app/__init__.py").exists()

    def test_api_is_package(self):
        """Should have __init__.py in api directory."""
        assert Path("app/api/__init__.py").exists()

    def test_routes_is_package(self):
        """Should have __init__.py in routes directory."""
        assert Path("app/api/routes/__init__.py").exists()

    def test_middleware_is_package(self):
        """Should have __init__.py in middleware directory."""
        assert Path("app/api/middleware/__init__.py").exists()

    def test_services_is_package(self):
        """Should have __init__.py in services directory."""
        assert Path("app/services/__init__.py").exists()

    def test_models_is_package(self):
        """Should have __init__.py in models directory."""
        assert Path("app/models/__init__.py").exists()

    def test_db_is_package(self):
        """Should have __init__.py in db directory."""
        assert Path("app/db/__init__.py").exists()

    def test_repositories_is_package(self):
        """Should have __init__.py in repositories directory."""
        assert Path("app/db/repositories/__init__.py").exists()

    def test_ml_is_package(self):
        """Should have __init__.py in ml directory."""
        assert Path("app/ml/__init__.py").exists()

    def test_tests_is_package(self):
        """Should have __init__.py in tests directory."""
        assert Path("tests/__init__.py").exists()

    def test_unit_is_package(self):
        """Should have __init__.py in unit tests directory."""
        assert Path("tests/unit/__init__.py").exists()

    def test_integration_is_package(self):
        """Should have __init__.py in integration tests directory."""
        assert Path("tests/integration/__init__.py").exists()


class TestImports:
    """Test that core modules can be imported without errors."""

    def test_can_import_app(self):
        """Should be able to import app package."""
        # Add current directory to path if not already there
        current_path = Path(".").absolute()
        if str(current_path) not in sys.path:
            sys.path.insert(0, str(current_path))
        
        try:
            import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app: {e}")

    def test_can_import_app_api(self):
        """Should be able to import app.api package."""
        current_path = Path(".").absolute()
        if str(current_path) not in sys.path:
            sys.path.insert(0, str(current_path))
        
        try:
            import app.api
            assert app.api is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app.api: {e}")

    def test_can_import_app_services(self):
        """Should be able to import app.services package."""
        current_path = Path(".").absolute()
        if str(current_path) not in sys.path:
            sys.path.insert(0, str(current_path))
        
        try:
            import app.services
            assert app.services is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app.services: {e}")

    def test_can_import_app_models(self):
        """Should be able to import app.models package."""
        current_path = Path(".").absolute()
        if str(current_path) not in sys.path:
            sys.path.insert(0, str(current_path))
        
        try:
            import app.models
            assert app.models is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app.models: {e}")

    def test_can_import_app_db(self):
        """Should be able to import app.db package."""
        current_path = Path(".").absolute()
        if str(current_path) not in sys.path:
            sys.path.insert(0, str(current_path))
        
        try:
            import app.db
            assert app.db is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app.db: {e}")

    def test_can_import_app_ml(self):
        """Should be able to import app.ml package."""
        current_path = Path(".").absolute()
        if str(current_path) not in sys.path:
            sys.path.insert(0, str(current_path))
        
        try:
            import app.ml
            assert app.ml is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app.ml: {e}")


class TestProjectFiles:
    """Test that required project files exist."""

    def test_requirements_file_exists(self):
        """Should have requirements.txt file."""
        assert Path("requirements.txt").exists()

    def test_pyproject_file_exists(self):
        """Should have pyproject.toml file."""
        assert Path("pyproject.toml").exists()

    def test_readme_file_exists(self):
        """Should have README.md file."""
        assert Path("README.md").exists()

    def test_conftest_exists(self):
        """Should have conftest.py for pytest fixtures."""
        assert Path("tests/conftest.py").exists()
