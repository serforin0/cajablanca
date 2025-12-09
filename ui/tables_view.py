# ui/tables_view.py
import customtkinter as ctk
from tkinter import messagebox

from core import storage
from core import tournament
from core import score_sheet


class TablesView(ctk.CTkFrame):
    """
    Vista gráfica de las mesas de la ronda 1.
    Cada mesa es un cuadrado con 4 sillas (A, B, C, D).
    Clic en una mesa = generar PDF de esa mesa.
    """

    ROUND_NUMBER = 1

    def __init__(self, master):
        super().__init__(master)

        self._build_header()
        self._build_scroll_area()
        self._load_round()

    # ---------- UI ----------

    def _build_header(self):
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=20, pady=10)

        title = ctk.CTkLabel(
            header,
            text=f"Ronda {self.ROUND_NUMBER} - Asignación de Mesas",
            font=("Roboto", 20, "bold"),
        )
        title.pack(side="left")

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

    # ---------- LÓGICA ----------

    def _load_round(self):
        # Limpiar scroll
        for w in self.scroll.winfo_children():
            w.destroy()

        mesas = storage.get_round_assignments(self.ROUND_NUMBER)

        if not mesas:
            label = ctk.CTkLabel(
                self.scroll,
                text=(
                    "No hay asignación de mesas para esta ronda.\n"
                    "Pulsa el botón 'Generar / Re-generar ronda'."
                ),
                font=("Roboto", 16),
                justify="center",
            )
            label.pack(pady=40)
            return

        # Mostrar mesas en una grilla (estilo salón)
        cols = 5  # número de mesas por fila aprox
        for idx, mesa in enumerate(mesas):
            row = idx // cols
            col = idx % cols
            widget = self._create_table_widget(self.scroll, mesa)
            widget.grid(row=row, column=col, padx=15, pady=15, sticky="n")

        for c in range(cols):
            self.scroll.grid_columnconfigure(c, weight=1)

    def _create_table_widget(self, parent, mesa_data: dict) -> ctk.CTkFrame:
        """
        Representación gráfica de una mesa de dominó:

               [ A ]
          [ D ][MESA][ B ]
               [ C ]

        La mesa completa es clicable para generar el PDF de esa mesa.
        """
        mesa_num = mesa_data["mesa"]

        frame = ctk.CTkFrame(parent, width=180, height=170, corner_radius=12)
        frame.grid_propagate(False)

        title = ctk.CTkLabel(
            frame,
            text=f"Mesa {mesa_num}",
            font=("Roboto", 14, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, pady=(4, 6))

        # Helper: nombre corto
        def short_name(p):
            ap = p["apellido"]
            ap_ini = f"{ap[0]}." if ap else ""
            return f"{p['nombre']} {ap_ini}"

        # Sillas
        seat_style = dict(
            width=70,
            height=30,
            corner_radius=6,
            fg_color="gray20",
            text_color="white",
            justify="center",
        )

        seat_A = ctk.CTkLabel(
            frame,
            text=f"A\n{short_name(mesa_data['A'])}",
            **seat_style,
        )
        seat_C = ctk.CTkLabel(
            frame,
            text=f"C\n{short_name(mesa_data['C'])}",
            **seat_style,
        )
        seat_B = ctk.CTkLabel(
            frame,
            text=f"B\n{short_name(mesa_data['B'])}",
            **seat_style,
        )
        seat_D = ctk.CTkLabel(
            frame,
            text=f"D\n{short_name(mesa_data['D'])}",
            **seat_style,
        )

        # Mesa cuadrada central
        table_center = ctk.CTkFrame(
            frame,
            width=80,
            height=50,
            fg_color="gray35",
            corner_radius=8,
        )

        # Posiciones en grilla
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        seat_A.grid(row=1, column=1, pady=(0, 4))
        seat_C.grid(row=3, column=1, pady=(4, 4))

        seat_D.grid(row=2, column=0, padx=(4, 4))
        table_center.grid(row=2, column=1, padx=4, pady=4)
        seat_B.grid(row=2, column=2, padx=(4, 4))

        # Hacer clic en cualquier parte de la mesa
        def bind_click(widget):
            widget.bind(
                "<Button-1>",
                lambda e, m=mesa_num: self._on_table_click(m),
            )

        for w in (frame, title, seat_A, seat_B, seat_C, seat_D, table_center):
            bind_click(w)

        return frame

    # ---------- EVENTOS ----------

    def _on_generate_round(self):
        if storage.get_round_assignments(self.ROUND_NUMBER):
            if not messagebox.askyesno(
                "Confirmar",
                "Ya existe una asignación para esta ronda.\n"
                "¿Quieres re-generarla al azar?",
            ):
                return

        ok, msg = tournament.generate_first_round()
        if not ok:
            messagebox.showerror("Error", msg)
            return

        messagebox.showinfo("Ronda", msg)
        self._load_round()

    def _on_generate_all_pdfs(self):
        try:
            count, folder = score_sheet.generate_score_sheets_for_round(
                self.ROUND_NUMBER
            )
            messagebox.showinfo(
                "Hojas generadas",
                f"Se generaron {count} hojas en:\n{folder}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error al generar PDF",
                str(e),
            )

    def _on_table_click(self, mesa_number: int):
        """
        Click en una mesa -> genera PDF SOLO de esa mesa.
        """
        try:
            path = score_sheet.generate_score_sheet_for_table(
                self.ROUND_NUMBER,
                mesa_number,
            )
            messagebox.showinfo(
                "Hoja generada",
                f"Se generó la hoja de la mesa {mesa_number}:\n{path}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error al generar PDF",
                f"No se pudo generar la hoja de la mesa {mesa_number}:\n{e}",
            )
