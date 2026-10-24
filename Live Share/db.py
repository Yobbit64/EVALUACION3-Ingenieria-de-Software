# Live Share/db.py
import os
import re
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import (
    OperationFailure,
    ServerSelectionTimeoutError,
    PyMongoError,
)
import bcrypt

_RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
load_dotenv(_RAIZ_PROYECTO / ".env")

# ---------- Logging (A02) ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_RAIZ_PROYECTO / "boutique.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
logger_auditoria = logging.getLogger("auditoria")

URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "tienda_boutique")
APP_ENV = os.getenv("APP_ENV", "development")


def _validar_uri(uri):
    """A02/A04: valida formato de URI y uso de TLS."""
    if not uri:
        return
    if not (uri.startswith("mongodb://") or uri.startswith("mongodb+srv://")):
        raise RuntimeError("MONGODB_URI inválida: debe empezar por mongodb:// o mongodb+srv://")
    if APP_ENV == "production":
        if "ssl=true" not in uri and "tls=true" not in uri and "+srv" not in uri:
            raise RuntimeError("En producción MONGODB_URI debe usar TLS (ssl=true o +srv).")
    else:
        if "ssl=true" not in uri and "tls=true" not in uri and "+srv" not in uri:
            logger.warning("MONGODB_URI sin TLS explícito. Asegúrese en producción.")


_validar_uri(URI or "")

# ---------- Lazy init ----------
_client = None
_db = None
inventario_col = None
clientes_col = None
ventas_col = None
usuarios_col = None
auditoria_col = None


