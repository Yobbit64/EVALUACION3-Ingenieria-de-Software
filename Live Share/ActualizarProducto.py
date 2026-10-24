import tkinter as tk
from tkinter import messagebox


class VentanaActualizarProducto(tk.Toplevel):
    def __init__(self, parent, lista_productos, callback_actualizar=None):
        """
        parent: ventana padre (inventario)
        lista_productos: referencia a la lista de productos del inventario
                         (listas de: [ID, Nombre, Categoría, Talla, Precio, Stock])
        callback_actualizar: función que se ejecuta al actualizar un producto
                             Recibe (producto_original, producto_actualizado)
        """
        super().__init__(parent)
        self.lista_productos = lista_productos
        self.callback_actualizar = callback_actualizar
        self.producto_actual = None   # producto cargado actualmente

        # ---------- Configuración básica ----------
        self.title("Actualizar producto")
        self.geometry("460x500")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        # Centrar respecto al padre
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (460 // 2)
        y = py + (ph // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título personalizada ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="Actualizar producto",
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

        # ---------- Fila ID + Botón Buscar ----------
        tk.Label(
            cuerpo, text="ID producto:",
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#34495e",
            anchor="w", width=12
        ).grid(row=0, column=0, sticky="w", pady=6)

        id_frame = tk.Frame(cuerpo, bg="white")
        id_frame.grid(row=0, column=1, sticky="ew", pady=6)

        self.e_id = tk.Entry(
            id_frame, font=("Segoe UI", 10),
            relief="solid", bd=1, bg="white", width=15
        )
        self.e_id.pack(side="left", ipady=4)
        self.e_id.bind("<Return>", lambda e: self.buscar_producto())

        tk.Button(
            id_frame,
            text="Buscar",
            font=("Segoe UI", 9, "bold"),
            bg="#3498db", fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief="flat", cursor="hand2",
            padx=12, pady=3,
            command=self.buscar_producto
        ).pack(side="left", padx=(6, 0))

        # ---------- Campos ----------
        self.e_nombre    = self._crear_campo(cuerpo, "Nombre:",    1)
        self.e_categoria = self._crear_campo(cuerpo, "Categoría:", 2)
        self.e_talla     = self._crear_campo(cuerpo, "Talla:",     3)
        self.e_precio    = self._crear_campo(cuerpo, "Precio:",    4)
        self.e_stock     = self._crear_campo(cuerpo, "Stock:",     5)
        self.e_codigo    = self._crear_campo(cuerpo, "Cód. Barras:", 6)

        # ---------- Mensaje de estado (oculto al inicio) ----------
        self.label_mensaje = tk.Label(
            cuerpo,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#e74c3c"
        )
        self.label_mensaje.grid(row=7, column=0, columnspan=2,
                                pady=(18, 5), sticky="w")

        # ---------- Botones ----------
        botones = tk.Frame(cuerpo, bg="white")
        botones.grid(row=8, column=0, columnspan=2, pady=(15, 0))

        tk.Button(
            botones,
            text="Actualizar",
            font=("Segoe UI", 10, "bold"),
            bg="#f39c12",
            fg="white",
            activebackground="#d68910",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=20, pady=6,
            command=self.actualizar
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
            padx=20, pady=6,
            command=self.destroy
        ).pack(side="left", padx=8)

        self.e_id.focus_set()

        # Callback al presionar Enter en cualquier campo
        for entry in (self.e_nombre, self.e_categoria, self.e_talla,
                      self.e_precio, self.e_stock):
            entry.bind("<Return>", lambda e: self.actualizar())

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
    def buscar_producto(self):
        """Busca el producto por ID y carga sus datos en el formulario."""
        id_buscado = self.e_id.get().strip()

        if not id_buscado:
            self._mostrar_mensaje("⚠ Datos no válidos", tipo="error")
            return

        # Buscar en la lista
        producto = None
        for p in self.lista_productos:
            if p[0] == id_buscado:
                producto = p
                break

        if producto is None:
            self._mostrar_mensaje("⚠ Datos no válidos", tipo="error")
            self._limpiar_campos(excepto_id=True)
            self.producto_actual = None
            return

        # Cargar datos en el formulario
        self.producto_actual = producto
        self._limpiar_campos(excepto_id=True)
        self.e_nombre.insert(0, producto[1])
        self.e_categoria.insert(0, producto[2])
        self.e_talla.insert(0, producto[3])
        self.e_precio.insert(0, str(producto[4]))
        self.e_stock.insert(0, str(producto[5]))
        if len(producto) > 6:
            self.e_codigo.insert(0, producto[6]) # NUEVO

        self.label_mensaje.config(text="")
        self.e_nombre.focus_set()

    # ---------------------------------------------------------------
    def actualizar(self):
        """Valida y aplica los cambios al producto cargado."""
        if self.producto_actual is None:
            self._mostrar_mensaje("⚠ Datos no válidos", tipo="error")
            return

        nombre = self.e_nombre.get().strip()
        categoria = self.e_categoria.get().strip()
        talla = self.e_talla.get().strip()
        precio_txt = self.e_precio.get().strip()
        stock_txt = self.e_stock.get().strip()
        codigo_barras = self.e_codigo.get().strip()

        # Validación de campos vacíos
        if not all([nombre, categoria, talla, precio_txt, stock_txt, codigo_barras]):
            self._mostrar_mensaje("⚠ Datos no válidos", tipo="error")
            return

        # Validación de números
        try:
            precio = int(precio_txt)
            stock = int(stock_txt)
            if precio < 0 or stock < 0:
                raise ValueError
        except ValueError:
            self._mostrar_mensaje("⚠ Datos no válidos", tipo="error")
            return

        # Armar producto actualizado (mismo ID)
        producto_actualizado = [
            self.producto_actual[0],  # ID no cambia
            nombre,
            categoria,
            talla,
            precio,
            stock,
            codigo_barras
        ]

        # Notificar al inventario
        if self.callback_actualizar:
            self.callback_actualizar(self.producto_actual, producto_actualizado)

        # Mensaje de éxito
        self._mostrar_mensaje("✓ Producto actualizado correctamente", tipo="exito")

        messagebox.showinfo(
            "Actualización exitosa",
            f"El producto '{nombre}' fue actualizado correctamente.",
            parent=self
        )
        self.destroy()

    # ---------------------------------------------------------------
    def _mostrar_mensaje(self, texto, tipo="error"):
        """Muestra un mensaje en la zona inferior del formulario."""
        if tipo == "exito":
            self.label_mensaje.config(text=texto, fg="#27ae60")
        else:
            self.label_mensaje.config(text=texto, fg="#e74c3c")

    # ---------------------------------------------------------------
    def _limpiar_campos(self, excepto_id=False):
        """Limpia los campos del formulario."""
        if not excepto_id:
            self.e_id.delete(0, tk.END)
        for entry in (self.e_nombre, self.e_categoria, self.e_talla,
                      self.e_precio, self.e_stock):
            entry.delete(0, tk.END)
        self.label_mensaje.config(text="")


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    productos = [
        ["001", "Polera negra",   "Poleras",    "M",  9990,  15],
        ["002", "Jeans azul",     "Pantalones", "32", 19990,  8],
        ["003", "Chaqueta cuero", "Chaquetas",  "L",  39990,  4],
    ]

    def al_actualizar(original, nuevo):
        idx = productos.index(original)
        productos[idx] = nuevo
        print("Actualizado:", nuevo)

    root = tk.Tk()
    root.title("Ventana padre de prueba")
    root.geometry("400x300")
    root.configure(bg="#f5f5f5")

    tk.Button(
        root,
        text="Abrir 'Actualizar producto'",
        font=("Segoe UI", 10, "bold"),
        bg="#3498db", fg="white",
        relief="flat", padx=15, pady=8,
        command=lambda: VentanaActualizarProducto(root, productos, al_actualizar)
    ).pack(expand=True)

    root.mainloop()