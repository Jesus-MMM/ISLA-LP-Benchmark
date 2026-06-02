"""
Tests para la aplicacion web FastAPI.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest

try:
    import fastapi  # noqa: F401
    import httpx  # noqa: F401
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not _FASTAPI_AVAILABLE, reason="FastAPI/httpx no instalado")
class TestWebApp:
    """Tests para la aplicacion web."""

    def test_create_app(self):
        """Test creacion de la app."""
        pytest.importorskip("fastapi")
        from src.web import create_app
        app = create_app()
        assert app.title == "ISLA LP Solver Web"

    def test_index_endpoint(self):
        """Test GET /."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert "ISLA LP Solver" in response.text

    def test_upload_no_file_no_text(self):
        """Test POST /upload sin archivo ni texto."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/upload")
        assert response.status_code == 200
        assert "No se proporciono" in response.text

    def test_upload_with_text(self):
        """Test POST /upload con texto."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/upload", data={"text": "max: x;\nx >= 0;"})
        assert response.status_code == 200
        assert "Problema" in response.text

    def test_upload_invalid_text(self):
        """Test POST /upload con texto invalido."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/upload", data={"text": "esto no es un LP"})
        assert response.status_code == 200
        assert "Error al parsear" in response.text

    def test_load_example_simple(self):
        """Test POST /load-example simple."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/load-example", data={"example": "simple"})
        assert response.status_code == 200

    def test_load_example_mip(self):
        """Test POST /load-example mip."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/load-example", data={"example": "mip"})
        assert response.status_code == 200

    def test_load_example_netlib(self):
        """Test POST /load-example netlib."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/load-example", data={"example": "netlib"})
        assert response.status_code == 200

    def test_solve_not_found(self):
        """Test POST /solve/<pid> con PID inexistente."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from src.web import create_app

        app = create_app()
        client = TestClient(app)
        response = client.post("/solve/nonexistent", data={"solver": "highs"})
        assert response.status_code == 200
        assert "Problema no encontrado" in response.text
