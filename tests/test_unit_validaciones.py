import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Live Share')))
from IdentificarCliente import VentanaIdentificarCliente
from NuevaVenta import VentanaNuevaVenta


class TestValidacionRUT:

    @pytest.fixture
    def ventana(self):
        return VentanaIdentificarCliente.__new__(VentanaIdentificarCliente)

    @pytest.mark.parametrize("rut", ["12345678-9", "12345678-K", "1234567-8", "9999999-k"])
    def test_ruts_validos(self, ventana, rut):
        assert ventana._validar_rut(rut) is True

    @pytest.mark.parametrize("rut", ["", "12345678", "12345678-A", "12.345.678-9",
                                     "12345678--9", "abc-def", None])
    def test_ruts_invalidos(self, ventana, rut):
        try:
            assert ventana._validar_rut(rut) is False
        except TypeError:
            pytest.fail("La validación de RUT no debe fallar con None")


class TestCarritoVenta:

    @pytest.fixture
    def ventana(self, mocker):
        v = VentanaNuevaVenta.__new__(VentanaNuevaVenta)
        v.catalogo = [
            ["PROD-001", "Polera", "Poleras", "M", 9990, 5, "111"],
            ["PROD-002", "Jeans", "Pantalones", "32", 19990, 0, "222"],
        ]
        v.items = []
        v.usuario = {"_id": "USR-002", "username": "vendedor1", "rol": "vendedor"}
        v._refrescar_tabla = mocker.MagicMock()
        v._ocultar_spin = mocker.MagicMock()
        return v

    def test_agregar_producto_con_stock(self, ventana, mocker):
        ventana._get_id_input = mocker.MagicMock(return_value="PROD-001")
        ventana.entry_id = mocker.MagicMock()
        ventana.agregar_producto()
        assert len(ventana.items) == 1
        assert ventana.items[0]["cantidad"] == 1
        assert ventana.items[0]["subtotal"] == 9990

    def test_agregar_producto_duplicado(self, ventana, mocker):
        ventana.items = [{"id_producto": "PROD-001", "nombre": "Polera"}]
        ventana._get_id_input = mocker.MagicMock(return_value="PROD-001")
        mocker.patch("NuevaVenta.messagebox.showinfo")
        ventana.agregar_producto()
        assert len(ventana.items) == 1

    def test_decrementar_no_baja_de_uno(self, ventana, mocker):
        ventana.items = [{
            "id_producto": "PROD-001", "precio_unitario": 9990,
            "cantidad": 1, "subtotal": 9990,
        }]
        ventana._item_seleccionado = mocker.MagicMock(return_value=ventana.items[0])
        ventana._decrementar()
        assert ventana.items[0]["cantidad"] == 1