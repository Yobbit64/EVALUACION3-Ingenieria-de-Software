import tkinter as tk


class VentanaConfirmarEliminacion(tk.Toplevel):
    def __init__(self, parent, producto, callback_eliminar=None):
        """
        parent: ventana padre (inventario)
        producto: lista [ID, Nombre, Categoría, Talla, Precio, Stock]
                  del producto a eliminar.
        callback_eliminar: función a ejecutar si el usuario confirma.
                           Recibe el producto eliminado.
        """
        super().__init__(parent)
        self.producto = producto
        self.callback_eliminar = callback_eliminar
        self.resultado = False  # por si se quiere consultar tras cerrar

        # ---------- Configuración básica ----------
        self.title("Confirmar eliminación")
        self.geometry("380x210")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        # Centrar respecto al padre
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (380 // 2)
        y = py + (ph // 2) - (210 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título personalizada ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="Confirmar eliminación",
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
            command=self.destroy
        ).pack(side="right", fill="y")

        # ---------- Cuerpo ----------
        cuerpo = tk.Frame(self, bg="white")
        cuerpo.pack(fill="both", expand=True, padx=30, pady=20)

        # Icono de advertencia
        icono_frame = tk.Frame(cuerpo, bg="white")
        icono_frame.pack(anchor="w", pady=(0, 8))

        tk.Label(
            icono_frame,
            text="⚠",
            font=("Segoe UI", 22, "bold"),
            bg="white",
            fg="#e74c3c"
        ).pack(side="left", padx=(0, 10))

        texto_frame = tk.Frame(icono_frame, bg="white")
        texto_frame.pack(side="left", anchor="w")

        tk.Label(
            texto_frame,
            text="Se eliminará el producto",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2c3e50",
            anchor="w"
        ).pack(anchor="w")

        # Mostrar nombre del producto (si viene en la lista)
        nombre = producto[1] if len(producto) > 1 else ""
        if nombre:
            tk.Label(
                texto_frame,
                text=f"«{nombre}»",
                font=("Segoe UI", 10, "italic"),
                bg="white",
                fg="#7f8c8d",
                anchor="w"
            ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            cuerpo,
            text="¿Está seguro?",
            font=("Segoe UI", 11),
            bg="white",
            fg="#34495e",
            anchor="w"
        ).pack(anchor="w", pady=(6, 0))

        # ---------- Botones ----------
        botones = tk.Frame(cuerpo, bg="white")
        botones.pack(side="bottom", anchor="e", pady=(15, 0))

        # Botón "No" (acción por defecto / focus)
        btn_no = tk.Button(
            botones,
            text="No",
            font=("Segoe UI", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=8,
            padx=10, pady=6,
            command=self.cancelar
        )
        btn_no.pack(side="left", padx=6)

        # Botón "Sí"
        btn_si = tk.Button(
            botones,
            text="Sí",
            font=("Segoe UI", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=8,
            padx=10, pady=6,
            command=self.confirmar
        )
        btn_si.pack(side="left", padx=6)

        # Atajos de teclado
        self.bind("<Escape>", lambda e: self.cancelar())
        self.bind("<Return>", lambda e: self.confirmar())

        # Foco inicial en "No" (más seguro)
        btn_no.focus_set()

    # ---------------------------------------------------------------
    def confirmar(self):
        """El usuario confirmó la eliminación."""
        self.resultado = True
        if self.callback_eliminar:
            self.callback_eliminar(self.producto)
        self.destroy()

    # ---------------------------------------------------------------
    def cancelar(self):
        """El usuario canceló la eliminación."""
        self.resultado = False
        self.destroy()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    productos = [
        ["001", "Polera negra",   "Poleras",    "M",  9990,  15],
        ["002", "Jeans azul",     "Pantalones", "32", 19990,  8],
        ["003", "Chaqueta cuero", "Chaquetas",  "L",  39990,  4],
    ]

    def al_eliminar(producto):
        productos.remove(producto)
        print("Eliminado:", producto)
        print("Quedan:", productos)

    root = tk.Tk()
    root.title("Ventana padre de prueba")
    root.geometry("420x320")
    root.configure(bg="#f5f5f5")

    tk.Label(
        root,
        text="Producto de prueba a eliminar:\n"
             "001 - Polera negra",
        font=("Segoe UI", 10),
        bg="#f5f5f5", fg="#34495e"
    ).pack(pady=20)

    tk.Button(
        root,
        text="Eliminar producto",
        font=("Segoe UI", 10, "bold"),
        bg="#e74c3c", fg="white",
        activebackground="#c0392b",
        relief="flat", padx=15, pady=8,
        command=lambda: VentanaConfirmarEliminacion(
            root, productos[0], al_eliminar
        )
    ).pack()

    root.mainloop()