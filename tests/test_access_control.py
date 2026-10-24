"""
Tests de control de acceso (OWASP A01:2025).
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'Live Share')
))

import db

ADMIN = {"_id": "USR-001", "username": "admin", "rol": "admin"}
VENDEDOR = {"_id": "USR-002", "username": "vendedor1", "rol": "vendedor"}
AUDITOR = {"_id": "USR-003", "username": "auditor1", "rol": "auditor"}


class TestInventarioPermisos:
    def test_admin_puede_crear(self, mocker):
        mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        assert db.insertar_producto(
            ADMIN, ["PROD-001", "X", "Cat", "M", 100, 1, "111"]
        ) is True

    def test_vendedor_no_puede_crear(self, mocker):
        mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        with pytest.raises(PermissionError, match="no tiene permiso 'crear'"):
            db.insertar_producto(
                VENDEDOR, ["PROD-001", "X", "Cat", "M", 100, 1, "111"]
            )

    def test_vendedor_no_puede_eliminar(self, mocker):
        mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        with pytest.raises(PermissionError, match="no tiene permiso 'eliminar'"):
            db.eliminar_producto(VENDEDOR, "PROD-001")

    def test_sin_sesion_no_puede_nada(self, mocker):
        mocker.patch("db.auditoria_col")
        with pytest.raises(PermissionError, match="Debe iniciar sesión"):
            db.obtener_productos(None)


class TestClientesPermisos:
    def test_vendedor_puede_crear(self, mocker):
        mocker.patch("db.clientes_col")
        mocker.patch("db.auditoria_col")
        datos = {
            "_id": "CLI-001", "nombre": "A", "apellido_paterno": "B",
            "apellido_materno": "C", "rut": "1-9", "telefono": "",
            "email": "", "calle": "", "numero": "", "comuna": "",
            "ciudad": "", "region": "", "fecha_nacimiento": "",
            "estado": "activo", "aceptado": True,
            "puede_recibir_promociones": False,
        }
        db.insertar_cliente(VENDEDOR, datos)

    def test_vendedor_no_puede_eliminar(self, mocker):
        mocker.patch("db.clientes_col")
        mocker.patch("db.auditoria_col")
        with pytest.raises(PermissionError):
            db.eliminar_cliente_db(VENDEDOR, "CLI-001")


class TestVentasAntiIDOR:
    def test_vendedor_solo_ve_sus_ventas(self, mocker):
        mock_ven = mocker.patch("db.ventas_col")
        mock_ven.find.return_value.sort.return_value = [
            {"_id": "VEN-001", "fecha_venta": "2026-10-19",
             "cliente": {"nombre": "A", "apellido": "B"},
             "total": 100, "estado": "Válida",
             "empleado_id": VENDEDOR["_id"]},
        ]
        mocker.patch("db.auditoria_col")

        ventas = db.obtener_ventas(VENDEDOR)
        assert len(ventas) == 1
        args, kwargs = mock_ven.find.call_args
        assert args[0] == {"empleado_id": VENDEDOR["_id"]}

    def test_admin_ve_todas_las_ventas(self, mocker):
        mock_ven = mocker.patch("db.ventas_col")
        mock_ven.find.return_value.sort.return_value = []
        mocker.patch("db.auditoria_col")

        db.obtener_ventas(ADMIN)
        args, _ = mock_ven.find.call_args
        assert args[0] == {}

    def test_vendedor_no_puede_ver_venta_ajena(self, mocker):
        mock_ven = mocker.patch("db.ventas_col")
        mock_ven.find_one.return_value = {
            "_id": "VEN-001", "empleado_id": "OTRO-USR",
            "productos": [], "cliente": {"nombre": "X"},
        }
        mocker.patch("db.auditoria_col")

        with pytest.raises(PermissionError, match="No tiene permiso"):
            db.obtener_venta_completa(VENDEDOR, "VEN-001")

    def test_vendedor_no_puede_anular(self, mocker):
        mocker.patch("db.ventas_col")
        mocker.patch("db.auditoria_col")
        with pytest.raises(PermissionError):
            db.anular_venta_db(VENDEDOR, "VEN-001", "x", "NC-001")

    def test_vendedor_no_puede_revertir(self, mocker):
        mocker.patch("db.ventas_col")
        mocker.patch("db.auditoria_col")
        with pytest.raises(PermissionError):
            db.revertir_venta_db(VENDEDOR, "VEN-001", "x", "NC-001")


class TestAuditoria:
    def test_acceso_denegado_se_registra(self, mocker):
        mock_aud = mocker.patch("db.auditoria_col")
        mocker.patch("db.inventario_col")

        with pytest.raises(PermissionError):
            db.eliminar_producto(VENDEDOR, "PROD-001")

        assert mock_aud.insert_one.called
        doc = mock_aud.insert_one.call_args[0][0]
        assert doc["accion"] == "ACCESO_DENEGADO"
        assert doc["rol"] == "vendedor"
