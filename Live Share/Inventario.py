# Live Share/Inventario.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from db import (
    obtener_productos, insertar_producto, actualizar_producto,
    eliminar_producto, PERMISOS,
)
from errores import manejar_excepcion

logger = logging.getLogger(__name__)


class ModuloInventario:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("Boutique - Inventario")
        self.root.geometry("820x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (820 // 2)
        y = (self.root.winfo_screenheight() // 2) - (540 // 2)
        self.root.geometry(f"+{x}+{y}")

        self.productos = []
        self.permisos = PERMISOS.get(self.usuario["rol"], {}).get("inventario", [])

        # ---------- Encabezado ----------
        header = tk.Frame(root, bg="#2c3e50", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="INVENTARIO",
            font=("Segoe UI", 13, "bold"),
            bg="#2c3e50", fg="white"
        ).pack(side="left", padx=20)

        busqueda_frame = tk.Frame(header, bg="#2c3e50")
        busqueda_frame.pack(side="right", padx=20)

        self.entry_buscar = tk.Entry(
            busqueda_frame, font=("Segoe UI", 10),
            width=20, relief="solid", bd=1
        )
        self.entry_buscar.pack(side="left", ipady=4)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_producto())

        tk.Button(
            busqueda_frame, text="🔍 Buscar producto",
            font=("Segoe UI", 9, "bold"),
            bg="#3498db", fg="white",
            activebackground="#2980b9", activeforeground="white",
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self.buscar_producto
        ).pack(side="left", padx=(6, 0))

        # ---------- Filtro por categoría ----------
        filtro_frame = tk.Frame(root, bg="#f5f5f5")
        filtro_frame.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(
            filtro_frame, text="Filtrar por categoría:",
            font=("Segoe UI", 10, "bold"),
            bg="#f5f5f5", fg="#34495e"
        ).pack(side="left")

        self.categorias = ["Todas las categorías", "Poleras", "Pantalones", "Chaquetas"]
        self.combo_categoria = ttk.Combobox(
            filtro_frame, values=self.categorias,
            state="readonly", font=("Segoe UI", 10), width=22
        )
        self.combo_categoria.current(0)
        self.combo_categoria.pack(side="left", padx=10)
        self.combo_categoria.bind("<<ComboboxSelected>>",
                                  lambda e: self.filtrar_por_categoria())

        # ---------- Tabla ----------
        tabla_frame = tk.Frame(root, bg="#f5f5f5")
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)

        scroll = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        columnas = ("ID", "Nombre", "Categoría", "Talla", "Precio", "Stock", "Cód. Barras")
        self.tabla = ttk.Treeview(
            tabla_frame, columns=columnas, show="headings",
            yscrollcommand=scroll.set, height=12
        )
        scroll.config(command=self.tabla.yview)

        anchos = {"ID": 70, "Nombre": 170, "Categoría": 100,
                  "Talla": 50, "Precio": 80, "Stock": 60, "Cód. Barras": 110}
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor="center")

        self.tabla.pack(fill="both", expand=True)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            background="white", foreground="#2c3e50",
            rowheight=26, fieldbackground="white",
            font=("Segoe UI", 10)
        )
        estilo.configure(
            "Treeview.Heading",
            background="#34495e", foreground="white",
            font=("Segoe UI", 10, "bold")
        )
        estilo.map("Treeview", background=[("selected", "#3498db")])

        # ---------- Botones de acción ----------
        botones_frame = tk.Frame(root, bg="#f5f5f5")
        botones_frame.pack(fill="x", padx=20, pady=(5, 20))

        if "crear" in self.permisos:
            self.crear_boton_accion(
                botones_frame, "Ingresar producto", "#27ae60", "#1e8449",
                self.ingresar_producto
            ).pack(side="left", padx=(0, 8))

        if "actualizar" in self.permisos:
            self.crear_boton_accion(
                botones_frame, "Actualizar producto", "#f39c12", "#d68910",
                self.actualizar_producto
            ).pack(side="left", padx=8)

        if "eliminar" in self.permisos:
            self.crear_boton_accion(
                botones_frame, "Eliminar", "#e74c3c", "#c0392b",
                self.eliminar_producto
            ).pack(side="left", padx=8)

        self.recargar_desde_db()

    # ---------------- Recarga y helpers ----------------
    def recargar_desde_db(self):
        try:
            self.productos = obtener_productos(self.usuario)
            self.cargar_tabla(self.productos)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="recargar inventario")

    def crear_boton_accion(self, parent, texto, color, color_activo, comando):
        return tk.Button(
            parent, text=texto,
            font=("Segoe UI", 10, "bold"),
            bg=color, fg="white",
            activebackground=color_activo, activeforeground="white",
            relief="flat", cursor="hand2", padx=14, pady=7,
            command=comando
        )

    def cargar_tabla(self, lista):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for prod in lista:
            try:
                precio_fmt = f"${int(prod[4]):,}".replace(",", ".")
            except (TypeError, ValueError):
                precio_fmt = "$0"
            self.tabla.insert(
                "", "end",
                values=(prod[0], prod[1], prod[2], prod[3],
                        precio_fmt, prod[5], prod[6])
            )

    def formatear_precio(self, valor):
        try:
            return f"${int(valor):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "$0"

    # ---------------- Acciones ----------------
    def buscar_producto(self):
        termino = self.entry_buscar.get().strip().lower()
        if not termino:
            self.cargar_tabla(self.productos)
            return
        filtrados = [
            p for p in self.productos
            if termino in str(p[1]).lower() or termino in str(p[0]).lower()
        ]
        self.cargar_tabla(filtrados)
        if not filtrados:
            messagebox.showinfo("Sin resultados",
                                "No se encontraron productos con ese criterio.",
                                parent=self.root)

    def filtrar_por_categoria(self):
        cat = self.combo_categoria.get()
        if cat == "Todas las categorías":
            self.cargar_tabla(self.productos)
        else:
            filtrados = [p for p in self.productos if p[2] == cat]
            self.cargar_tabla(filtrados)

    def ingresar_producto(self):
        from IngresarProducto import VentanaIngresarProducto

        def agregar(producto):
            try:
                # Validación positiva (A05)
                if not producto.get("nombre") or not producto.get("categoria"):
                    raise ValueError("Nombre y categoría son obligatorios.")
                if int(producto["precio"]) < 0 or int(producto["stock"]) < 0:
                    raise ValueError("Precio y stock deben ser positivos.")

                nuevo_id = self.siguiente_id()
                lista = [
                    nuevo_id,
                    producto["nombre"], producto["categoria"], producto["talla"],
                    producto["precio"], producto["stock"], producto["codigo_barras"],
                ]
                insertar_producto(self.usuario, lista)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="ingresar producto")

        try:
            VentanaIngresarProducto(self.root, callback_guardar=agregar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir ventana ingresar producto")

    def actualizar_producto(self):
        from ActualizarProducto import VentanaActualizarProducto

        def aplicar(original, nuevo):
            try:
                if int(nuevo[4]) < 0 or int(nuevo[5]) < 0:
                    raise ValueError("Precio y stock deben ser positivos.")
                actualizar_producto(self.usuario, original[0], nuevo)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="actualizar producto")

        try:
            ventana = VentanaActualizarProducto(
                self.root, self.productos, callback_actualizar=aplicar
            )
            sel = self.tabla.selection()
            if sel:
                id_sel = self.tabla.item(sel[0], "values")[0]
                ventana.e_id.insert(0, id_sel)
                ventana.buscar_producto()
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir ventana actualizar producto")

    def eliminar_producto(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención",
                                   "Seleccione un producto para eliminar.",
                                   parent=self.root)
            return

        valores = self.tabla.item(sel[0], "values")
        id_producto = valores[0]

        from EliminarProducto import VentanaConfirmarEliminacion

        def aplicar(producto_a_eliminar):
            try:
                eliminar_producto(self.usuario, id_producto)
                self.recargar_desde_db()
                messagebox.showinfo(
                    "Eliminado",
                    f"El producto '{producto_a_eliminar[1]}' fue eliminado.",
                    parent=self.root
                )
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="eliminar producto")

        producto = self.buscar_por_id(id_producto)
        if not producto:
            messagebox.showwarning("No encontrado",
                                   "El producto ya no existe.",
                                   parent=self.root)
            return

        try:
            VentanaConfirmarEliminacion(self.root, producto,
                                        callback_eliminar=aplicar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir confirmar eliminación")

    def buscar_por_id(self, id_prod):
        for p in self.productos:
            if p[0] == id_prod:
                return p
        return None

    def siguiente_id(self):
        if not self.productos:
            return "PROD-001"
        max_num = 0
        for p in self.productos:
            try:
                num = int(p[0].split("-")[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return f"PROD-{max_num + 1:03d}"