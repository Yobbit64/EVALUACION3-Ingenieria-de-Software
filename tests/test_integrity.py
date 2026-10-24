"""Tests de integridad de dependencias (A08:2025)."""
import os


RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _leer(nombre):
    with open(os.path.join(RAIZ, nombre), encoding="utf-8") as f:
        return f.read()


class TestIntegridadDependencias:
    def test_requirements_tiene_hashes(self):
        contenido = _leer("requirements.txt")
        assert "--hash=sha256:" in contenido

    def test_requirements_dev_tiene_hashes(self):
        contenido = _leer("requirements-dev.txt")
        assert "--hash=sha256:" in contenido

    def test_requirements_in_sin_hashes(self):
        contenido = _leer("requirements.in")
        assert "--hash=" not in contenido


class TestIntegridadCodigo:
    def test_no_pickle(self):
        for dirpath, _, files in os.walk(os.path.join(RAIZ, "Live Share")):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(dirpath, f), encoding="utf-8") as fh:
                        contenido = fh.read()
                    assert "import pickle" not in contenido, f"pickle en {f}"
                    assert "yaml.load(" not in contenido, f"yaml.load inseguro en {f}"
