# Live Share/Clientes.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from db import (
    obtener_clientes, eliminar_cliente_db, obtener_cliente_completo,
    insertar_cliente, actualizar_cliente_db, PERMISOS,
)
from errores import manejar_excepcion

logger = logging.getLogger(__name__)


class ModuloClientes:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("Boutique - Clientes")
        self.root.geometry("880x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (880 // 2)
        y = (self.root.winfo_screenheight() // 2) - (540 // 2)
        self.root.geometry(f"+{x}+{y}")

        self.clientes = []
        self.permisos = PERMISOS.get(self.usuario["rol"], {}).get("clientes", [])

        # ---------- Encabezado ----------
        header = tk.Frame(root, bg="#2c3e50", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="CLIENTES", font=("Segoe UI", 13, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=20)

        busqueda_frame = tk.Frame(header, bg="#2c3e50")
        busqueda_frame.pack(side="right", padx=20)

        self.entry_buscar = tk.Entry(busqueda_frame, font=("Segoe UI", 10),
                                     width=20, relief="solid", bd=1)
        self.entry_buscar.pack(side="left", ipady=4)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_cliente())

        tk.Button(busqueda_frame, text="🔍 Buscar cliente",
                  font=("Segoe UI", 9, "bold"),
                  bg="#3498db", fg="white", relief="flat", cursor="hand2",
                  padx=10, pady=4, command=self.buscar_cliente
                  ).pack(side="left", padx=(6, 0))

        # ---------- Tabla ----------
        tabla_frame = tk.Frame(root, bg="#f5f5f5")
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        scroll = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        columnas = ("ID", "Nombre", "A. Paterno", "A. Materno",
                    "RUT", "Teléfono", "Email")
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings",
                                  yscrollcommand=scroll.set, height=12)
        scroll.config(command=self.tabla.yview)

        anchos = {"ID": 70, "Nombre": 100, "A. Paterno": 100, "A. Materno": 100,
                  "RUT": 90, "Teléfono": 100, "Email": 150}
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor="center")

        self.tabla.pack(fill="both", expand=True)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", background="white", foreground="#2c3e50",
                         rowheight=26, fieldbackground="white",
                         font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", background="#34495e",
                         foreground="white", font=("Segoe UI", 10, "bold"))
        estilo.map("Treeview", background=[("selected", "#3498db")])

        # ---------- Botones según rol ----------
        botones_frame = tk.Frame(root, bg="#f5f5f5")
        botones_frame.pack(fill="x", padx=20, pady=(5, 20))

        if "leer" in self.permisos:
            self.crear_boton(botones_frame, "Ver detalle", "#3498db", "#2980b9",
                             self.ver_detalle_cliente).pack(side="left", padx=(0, 8))
        if "crear" in self.permisos:
            self.crear_boton(botones_frame, "Registrar cliente", "#27ae60", "#1e8449",
                             self.registrar_cliente).pack(side="left", padx=8)
        if "actualizar" in self.permisos:
            self.crear_boton(botones_frame, "Actualizar cliente", "#f39c12", "#d68910",
                             self.actualizar_cliente).pack(side="left", padx=8)
        if "eliminar" in self.permisos:
            self.crear_boton(botones_frame, "Eliminar", "#e74c3c", "#c0392b",
                             self.eliminar_cliente).pack(side="left", padx=8)

        self.recargar_desde_db()

    # ---------------- Recarga y helpers ----------------
    def recargar_desde_db(self):
        try:
            self.clientes = obtener_clientes(self.usuario)
            self.cargar_tabla(self.clientes)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="recargar clientes")

    def crear_boton(self, parent, texto, color, color_activo, comando):
        return tk.Button(parent, text=texto, font=("Segoe UI", 10, "bold"),
                         bg=color, fg="white", activebackground=color_activo,
                         activeforeground="white", relief="flat",
                         cursor="hand2", padx=14, pady=7, command=comando)

    def cargar_tabla(self, lista):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for c in lista:
            self.tabla.insert("", "end",
                              values=(c[0], c[1], c[2], c[3], c[4], c[5], c[6]))

    def siguiente_id(self):
        if not self.clientes:
            return "CLI-001"
        max_num = 0
        for c in self.clientes:
            try:
                num = int(str(c[0]).split("-")[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return f"CLI-{max_num + 1:03d}"

    def obtener_seleccionado(self):
        sel = self.tabla.selection()
        if not sel:
            return None
        return self.tabla.item(sel[0], "values")[0]

    # ---------------- Acciones ----------------
    def buscar_cliente(self):
        termino = self.entry_buscar.get().strip().lower()
        if not termino:
            self.cargar_tabla(self.clientes)
            return
        filtrados = [c for c in self.clientes
                     if any(termino in str(campo).lower() for campo in c)]
        self.cargar_tabla(filtrados)
        if not filtrados:
            messagebox.showinfo("Sin resultados", "No se encontraron clientes.",
                                parent=self.root)

    def ver_detalle_cliente(self):
        id_cliente = self.obtener_seleccionado()
        if not id_cliente:
            messagebox.showwarning("Atención", "Seleccione un cliente.",
                                   parent=self.root)
            return

        try:
            doc = obtener_cliente_completo(self.usuario, id_cliente)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="ver detalle cliente")
            return

        if not doc:
            messagebox.showwarning("No encontrado",
                                   "El cliente ya no existe.",
                                   parent=self.root)
            return

        def fmt_fecha(f_str):
            return str(f_str)[:10] if f_str else "—"

        def fmt_bool(valor):
            return "Sí" if valor else "No"

        direc = doc.get("direccion", {}) or {}
        hist = doc.get("historial_compras", {}) or {}
        cons = doc.get("consentimiento_datos", {}) or {}
        cambios = doc.get("historial_cambios", []) or []

        texto_cambios = ""
        for c in cambios:
            texto_cambios += (
                f"  • Fecha: {fmt_fecha(c.get('fecha'))}\n"
                f"    Usuario: {c.get('usuario', '—')}\n"
                f"    Acción: {c.get('accion', '—')}\n"
                f"    Detalle: {c.get('detalle', '—')}\n\n"
            )
        if not texto_cambios:
            texto_cambios = "  No hay registros de cambios.\n"

        monto = hist.get('monto_total', 0) or 0
        try:
            monto_fmt = f"${int(monto):,}".replace(",", ".")
        except (TypeError, ValueError):
            monto_fmt = "$0"

        msg = (
            f"ID: {doc.get('_id', '—')}\n"
            f"Nombre: {doc.get('nombre','')} {doc.get('apellido_paterno','')} "
            f"{doc.get('apellido_materno','')}\n"
            f"RUT: {doc.get('rut','—')} | Teléfono: {doc.get('telefono','—')}\n"
            f"Email: {doc.get('email','—')}\n"
            f"Dirección: {direc.get('calle','—')} {direc.get('numero','')}, "
            f"{direc.get('comuna','')}, {direc.get('ciudad','')}, "
            f"{direc.get('region','')}\n"
            f"F. Nacimiento: {fmt_fecha(doc.get('fecha_nacimiento'))}\n"
            f"F. Registro: {fmt_fecha(doc.get('fecha_registro'))}\n"
            f"F. Actualización: {fmt_fecha(doc.get('fecha_actualizacion'))}\n"
            f"Estado: {str(doc.get('estado','—')).capitalize()}\n\n"
            f"--- HISTORIAL DE COMPRAS ---\n"
            f"Total compras: {hist.get('total_compras', 0)}\n"
            f"Monto total: {monto_fmt}\n"
            f"Última compra: {fmt_fecha(hist.get('ultima_compra'))}\n\n"
            f"--- CONSENTIMIENTO ---\n"
            f"Aceptado: {fmt_bool(cons.get('aceptado'))}\n"
            f"F. Aceptación: {fmt_fecha(cons.get('fecha_aceptacion'))}\n"
            f"Finalidad: {cons.get('finalidad','—')}\n"
            f"Recibir promociones: {fmt_bool(cons.get('puede_recibir_promociones'))}\n\n"
            f"--- AUDITORÍA ---\n"
            f"Usuario creación: {doc.get('usuario_creacion','—')}\n"
            f"Usuario actualización: {doc.get('usuario_actualizacion','—')}\n\n"
            f"--- HISTORIAL DE CAMBIOS ---\n{texto_cambios}"
        )
        messagebox.showinfo("Detalle del Cliente", msg, parent=self.root)

    def registrar_cliente(self):
        from RegistrarCliente import VentanaRegistrarCliente

        def agregar(datos):
            try:
                # Validación positiva (A05)
                if not datos.get("nombre") or not datos.get("apellido_paterno"):
                    raise ValueError("Nombre y apellido paterno son obligatorios.")
                if not datos.get("rut"):
                    raise ValueError("El RUT es obligatorio.")

                datos["_id"] = self.siguiente_id()
                insertar_cliente(self.usuario, datos)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="registrar cliente")

        try:
            VentanaRegistrarCliente(self.root, callback_guardar=agregar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir registrar cliente")

    def actualizar_cliente(self):
        id_cliente = self.obtener_seleccionado()
        if not id_cliente:
            messagebox.showwarning("Atención",
                                   "Seleccione un cliente para actualizar.",
                                   parent=self.root)
            return

        try:
            doc_completo = obtener_cliente_completo(self.usuario, id_cliente)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="obtener cliente para actualizar")
            return

        if not doc_completo:
            messagebox.showwarning("No encontrado",
                                   "El cliente ya no existe.",
                                   parent=self.root)
            return

        def aplicar(id_c, datos):
            try:
                if not datos.get("nombre") or not datos.get("rut"):
                    raise ValueError("Nombre y RUT son obligatorios.")
                actualizar_cliente_db(self.usuario, id_c, datos)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="actualizar cliente")

        try:
            from ActualizarCliente import VentanaActualizarCliente
            VentanaActualizarCliente(self.root, doc_completo, aplicar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir actualizar cliente")

    def eliminar_cliente(self):
        id_cliente = self.obtener_seleccionado()
        if not id_cliente:
            return

        from EliminarCliente import VentanaConfirmarEliminacionCliente
        c_simulado = self.tabla.item(self.tabla.selection()[0], "values")

        def aplicar(_):
            try:
                eliminar_cliente_db(self.usuario, id_cliente)
                self.recargar_desde_db()
                messagebox.showinfo("Eliminado",
                                    "Cliente eliminado correctamente.",
                                    parent=self.root)
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="eliminar cliente")

        try:
            VentanaConfirmarEliminacionCliente(self.root, c_simulado, aplicar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir confirmar eliminar cliente")