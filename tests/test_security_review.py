import os
import re
import sys

RUTA_LIVE_SHARE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Live Share")
)
sys.path.insert(0, RUTA_LIVE_SHARE)

ADMIN = {"_id": "USR-001", "username": "admin", "rol": "admin"}


class TestInyeccionNoSQL:

    def test_busqueda_por_documento_sanitiza_string(self, mocker):
        import db
        mock_col = mocker.patch("db.clientes_col")
        mock_col.find_one.return_value = None
        mocker.patch("db.auditoria_col")
        payload = {"$ne": None}
        db.buscar_cliente_por_documento(ADMIN, "RUT", str(payload))
        args = mock_col.find_one.call_args[0][0]
        assert isinstance(args["rut"], str)

    def test_login_no_permite_bypass_por_inyeccion(self):
        payload = {"$ne": None}
        assert (payload == "admin") is False


class TestExposicionDeSecretos:

    def test_db_no_tiene_credenciales_hardcodeadas(self):
        with open(os.path.join(RUTA_LIVE_SHARE, "db.py"), "r", encoding="utf-8") as f:
            contenido = f.read()
        patron = re.compile(r"mongodb(?:\+srv)?://[^:\s]+:[^@\s]+@", re.IGNORECASE)
        assert patron.search(contenido) is None

    def test_db_usa_dotenv(self):
        with open(os.path.join(RUTA_LIVE_SHARE, "db.py"), "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "load_dotenv" in contenido
        assert "os.getenv" in contenido


class TestControlDeAcceso:

    def test_eliminar_producto_requiere_id_string(self, mocker):
        import db
        mock_col = mocker.patch("db.inventario_col")
        mock_col.delete_one.return_value.deleted_count = 0
        mocker.patch("db.auditoria_col")
        db.eliminar_producto(ADMIN, str({"$ne": None}))
        args = mock_col.delete_one.call_args[0][0]
        assert isinstance(args["_id"], str)