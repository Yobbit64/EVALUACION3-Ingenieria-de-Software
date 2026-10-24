import tkinter as tk
from tkinter import messagebox


class VentanaIngresarProducto(tk.Toplevel):
    def __init__(self, parent, callback_guardar=None):
        """
        parent: ventana padre (inventario)
        callback_guardar: función que recibe el diccionario del producto
                          cuando se presiona Aceptar.
        """
        super().__init__(parent)
        self.callback_guardar = callback_guardar

        # ---------- Configuración básica ----------
        self.title("Ingresar producto")
        self.geometry("440x480")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        # Centrar respecto al padre
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (440 // 2)
        y = py + (ph // 2) - (480 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título personalizada ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="Ingresar producto",
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
        cuerpo.pack(fill="both", expand=True, padx=25, pady=20)

        # Campos del formulario
        self.e_nombre    = self._crear_campo(cuerpo, "Nombre:",      0)
        self.e_categoria = self._crear_campo(cuerpo, "Categoría:",   1)
        self.e_talla     = self._crear_campo(cuerpo, "Talla:",       2)
        self.e_precio    = self._crear_campo(cuerpo, "Precio:",      3)
        self.e_stock     = self._crear_campo(cuerpo, "Stock:",       4)
        self.e_codigo    = self._crear_campo(cuerpo, "Cód. Barras:", 5)

        # ---------- Mensaje de éxito (oculto al inicio) ----------
        self.label_exito = tk.Label(
            cuerpo,
            text="✓ Producto ingresado exitosamente",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#27ae60"
        )
        self.label_exito.grid(row=6, column=0, columnspan=2,
                              pady=(18, 5), sticky="w")

        # ---------- Botones ----------
        botones = tk.Frame(cuerpo, bg="white")
        botones.grid(row=7, column=0, columnspan=2, pady=(15, 0))

        tk.Button(
            botones,
            text="Aceptar",
            font=("Segoe UI", 10, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#1e8449",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=22,
            pady=6,
            command=self.aceptar
        ).pack(side="left", padx=8)

        tk.Button(
            botones,
            text="Cerrar",
            font=("Segoe UI", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=22,
            pady=6,
            command=self.destroy
        ).pack(side="left", padx=8)

        # Enfocar el primer campo
        self.e_nombre.focus_set()

    # ---------------------------------------------------------------
    def _crear_campo(self, parent, etiqueta, fila):
        """Crea una fila (etiqueta + entry) alineada."""
        tk.Label(
            parent,
            text=etiqueta,
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#34495e",
            anchor="w",
            width=12
        ).grid(row=fila, column=0, sticky="w", pady=6)

        entry = tk.Entry(
            parent,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            bg="white",
            width=25
        )
        entry.grid(row=fila, column=1, sticky="ew", ipady=4, pady=6)
        parent.grid_columnconfigure(1, weight=1)
        return entry

    # ---------------------------------------------------------------
    def aceptar(self):
        # Ya no leemos self.e_id porque no existe
        nombre = self.e_nombre.get().strip()
        categoria = self.e_categoria.get().strip()
        talla = self.e_talla.get().strip()
        precio_txt = self.e_precio.get().strip()
        stock_txt = self.e_stock.get().strip()
        codigo_barras = self.e_codigo.get().strip()

        if not all([nombre, categoria, talla, precio_txt, stock_txt, codigo_barras]):
            messagebox.showwarning("Campos incompletos", "Por favor complete todos los campos.", parent=self)
            return

        try:
            precio = int(precio_txt)
            stock = int(stock_txt)
            if precio < 0 or stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Datos inválidos", "Precio y Stock deben ser números enteros positivos.", parent=self)
            return

        # Armamos el diccionario SIN el ID (el inventario se lo asignará)
        producto = {
            "nombre": nombre,
            "categoria": categoria,
            "talla": talla,
            "precio": precio,
            "stock": stock,
            "codigo_barras": codigo_barras
        }

        # Notificar al padre
        if self.callback_guardar:
            self.callback_guardar(producto)
        
        # ... resto de la lógica de mensajes ...
    # ---------------------------------------------------------------
    def _limpiar(self):
        """Limpia todos los campos y devuelve el foco al primero."""
        for entry in (self.e_nombre, self.e_categoria, self.e_talla,
                      self.e_precio, self.e_stock, self.e_codigo):
            entry.delete(0, tk.END)
        self.label_exito.config(text="")
        self.e_nombre.focus_set()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    def guardar(producto):
        print("Producto recibido:", producto)

    root = tk.Tk()
    root.title("Ventana padre de prueba")
    root.geometry("400x300")
    root.configure(bg="#f5f5f5")

    tk.Button(
        root,
        text="Abrir 'Ingresar producto'",
        font=("Segoe UI", 10, "bold"),
        bg="#3498db", fg="white",
        relief="flat", padx=15, pady=8,
        command=lambda: VentanaIngresarProducto(root, guardar)
    ).pack(expand=True)

    root.mainloop()