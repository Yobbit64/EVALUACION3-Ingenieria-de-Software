"""
Script de SEED inicial: crea los usuarios admin y vendedor en MongoDB.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Live Share"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import bcrypt
from datetime import datetime
import db


def crear_usuario_si_no_existe(username, password, rol, nombre_completo):
    db._init_cols()
    existente = db._usr().find_one({"username": username})
    if existente:
        print(f"  [SKIP] Usuario '{username}' ya existe (rol={existente['rol']}).")
        return

    usuarios = list(db._usr().find({}, {"_id": 1}))
    max_num = max((db._extraer_numero_id(u.get("_id")) for u in usuarios), default=0)
    nuevo_id = f"USR-{max_num + 1:03d}"

    fecha = datetime.now().isoformat()
    doc = {
        "_id": nuevo_id,
        "username": username,
        "password_hash": bcrypt.hashpw(password.encode("utf-8"),
                                       bcrypt.gensalt()).decode("utf-8"),
        "rol": rol,
        "nombre_completo": nombre_completo,
        "email": "",
        "activo": True,
        "fecha_creacion": fecha,
        "fecha_actualizacion": fecha,
        "ultimo_login": None,
        "historial_cambios": [{
            "fecha": fecha,
            "usuario": "sistema",
            "accion": "creacion",
            "detalle": "Usuario creado por script de seed",
        }],
    }
    db._usr().insert_one(doc)
    print(f"  [OK] Usuario '{username}' creado con rol '{rol}' (id={nuevo_id})")


def main():
    print("=== Seed de usuarios iniciales ===\n")

    admin_user = os.getenv("SEED_ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("SEED_ADMIN_PASSWORD")
    vend_user = os.getenv("SEED_VENDEDOR_USERNAME", "vendedor1")
    vend_pass = os.getenv("SEED_VENDEDOR_PASSWORD")

    if not admin_pass:
        print("ERROR: Falta SEED_ADMIN_PASSWORD en .env")
        sys.exit(1)

    try:
        db.ping()
    except Exception as e:
        print(f"ERROR: No se pudo conectar a MongoDB: {e}")
        sys.exit(1)

    print("\nCreando usuarios...")
    crear_usuario_si_no_existe(admin_user, admin_pass, "admin",
                               "Administrador del Sistema")

    if vend_pass:
        crear_usuario_si_no_existe(vend_user, vend_pass, "vendedor",
                                   "Vendedor de Prueba")
    else:
        print("  [WARN] SEED_VENDEDOR_PASSWORD no definido. Se omite vendedor.")

    print("\n=== Seed completado ===")


if __name__ == "__main__":
    main()
