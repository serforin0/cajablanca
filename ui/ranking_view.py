# ui/ranking_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox

from core import tournament


class RankingView(ctk.CTkFrame):
    """
    Pantalla: Ranking final (R, G, P, E).
    """

    def __init__(self, master):
        super().__init__(master)

        self._build_header()
        self._build_table()
        self._load_ranking()

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=10, pady=(0, 16))

        title = ctk.CTkLabel(
            header,
            text="Ranking",
            font=("Roboto", 22, "bold"),
        )
        title.pack(side="left", padx=12, pady=10)

        self.btn_refresh = ctk.CTkButton(
            header,
            text="Recalcular / Recargar",
            command=self._on_refresh,
            height=30,
        )
        self.btn_refresh.pack(side="right", padx=12)

    def _build_table(self):
        table_frame = ctk.CTkFrame(self, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("R", "id", "nombre", "apellido", "G", "P", "E")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
        )

        self.tree.heading("R", text="R")
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("apellido", text="Apellido")
        self.tree.heading("G", text="G")
        self.tree.heading("P", text="P")
        self.tree.heading("E", text="E")

        self.tree.column("R", width=50, anchor="center")
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nombre", width=160)
        self.tree.column("apellido", width=160)
        self.tree.column("G", width=60, anchor="center")
        self.tree.column("P", width=80, anchor="center")
        self.tree.column("E", width=100, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)
        vsb.grid(row=0, column=1, sticky="ns", pady=12, padx=(0, 12))

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def _clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _load_ranking(self):
        self._clear()
        try:
            rows = tournament.get_ranking()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el ranking:\n{e}")
            return

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    r["R"],
                    r["id"],
                    r["nombre"],
                    r["apellido"],
                    r["G"],
                    r["P"],
                    r["E"],
                ),
            )

    def _on_refresh(self):
        try:
            tournament.recompute_ranking()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo recalcular:\n{e}")
            return

        self._load_ranking()
        messagebox.showinfo("Ranking", "Ranking actualizado.")