def _init_cols():
    global _client, _db, inventario_col, clientes_col, ventas_col, usuarios_col, auditoria_col
    if _client is not None and _db is not None:
        return
    if not URI:
        raise RuntimeError(
            "MONGODB_URI no está definida. Configure el archivo .env."
        )
    try:
        _client = MongoClient(URI, server_api=ServerApi("1"),
                              serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
    except OperationFailure as e:
        raise RuntimeError("Credenciales de MongoDB inválidas.") from e
    except ServerSelectionTimeoutError as e:
        raise RuntimeError(
            "No se pudo conectar a MongoDB (timeout). "
            "Verifique su red o la whitelist de IP en Atlas."
        ) from e
    except PyMongoError as e:
        raise RuntimeError(f"Error de MongoDB: {type(e).__name__}") from e

    _db = _client[DB_NAME]
    inventario_col = _db["inventario"]
    clientes_col = _db["cliente"]
    ventas_col = _db["ventas"]
    usuarios_col = _db["usuarios"]
    auditoria_col = _db["auditoria"]


def _inv():
    if inventario_col is None:
        _init_cols()
    return inventario_col


def _cli():
    if clientes_col is None:
        _init_cols()
    return clientes_col


def _ven():
    if ventas_col is None:
        _init_cols()
    return ventas_col


def _usr():
    if usuarios_col is None:
        _init_cols()
    return usuarios_col


def _aud():
    if auditoria_col is None:
        _init_cols()
    return auditoria_col


def ping():
    try:
        if _client is None:
            _init_cols()
        _client.admin.command("ping")
        logger.info("Conectado a MongoDB Atlas")
    except Exception as e:
        logger.error("Error de conexión: %s", e)
        raise


# ---------- Helper ID ----------
def _extraer_numero_id(id_str):
    try:
        return int(str(id_str).split("-")[1])
    except (IndexError, ValueError, AttributeError) as e:
        logger.warning("ID inválido ignorado: %r (%s)", id_str, e)
        return 0


# ============================================================
# CONTROL DE ACCESO (A01)
# ============================================================
PERMISOS = {
    "admin": {
        "inventario": ["crear", "leer", "actualizar", "eliminar"],
        "clientes":   ["crear", "leer", "actualizar", "eliminar"],
        "ventas":     ["crear", "leer", "anular", "revertir"],
        "usuarios":   ["crear", "leer", "actualizar", "eliminar"],
    },
    "vendedor": {
        "inventario": ["leer"],
        "clientes":   ["crear", "leer"],
        "ventas":     ["crear", "leer"],
        "usuarios":   [],
    },
    "auditor": {
        "inventario": ["leer"],
        "clientes":   ["leer"],
        "ventas":     ["leer"],
        "usuarios":   ["leer"],
    },
}


def _registrar_auditoria(usuario, accion, modulo, detalle):
    try:
        _aud().insert_one({
            "_id": f"AUD-{uuid.uuid4().hex[:12].upper()}",
            "fecha": datetime.now().isoformat(),
            "usuario_id": (usuario or {}).get("_id", "ANON"),
            "username": (usuario or {}).get("username", "anonimo"),
            "rol": (usuario or {}).get("rol", "desconocido"),
            "accion": accion,
            "modulo": modulo,
            "detalle": detalle,
            "ip": "local",
        })
    except Exception as e:
        logger_auditoria.error("No se pudo registrar auditoría: %s", e)


def verificar_permiso(usuario, modulo, accion):
    if not usuario:
        _registrar_auditoria(None, "ACCESO_DENEGADO", modulo,
                             f"Sin sesión intentó '{accion}'")
        raise PermissionError(f"Debe iniciar sesión para '{accion}' en '{modulo}'")
    rol = usuario.get("rol")
    if rol not in PERMISOS:
        _registrar_auditoria(usuario, "ACCESO_DENEGADO", modulo,
                             f"Rol desconocido: {rol}")
        raise PermissionError(f"Rol desconocido: {rol}")
    if accion not in PERMISOS[rol].get(modulo, []):
        _registrar_auditoria(usuario, "ACCESO_DENEGADO", modulo,
                             f"Rol '{rol}' intentó '{accion}'")
        raise PermissionError(
            f"El rol '{rol}' no tiene permiso '{accion}' en '{modulo}'"
        )


# ============================================================
# AUTENTICACIÓN (A07)
# ============================================================
MAX_INTENTOS = 5
BLOQUEO_MINUTOS = 15


def _esta_bloqueado(user_doc):
    hasta = user_doc.get("bloqueado_hasta")
    if not hasta:
        return False
    try:
        return datetime.fromisoformat(hasta) > datetime.now()
    except (ValueError, TypeError):
        return False


def _validar_fortaleza_password(password):
    """A07: valida fortaleza mínima de contraseña."""
    if not isinstance(password, str):
        return False, "La contraseña debe ser texto."
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "Debe contener al menos una mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "Debe contener al menos una minúscula."
    if not re.search(r"\d", password):
        return False, "Debe contener al menos un dígito."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=~`\[\]\\/;']", password):
        return False, "Debe contener al menos un símbolo."
    return True, ""


def obtener_usuario(username):
    return _usr().find_one({"username": username, "activo": True})


def obtener_usuario_por_id(user_id):
    return _usr().find_one({"_id": user_id, "activo": True})


def autenticar_usuario(username, password):
    """A07: bloqueo persistente con $inc atómico."""
    user = obtener_usuario(username)
    if not user:
        return None

    if _esta_bloqueado(user):
        _registrar_auditoria(user, "LOGIN_BLOQUEADO", "auth",
                             "Cuenta bloqueada, intento de login")
        return None

    try:
        ok = bcrypt.checkpw(password.encode("utf-8"),
                            user["password_hash"].encode("utf-8"))
    except ValueError:
        ok = False

    if not ok:
        # $inc atómico: no leemos el valor, lo incrementamos y leemos el resultado
        resultado = _usr().find_one_and_update(
            {"_id": user["_id"]},
            {"$inc": {"intentos_fallidos": 1}},
            return_document=True,   # devuelve el doc DESPUÉS del update
        )
        intentos = (resultado or {}).get("intentos_fallidos", 1)

        if intentos >= MAX_INTENTOS:
            hasta = (datetime.now() + timedelta(minutes=BLOQUEO_MINUTOS)).isoformat()
            _usr().update_one(
                {"_id": user["_id"]},
                {"$set": {"bloqueado_hasta": hasta, "intentos_fallidos": 0}},
            )
            _registrar_auditoria(user, "LOGIN_BLOQUEADO", "auth",
                                 f"Cuenta bloqueada hasta {hasta}")
        else:
            _registrar_auditoria(user, "LOGIN_FALLIDO", "auth",
                                 f"Intento {intentos}/{MAX_INTENTOS}")
        return None

    _usr().update_one(
        {"_id": user["_id"]},
        {"$set": {
            "ultimo_login": datetime.now().isoformat(),
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
        }},
    )
    _registrar_auditoria(user, "LOGIN_OK", "auth", "Inicio de sesión")
    return user


def crear_usuario(usuario_actual, username, password, rol,
                  nombre_completo="", email=""):
    verificar_permiso(usuario_actual, "usuarios", "crear")
    if rol not in PERMISOS:
        raise ValueError(f"Rol inválido: {rol}. Válidos: {list(PERMISOS)}")
    if obtener_usuario(username):
        raise ValueError(f"El usuario '{username}' ya existe")
    ok, msg = _validar_fortaleza_password(password)
    if not ok:
        raise ValueError(msg)

    usuarios = list(_usr().find({}, {"_id": 1}))
    max_num = max((_extraer_numero_id(u.get("_id")) for u in usuarios), default=0)
    nuevo_id = f"USR-{max_num + 1:03d}"

    fecha = datetime.now().isoformat()
    doc = {
        "_id": nuevo_id,
        "username": username,
        "password_hash": bcrypt.hashpw(password.encode("utf-8"),
                                       bcrypt.gensalt()).decode("utf-8"),
        "rol": rol,
        "nombre_completo": nombre_completo or username,
        "email": email,
        "activo": True,
        "intentos_fallidos": 0,
        "bloqueado_hasta": None,
        "fecha_creacion": fecha,
        "fecha_actualizacion": fecha,
        "ultimo_login": None,
        "historial_cambios": [{
            "fecha": fecha,
            "usuario": (usuario_actual or {}).get("username", "sistema"),
            "accion": "creacion",
            "detalle": f"Usuario '{username}' creado con rol '{rol}'",
        }],
    }
    _usr().insert_one(doc)
    _registrar_auditoria(usuario_actual, "USUARIO_CREADO", "usuarios",
                         f"Creó usuario '{username}' con rol '{rol}'")
    return doc


def listar_usuarios(usuario_actual):
    verificar_permiso(usuario_actual, "usuarios", "leer")
    return list(_usr().find({}, {"password_hash": 0}))


# ============================================================
# INVENTARIO
# ============================================================
def doc_a_lista(doc):
    return [
        doc.get("_id", ""), doc.get("nombre", ""), doc.get("categoria", ""),
        doc.get("talla", ""), doc.get("precio", 0),
        doc.get("unidades_disponibles", 0), doc.get("codigo_barras", ""),
    ]


def lista_a_doc(lista):
    return {
        "_id": lista[0], "nombre": lista[1], "categoria": lista[2],
        "talla": lista[3], "precio": int(lista[4]),
        "unidades_disponibles": int(lista[5]), "codigo_barras": lista[6],
    }


def obtener_productos(usuario):
    verificar_permiso(usuario, "inventario", "leer")
    return [doc_a_lista(d) for d in _inv().find()]


def insertar_producto(usuario, lista):
    verificar_permiso(usuario, "inventario", "crear")
    _inv().insert_one(lista_a_doc(lista))
    _registrar_auditoria(usuario, "PRODUCTO_CREADO", "inventario",
                         f"Creó producto {lista[0]}")
    return True


def actualizar_producto(usuario, id_producto, lista_actualizada):
    verificar_permiso(usuario, "inventario", "actualizar")
    doc = lista_a_doc(lista_actualizada)
    doc.pop("_id", None)
    r = _inv().update_one({"_id": id_producto}, {"$set": doc})
    _registrar_auditoria(usuario, "PRODUCTO_ACTUALIZADO", "inventario",
                         f"Actualizó producto {id_producto}")
    return r.modified_count > 0


def eliminar_producto(usuario, id_producto):
    verificar_permiso(usuario, "inventario", "eliminar")
    r = _inv().delete_one({"_id": str(id_producto)})
    _registrar_auditoria(usuario, "PRODUCTO_ELIMINADO", "inventario",
                         f"Eliminó producto {id_producto}")
    return r.deleted_count > 0


def buscar_producto_por_id(usuario, id_producto):
    verificar_permiso(usuario, "inventario", "leer")
    doc = _inv().find_one({"_id": id_producto})
    return doc_a_lista(doc) if doc else None


# ============================================================
# CLIENTES
# ============================================================
def doc_a_lista_cliente(doc):
    return [
        doc.get("_id", ""), doc.get("nombre", ""), doc.get("apellido_paterno", ""),
        doc.get("apellido_materno", ""), doc.get("rut", ""),
        doc.get("telefono", ""), doc.get("email", ""),
    ]


def obtener_clientes(usuario):
    verificar_permiso(usuario, "clientes", "leer")
    return [doc_a_lista_cliente(d) for d in _cli().find()]


def obtener_cliente_completo(usuario, id_cliente):
    verificar_permiso(usuario, "clientes", "leer")
    return _cli().find_one({"_id": id_cliente})


def insertar_cliente(usuario, datos):
    verificar_permiso(usuario, "clientes", "crear")
    fecha = datetime.now().isoformat()
    doc = {
        "_id": datos["_id"], "nombre": datos["nombre"],
        "apellido_paterno": datos["apellido_paterno"],
        "apellido_materno": datos["apellido_materno"],
        "rut": str(datos["rut"]), "telefono": datos["telefono"],
        "email": datos["email"],
        "direccion": {
            "calle": datos["calle"], "numero": datos["numero"],
            "comuna": datos["comuna"], "ciudad": datos["ciudad"],
            "region": datos["region"],
        },
        "fecha_nacimiento": datos["fecha_nacimiento"],
        "fecha_registro": fecha, "fecha_actualizacion": fecha,
        "estado": datos["estado"],
        "historial_compras": {"total_compras": 0, "monto_total": 0, "ultima_compra": None},
        "consentimiento_datos": {
            "aceptado": datos["aceptado"], "fecha_aceptacion": fecha,
            "finalidad": "gestion_comercial_y_promociones",
            "puede_recibir_promociones": datos["puede_recibir_promociones"],
        },
        "usuario_creacion": usuario["username"],
        "usuario_actualizacion": usuario["username"],
        "historial_cambios": [{
            "fecha": fecha, "usuario": usuario["username"],
            "accion": "creacion", "detalle": "Cliente registrado exitosamente",
        }],
    }
    _cli().insert_one(doc)
    _registrar_auditoria(usuario, "CLIENTE_CREADO", "clientes",
                         f"Creó cliente {datos['_id']}")
    return doc


def actualizar_cliente_db(usuario, id_cliente, datos):
    verificar_permiso(usuario, "clientes", "actualizar")
    fecha = datetime.now().isoformat()
    actual = _cli().find_one({"_id": id_cliente})
    fecha_acept = (actual.get("consentimiento_datos") or {}).get("fecha_aceptacion")
    if not fecha_acept and datos.get("aceptado"):
        fecha_acept = fecha
    _cli().update_one(
        {"_id": id_cliente},
        {
            "$set": {
                "nombre": datos["nombre"],
                "apellido_paterno": datos["apellido_paterno"],
                "apellido_materno": datos["apellido_materno"],
                "rut": str(datos["rut"]), "telefono": datos["telefono"],
                "email": datos["email"],
                "direccion": {
                    "calle": datos["calle"], "numero": datos["numero"],
                    "comuna": datos["comuna"], "ciudad": datos["ciudad"],
                    "region": datos["region"],
                },
                "fecha_nacimiento": datos["fecha_nacimiento"],
                "fecha_actualizacion": fecha,
                "estado": datos["estado"],
                "usuario_actualizacion": usuario["username"],
                "consentimiento_datos": {
                    "aceptado": datos["aceptado"],
                    "fecha_aceptacion": fecha_acept,
                    "finalidad": datos["finalidad"],
                    "puede_recibir_promociones": datos["puede_recibir_promociones"],
                },
            },
            "$push": {"historial_cambios": {
                "fecha": fecha, "usuario": usuario["username"],
                "accion": "actualizacion",
                "detalle": "Datos del cliente actualizados desde el sistema",
            }},
        },
    )
    _registrar_auditoria(usuario, "CLIENTE_ACTUALIZADO", "clientes",
                         f"Actualizó cliente {id_cliente}")


def eliminar_cliente_db(usuario, id_cliente):
    verificar_permiso(usuario, "clientes", "eliminar")
    r = _cli().delete_one({"_id": id_cliente})
    _registrar_auditoria(usuario, "CLIENTE_ELIMINADO", "clientes",
                         f"Eliminó cliente {id_cliente}")
    return r.deleted_count > 0


def buscar_cliente_por_documento(usuario, tipo_doc, numero_doc):
    verificar_permiso(usuario, "clientes", "leer")
    return _cli().find_one({"rut": str(numero_doc)})


def obtener_cliente_generico(usuario):
    verificar_permiso(usuario, "clientes", "leer")
    cliente = _cli().find_one({"_id": "CLI-000"})
    if not cliente:
        fecha = datetime.now().isoformat()
        cliente = {
            "_id": "CLI-000", "nombre": "Público",
            "apellido_paterno": "General", "apellido_materno": "",
            "rut": "00000000-0", "telefono": "", "email": "",
            "direccion": {"calle": "", "numero": "", "comuna": "", "ciudad": "", "region": ""},
            "fecha_nacimiento": "", "fecha_registro": fecha,
            "fecha_actualizacion": fecha, "estado": "activo",
            "historial_compras": {"total_compras": 0, "monto_total": 0, "ultima_compra": None},
            "consentimiento_datos": {
                "aceptado": False, "fecha_aceptacion": None,
                "finalidad": "", "puede_recibir_promociones": False,
            },
            "usuario_creacion": "sistema", "usuario_actualizacion": "sistema",
            "historial_cambios": [],
        }
        _cli().insert_one(cliente)
    return cliente


def crear_cliente_rapido(usuario, nombre, apellido, documento, tipo_doc="RUT"):
    verificar_permiso(usuario, "clientes", "crear")
    clientes = list(_cli().find({}, {"_id": 1}))
    max_num = max((_extraer_numero_id(c.get("_id")) for c in clientes), default=0)
    nuevo_id = f"CLI-{max_num + 1:03d}"
    fecha = datetime.now().isoformat()
    cliente = {
        "_id": nuevo_id, "nombre": nombre,
        "apellido_paterno": apellido, "apellido_materno": "",
        "rut": str(documento) if tipo_doc == "RUT" else "",
        "telefono": "", "email": "",
        "direccion": {"calle": "", "numero": "", "comuna": "", "ciudad": "", "region": ""},
        "fecha_nacimiento": "", "fecha_registro": fecha,
        "fecha_actualizacion": fecha, "estado": "activo",
        "historial_compras": {"total_compras": 0, "monto_total": 0, "ultima_compra": None},
        "consentimiento_datos": {
            "aceptado": True, "fecha_aceptacion": fecha,
            "finalidad": "gestion_comercial", "puede_recibir_promociones": False,
        },
        "usuario_creacion": usuario["username"],
        "usuario_actualizacion": usuario["username"],
        "historial_cambios": [{
            "fecha": fecha, "usuario": usuario["username"],
            "accion": "creacion_rapida", "detalle": "Cliente creado en venta",
        }],
    }
    _cli().insert_one(cliente)
    _registrar_auditoria(usuario, "CLIENTE_RAPIDO", "clientes",
                         f"Creó cliente rápido {nuevo_id}")
    return cliente


# ============================================================
# VENTAS (con reglas de negocio - A06)
# ============================================================
def siguiente_id_venta():
    ventas = list(_ven().find({}, {"_id": 1}))
    max_num = max((_extraer_numero_id(v.get("_id")) for v in ventas), default=0)
    return f"VEN-{max_num + 1:03d}"


def siguiente_folio_comprobante():
    ventas = list(_ven().find(
        {"comprobante.folio": {"$exists": True}}, {"comprobante.folio": 1}
    ))
    max_num = max(
        (_extraer_numero_id(v.get("comprobante", {}).get("folio")) for v in ventas),
        default=0,
    )
    return f"BOL-{max_num + 1:06d}"


def siguiente_nota_credito():
    ventas = list(_ven().find(
        {}, {"anulacion.nota_credito": 1, "reversion.nota_credito": 1}
    ))
    max_num = 0
    for v in ventas:
        for campo in ("anulacion", "reversion"):
            data = v.get(campo) or {}
            max_num = max(max_num, _extraer_numero_id(data.get("nota_credito")))
    return f"NC-{max_num + 1:03d}"


def insertar_venta(usuario, datos_venta):
    verificar_permiso(usuario, "ventas", "crear")

    # Reglas de negocio (A06)
    if datos_venta["cliente"]["id_cliente"] == usuario["_id"]:
        raise ValueError("No puede vender a su propio usuario.")
    if datos_venta["total"] <= 0:
        raise ValueError("El total debe ser mayor a 0.")
    for p in datos_venta["productos"]:
        if p["cantidad"] <= 0 or p["cantidad"] > 100:
            raise ValueError(f"Cantidad inválida para {p['id_producto']}")

    fecha = datetime.now().isoformat() + "Z"
    id_transaccion = f"TRX-{uuid.uuid4().hex[:12].upper()}"
    doc = {
        "_id": datos_venta["_id"],
        "fecha_venta": fecha,
        "estado": "Válida",
        "empleado": usuario["username"],
        "empleado_id": usuario["_id"],
        "cliente": datos_venta["cliente"],
        "productos": datos_venta["productos"],
        "subtotal": datos_venta["subtotal"],
        "descuento": 0,
        "total": datos_venta["total"],
        "metodo_pago": datos_venta["metodo_pago"].lower(),
        "estado_pago": "pagado",
        "detalles_pago": {
            "proveedor": "Mercado Pago" if datos_venta["metodo_pago"] != "Efectivo" else "Caja",
            "id_transaccion": id_transaccion,
            "codigo_autorizacion": "AUTH-000000",
            "ultimos_4_digitos": "0000",
            "tipo_tarjeta": datos_venta["metodo_pago"].lower(),
        },
        "comprobante": {
            "tipo": datos_venta["comprobante"].lower(),
            "folio": datos_venta["folio"],
            "fecha_emision": fecha,
            "url_pdf": f"https://storage.boutique.cl/comprobantes/{datos_venta['folio']}.pdf",
        },
        "anulacion": None, "reversion": None,
        "historial_cambios": [
            {"fecha": fecha, "usuario": usuario["username"],
             "accion": "creacion", "detalle": "Venta registrada exitosamente"},
            {"fecha": fecha, "usuario": usuario["username"],
             "accion": "emision_comprobante",
             "detalle": f"{datos_venta['comprobante']} {datos_venta['folio']} emitida"},
        ],
        "fecha_actualizacion": fecha,
    }
    _ven().insert_one(doc)
    for prod in datos_venta["productos"]:
        _inv().update_one(
            {"_id": prod["id_producto"]},
            {"$inc": {"unidades_disponibles": -prod["cantidad"]}},
        )
    _registrar_auditoria(usuario, "VENTA_CREADA", "ventas",
                         f"Registró venta {datos_venta['_id']}")


def obtener_ventas(usuario):
    verificar_permiso(usuario, "ventas", "leer")
    filtro = {} if usuario["rol"] == "admin" else {"empleado_id": usuario["_id"]}
    out = []
    for v in _ven().find(filtro).sort("fecha_venta", -1):
        out.append([
            v["_id"],
            v.get("fecha_venta", "")[:10],
            f"{v['cliente'].get('nombre','')} {v['cliente'].get('apellido','')}",
            v["total"], v["estado"],
        ])
    return out


def obtener_venta_completa(usuario, id_venta):
    verificar_permiso(usuario, "ventas", "leer")
    venta = _ven().find_one({"_id": id_venta})
    if not venta:
        return None
    if usuario["rol"] != "admin" and venta.get("empleado_id") != usuario["_id"]:
        _registrar_auditoria(usuario, "ACCESO_DENEGADO", "ventas",
                             f"Intento de ver venta ajena {id_venta}")
        raise PermissionError("No tiene permiso para ver esta venta")
    return venta


def anular_venta_db(usuario, id_venta, motivo, folio_nc):
    verificar_permiso(usuario, "ventas", "anular")
    fecha = datetime.now().isoformat() + "Z"
    if not _ven().find_one({"_id": id_venta}):
        return False
    _ven().update_one(
        {"_id": id_venta},
        {
            "$set": {
                "estado": "Anulada",
                "anulacion": {
                    "fecha": fecha, "motivo": motivo,
                    "nota_credito": folio_nc, "usuario": usuario["username"],
                },
                "fecha_actualizacion": fecha,
            },
            "$push": {"historial_cambios": {
                "fecha": fecha, "usuario": usuario["username"],
                "accion": "anulacion", "detalle": f"Venta anulada. Motivo: {motivo}",
            }},
        },
    )
    _registrar_auditoria(usuario, "VENTA_ANULADA", "ventas",
                         f"Anuló venta {id_venta}: {motivo}")
    return True


def revertir_venta_db(usuario, id_venta, motivo, folio_nc):
    verificar_permiso(usuario, "ventas", "revertir")
    fecha = datetime.now().isoformat() + "Z"
    doc = _ven().find_one({"_id": id_venta})
    if not doc:
        return False
    _ven().update_one(
        {"_id": id_venta},
        {
            "$set": {
                "estado": "Revertida",
                "reversion": {
                    "fecha": fecha, "motivo": motivo,
                    "nota_credito": folio_nc, "usuario": usuario["username"],
                },
                "fecha_actualizacion": fecha,
            },
            "$push": {"historial_cambios": {
                "fecha": fecha, "usuario": usuario["username"],
                "accion": "reversion", "detalle": f"Venta revertida. Motivo: {motivo}",
            }},
        },
    )
    for prod in doc.get("productos", []):
        _inv().update_one(
            {"_id": prod["id_producto"]},
            {"$inc": {"unidades_disponibles": prod["cantidad"]}},
        )
    _registrar_auditoria(usuario, "VENTA_REVERTIDA", "ventas",
                         f"Revirtió venta {id_venta}: {motivo}")
    return True


# ============================================================
# MANTENIMIENTO (A09)
# ============================================================
def limpiar_auditoria_antigua(dias=90):
    """A09: elimina eventos de auditoría más viejos que N días."""
    limite = (datetime.now() - timedelta(days=dias)).isoformat()
    r = _aud().delete_many({"fecha": {"$lt": limite}})
    logger.info("Auditoría: %d eventos eliminados (más viejos de %d días)",
                r.deleted_count, dias)
    return r.deleted_count