"""
Tests de cadena de suministro (OWASP A03:2025).
Verifican versiones pinneadas, separación dev/prod y presencia de SBOM/CI.
"""
import os
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _leer(nombre):
    with open(os.path.join(RAIZ, nombre), "r", encoding="utf-8") as f:
        return f.read()


class TestVersionesPinneadas:
    @pytest.mark.parametrize("archivo", ["requirements.txt", "requirements-dev.txt"])
    def test_versiones_exactas(self, archivo):
        contenido = _leer(archivo)
        for linea in contenido.splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or linea.startswith("-"):
                continue
            assert "==" in linea, (
                f"Dependencia sin versión exacta en {archivo}: {linea!r}"
            )


class TestSeparacionDevProd:
    def test_dev_no_esta_en_produccion(self):
        prod = _leer("requirements.txt")
        for dep in ["pytest", "mongomock", "bandit", "pip-audit"]:
            assert dep not in prod, f"'{dep}' no debe estar en requirements.txt"

    def test_produccion_incluye_criticas(self):
        prod = _leer("requirements.txt")
        for dep in ["pymongo", "bcrypt", "python-dotenv"]:
            assert dep in prod


class TestSBOMyCI:
    def test_ci_genera_sbom(self):
        yml = _leer(".github/workflows/security.yml")
        assert "cyclonedx-py" in yml

    def test_ci_corre_pip_audit(self):
        yml = _leer(".github/workflows/security.yml")
        assert "pip-audit" in yml

    def test_ci_tiene_cron(self):
        yml = _leer(".github/workflows/security.yml")
        assert "schedule" in yml and "cron" in yml


class TestEnvExample:
    def test_env_example_sin_secretos_reales(self):
        contenido = _leer(".env.example")
        # No debe contener la password antigua ni URIs reales
        assert "UtyO52Gzk3plCfFs" not in contenido
        assert "ac-cl0wflm" not in contenido