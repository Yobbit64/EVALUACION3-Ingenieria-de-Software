import pytest
import mongomock
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Live Share')))


ADMIN = {"_id": "USR-001", "username": "admin", "rol": "admin"}


@pytest.fixture
def db_en_memoria(monkeypatch):
    cliente_mock = mongomock.MongoClient()
    db_test = cliente_mock["boutique_test"]

    import db
    monkeypatch.setattr("db.inventario_col", db_test["inventario"])
    monkeypatch.setattr("db.ventas_col", db_test["ventas"])
    monkeypatch.setattr("db.clientes_col", db_test["cliente"])
    monkeypatch.setattr("db.usuarios_col", db_test["usuarios"])
    monkeypatch.setattr("db.auditoria_col", db_test["auditoria"])
    return db


class TestFlujoVentaCompleto:

    def test_venta_completa_actualiza_inventario(self, db_en_memoria):
        db_en_memoria.insertar_producto(
            ADMIN, ["PROD-001", "Polera", "Poleras", "M", 9990, 10, "111"]
        )
        db_en_memoria.insertar_venta(ADMIN, {
            "_id": "VEN-001",
            "cliente": {"id_cliente": "CLI-000", "nombre": "Público", "apellido": "General"},
            "productos": [{"id_producto": "PROD-001", "cantidad": 3}],
            "subtotal": 29970, "total": 29970,
            "metodo_pago": "Efectivo", "comprobante": "Boleta", "folio": "BOL-000001",
        })
        producto = db_en_memoria.inventario_col.find_one({"_id": "PROD-001"})
        assert producto["unidades_disponibles"] == 7
        venta = db_en_memoria.ventas_col.find_one({"_id": "VEN-001"})
        assert venta["estado"] == "Válida"

    def test_reversion_reintegra_stock_completo(self, db_en_memoria):
        db_en_memoria.insertar_producto(
            ADMIN, ["PROD-001", "Polera", "Poleras", "M", 9990, 10, "111"]
        )
        db_en_memoria.insertar_venta(ADMIN, {
            "_id": "VEN-001",
            "cliente": {"id_cliente": "CLI-000", "nombre": "Público", "apellido": "General"},
            "productos": [{"id_producto": "PROD-001", "cantidad": 4}],
            "subtotal": 39960, "total": 39960,
            "metodo_pago": "Efectivo", "comprobante": "Boleta", "folio": "BOL-000001",
        })
        assert db_en_memoria.inventario_col.find_one({"_id": "PROD-001"})["unidades_disponibles"] == 6

        db_en_memoria.revertir_venta_db(ADMIN, "VEN-001", "Prueba", "NC-001")

        assert db_en_memoria.inventario_col.find_one({"_id": "PROD-001"})["unidades_disponibles"] == 10
        venta = db_en_memoria.ventas_col.find_one({"_id": "VEN-001"})
        assert venta["estado"] == "Revertida"

    def test_anulacion_no_afecta_stock(self, db_en_memoria):
        db_en_memoria.insertar_producto(
            ADMIN, ["PROD-001", "Polera", "Poleras", "M", 9990, 10, "111"]
        )
        db_en_memoria.insertar_venta(ADMIN, {
            "_id": "VEN-001",
            "cliente": {"id_cliente": "CLI-000", "nombre": "Público", "apellido": "General"},
            "productos": [{"id_producto": "PROD-001", "cantidad": 2}],
            "subtotal": 19980, "total": 19980,
            "metodo_pago": "Efectivo", "comprobante": "Boleta", "folio": "BOL-000001",
        })
        db_en_memoria.anular_venta_db(ADMIN, "VEN-001", "Error", "NC-001")
        assert db_en_memoria.inventario_col.find_one({"_id": "PROD-001"})["unidades_disponibles"] == 8


class TestIntegridadReferencial:

    def test_venta_siempre_tiene_cliente_valido(self, db_en_memoria):
        cliente_gen = db_en_memoria.obtener_cliente_generico(ADMIN)
        db_en_memoria.insertar_venta(ADMIN, {
            "_id": "VEN-001",
            "cliente": {
                "id_cliente": cliente_gen["_id"],
                "nombre": cliente_gen["nombre"],
                "apellido": cliente_gen["apellido_paterno"],
            },
            "productos": [{"id_producto": "PROD-999", "cantidad": 1}],
            "subtotal": 100, "total": 100,
            "metodo_pago": "Efectivo", "comprobante": "Boleta", "folio": "BOL-000001",
        })
        venta = db_en_memoria.ventas_col.find_one({"_id": "VEN-001"})
        assert venta["cliente"]["id_cliente"] == "CLI-000"