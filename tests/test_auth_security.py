"""Tests de autenticación (A07:2025)."""
import pytest
import db

ADMIN = {"_id": "USR-001", "username": "admin", "rol": "admin"}


class TestBloqueoIntentos:
    def test_bloqueo_tras_intentos_fallidos(self, mocker):
        mock_usr = mocker.patch("db.usuarios_col")
        mocker.patch("db.auditoria_col")

        # El usuario existe, no está bloqueado, con contador 0
        mock_usr.find_one.return_value = {
            "_id": "USR-001", "username": "admin", "rol": "admin",
            "activo": True, "password_hash": "$2b$12$invalido",
            "intentos_fallidos": 0, "bloqueado_hasta": None,
        }

        # Simulamos el $inc: find_one_and_update devuelve un doc con el contador
        # incrementado en cada llamada
        contador = {"n": 0}

        def _find_one_and_update(*args, **kwargs):
            contador["n"] += 1
            return {
                "_id": "USR-001", "username": "admin", "rol": "admin",
                "activo": True, "intentos_fallidos": contador["n"],
                "bloqueado_hasta": None,
            }

        mock_usr.find_one_and_update.side_effect = _find_one_and_update
        mock_usr.update_one.return_value = mocker.MagicMock()

        # 5 intentos fallidos
        for _ in range(5):
            db.autenticar_usuario("admin", "malo")

        # La última update_one debe haber activado bloqueado_hasta
        llamadas = [str(c) for c in mock_usr.update_one.call_args_list]
        assert any("bloqueado_hasta" in c for c in llamadas), (
            f"No se bloqueó la cuenta. Llamadas: {llamadas}"
        )

        # El contador debe haber llegado a 5
        assert contador["n"] == 5


class TestFortalezaPassword:
    def test_password_corta_rechazada(self, mocker):
        # find_one devuelve None → el usuario NO existe
        mock_usr = mocker.patch("db.usuarios_col")
        mock_usr.find_one.return_value = None
        mock_usr.find.return_value = []
        mocker.patch("db.auditoria_col")

        with pytest.raises(ValueError, match="12 caracteres"):
            db.crear_usuario(ADMIN, "test", "corta", "vendedor")

    def test_password_sin_simbolo_rechazada(self, mocker):
        mock_usr = mocker.patch("db.usuarios_col")
        mock_usr.find_one.return_value = None  # usuario no existe
        mock_usr.find.return_value = []
        mocker.patch("db.auditoria_col")

        with pytest.raises(ValueError, match="símbolo"):
            db.crear_usuario(ADMIN, "test", "Abcdefgh1234", "vendedor")

    def test_password_fuerte_aceptada(self, mocker):
        mock_usr = mocker.patch("db.usuarios_col")
        mock_usr.find_one.return_value = None
        mock_usr.find.return_value = []
        mocker.patch("db.auditoria_col")

        db.crear_usuario(ADMIN, "nuevo", "Abcdefgh1234!", "vendedor")
        assert mock_usr.insert_one.called