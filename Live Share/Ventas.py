# Live Share/Ventas.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from db import (
    obtener_ventas, siguiente_id_venta, siguiente_folio_comprobante,
    obtener_venta_completa, obtener_productos, insertar_venta,
    anular_venta_db, revertir_venta_db, siguiente_nota_credito,
    PERMISOS,
)
from errores import manejar_excepcion

logger = logging.getLogger(__name__)


class ModuloVentas:
    def __init__(self, root, usuario):
        self.root = root
        self.usuario = usuario
        self.root.title("Boutique - Ventas")
        self.root.geometry("880x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (880 // 2)
        y = (self.root.winfo_screenheight() // 2) - (540 // 2)
        self.root.geometry(f"+{x}+{y}")

        self.ventas = []
        self.permisos = PERMISOS.get(self.usuario["rol"], {}).get("ventas", [])

        # ---------- Encabezado ----------
        header = tk.Frame(root, bg="#2c3e50", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="VENTAS", font=("Segoe UI", 13, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=20)

        busqueda_frame = tk.Frame(header, bg="#2c3e50")
        busqueda_frame.pack(side="right", padx=20)

        self.entry_buscar = tk.Entry(busqueda_frame, font=("Segoe UI", 10),
                                     width=20, relief="solid", bd=1)
        self.entry_buscar.pack(side="left", ipady=4)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_venta())

        tk.Button(busqueda_frame, text="🔍 Buscar venta",
                  font=("Segoe UI", 9, "bold"),
                  bg="#3498db", fg="white", relief="flat", cursor="hand2",
                  padx=10, pady=4, command=self.buscar_venta
                  ).pack(side="left", padx=(6, 0))

        # ---------- Tabla ----------
        tabla_frame = tk.Frame(root, bg="#f5f5f5")
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        scroll = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        columnas = ("Código", "Fecha", "Cliente", "Total", "Estado")
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings",
                                  yscrollcommand=scroll.set, height=12)
        scroll.config(command=self.tabla.yview)

        anchos = {"Código": 90, "Fecha": 120, "Cliente": 180,
                  "Total": 120, "Estado": 150}
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

        self.tabla.tag_configure("valida", foreground="#27ae60")
        self.tabla.tag_configure("anulada", foreground="#e74c3c")
        self.tabla.tag_configure("revertida", foreground="#e67e22")

        self.tabla.bind("<Double-1>", lambda e: self.ver_detalle_venta())

        # ---------- Botones según rol ----------
        botones_frame = tk.Frame(root, bg="#f5f5f5")
        botones_frame.pack(fill="x", padx=20, pady=(5, 20))

        if "crear" in self.permisos:
            self.crear_boton_accion(botones_frame, "Nueva venta",
                                    "#27ae60", "#1e8449",
                                    self.nueva_venta).pack(side="left", padx=(0, 8))
        if "anular" in self.permisos:
            self.crear_boton_accion(botones_frame, "Anular venta",
                                    "#e74c3c", "#c0392b",
                                    self.anular_venta).pack(side="left", padx=8)
        if "revertir" in self.permisos:
            self.crear_boton_accion(botones_frame, "Revertir venta",
                                    "#e67e22", "#ca6f1e",
                                    self.revertir_venta).pack(side="left", padx=8)

        self.recargar_desde_db()

    # ---------------- Recarga y helpers ----------------
    def recargar_desde_db(self):
        try:
            self.ventas = obtener_ventas(self.usuario)
            self.cargar_tabla(self.ventas)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="recargar ventas")

    def crear_boton_accion(self, parent, texto, color, color_activo, comando):
        return tk.Button(parent, text=texto, font=("Segoe UI", 10, "bold"),
                         bg=color, fg="white", activebackground=color_activo,
                         activeforeground="white", relief="flat",
                         cursor="hand2", padx=14, pady=7, command=comando)

    def cargar_tabla(self, lista):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for v in lista:
            codigo, fecha, cliente, total, estado = v
            try:
                total_fmt = f"${int(total):,}".replace(",", ".")
            except (TypeError, ValueError):
                total_fmt = "$0"
            tag = "valida"
            if estado == "Anulada":
                tag = "anulada"
            elif estado == "Revertida":
                tag = "revertida"
            self.tabla.insert("", "end",
                              values=(codigo, fecha, cliente, total_fmt, estado),
                              tags=(tag,))

    def formatear_precio(self, valor):
        try:
            return f"${int(valor):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "$0"

    def obtener_seleccionada(self):
        sel = self.tabla.selection()
        if not sel:
            return None
        return self.tabla.item(sel[0], "values")[0]

    # ---------------- Acciones ----------------
    def buscar_venta(self):
        termino = self.entry_buscar.get().strip().lower()
        if not termino:
            self.cargar_tabla(self.ventas)
            return
        filtradas = [v for v in self.ventas
                     if any(termino in str(campo).lower() for campo in v)]
        self.cargar_tabla(filtradas)
        if not filtradas:
            messagebox.showinfo("Sin resultados",
                                "No se encontraron ventas.",
                                parent=self.root)

    def nueva_venta(self):
        from NuevaVenta import VentanaNuevaVenta

        def agregar(datos_venta):
            try:
                if not datos_venta.get("productos"):
                    raise ValueError("La venta no tiene productos.")
                if datos_venta.get("total", 0) <= 0:
                    raise ValueError("El total debe ser mayor a 0.")

                datos_venta["_id"] = siguiente_id_venta()
                datos_venta["folio"] = siguiente_folio_comprobante()
                insertar_venta(self.usuario, datos_venta)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="nueva venta")

        try:
            catalogo = obtener_productos(self.usuario)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="cargar catálogo nueva venta")
            return

        cliente_demo = {
            "id_cliente": "CLI-001",
            "nombre": "María",
            "apellido": "González",
        }

        try:
            VentanaNuevaVenta(
                self.root,
                catalogo=catalogo,
                cliente_dict=cliente_demo,
                callback_guardar=agregar,
                usuario=self.usuario,
            )
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir nueva venta")

    def ver_detalle_venta(self):
        id_venta = self.obtener_seleccionada()
        if not id_venta:
            return

        try:
            doc = obtener_venta_completa(self.usuario, id_venta)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="ver detalle venta")
            return

        if not doc:
            messagebox.showwarning("No encontrada",
                                   "La venta ya no existe.",
                                   parent=self.root)
            return

        fecha_venta = str(doc.get('fecha_venta', ''))[:16].replace('T', ' ')
        cli = doc.get('cliente', {}) or {}
        comp = doc.get('comprobante', {}) or {}

        try:
            total_fmt = f"${int(doc.get('total', 0)):,}".replace(",", ".")
        except (TypeError, ValueError):
            total_fmt = "$0"

        msg = (
            f"ID Venta: {doc.get('_id')}\n"
            f"Fecha: {fecha_venta}\n"
            f"Empleado: {doc.get('empleado','—')}\n"
            f"Cliente: {cli.get('nombre','')} {cli.get('apellido','')}\n"
            f"Total: {total_fmt}\n"
            f"Pago: {str(doc.get('metodo_pago','')).capitalize()} "
            f"({doc.get('estado_pago','')})\n"
            f"Comprobante: {str(comp.get('tipo','')).capitalize()} - "
            f"{comp.get('folio','')}\n\n"
            f"--- PRODUCTOS ---\n"
        )
        for p in doc.get("productos", []) or []:
            try:
                sub_fmt = f"${int(p.get('subtotal', 0)):,}".replace(",", ".")
            except (TypeError, ValueError):
                sub_fmt = "$0"
            msg += f"- {p.get('cantidad', 0)}x {p.get('nombre', '—')} ({sub_fmt})\n"

        messagebox.showinfo("Detalle de venta", msg, parent=self.root)

    def anular_venta(self):
        id_venta = self.obtener_seleccionada()
        if not id_venta:
            messagebox.showwarning("Atención",
                                   "Seleccione una venta para anular.",
                                   parent=self.root)
            return

        try:
            doc = obtener_venta_completa(self.usuario, id_venta)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="obtener venta para anular")
            return

        if not doc:
            messagebox.showwarning("No encontrada",
                                   "La venta ya no existe.",
                                   parent=self.root)
            return
        if doc.get("estado") != "Válida":
            messagebox.showwarning("No permitido",
                                   "Solo se pueden anular ventas válidas.",
                                   parent=self.root)
            return

        from AnularVenta import VentanaAnularVenta

        def aplicar(v, nc, motivo):
            try:
                anular_venta_db(self.usuario, id_venta, motivo, nc)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="anular venta")

        venta_formato_lista = [
            doc["_id"], doc["fecha_venta"],
            doc["cliente"]["id_cliente"], doc["total"],
            doc["estado"], None,
        ]
        try:
            nc_simulado = siguiente_nota_credito()
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="generar NC")
            return

        try:
            VentanaAnularVenta(self.root, venta_formato_lista, nc_simulado, aplicar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir anular venta")

    def revertir_venta(self):
        id_venta = self.obtener_seleccionada()
        if not id_venta:
            messagebox.showwarning("Atención",
                                   "Seleccione una venta para revertir.",
                                   parent=self.root)
            return

        try:
            doc = obtener_venta_completa(self.usuario, id_venta)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="obtener venta para revertir")
            return

        if not doc:
            messagebox.showwarning("No encontrada",
                                   "La venta ya no existe.",
                                   parent=self.root)
            return
        if doc.get("estado") != "Válida":
            messagebox.showwarning("No permitido",
                                   "Solo se pueden revertir ventas válidas.",
                                   parent=self.root)
            return

        from RevertirVenta import VentanaRevertirVenta

        def aplicar(v, nc, motivo):
            try:
                revertir_venta_db(self.usuario, id_venta, motivo, nc)
                self.recargar_desde_db()
            except Exception as e:
                manejar_excepcion(self.root, e, contexto="revertir venta")

        venta_formato_lista = [
            doc["_id"], doc["fecha_venta"],
            doc["cliente"]["id_cliente"], doc["total"],
            doc["estado"], None,
        ]
        try:
            nc_simulado = siguiente_nota_credito()
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="generar NC reversión")
            return

        try:
            VentanaRevertirVenta(self.root, venta_formato_lista, nc_simulado, aplicar)
        except Exception as e:
            manejar_excepcion(self.root, e, contexto="abrir revertir venta")


# ==================== EJECUCIÓN DIRECTA ====================
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    from Vistas import LoginBoutique
    root = tk.Tk()
    LoginBoutique(root)
    root.mainloop()