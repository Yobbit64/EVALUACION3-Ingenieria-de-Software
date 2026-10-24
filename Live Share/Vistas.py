# Live Share/Vistas.py
import tkinter as tk
from tkinter import messagebox
import logging

from db import (
    autenticar_usuario,
    obtener_usuario,
    _esta_bloqueado,
    PERMISOS,
)
from errores import manejar_excepcion

logger = logging.getLogger(__name__)


# ==================== LOGIN ====================
class LoginBoutique:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Boutique")
        self.root.geometry("420x340")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (420 // 2)
        y = (self.root.winfo_screenheight() // 2) - (340 // 2)
        self.root.geometry(f"+{x}+{y}")


        tk.Label(root, text="SISTEMA BOUTIQUE",
                 font=("Segoe UI", 16, "bold"),
                 bg="#f5f5f5", fg="#2c3e50").pack(pady=(25, 20))

        frame = tk.Frame(root, bg="#f5f5f5")
        frame.pack(padx=40, fill="x")

        tk.Label(frame, text="Usuario", font=("Segoe UI", 10, "bold"),
                 bg="#f5f5f5", fg="#34495e", anchor="w").pack(fill="x")

        self.entry_usuario = tk.Entry(frame, font=("Segoe UI", 11),
                                      relief="solid", bd=1, bg="white")
        self.entry_usuario.pack(fill="x", ipady=5, pady=(3, 12))

        tk.Label(frame, text="Contraseña", font=("Segoe UI", 10, "bold"),
                 bg="#f5f5f5", fg="#34495e", anchor="w").pack(fill="x")

        self.entry_password = tk.Entry(frame, font=("Segoe UI", 11),
                                       show="•", relief="solid", bd=1, bg="white")
        self.entry_password.pack(fill="x", ipady=5, pady=(3, 18))

        tk.Button(root, text="Iniciar sesión",
                  font=("Segoe UI", 11, "bold"),
                  bg="#3498db", fg="white",
                  activebackground="#2980b9", activeforeground="white",
                  relief="flat", cursor="hand2", padx=20, pady=7,
                  command=self.iniciar_sesion).pack(pady=(0, 15))

        self.label_error = tk.Label(root, text="", font=("Segoe UI", 9),
                                    bg="#f5f5f5", fg="#e74c3c")
        self.label_error.pack()

        self.root.bind("<Return>", lambda e: self.iniciar_sesion())

    def iniciar_sesion(self):
        usuario_input = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        try:
            user = autenticar_usuario(usuario_input, password)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="login")
            return

        if user:
            self.root.destroy()
            panel_root = tk.Tk()
            panel_root.report_callback_exception = _report_callback_exception
            PanelPrincipal(panel_root, usuario=user)
            panel_root.mainloop()
# --- En el método iniciar_sesion, reemplaza el bloque else (líneas 85 a 93) ---
        else:
            # Verificamos si el usuario existe y está bloqueado en la BD
            try:
                doc = obtener_usuario(usuario_input)
            except Exception:
                doc = None
            if doc and _esta_bloqueado(doc):
                messagebox.showerror(
                    "Cuenta bloqueada",
                    f"Su cuenta está bloqueada hasta "
                    f"{doc['bloqueado_hasta'][:16]}. Intente más tarde.",
                    parent=self.root,
                )
                self.entry_password.delete(0, tk.END)
                return

            # Si no está bloqueado, solo mostramos error genérico
            self.label_error.config(text="⚠ Datos incorrectos.")

        self.entry_password.delete(0, tk.END)


# ==================== PANEL PRINCIPAL ====================
class PanelPrincipal:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario              # dict con _id, username, rol

        self.root.title(f"Boutique - Panel Principal ({usuario['username']})")
        self.root.geometry("720x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (720 // 2)
        y = (self.root.winfo_screenheight() // 2) - (420 // 2)
        self.root.geometry(f"+{x}+{y}")

        # Encabezado
        header = tk.Frame(root, bg="#2c3e50", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="BOUTIQUE - PANEL PRINCIPAL",
                 font=("Segoe UI", 13, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=20)

        tk.Label(header,
                 text=f"{usuario['nombre_completo']}  |  Rol: {usuario['rol'].upper()}",
                 font=("Segoe UI", 10),
                 bg="#2c3e50", fg="#ecf0f1").pack(side="right", padx=20)

        # Contenido
        contenido = tk.Frame(root, bg="#f5f5f5")
        contenido.pack(expand=True, fill="both", padx=40, pady=40)

        botones_frame = tk.Frame(contenido, bg="#f5f5f5")
        botones_frame.pack(expand=True)

        # Solo se muestran los módulos que el rol puede al menos "leer"
        permisos = PERMISOS.get(usuario["rol"], {})

        col = 0
        if "inventario" in permisos:
            self.crear_boton(botones_frame, "INVENTARIO", "📦",
                             "#3498db", "#2980b9", self.abrir_inventario)\
                .grid(row=0, column=col, padx=15); col += 1

        if "ventas" in permisos:
            self.crear_boton(botones_frame, "VENTAS", "💰",
                             "#27ae60", "#1e8449", self.abrir_ventas)\
                .grid(row=0, column=col, padx=15); col += 1

        if "clientes" in permisos:
            self.crear_boton(botones_frame, "CLIENTES", "👥",
                             "#e67e22", "#ca6f1e", self.abrir_clientes)\
                .grid(row=0, column=col, padx=15); col += 1

        # Pie
        pie = tk.Frame(root, bg="#f5f5f5")
        pie.pack(fill="x", padx=20, pady=(0, 20))

        tk.Button(pie, text="Cerrar sesión",
                  font=("Segoe UI", 10, "bold"),
                  bg="#e74c3c", fg="white",
                  activebackground="#c0392b", activeforeground="white",
                  relief="flat", cursor="hand2", padx=15, pady=6,
                  command=self.cerrar_sesion).pack(side="right")

    def crear_boton(self, parent, texto, icono, color, color_activo, comando):
        frame = tk.Frame(parent, bg="white", bd=0, highlightthickness=1,
                         highlightbackground="#dcdcdc")
        tk.Button(frame, text=f"{icono}\n\n{texto}",
                  font=("Segoe UI", 12, "bold"),
                  bg=color, fg="white",
                  activebackground=color_activo, activeforeground="white",
                  relief="flat", cursor="hand2",
                  width=14, height=6,
                  command=comando).pack(padx=2, pady=2)
        return frame

    def abrir_inventario(self):
        from Inventario import ModuloInventario
        ventana = tk.Toplevel(self.root)
        ModuloInventario(ventana, usuario=self.usuario)

    def abrir_ventas(self):
        from Ventas import ModuloVentas
        ventana = tk.Toplevel(self.root)
        ModuloVentas(ventana, usuario=self.usuario)

    def abrir_clientes(self):
        from Clientes import ModuloClientes
        ventana = tk.Toplevel(self.root)
        ModuloClientes(ventana, usuario=self.usuario)

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión",
                               "¿Está seguro que desea cerrar sesión?"):
            self.root.destroy()
            login_root = tk.Tk()
            LoginBoutique(login_root)
            login_root.mainloop()


# ==================== EJECUCIÓN ====================
# ==================== EJECUCIÓN ====================
def _main_guardian():
    """Guardián global: captura cualquier excepción no controlada (A10)."""
    import traceback
    from tkinter import messagebox
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        root = tk.Tk()
        root.report_callback_exception = _report_callback_exception
        LoginBoutique(root)
        root.mainloop()
    except SystemExit:
        raise
    except Exception as exc:
        logging.getLogger("main").exception("Fallo fatal en la aplicación")
        try:
            messagebox.showerror(
                "Error fatal",
                "La aplicación encontró un error inesperado y debe cerrarse.",
            )
        except Exception:
            # No se puede mostrar el messagebox, solo loguear (S110)
            logging.getLogger("main").exception(
                "No se pudo mostrar el messagebox de error fatal"
            )
        traceback.print_exc()
        raise SystemExit(1) from exc


def _report_callback_exception(exc, val, tb):
    """Callback para excepciones dentro de event handlers de Tkinter."""
    import logging
    logging.getLogger("tkinter").exception(
        "Excepción no controlada en callback de Tkinter",
        exc_info=(exc, val, tb),
    )
    try:
        messagebox.showerror(
            "Error inesperado",
            "Ocurrió un error al procesar la acción.\n"
            "Intente nuevamente. Si persiste, contacte al administrador.",
        )
    except Exception:
        logging.getLogger("tkinter").exception(
            "No se pudo mostrar el messagebox de error en callback de Tkinter"
        )


if __name__ == "__main__":
    _main_guardian()