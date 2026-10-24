import tkinter as tk
from tkinter import ttk, messagebox

class VentanaActualizarCliente(tk.Toplevel):
    def __init__(self, parent, doc_cliente, callback_actualizar=None):
        super().__init__(parent)
        self.doc_cliente = doc_cliente
        self.callback_actualizar = callback_actualizar

        self.title("Actualizar cliente")
        self.geometry("480x580")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (480 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (580 // 2)
        self.geometry(f"+{x}+{y}")

        # --- Barra de título ---
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=f"Actualizar: {doc_cliente['_id']}", font=("Segoe UI", 11, "bold"), bg="#2c3e50", fg="white").pack(side="left", padx=15)
        tk.Button(barra, text="✕", bg="#2c3e50", fg="white", relief="flat", command=self.destroy).pack(side="right", fill="y")

        # --- Contenedor de Pestañas ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=15)

        # Pestaña 1: Datos Personales
        tab1 = tk.Frame(notebook, bg="white")
        notebook.add(tab1, text="Datos Personales")
        
        self.e_nombre    = self._crear_campo(tab1, "Nombre:", 0, doc_cliente.get("nombre", ""))
        self.e_ap_pat    = self._crear_campo(tab1, "Ap. Paterno:", 1, doc_cliente.get("apellido_paterno", ""))
        self.e_ap_mat    = self._crear_campo(tab1, "Ap. Materno:", 2, doc_cliente.get("apellido_materno", ""))
        self.e_rut       = self._crear_campo(tab1, "RUT:", 3, doc_cliente.get("rut", ""))
        self.e_telefono  = self._crear_campo(tab1, "Teléfono:", 4, doc_cliente.get("telefono", ""))
        self.e_email     = self._crear_campo(tab1, "Email:", 5, doc_cliente.get("email", ""))
        self.e_fecha_nac = self._crear_campo(tab1, "F. Nacimiento (YYYY-MM-DD):", 6, str(doc_cliente.get("fecha_nacimiento", ""))[:10])
        self.e_estado    = self._crear_combo(tab1, "Estado:", 7, ["activo", "inactivo"], doc_cliente.get("estado", "activo"))

        # Pestaña 2: Dirección
        tab2 = tk.Frame(notebook, bg="white")
        notebook.add(tab2, text="Dirección")
        
        dir = doc_cliente.get("direccion", {})
        self.e_calle  = self._crear_campo(tab2, "Calle:", 0, dir.get("calle", ""))
        self.e_numero = self._crear_campo(tab2, "Número:", 1, dir.get("numero", ""))
        self.e_comuna = self._crear_campo(tab2, "Comuna:", 2, dir.get("comuna", ""))
        self.e_ciudad = self._crear_campo(tab2, "Ciudad:", 3, dir.get("ciudad", ""))
        self.e_region = self._crear_campo(tab2, "Región:", 4, dir.get("region", ""))

        # Pestaña 3: Consentimiento
        tab3 = tk.Frame(notebook, bg="white")
        notebook.add(tab3, text="Consentimiento")
        
        cons = doc_cliente.get("consentimiento_datos", {})
        
        # Checkbox para aceptado
        self.var_aceptado = tk.BooleanVar(value=cons.get("aceptado", False))
        chk_aceptado = tk.Checkbutton(tab3, text="Acepta uso de datos", variable=self.var_aceptado, bg="white", font=("Segoe UI", 10))
        chk_aceptado.grid(row=0, column=0, columnspan=2, sticky="w", pady=10, padx=10)

        # Checkbox para promociones
        self.var_promos = tk.BooleanVar(value=cons.get("puede_recibir_promociones", False))
        chk_promos = tk.Checkbutton(tab3, text="Acepta recibir promociones", variable=self.var_promos, bg="white", font=("Segoe UI", 10))
        chk_promos.grid(row=1, column=0, columnspan=2, sticky="w", pady=5, padx=10)

        self.e_finalidad = self._crear_campo(tab3, "Finalidad:", 2, cons.get("finalidad", "gestion_comercial_y_promociones"))

        # --- Botones (fuera del notebook) ---
        botones = tk.Frame(self, bg="white")
        botones.pack(pady=(0, 15))
        tk.Button(botones, text="Guardar Cambios", bg="#f39c12", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=6, command=self.actualizar).pack(side="left", padx=8)
        tk.Button(botones, text="Cancelar", bg="#95a5a6", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=6, command=self.destroy).pack(side="left", padx=8)

    def _crear_campo(self, parent, etiqueta, fila, valor_inicial=""):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e", anchor="w").grid(row=fila, column=0, sticky="w", pady=6, padx=10)
        entry = tk.Entry(parent, font=("Segoe UI", 10), relief="solid", bd=1, bg="white")
        entry.grid(row=fila, column=1, sticky="ew", ipady=4, pady=6, padx=(0, 10))
        entry.insert(0, valor_inicial)
        parent.grid_columnconfigure(1, weight=1)
        return entry

    def _crear_combo(self, parent, etiqueta, fila, valores, valor_inicial):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e", anchor="w").grid(row=fila, column=0, sticky="w", pady=6, padx=10)
        combo = ttk.Combobox(parent, values=valores, state="readonly", font=("Segoe UI", 10))
        combo.grid(row=fila, column=1, sticky="ew", ipady=4, pady=6, padx=(0, 10))
        combo.set(valor_inicial)
        parent.grid_columnconfigure(1, weight=1)
        return combo

    def actualizar(self):
        self.update_idletasks() # Forzar actualización visual de los checkboxes

        datos = {
            "nombre": self.e_nombre.get().strip(),
            "apellido_paterno": self.e_ap_pat.get().strip(),
            "apellido_materno": self.e_ap_mat.get().strip(),
            "rut": self.e_rut.get().strip(),
            "telefono": self.e_telefono.get().strip(),
            "email": self.e_email.get().strip(),
            "fecha_nacimiento": self.e_fecha_nac.get().strip(),
            "estado": self.e_estado.get().strip().lower(), # Forzar minúsculas (activo / inactivo)
            "calle": self.e_calle.get().strip(),
            "numero": self.e_numero.get().strip(),
            "comuna": self.e_comuna.get().strip(),
            "ciudad": self.e_ciudad.get().strip(),
            "region": self.e_region.get().strip(),
            "aceptado": bool(self.var_aceptado.get()), 
            "puede_recibir_promociones": bool(self.var_promos.get()),
            "finalidad": self.e_finalidad.get().strip()
        }

        if not datos["nombre"] or not datos["rut"]:
            messagebox.showwarning("Atención", "Nombre y RUT son obligatorios.", parent=self)
            return

        if self.callback_actualizar:
            self.callback_actualizar(self.doc_cliente["_id"], datos)
            
        self.destroy()