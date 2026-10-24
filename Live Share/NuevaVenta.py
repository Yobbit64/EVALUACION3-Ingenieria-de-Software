import tkinter as tk
from tkinter import ttk, messagebox


class VentanaNuevaVenta(tk.Toplevel):
    def __init__(self, parent, catalogo=None, cliente_dict=None,
                 callback_guardar=None, usuario=None):
        super().__init__(parent)
        self.callback_guardar = callback_guardar
        self.usuario = usuario or {"username": "anonimo", "rol": "vendedor", "_id": "ANON"}
        
        # Cliente por defecto (se sobreescribe al identificarlo)
        self.cliente_dict = cliente_dict or {"id_cliente": "CLI-000", "nombre": "Cliente", "apellido": "Genérico"}
        
        # Catálogo desde la base de datos o demo
        if catalogo is None:
            self.catalogo = [
                ["PROD-001", "Polera negra",   "Poleras",    "M",  9990,  15, "111111"],
                ["PROD-002", "Jeans azul",     "Pantalones", "32", 19990, 8,  "222222"],
                ["PROD-003", "Chaqueta cuero", "Chaquetas",  "L",  39990, 4,  "333333"],
            ]
        else:
            self.catalogo = catalogo

        # Lista de ítems (diccionarios)
        self.items = []

        # ---------- Configuración básica ----------
        self.title("Nueva venta")
        self.geometry("700x560")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (700 // 2)
        y = py + (ph // 2) - (560 // 2)
        self.geometry(f"+{x}+{y}")

        # ---------- Barra de título ----------
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text="Nueva venta", font=("Segoe UI", 11, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=15)

        tk.Button(barra, text="Cerrar", font=("Segoe UI", 9, "bold"),
                  bg="#2c3e50", fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=14, command=self.destroy).pack(side="right", fill="y")

        # ---------- Cuerpo ----------
        cuerpo = tk.Frame(self, bg="white")
        cuerpo.pack(fill="both", expand=True, padx=20, pady=15)

        # --- Búsqueda ---
        buscar_frame = tk.Frame(cuerpo, bg="white")
        buscar_frame.pack(fill="x", pady=(0, 12))

        tk.Label(buscar_frame, text="🔍", font=("Segoe UI", 11), bg="white").pack(side="left", padx=(0, 6))

        self.entry_id = tk.Entry(buscar_frame, font=("Segoe UI", 10), relief="solid", bd=1, width=22, fg="#95a5a6")
        self.entry_id.insert(0, "ID producto")
        self.entry_id.pack(side="left", ipady=4)
        self.entry_id.bind("<FocusIn>", self._limpiar_placeholder)
        self.entry_id.bind("<FocusOut>", self._poner_placeholder)
        self.entry_id.bind("<Return>", lambda e: self.agregar_producto())

        tk.Button(buscar_frame, text="Agregar producto", font=("Segoe UI", 9, "bold"),
                  bg="#3498db", fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=4, command=self.agregar_producto).pack(side="left", padx=6)

        # --- Tabla ---
        tabla_frame = tk.Frame(cuerpo, bg="white")
        tabla_frame.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        columnas = ("ID", "Nombre", "Precio", "Cantidad", "Subtotal")
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings", yscrollcommand=scroll.set, height=9)
        scroll.config(command=self.tabla.yview)

        anchos = {"ID": 80, "Nombre": 170, "Precio": 100, "Cantidad": 130, "Subtotal": 110}
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor="center")

        self.tabla.pack(fill="both", expand=True)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", background="white", foreground="#2c3e50", rowheight=32, fieldbackground="white", font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", background="#34495e", foreground="white", font=("Segoe UI", 10, "bold"))
        estilo.map("Treeview", background=[("selected", "#3498db")])

        # --- Overlay del spin (▲ N ▼) ---
        self.spin_frame = tk.Frame(self.tabla, bg="#ecf0f1", bd=1, relief="solid")
        
        self.btn_up = tk.Button(self.spin_frame, text="▲", font=("Segoe UI", 7, "bold"),
                                bg="#ecf0f1", fg="#2c3e50", relief="flat", bd=0, cursor="hand2",
                                command=self._incrementar)
        self.btn_up.pack(side="left", fill="y")

        self.lbl_cant = tk.Label(self.spin_frame, text="1", font=("Segoe UI", 10, "bold"),
                                 bg="#ecf0f1", fg="#2c3e50", width=3)
        self.lbl_cant.pack(side="left", fill="both", expand=True)

        self.btn_down = tk.Button(self.spin_frame, text="▼", font=("Segoe UI", 7, "bold"),
                                  bg="#ecf0f1", fg="#2c3e50", relief="flat", bd=0, cursor="hand2",
                                  command=self._decrementar)
        self.btn_down.pack(side="left", fill="y")

        # --- Etiqueta de alerta de stock ---
        self.lbl_alerta_stock = tk.Label(self, text="⚠ Stock insuficiente", 
                                         font=("Segoe UI", 9, "bold"), 
                                         bg="white", fg="#e74c3c")

        self.tabla.bind("<<TreeviewSelect>>", self._on_select)
        self.tabla.bind("<Button-1>", self._on_click)

        # --- Botón eliminar ---
        acciones_frame = tk.Frame(cuerpo, bg="white")
        acciones_frame.pack(fill="x", pady=(10, 0))

        tk.Button(acciones_frame, text="Eliminar producto de la venta", font=("Segoe UI", 9, "bold"),
                  bg="#e74c3c", fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=5, command=self.eliminar_producto).pack(side="left")

        # --- Total ---
        total_frame = tk.Frame(cuerpo, bg="white")
        total_frame.pack(fill="x", pady=(18, 4))

        self.lbl_total = tk.Label(total_frame, text="TOTAL: $0", font=("Segoe UI", 14, "bold"),
                                  bg="white", fg="#2c3e50")
        self.lbl_total.pack(side="right")

        # --- Botón Realizar venta ---
        boton_frame = tk.Frame(cuerpo, bg="white")
        boton_frame.pack(fill="x", pady=(4, 0))

        tk.Button(boton_frame, text="Realizar venta", font=("Segoe UI", 10, "bold"),
                  bg="#27ae60", fg="white", relief="flat", cursor="hand2",
                  padx=18, pady=7, command=self.realizar_venta).pack(side="right")

    # ==================== Placeholder ====================
    def _limpiar_placeholder(self, e=None):
        if self.entry_id.get() == "ID producto":
            self.entry_id.delete(0, tk.END)
            self.entry_id.config(fg="#2c3e50")

    def _poner_placeholder(self, e=None):
        if not self.entry_id.get().strip():
            self.entry_id.insert(0, "ID producto")
            self.entry_id.config(fg="#95a5a6")

    def _get_id_input(self):
        v = self.entry_id.get().strip()
        return "" if v == "ID producto" else v

    # ==================== Búsqueda y agregar ====================
    def _buscar_en_catalogo(self, idp):
        for p in self.catalogo:
            if p[0] == idp:
                return p
        return None

    def agregar_producto(self):
        idp = self._get_id_input()
        if not idp:
            messagebox.showwarning("Atención", "Ingrese un ID de producto.", parent=self)
            return

        for it in self.items:
            if it["id_producto"] == idp:
                messagebox.showinfo("Ya agregado", f"El producto '{it['nombre']}' ya está en la venta.", parent=self)
                return

        prod = self._buscar_en_catalogo(idp)
        if not prod:
            messagebox.showerror("No encontrado", f"No existe un producto con ID '{idp}'.", parent=self)
            return

        item = {
            "id_producto": prod[0],
            "nombre": prod[1],
            "categoria": prod[2],
            "talla": prod[3],
            "color": "No especificado",
            "marca": "No especificada",
            "precio_unitario": prod[4],
            "cantidad": 1,
            "subtotal": prod[4]
        }
        self.items.append(item)
        self._refrescar_tabla()
        self._ocultar_spin()

        self.entry_id.delete(0, tk.END)
        self.entry_id.focus_set()

    def eliminar_producto(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto para eliminar.", parent=self)
            return
        valores = self.tabla.item(sel[0], "values")
        idp = valores[0]
        self.items = [it for it in self.items if it["id_producto"] != idp]
        self._ocultar_spin()
        self._refrescar_tabla()

    # ==================== Refresco de tabla ====================
    def _fmt(self, valor):
        return f"${valor:,}".replace(",", ".")

    def _refrescar_tabla(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for it in self.items:
            self.tabla.insert(
                "", "end",
                values=(it["id_producto"], it["nombre"], self._fmt(it["precio_unitario"]), it["cantidad"], self._fmt(it["subtotal"]))
            )
        self._actualizar_total()

    def _refrescar_preservando_seleccion(self, idp):
        self._refrescar_tabla()
        for fila in self.tabla.get_children():
            valores = self.tabla.item(fila, "values")
            if valores[0] == idp:
                self.tabla.selection_set(fila)
                self.tabla.focus(fila)
                self.after(20, lambda: self._on_select(None))
                break

    def _actualizar_total(self):
        total = sum(it["subtotal"] for it in self.items)
        self.lbl_total.config(text=f"TOTAL: {self._fmt(total)}")

    # ==================== Overlay del spin ====================
    def _on_select(self, event):
        sel = self.tabla.selection()
        if not sel:
            self._ocultar_spin()
            self.lbl_alerta_stock.place_forget()
            return
        item_id = sel[0]
        bbox = self.tabla.bbox(item_id, column="Cantidad")
        if not bbox:
            self._ocultar_spin()
            return
        x, y, w, h = bbox

        valores = self.tabla.item(item_id, "values")
        idp = valores[0]
        item = next((i for i in self.items if i["id_producto"] == idp), None)
        if not item:
            self._ocultar_spin()
            return

        self.lbl_cant.config(text=str(item["cantidad"]))
        self.spin_frame.place(x=x + 2, y=y + 2, width=w - 4, height=h - 4)
        self.spin_frame.lift()

        self.lbl_alerta_stock.place(x=x + w + 10, y=y + 5)
        self.lbl_alerta_stock.place_forget()
        
        self._verificar_stock_visual(item)

    def _on_click(self, event):
        region = self.tabla.identify("region", event.x, event.y)
        if region != "cell":
            self._ocultar_spin()

    def _ocultar_spin(self):
        self.spin_frame.place_forget()
        self.lbl_alerta_stock.place_forget()

    def _item_seleccionado(self):
        sel = self.tabla.selection()
        if not sel:
            return None
        valores = self.tabla.item(sel[0], "values")
        idp = valores[0]
        return next((i for i in self.items if i["id_producto"] == idp), None)

    def _verificar_stock_visual(self, item):
        prod = self._buscar_en_catalogo(item["id_producto"])
        stock_disponible = prod[5] if prod else 0

        if item["cantidad"] > stock_disponible:
            self.lbl_alerta_stock.place(x=self.spin_frame.winfo_x() + self.spin_frame.winfo_width() + 10, 
                                        y=self.spin_frame.winfo_y() + 5)
        else:
            self.lbl_alerta_stock.place_forget()

    def _incrementar(self):
        item = self._item_seleccionado()
        if not item:
            return
        item["cantidad"] += 1
        item["subtotal"] = item["precio_unitario"] * item["cantidad"]
        self.lbl_cant.config(text=str(item["cantidad"]))
        self._refrescar_preservando_seleccion(item["id_producto"])
        self._verificar_stock_visual(item)

    def _decrementar(self):
        item = self._item_seleccionado()
        if not item or item["cantidad"] <= 1:
            return
        item["cantidad"] -= 1
        item["subtotal"] = item["precio_unitario"] * item["cantidad"]
        self.lbl_cant.config(text=str(item["cantidad"]))
        self._refrescar_preservando_seleccion(item["id_producto"])
        self._verificar_stock_visual(item)

    # ==================== Realizar venta ====================
    def realizar_venta(self):
        if not self.items:
            messagebox.showwarning("Venta vacía", "Agregue al menos un producto.", parent=self)
            return

        # --- VALIDACIÓN DE STOCK GLOBAL ---
        stock_insuficiente = False
        for item in self.items:
            prod = self._buscar_en_catalogo(item["id_producto"])
            if prod and item["cantidad"] > prod[5]:
                stock_insuficiente = True
                break

        if stock_insuficiente:
            respuesta = messagebox.askyesno(
                "Stock insuficiente",
                "El stock de productos es insuficiente para la cantidad seleccionada.\n\n"
                "¿Continuar venta de todos modos?",
                parent=self
            )
            if not respuesta:
                return
        # -----------------------------------

        # --- PASO 1: IDENTIFICAR CLIENTE ---
        from IdentificarCliente import VentanaIdentificarCliente
        
        def cliente_identificado(cliente_dict):
            self.cliente_dict = cliente_dict
            self._continuar_venta() # <-- Aquí llamamos al método que faltaba

        v_cli = VentanaIdentificarCliente(self, cliente_identificado, usuario=self.usuario)
        self.wait_window(v_cli)

    # ==================== NUEVO MÉTODO: CONTINUAR VENTA ====================
    def _continuar_venta(self):
        """Continúa el flujo de pago una vez identificado el cliente."""
        total = sum(it["subtotal"] for it in self.items)

        # 1) Pedir medio de pago
        from MedioPago import VentanaMedioPago
        v_mp = VentanaMedioPago(self, "", total)
        self.wait_window(v_mp)
        if not v_mp.resultado: return
        medio_pago = v_mp.resultado

        # 2) Pedir comprobante
        from Comprobante import VentanaEmitirComprobante
        v_cp = VentanaEmitirComprobante(self, "", total, self.cliente_dict.get("_id", "CLI-000"))
        self.wait_window(v_cp)
        if not v_cp.resultado: return
        comprobante = v_cp.resultado

        # 3) Confirmación final
        if not messagebox.askyesno("Confirmar venta", f"¿Registrar la venta por {self._fmt(total)}?", parent=self):
            return

        # 4) Armar el paquete de datos con el cliente real
        datos_venta = {
            "cliente": {
                "id_cliente": self.cliente_dict.get("_id", "CLI-000"),
                "nombre": self.cliente_dict.get("nombre", ""),
                "apellido": f"{self.cliente_dict.get('apellido_paterno','')} "
                            f"{self.cliente_dict.get('apellido_materno','')}".strip()
            },
            "productos": self.items,
            "subtotal": total,
            "total": total,
            "metodo_pago": medio_pago,
            "comprobante": comprobante,
            "empleado_id": self.usuario["_id"],       # ← NUEVO (anti-IDOR)
            "empleado_username": self.usuario["username"],
        }

        if self.callback_guardar:
            self.callback_guardar(datos_venta)

        messagebox.showinfo("Venta registrada", "✓ Venta registrada exitosamente en MongoDB.", parent=self)
        self.destroy()


# ==================== PRUEBA AISLADA ====================
if __name__ == "__main__":
    def guardar(venta):
        print("Venta registrada:", venta)

    root = tk.Tk()
    root.title("Prueba")
    root.geometry("420x320")
    root.configure(bg="#f5f5f5")

    tk.Button(root, text="Abrir 'Nueva venta'",
              font=("Segoe UI", 10, "bold"),
              bg="#3498db", fg="white",
              relief="flat", padx=15, pady=8,
              command=lambda: VentanaNuevaVenta(
                  root, callback_guardar=guardar)
              ).pack(expand=True)

    root.mainloop()