# Live Share/errores.py
"""
Manejo centralizado de excepciones (OWASP A10:2025).
Evita exponer stack traces al usuario y registra incidentes.
"""
import logging
from tkinter import messagebox

logger = logging.getLogger("errores")


class AppError(Exception):
    """Excepción base de la aplicación con mensaje apto para el usuario."""

    def __init__(self, mensaje_usuario, detalle_tecnico=""):
        super().__init__(detalle_tecnico or mensaje_usuario)
        self.mensaje_usuario = mensaje_usuario
        self.detalle_tecnico = detalle_tecnico


class ErrorConexion(AppError):
    pass


class ErrorAutenticacion(AppError):
    pass


class ErrorPermiso(AppError):
    pass


class ErrorDatos(AppError):
    pass


def manejar_excepcion(parent, excepcion, contexto="Operación"):
    """
    Convierte cualquier excepción en un mensaje seguro para el usuario.
    Registra el detalle técnico en el log (no en pantalla).
    """
    if isinstance(excepcion, PermissionError):
        # A01: ya lo capturamos en cada ventana, pero por si acaso
        logger.warning("[%s] PermissionError: %s", contexto, excepcion)
        messagebox.showerror("Acceso denegado", str(excepcion), parent=parent)
        return

    if isinstance(excepcion, AppError):
        logger.warning("[%s] %s: %s",
                       contexto, type(excepcion).__name__, excepcion)
        messagebox.showerror("Error", excepcion.mensaje_usuario, parent=parent)
        return

    # Excepción inesperada: log completo, mensaje genérico
    logger.exception("[%s] Excepción no controlada", contexto)
    messagebox.showerror(
        "Error inesperado",
        "Ocurrió un error inesperado. Intente nuevamente.\n"
        "Si el problema persiste, contacte al administrador.",
        parent=parent,
    )