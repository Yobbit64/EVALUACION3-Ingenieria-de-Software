import tkinter as tk


class VentanaEmitirComprobante(tk.Toplevel):
    def __init__(self, parent, codigo_venta="", total=0, cliente=""):
        """
        parent: ventana padre (nueva venta)
        codigo_venta: código de la venta (para mostrar en la info)
        total: monto total de la venta
        cliente: ID del cliente asociado
        """
        super().__init__(parent)
        self.codigo_venta = codigo_venta
        self.total = total
        self.cliente = cliente
        self.resultado = None   # "Boleta" / "Factura" / "Comprobante interno" o None

        # ---------- Configuración básica ----------
        self.title("Emitir comprobante")
        self.geometry("360x290")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        # Centrar respecto al padre
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (360 // 2)
        y = py + (ph // 2) - (290 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título personalizada ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="Emitir comprobante",
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

        # Info opcional (código, cliente, total)
        if codigo_venta or total or cliente:
            partes = []
            if codigo_venta:
                partes.append(f"Venta: {codigo_venta}")
            if cliente:
                partes.append(f"Cliente: {cliente}")
            if total:
                total_fmt = f"${total:,}".replace(",", ".")
                partes.append(f"Total: {total_fmt}")

            tk.Label(
                cuerpo,
                text="   •   ".join(partes),
                font=("Segoe UI", 9, "italic"),
                bg="white",
                fg="#7f8c8d"
            ).pack(pady=(0, 12))

        # ---------- Botones de comprobante ----------
        self._crear_boton(cuerpo, "Generar boleta",        "🧾",
                          "#3498db", "#2980b9")
        self._crear_boton(cuerpo, "Emitir factura",        "📄",
                          "#9b59b6", "#7d3c98")
        self._crear_boton(cuerpo, "Comprobante interno",   "🧮",
                          "#27ae60", "#1e8449")

        self.bind("<Escape>", lambda e: self.cancelar())

    # ---------------------------------------------------------------
    def _crear_boton(self, parent, texto, icono, color, color_activo):
        """Crea un botón ancho con icono + texto para cada tipo."""
        btn = tk.Button(
            parent,
            text=f"{icono}   {texto}",
            font=("Segoe UI", 11, "bold"),
            bg=color,
            fg="white",
            activebackground=color_activo,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            anchor="w",
            padx=14,
            pady=10,
            command=lambda t=texto: self.seleccionar(t)
        )
        btn.pack(fill="x", pady=6)
        return btn

    # ---------------------------------------------------------------
    def seleccionar(self, tipo):
        """Guarda la selección y cierra la ventana."""
        self.resultado = tipo
        self.destroy()

    # ---------------------------------------------------------------
    def cancelar(self):
        self.resultado = None
        self.destroy()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Prueba")
    root.geometry("420x300")
    root.configure(bg="#f5f5f5")

    def abrir():
        v = VentanaEmitirComprobante(root, "V-0004", 39970, "1042")
        root.wait_window(v)
        print("Comprobante elegido:", v.resultado)

    tk.Button(
        root, text="Abrir 'Emitir comprobante'",
        font=("Segoe UI", 10, "bold"),
        bg="#3498db", fg="white",
        relief="flat", padx=15, pady=8,
        command=abrir
    ).pack(expand=True)

    root.mainloop()