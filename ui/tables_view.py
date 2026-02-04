# ui/tables_view.py
import customtkinter as ctk
from tkinter import messagebox

from core import storage
from core import tournament
from core import score_sheet


class TablesView(ctk.CTkFrame):
    """
    Vista gráfica de las mesas por ronda (1..5).
    Cada mesa es un cuadrado con 4 sillas (A, B, C, D).
    - Click en una mesa: genera PDF de esa mesa.
    - Botón "Cambiar estado": Jugando / Terminado (color y texto).
    """

    def __init__(self, master):
        super().__init__(master)

        self.round_var = ctk.StringVar(value="1")

        self._build_header()
        self._build_scroll_area()
        self._load_round()

    # ---------- UI ----------

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=10, pady=(0, 16))

        self.title_label = ctk.CTkLabel(
            header,
            text="Ronda 1 - Asignación de Mesas",
            font=("Roboto", 22, "bold"),
        )
        self.title_label.pack(side="left", padx=12, pady=8)

        # Selector de ronda
        ctk.CTkLabel(header, text="Ronda:").pack(side="left", padx=(18, 6))
        self.round_combo = ctk.CTkComboBox(
            header,
            values=["1", "2", "3", "4", "5"],
            variable=self.round_var,
            width=90,
            command=lambda _: self._on_round_change(),
        )
        self.round_combo.pack(side="left", padx=(0, 12), pady=8)

        self.btn_generate = ctk.CTkButton(
            header,
            text="Generar / Re-generar ronda",
            command=self._on_generate_round,
        )
        self.btn_generate.pack(side="right", padx=10)

        self.btn_pdf_all = ctk.CTkButton(
            header,
            text="Generar TODAS las hojas (PDF)",
            command=self._on_generate_all_pdfs,
        )
        self.btn_pdf_all.pack(side="right", padx=10)

    def _build_scroll_area(self):
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # ---------- HELPERS ----------

    def _get_round_number(self) -> int:
        try:
            r = int(self.round_var.get())
            if r < 1:
                return 1
            if r > 5:
                return 5
            return r
        except Exception:
            return 1

    def _set_title(self):
        rnd = self._get_round_number()
        self.title_label.configure(text=f"Ronda {rnd} - Asignación de Mesas")

    # ---------- LÓGICA ----------

    def _on_round_change(self):
        self._load_round()

    def _load_round(self):
        self._set_title()

        # Limpiar scroll
        for w in self.scroll.winfo_children():
            w.destroy()

        rnd = self._get_round_number()
        mesas = storage.get_round_assignments(rnd)
        statuses = storage.get_tables_status(rnd)

        if not mesas:
            label = ctk.CTkLabel(
                self.scroll,
                text=(
                    f"No hay asignación de mesas para la ronda {rnd}.\n"
                    "Pulsa el botón 'Generar / Re-generar ronda'."
                ),
                font=("Roboto", 16),
                justify="center",
            )
            label.pack(pady=40)
            return

        cols = 4  # 4 mesas por fila
        for idx, mesa in enumerate(mesas):
            row = idx // cols
            col = idx % cols
            status = statuses.get(mesa["mesa"], "playing")
            widget = self._create_table_widget(self.scroll, rnd, mesa, status)
            widget.grid(row=row, column=col, padx=20, pady=20, sticky="n")

        for c in range(cols):
            self.scroll.grid_columnconfigure(c, weight=1)

    def _apply_status_style(self, frame, status_label, status: str):
        """Aplica colores y texto según el estado."""
        if status == "playing":
            frame.configure(fg_color="#0f3312")
            status_label.configure(
                text="Jugando",
                fg_color="#2e7d32",
                text_color="white",
            )
        else:
            frame.configure(fg_color="#3a0c0c")
            status_label.configure(
                text="Terminado",
                fg_color="#b3261e",
                text_color="white",
            )

    def _create_table_widget(self, parent, round_number: int, mesa_data: dict, status: str) -> ctk.CTkFrame:
        """
        Representación gráfica de una mesa de dominó:

               [  A  ]
          [  D ][MESA][  B ]
               [  C  ]
        """
        mesa_num = mesa_data["mesa"]
        frame = ctk.CTkFrame(parent, corner_radius=12)

        title = ctk.CTkLabel(
            frame,
            text=f"Mesa {mesa_num}",
            font=("Roboto", 14, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, pady=(4, 8))

        def seat_text(letter: str, p: dict) -> str:
            return f"{letter}\n#{p['id']} {p['nombre']}"

        seat_style = dict(
            width=110,
            height=45,
            corner_radius=6,
            fg_color="gray25",
            text_color="white",
            justify="center",
            font=("Roboto", 11),
        )

        seat_A = ctk.CTkLabel(frame, text=seat_text("A", mesa_data["A"]), **seat_style)
        seat_C = ctk.CTkLabel(frame, text=seat_text("C", mesa_data["C"]), **seat_style)
        seat_B = ctk.CTkLabel(frame, text=seat_text("B", mesa_data["B"]), **seat_style)
        seat_D = ctk.CTkLabel(frame, text=seat_text("D", mesa_data["D"]), **seat_style)

        table_center = ctk.CTkFrame(
            frame,
            width=80,
            height=50,
            fg_color="gray40",
            corner_radius=8,
        )

        for r in range(1, 5):
            frame.grid_rowconfigure(r, weight=1)
        for c in range(3):
            frame.grid_columnconfigure(c, weight=1)

        seat_A.grid(row=1, column=1, pady=(0, 6))
        seat_D.grid(row=2, column=0, padx=(6, 6), pady=4)
        table_center.grid(row=2, column=1, padx=4, pady=4)
        seat_B.grid(row=2, column=2, padx=(6, 6), pady=4)
        seat_C.grid(row=3, column=1, pady=(6, 4))

        status_label = ctk.CTkLabel(
            frame,
            text="",
            corner_radius=6,
            text_color="white",
            font=("Roboto", 11, "bold"),
        )
        status_label.grid(row=4, column=0, columnspan=3, pady=(4, 4), sticky="ew")

        toggle_btn = ctk.CTkButton(
            frame,
            text="Cambiar estado",
            height=26,
            font=("Roboto", 11),
            command=lambda r=round_number, m=mesa_num, sl=status_label, fr=frame: self._toggle_status(
                r, m, sl, fr
            ),
        )
        toggle_btn.grid(row=5, column=0, columnspan=3, pady=(2, 6), padx=10, sticky="ew")

        self._apply_status_style(frame, status_label, status)

        def bind_click(widget):
            widget.bind(
                "<Button-1>",
                lambda e, r=round_number, m=mesa_num: self._on_table_click(r, m),
            )

        for w in (frame, title, seat_A, seat_B, seat_C, seat_D, table_center):
            bind_click(w)

        return frame

    # ---------- EVENTOS ----------

    def _on_generate_round(self):
        rnd = self._get_round_number()

        if storage.get_round_assignments(rnd):
            if not messagebox.askyesno(
                "Confirmar",
                f"Ya existe una asignación para la ronda {rnd}.\n"
                "¿Quieres re-generarla?",
            ):
                return

        # ✅ aquí llamaremos un generador general
        # Debes tener en core/tournament.py:
        # generate_round(1..5)
        if hasattr(tournament, "generate_round"):
            ok, msg = tournament.generate_round(rnd)
        else:
            # fallback si todavía no lo creaste:
            if rnd == 1:
                ok, msg = tournament.generate_first_round()
            else:
                ok, msg = (False, "Falta implementar tournament.generate_round() para rondas 2..5.")

        if not ok:
            messagebox.showerror("Error", msg)
            return

        messagebox.showinfo("Ronda", msg)
        self._load_round()

    def _on_generate_all_pdfs(self):
        rnd = self._get_round_number()
        try:
            count, folder = score_sheet.generate_score_sheets_for_round(rnd)
            messagebox.showinfo(
                "Hojas generadas",
                f"Se generaron {count} hojas en:\n{folder}",
            )
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))

    def _on_table_click(self, round_number: int, mesa_number: int):
        """Click en una mesa -> genera PDF SOLO de esa mesa."""
        try:
            path = score_sheet.generate_score_sheet_for_table(round_number, mesa_number)
            messagebox.showinfo(
                "Hoja generada",
                f"Se generó la hoja de la ronda {round_number}, mesa {mesa_number}:\n{path}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error al generar PDF",
                f"No se pudo generar la hoja:\n{e}",
            )

    def _toggle_status(self, round_number: int, mesa_number: int, status_label, frame):
        current = storage.get_table_status(round_number, mesa_number)
        new_status = "finished" if current == "playing" else "playing"
        storage.set_table_status(round_number, mesa_number, new_status)
        self._apply_status_style(frame, status_label, new_status)
