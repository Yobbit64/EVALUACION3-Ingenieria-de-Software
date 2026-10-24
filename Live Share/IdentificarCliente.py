# IdentificarCliente.py
import tkinter as tk
from tkinter import ttk, messagebox
import re
from db import buscar_cliente_por_documento, crear_cliente_rapido, obtener_cliente_generico

class VentanaIdentificarCliente(tk.Toplevel):
    def __init__(self, parent, callback_cliente, usuario=None):
        super().__init__(parent)
        self.callback_cliente = callback_cliente
        self.usuario = usuario or {"username": "anonimo", "rol": "vendedor", "_id": "ANON"}
        self.cliente_seleccionado = None

        self.title("Identificar Cliente")
        self.geometry("400x320")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (320 // 2)
        self.geometry(f"+{x}+{y}")

        # Barra de título
        barra = tk.Frame(self, bg="#2c3e50", height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text="Identificación de Cliente", font=("Segoe UI", 11, "bold"), bg="#2c3e50", fg="white").pack(side="left", padx=15)
        tk.Button(barra, text="✕", bg="#2c3e50", fg="white", relief="flat", command=self.cancelar).pack(side="right", fill="y")

        cuerpo = tk.Frame(self, bg="white")
        cuerpo.pack(fill="both", expand=True, padx=25, pady=20)

        # Tipo de documento
        tk.Label(cuerpo, text="Tipo de Documento:", font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e", anchor="w").pack(fill="x")
        self.combo_tipo = ttk.Combobox(cuerpo, values=["RUT", "Pasaporte", "DNI Extranjero", "Otro"], state="readonly", font=("Segoe UI", 10))
        self.combo_tipo.current(0)
        self.combo_tipo.pack(fill="x", pady=(2, 10))
        self.combo_tipo.bind("<<ComboboxSelected>>", self._on_tipo_change)

        # Número de documento
        tk.Label(cuerpo, text="Número de Documento:", font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e", anchor="w").pack(fill="x")
        self.entry_doc = tk.Entry(cuerpo, font=("Segoe UI", 11), relief="solid", bd=1)
        self.entry_doc.pack(fill="x", ipady=5, pady=(2, 5))
        
        self.lbl_error = tk.Label(cuerpo, text="", font=("Segoe UI", 8), bg="white", fg="#e74c3c")
        self.lbl_error.pack(anchor="w")

        # Botones de acción
        tk.Button(cuerpo, text="Buscar Cliente", font=("Segoe UI", 10, "bold"), bg="#3498db", fg="white", relief="flat", pady=6, command=self.buscar).pack(fill="x", pady=(15, 5))
        tk.Button(cuerpo, text="Cliente General / Sin Identificar", font=("Segoe UI", 10, "bold"), bg="#95a5a6", fg="white", relief="flat", pady=6, command=self.cliente_general).pack(fill="x")

    def _on_tipo_change(self, event=None):
        tipo = self.combo_tipo.get()
        if tipo == "RUT":
            self.entry_doc.config(fg="black")
            self.lbl_error.config(text="Formato esperado: 12345678-9")
        else:
            self.entry_doc.config(fg="black")
            self.lbl_error.config(text="Ingrese el número de pasaporte o documento.")

    def _validar_rut(self, rut):
        """Valida el formato del RUT chileno. Tolera None y tipos no string."""
        # Defensa: normalizar entrada antes de validar
        if rut is None or not isinstance(rut, str):
            return False
        
        rut = rut.strip()
        if not rut:
            return False
        
        # Regex estricta: 7-8 dígitos, guion, dígito o K/k
        if not re.match(r"^\d{7,8}-[\dkK]$", rut):
            return False
        
        return True

    def buscar(self):
        tipo = self.combo_tipo.get()
        doc = self.entry_doc.get().strip()

        if not doc:
            self.lbl_error.config(text="⚠ Ingrese un documento.")
            return

        # Validación específica si es RUT
        if tipo == "RUT" and not self._validar_rut(doc):
            self.lbl_error.config(text="⚠ Formato de RUT inválido (XX.XXX.XXX-X).")
            return

        # Buscar en la base de datos
        cliente = buscar_cliente_por_documento(self.usuario, tipo, doc)

        if cliente:
            # Cliente existe (Éxito)
            self.cliente_seleccionado = cliente
            self._devolver_cliente()
        else:
            # Excepción 1: Cliente no existe -> Registro Rápido
            self.lbl_error.config(text="")
            respuesta = messagebox.askyesno("Cliente no encontrado", 
                f"No se encontró ningún cliente con el documento {doc}.\n\n¿Desea registrar un cliente rápido?", parent=self)
            
            if respuesta:
                self._abrir_registro_rapido(doc, tipo)

    def _abrir_registro_rapido(self, doc, tipo):
        # Ventana modal simple para pedir Nombre y Apellido
        top = tk.Toplevel(self)
        top.title("Registro Rápido")
        top.geometry("300x200")
        top.transient(self)
        top.wait_visibility()
        top.grab_set()

        tk.Label(top, text="Nombre:", font=("Segoe UI", 9, "bold")).pack(pady=(10,0))
        e_nombre = tk.Entry(top)
        e_nombre.pack(pady=2)

        tk.Label(top, text="Apellido:", font=("Segoe UI", 9, "bold")).pack(pady=(5,0))
        e_apellido = tk.Entry(top)
        e_apellido.pack(pady=2)

        def guardar():
            nom = e_nombre.get().strip()
            ape = e_apellido.get().strip()
            if not nom or not ape:
                messagebox.showwarning("Atención", "Nombre y Apellido son obligatorios.", parent=top)
                return
            
            # Crear cliente en Mongo
            nuevo_cliente = crear_cliente_rapido(
                self.usuario, nom, ape, doc, tipo
            )
            self.cliente_seleccionado = nuevo_cliente
            top.destroy()
            self._devolver_cliente()

        tk.Button(top, text="Guardar y Continuar", bg="#27ae60", fg="white", command=guardar).pack(pady=15)

    def cliente_general(self):
        try:
            cliente_gen = obtener_cliente_generico(self.usuario)
            self.cliente_seleccionado = cliente_gen
            self._devolver_cliente()
        except PermissionError as e:
            messagebox.showerror("Acceso denegado", str(e), parent=self)

    def _devolver_cliente(self):
        if self.callback_cliente:
            self.callback_cliente(self.cliente_seleccionado)
        self.destroy()

    def cancelar(self):
        self.destroy()