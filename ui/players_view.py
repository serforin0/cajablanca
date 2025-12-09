# ui/players_view.py
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

from core import storage


class PlayersView(ctk.CTkFrame):
    """
    Pantalla para registrar jugadores y ver la lista.
    """

    PAGO_FIJO = 5000

    def __init__(self, master):
        super().__init__(master)

        # Layout general: arriba formulario, abajo tabla
        self._build_form()
        self._build_table()
        self._load_players()

    # ---------------- FORMULARIO ----------------
    def _build_form(self):
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=20)

        title_label = ctk.CTkLabel(
            form_frame,
            text="Registro de jugadores",
            font=("Roboto", 20, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky="w")

        # Nombre
        ctk.CTkLabel(form_frame, text="Nombre:").grid(row=1, column=0, sticky="w")
        self.entry_nombre = ctk.CTkEntry(form_frame, width=200)
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Apellido
        ctk.CTkLabel(form_frame, text="Apellido:").grid(row=1, column=2, sticky="w")
        self.entry_apellido = ctk.CTkEntry(form_frame, width=200)
        self.entry_apellido.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Cédula
        ctk.CTkLabel(form_frame, text="Cédula:").grid(row=2, column=0, sticky="w")
        self.entry_cedula = ctk.CTkEntry(form_frame, width=200)
        self.entry_cedula.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Teléfono
        ctk.CTkLabel(form_frame, text="Teléfono:").grid(row=2, column=2, sticky="w")
        self.entry_telefono = ctk.CTkEntry(form_frame, width=200)
        self.entry_telefono.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Pago fijo
        ctk.CTkLabel(form_frame, text="Pago por jugador:").grid(
            row=3, column=0, sticky="w"
        )
        self.label_pago = ctk.CTkLabel(
            form_frame,
            text=f"{self.PAGO_FIJO:,.0f} RD$",
            font=("Roboto", 14, "bold"),
        )
        self.label_pago.grid(row=3, column=1, sticky="w", pady=5)

        # Botón registrar
        self.btn_registrar = ctk.CTkButton(
            form_frame,
            text="Registrar jugador",
            command=self._on_registrar_click,
        )
        self.btn_registrar.grid(row=3, column=3, padx=5, pady=5, sticky="e")

        # Info de cantidad y total
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.label_cantidad = ctk.CTkLabel(info_frame, text="Jugadores: 0 / 100")
        self.label_cantidad.pack(side="left", padx=(5, 20))

        self.label_total = ctk.CTkLabel(info_frame, text="Total recaudado: 0 RD$")
        self.label_total.pack(side="left")

    # ---------------- TABLA ----------------
    def _build_table(self):
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("id", "nombre", "apellido", "cedula", "telefono", "pago")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
        )

        # Encabezados
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("apellido", text="Apellido")
        self.tree.heading("cedula", text="Cédula")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("pago", text="Pago (RD$)")

        # Tamaño de columnas
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nombre", width=120)
        self.tree.column("apellido", width=120)
        self.tree.column("cedula", width=120)
        self.tree.column("telefono", width=120)
        self.tree.column("pago", width=100, anchor="e")

        # Scroll vertical
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    # ---------------- LÓGICA ----------------
    def _load_players(self):
        # Limpiar
        for item in self.tree.get_children():
            self.tree.delete(item)

        players = storage.get_all_players()

        for p in players:
            self.tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["nombre"],
                    p["apellido"],
                    p["cedula"],
                    p["telefono"],
                    p["pago"],
                ),
            )

        # Actualizar contadores
        count = len(players)
        total = count * self.PAGO_FIJO
        self.label_cantidad.configure(text=f"Jugadores: {count} / 100")
        self.label_total.configure(text=f"Total recaudado: {total:,.0f} RD$")

    def _on_registrar_click(self):
        nombre = self.entry_nombre.get()
        apellido = self.entry_apellido.get()
        cedula = self.entry_cedula.get()
        telefono = self.entry_telefono.get()

        ok, msg = storage.add_player(nombre, apellido, cedula, telefono, self.PAGO_FIJO)

        if not ok:
            messagebox.showerror("Error", msg)
            return

        # Limpia campos
        self.entry_nombre.delete(0, tk.END)
        self.entry_apellido.delete(0, tk.END)
        self.entry_cedula.delete(0, tk.END)
        self.entry_telefono.delete(0, tk.END)

        # Recarga tabla y contadores
        self._load_players()
        messagebox.showinfo("Éxito", msg)
