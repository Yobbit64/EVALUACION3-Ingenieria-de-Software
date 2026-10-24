"""
Consulta la colección 'auditoria' y genera un reporte de alertas (A09:2025).
Uso:
    python scripts/alertas.py
    python scripts/alertas.py --horas 24
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Live Share"))
import db


UMBRAL_ACCESOS_DENEGADOS = 5
UMBRAL_LOGINS_FALLIDOS = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--horas", type=int, default=1,
                        help="Ventana en horas (por defecto 1)")
    args = parser.parse_args()

    db._init_cols()
    ahora = datetime.now()
    desde = (ahora - timedelta(hours=args.horas)).isoformat()

    accesos = list(db._aud().find({
        "accion": "ACCESO_DENEGADO",
        "fecha": {"$gte": desde},
    }))
    if len(accesos) >= UMBRAL_ACCESOS_DENEGADOS:
        print(f"[ALERTA {ahora.isoformat()}] "
              f"{len(accesos)} accesos denegados en las ultimas {args.horas}h.")
        for a in accesos[:5]:
            print(f"  - {a.get('username')} intento {a.get('accion')} "
                  f"en {a.get('modulo')}")

    fallidos = list(db._aud().find({
        "accion": "LOGIN_FALLIDO",
        "fecha": {"$gte": desde},
    }))
    if len(fallidos) >= UMBRAL_LOGINS_FALLIDOS:
        print(f"[ALERTA {ahora.isoformat()}] "
              f"{len(fallidos)} logins fallidos en las ultimas {args.horas}h.")

    if not accesos and not fallidos:
        print(f"[{ahora.isoformat()}] Sin alertas.")


if __name__ == "__main__":
    main()
