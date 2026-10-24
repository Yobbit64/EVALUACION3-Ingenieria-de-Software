import db

ADMIN = {"_id": "USR-001", "username": "admin", "rol": "admin"}


def test_inv_respeta_mock(mocker):
    mock_col = mocker.patch("db.inventario_col")
    mock_col.find.return_value = []
    mocker.patch("db.auditoria_col")
    assert db.obtener_productos(ADMIN) == []


def test_cli_respeta_mock(mocker):
    mock_col = mocker.patch("db.clientes_col")
    mock_col.find.return_value = []
    mocker.patch("db.auditoria_col")
    assert db.obtener_clientes(ADMIN) == []


def test_ven_respeta_mock(mocker):
    mock_col = mocker.patch("db.ventas_col")
    mock_col.find.return_value.sort.return_value = []
    mocker.patch("db.auditoria_col")
    assert db.obtener_ventas(ADMIN) == []