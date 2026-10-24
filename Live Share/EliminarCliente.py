import tkinter as tk


class VentanaConfirmarEliminacionCliente(tk.Toplevel):
    def __init__(self, parent, cliente, callback_eliminar=None):
        """
        parent: ventana padre (módulo de clientes)
        cliente: lista [ID, Nombre, Apellido, Teléfono, Email, Dirección]
        callback_eliminar: función(cliente) al confirmar
        """
        super().__init__(parent)
        self.cliente = cliente
        self.callback_eliminar = callback_eliminar
        self.resultado = False

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

        # Icono + mensaje
        fila = tk.Frame(cuerpo, bg="white")
        fila.pack(anchor="w", pady=(0, 8))

        tk.Label(
            fila,
            text="⚠",
            font=("Segoe UI", 22, "bold"),
            bg="white",
            fg="#e74c3c"
        ).pack(side="left", padx=(0, 10))

        texto_frame = tk.Frame(fila, bg="white")
        texto_frame.pack(side="left", anchor="w")

        tk.Label(
            texto_frame,
            text="Se eliminará el cliente",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2c3e50",
            anchor="w"
        ).pack(anchor="w")

        # Nombre completo del cliente
        nombre_completo = f"{cliente[1]} {cliente[2]}" if len(cliente) > 2 else ""
        if nombre_completo.strip():
            tk.Label(
                texto_frame,
                text=f"«{nombre_completo}»",
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

        tk.Button(
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
        ).pack(side="left", padx=6)

        # Atajos
        self.bind("<Escape>", lambda e: self.cancelar())
        self.bind("<Return>", lambda e: self.confirmar())
        btn_no.focus_set()

    # ---------------------------------------------------------------
    def confirmar(self):
        self.resultado = True
        if self.callback_eliminar:
            self.callback_eliminar(self.cliente)
        self.destroy()

    # ---------------------------------------------------------------
    def cancelar(self):
        self.resultado = False
        self.destroy()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    clientes = [
        ["1042", "María", "Pérez", "912345678", "m@p.cl", "Av. Providencia 123"],
        ["1088", "Juan",  "Soto",  "998765432", "j@s.cl", "Los Leones 456"],
    ]

    def al_eliminar(c):
        clientes.remove(c)
        print("Eliminado:", c)
        print("Quedan:", clientes)

    root = tk.Tk()
    root.title("Prueba")
    root.geometry("440x320")
    root.configure(bg="#f5f5f5")

    tk.Label(
        root,
        text="Cliente de prueba a eliminar:\n1042 - María Pérez",
        font=("Segoe UI", 10),
        bg="#f5f5f5", fg="#34495e"
    ).pack(pady=20)

    tk.Button(
        root,
        text="Eliminar cliente",
        font=("Segoe UI", 10, "bold"),
        bg="#e74c3c", fg="white",
        activebackground="#c0392b",
        relief="flat", padx=15, pady=8,
        command=lambda: VentanaConfirmarEliminacionCliente(
            root, clientes[0], al_eliminar
        )
    ).pack()

    root.mainloop()