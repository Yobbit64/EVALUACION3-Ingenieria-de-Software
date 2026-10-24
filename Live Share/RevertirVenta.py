import tkinter as tk
from tkinter import messagebox


class VentanaRevertirVenta(tk.Toplevel):
    """
    Flujo completo de reversión:
      1) Confirmación "¿Está seguro?" (con aviso de reintegro al inventario)
      2) Si acepta → captura del motivo de reversión
      3) Ejecuta callback_revertir(venta, nc, motivo)
    """

    def __init__(self, parent, venta, nc, callback_revertir=None):
        """
        parent: ventana padre (módulo de ventas)
        venta: [Código, Fecha, Cliente, Total, Estado, NC, ...]
        nc: número de Nota de Crédito a generar (ej: "NC-03")
        callback_revertir: función(venta, nc, motivo) a ejecutar al confirmar
        """
        super().__init__(parent)
        self.venta = venta
        self.nc = nc
        self.callback_revertir = callback_revertir

        # ---------- Configuración básica ----------
        self.title("Revertir venta")
        self.geometry("400x240")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.wait_visibility()  # <-- AÑADIR ESTO
        self.grab_set()

        # Centrar respecto al padre
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (400 // 2)
        y = py + (ph // 2) - (240 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text="Revertir venta",
                 font=("Segoe UI", 11, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=15)

        tk.Button(barra, text="✕",
                  font=("Segoe UI", 11, "bold"),
                  bg="#2c3e50", fg="white",
                  activebackground="#e74c3c",
                  activeforeground="white",
                  relief="flat", bd=0, cursor="hand2",
                  padx=12, command=self.cancelar
                  ).pack(side="right", fill="y")

        # ---------- Cuerpo ----------
        cuerpo = tk.Frame(self, bg="white")
        cuerpo.pack(fill="both", expand=True, padx=30, pady=20)

        # Icono + mensaje principal
        fila = tk.Frame(cuerpo, bg="white")
        fila.pack(anchor="w", pady=(5, 10))

        tk.Label(fila, text="↺", font=("Segoe UI", 22, "bold"),
                 bg="white", fg="#e67e22").pack(side="left", padx=(0, 10))

        texto_frame = tk.Frame(fila, bg="white")
        texto_frame.pack(side="left", anchor="w")

        # Texto largo (dos líneas) con el aviso de reintegro
        tk.Label(texto_frame,
                 text="Se revertirá la venta y se",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#2c3e50", anchor="w",
                 justify="left").pack(anchor="w")

        tk.Label(texto_frame,
                 text="reintegrarán las unidades al inventario",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#2c3e50", anchor="w",
                 justify="left").pack(anchor="w")

        cod = venta[0] if venta else ""
        if cod:
            tk.Label(texto_frame, text=f"«{cod}»",
                     font=("Segoe UI", 10, "italic"),
                     bg="white", fg="#7f8c8d",
                     anchor="w").pack(anchor="w", pady=(2, 0))

        tk.Label(cuerpo, text="¿Está seguro?",
                 font=("Segoe UI", 11),
                 bg="white", fg="#34495e",
                 anchor="w").pack(anchor="w", pady=(6, 0))

        # ---------- Botones ----------
        botones = tk.Frame(cuerpo, bg="white")
        botones.pack(side="bottom", anchor="e", pady=(15, 0))

        btn_no = tk.Button(botones, text="No",
                           font=("Segoe UI", 10, "bold"),
                           bg="#95a5a6", fg="white",
                           activebackground="#7f8c8d",
                           activeforeground="white",
                           relief="flat", cursor="hand2",
                           width=8, padx=10, pady=6,
                           command=self.cancelar)
        btn_no.pack(side="left", padx=6)

        btn_si = tk.Button(botones, text="Sí",
                           font=("Segoe UI", 10, "bold"),
                           bg="#e67e22", fg="white",
                           activebackground="#ca6f1e",
                           activeforeground="white",
                           relief="flat", cursor="hand2",
                           width=8, padx=10, pady=6,
                           command=self.paso_si)
        btn_si.pack(side="left", padx=6)

        self.bind("<Escape>", lambda e: self.cancelar())
        self.bind("<Return>", lambda e: self.paso_si())
        btn_no.focus_set()

    # ---------------------------------------------------------------
    def paso_si(self):
        """El usuario confirmó → abrir diálogo de motivo."""
        self.destroy()
        ventana_motivo = VentanaMotivoReversion(
            self.master, self.venta, self.nc, self.callback_revertir
        )
        self.master.wait_window(ventana_motivo)

    def cancelar(self):
        self.destroy()


# ==================== SEGUNDO PASO: MOTIVO ====================
class VentanaMotivoReversion(tk.Toplevel):
    def __init__(self, parent, venta, nc, callback_revertir=None):
        super().__init__(parent)
        self.venta = venta
        self.nc = nc
        self.callback_revertir = callback_revertir

        # ---------- Configuración básica ----------
        self.title("Ingrese motivo de reversión")
        self.geometry("480x240")
        self.resizable(False, False)
        self.configure(bg="white")
        self.wait_visibility()  # <-- AÑADIR ESTO
        self.grab_set()

        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (480 // 2)
        y = py + (ph // 2) - (240 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text="Ingrese motivo de reversión",
                 font=("Segoe UI", 11, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=15)

        tk.Button(barra, text="✕",
                  font=("Segoe UI", 11, "bold"),
                  bg="#2c3e50", fg="white",
                  activebackground="#e74c3c",
                  activeforeground="white",
                  relief="flat", bd=0, cursor="hand2",
                  padx=12, command=self.cancelar
                  ).pack(side="right", fill="y")

        # ---------- Cuerpo ----------
        cuerpo = tk.Frame(self, bg="white")
        cuerpo.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(cuerpo, text="Motivo de reversión:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#34495e",
                 anchor="w").pack(anchor="w", pady=(0, 6))

        self.entry_motivo = tk.Entry(cuerpo, font=("Segoe UI", 10),
                                     relief="solid", bd=1, bg="white")
        self.entry_motivo.pack(fill="x", ipady=5)
        self.entry_motivo.focus_set()
        self.entry_motivo.bind("<Return>", lambda e: self.confirmar())

        # Etiqueta de error (oculta al inicio)
        self.label_error = tk.Label(cuerpo, text="",
                                    font=("Segoe UI", 9, "bold"),
                                    bg="white", fg="#e67e22")
        self.label_error.pack(anchor="w", pady=(4, 0))

        # ---------- Botones ----------
        botones = tk.Frame(cuerpo, bg="white")
        botones.pack(side="bottom", anchor="e", pady=(18, 0))

        tk.Button(botones, text="Cancelar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#95a5a6", fg="white",
                  activebackground="#7f8c8d",
                  activeforeground="white",
                  relief="flat", cursor="hand2",
                  padx=16, pady=6,
                  command=self.cancelar).pack(side="left", padx=6)

        tk.Button(botones, text="Confirmar reversión",
                  font=("Segoe UI", 10, "bold"),
                  bg="#e67e22", fg="white",
                  activebackground="#ca6f1e",
                  activeforeground="white",
                  relief="flat", cursor="hand2",
                  padx=16, pady=6,
                  command=self.confirmar).pack(side="left", padx=6)

        self.bind("<Escape>", lambda e: self.cancelar())

    # ---------------------------------------------------------------
    def confirmar(self):
        motivo = self.entry_motivo.get().strip()

        if not motivo:
            self.label_error.config(
                text="⚠ Debe ingresar un motivo para continuar.")
            self.entry_motivo.focus_set()
            return

        if len(motivo) < 5:
            self.label_error.config(
                text="⚠ El motivo debe tener al menos 5 caracteres.")
            self.entry_motivo.focus_set()
            return

        # Confirmación final
        if not messagebox.askyesno(
            "Confirmar reversión",
            f"¿Confirmar la reversión de la venta {self.venta[0]}?\n\n"
            f"Se generará la Nota de Crédito: {self.nc}\n"
            f"Las unidades volverán al inventario.\n"
            f"Motivo: {motivo}",
            parent=self
        ):
            return

        if self.callback_revertir:
            self.callback_revertir(self.venta, self.nc, motivo)

        messagebox.showinfo(
            "Venta revertida",
            f"✓ Venta {self.venta[0]} revertida correctamente.\n"
            f"Nota de Crédito generada: {self.nc}\n"
            f"Unidades reintegradas al inventario.",
            parent=self
        )
        self.destroy()

    def cancelar(self):
        self.destroy()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Prueba")
    root.geometry("480x320")
    root.configure(bg="#f5f5f5")

    venta_demo = ["V-0003", "13/05/2025", "1100", 49980, "Válida", None]

    def aplicar(v, nc, motivo):
        v[4] = "Revertida"
        v[5] = nc
        print(f"✔ Venta {v[0]} revertida | NC: {nc} | Motivo: {motivo}")

    def abrir():
        VentanaRevertirVenta(root, venta_demo, "NC-04", aplicar)

    tk.Button(root, text="Revertir venta",
              font=("Segoe UI", 10, "bold"),
              bg="#e67e22", fg="white",
              relief="flat", padx=15, pady=8,
              command=abrir).pack(expand=True)

    root.mainloop()