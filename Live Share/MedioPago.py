import tkinter as tk


class VentanaMedioPago(tk.Toplevel):
    def __init__(self, parent, codigo_venta="", total=0):
        """
        parent: ventana padre (nueva venta)
        codigo_venta: código de la venta en curso (para mostrar en el título)
        total: monto total a pagar (para mostrar en la parte inferior)
        """
        super().__init__(parent)
        self.resultado = None   # "Débito" / "Crédito" / "Efectivo" o None

        # ---------- Configuración básica ----------
        self.title("Seleccionar medio de pago")
        self.geometry("340x270")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        # Centrar respecto al padre
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (340 // 2)
        y = py + (ph // 2) - (270 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título personalizada ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="Seleccionar medio de pago",
            font=("Segoe UI", 11, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(side="left", padx=15)

        tk.Button(
            barra,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            bg="#2c3e50",
            fg="white",
            activebackground="#e74c3c",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            command=self.cancelar
        ).pack(side="right", fill="y")

        # ---------- Cuerpo ----------
        cuerpo = tk.Frame(self, bg="white")
        cuerpo.pack(fill="both", expand=True, padx=25, pady=20)

        # Info (código + total) si se proporcionan
        if codigo_venta or total:
            info = f"Venta: {codigo_venta}" if codigo_venta else ""
            if total:
                info += f"   •   Total: ${total:,}".replace(",", ".")
            tk.Label(
                cuerpo,
                text=info.strip(),
                font=("Segoe UI", 9, "italic"),
                bg="white",
                fg="#7f8c8d"
            ).pack(pady=(0, 12))

        # ---------- Botones de medios de pago ----------
        self._crear_boton(cuerpo, "Débito",   "#3498db", "#2980b9")
        self._crear_boton(cuerpo, "Crédito",  "#9b59b6", "#7d3c98")
        self._crear_boton(cuerpo, "Efectivo", "#27ae60", "#1e8449")

        # Atajos de teclado
        self.bind("<Escape>", lambda e: self.cancelar())

    # ---------------------------------------------------------------
    def _crear_boton(self, parent, texto, color, color_activo):
        """Crea un botón ancho para cada medio de pago."""
        btn = tk.Button(
            parent,
            text=texto,
            font=("Segoe UI", 11, "bold"),
            bg=color,
            fg="white",
            activebackground=color_activo,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            pady=10,
            command=lambda t=texto: self.seleccionar(t)
        )
        btn.pack(fill="x", pady=6)
        return btn

    # ---------------------------------------------------------------
    def seleccionar(self, medio):
        """Guarda la selección y cierra la ventana."""
        self.resultado = medio
        self.destroy()

    # ---------------------------------------------------------------
    def cancelar(self):
        """Cierra sin seleccionar medio de pago."""
        self.resultado = None
        self.destroy()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Prueba")
    root.geometry("400x300")
    root.configure(bg="#f5f5f5")

    def abrir():
        v = VentanaMedioPago(root, "V-0004", 39970)
        root.wait_window(v)
        print("Medio elegido:", v.resultado)

    tk.Button(
        root, text="Abrir 'Seleccionar medio de pago'",
        font=("Segoe UI", 10, "bold"),
        bg="#3498db", fg="white",
        relief="flat", padx=15, pady=8,
        command=abrir
    ).pack(expand=True)

    root.mainloop()