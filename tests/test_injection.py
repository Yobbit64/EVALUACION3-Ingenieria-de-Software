"""Tests de validación positiva (A05:2025)."""
import re


class TestValidacionPositiva:
    def test_nombre_valido(self):
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,50}$"
        assert re.match(patron, "Juan Pérez")
        assert re.match(patron, "María José")

    def test_nombre_con_numeros_rechazado(self):
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,50}$"
        assert not re.match(patron, "Juan123")

    def test_nombre_con_script_rechazado(self):
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,50}$"
        assert not re.match(patron, "<script>")

    def test_rut_valido(self):
        patron = r"^\d{7,8}-[\dkK]$"
        assert re.match(patron, "12345678-9")
        assert re.match(patron, "12345678-K")

    def test_rut_invalido(self):
        patron = r"^\d{7,8}-[\dkK]$"
        assert not re.match(patron, "12345678")
        assert not re.match(patron, "abc-def")
        assert not re.match(patron, "12.345.678-9")

    def test_email_valido(self):
        patron = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        assert re.match(patron, "user@example.com")
        assert not re.match(patron, "noemail")
