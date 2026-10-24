"""
Configuración global de pytest.
- Setea MONGODB_URI dummy ANTES de que cualquier test importe db.py.
- Expone fixtures de usuarios.
"""
import os
import sys

# CRÍTICO: setear la env var ANTES de importar db
os.environ.setdefault("MONGODB_URI", "mongodb://fake:fake@localhost:27017/test_db")
os.environ.setdefault("MONGODB_DB", "test_boutique")

# Añadir Live Share al path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'Live Share')
))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _env_mongodb_dummy(monkeypatch):
    """Redundante con os.environ.setdefault, pero garantiza el valor en cada test."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://fake:fake@localhost:27017/test_db")
    monkeypatch.setenv("MONGODB_DB", "test_boutique")


@pytest.fixture
def usuario_admin():
    return {"_id": "USR-001", "username": "admin", "rol": "admin"}


@pytest.fixture
def usuario_vendedor():
    return {"_id": "USR-002", "username": "vendedor1", "rol": "vendedor"}