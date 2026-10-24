"""
Pruebas unitarias de la capa de datos (db.py), adaptadas a la API con roles.
"""
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Live Share')))
import db


ADMIN = {"_id": "USR-001", "username": "admin", "rol": "admin"}


class TestInventarioUnit:

    def test_obtener_productos_mapea_correctamente(self, mocker):
        mock_col = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        mock_col.find.return_value = [{
            "_id": "PROD-001", "nombre": "Polera", "categoria": "Poleras",
            "talla": "M", "precio": 9990, "unidades_disponibles": 5,
            "codigo_barras": "111",
        }]
        assert db.obtener_productos(ADMIN) == [
            ["PROD-001", "Polera", "Poleras", "M", 9990, 5, "111"]
        ]

    def test_obtener_productos_sin_codigo_barras(self, mocker):
        mock_col = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        mock_col.find.return_value = [{
            "_id": "PROD-002", "nombre": "Jean", "categoria": "Pantalones",
            "talla": "32", "precio": 19990, "unidades_disponibles": 3,
        }]
        assert db.obtener_productos(ADMIN)[0][6] == ""

    def test_insertar_producto_arma_documento_bson(self, mocker):
        mock_col = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        db.insertar_producto(ADMIN, ["PROD-003", "Chaqueta", "Chaquetas", "L", 39990, 2, "222"])
        doc = mock_col.insert_one.call_args[0][0]
        assert doc["_id"] == "PROD-003"
        assert doc["precio"] == 39990

    def test_actualizar_producto_no_modifica_id(self, mocker):
        mock_col = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")
        mock_col.update_one.return_value.modified_count = 1
        db.actualizar_producto(ADMIN, "PROD-001",
                               ["PROD-001", "Nuevo", "Cat", "M", 100, 5, "999"])
        set_doc = mock_col.update_one.call_args[0][1]["$set"]
        assert "_id" not in set_doc


class TestVentasUnit:

    def test_siguiente_id_venta_lista_vacia(self, mocker):
        mocker.patch("db.ventas_col").find.return_value = []
        assert db.siguiente_id_venta() == "VEN-001"

    def test_siguiente_id_venta_continua_secuencia(self, mocker):
        mocker.patch("db.ventas_col").find.return_value = [
            {"_id": "VEN-001"}, {"_id": "VEN-007"}, {"_id": "VEN-003"},
        ]
        assert db.siguiente_id_venta() == "VEN-008"

    def test_insertar_venta_descuenta_stock(self, mocker):
        m_ven = mocker.patch("db.ventas_col")
        m_inv = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")

        db.insertar_venta(ADMIN, {
            "_id": "VEN-001",
            "cliente": {"id_cliente": "CLI-001", "nombre": "X", "apellido": "Y"},
            "productos": [
                {"id_producto": "PROD-001", "cantidad": 2},
                {"id_producto": "PROD-002", "cantidad": 1},
            ],
            "subtotal": 50000, "total": 50000,
            "metodo_pago": "Débito", "comprobante": "Boleta", "folio": "BOL-000001",
        })
        assert m_ven.insert_one.call_count == 1
        assert m_inv.update_one.call_count == 2

    def test_revertir_venta_suma_stock(self, mocker):
        m_ven = mocker.patch("db.ventas_col")
        m_ven.find_one.return_value = {
            "_id": "VEN-001",
            "productos": [{"id_producto": "PROD-001", "cantidad": 3}],
        }
        m_inv = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")

        assert db.revertir_venta_db(ADMIN, "VEN-001", "motivo", "NC-001") is True
        assert m_inv.update_one.call_args[0][1] == {"$inc": {"unidades_disponibles": 3}}

    def test_revertir_venta_inexistente(self, mocker):
        m_ven = mocker.patch("db.ventas_col")
        m_ven.find_one.return_value = None
        m_inv = mocker.patch("db.inventario_col")
        mocker.patch("db.auditoria_col")

        assert db.revertir_venta_db(ADMIN, "VEN-X", "motivo", "NC-001") is False
        m_inv.update_one.assert_not_called()


class TestClientesUnit:

    def test_obtener_cliente_generico_lo_crea_si_no_existe(self, mocker):
        mock_col = mocker.patch("db.clientes_col")
        mock_col.find_one.return_value = None
        mocker.patch("db.auditoria_col")

        cliente = db.obtener_cliente_generico(ADMIN)
        mock_col.insert_one.assert_called_once()
        assert mock_col.insert_one.call_args[0][0]["_id"] == "CLI-000"
        assert cliente["_id"] == "CLI-000"

    def test_obtener_cliente_generico_no_duplica(self, mocker):
        mock_col = mocker.patch("db.clientes_col")
        mock_col.find_one.return_value = {"_id": "CLI-000", "nombre": "Público"}
        mocker.patch("db.auditoria_col")

        cliente = db.obtener_cliente_generico(ADMIN)
        mock_col.insert_one.assert_not_called()
        assert cliente["_id"] == "CLI-000"