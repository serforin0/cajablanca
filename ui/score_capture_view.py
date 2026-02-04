# ui/score_capture_view.py
import customtkinter as ctk
from tkinter import messagebox

from core import storage
from core import tournament


class ScoreCaptureView(ctk.CTkFrame):
    """
    Pantalla: Captura de puntos por mesa.
    Convención:
      Equipo A = letras A y B
      Equipo B = letras C y D
    """

    def __init__(self, master):
        super().__init__(master)

        self.round_var = ctk.StringVar(value="1")
        self.mesa_var = ctk.StringVar(value="")

        self._build_header()
        self._build_body()

        self._load_round_tables()
        self._refresh_table_detail()

    # ---------- UI ----------

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=10, pady=(0, 16))

        title = ctk.CTkLabel(
            header,
            text="Captura de puntos",
            font=("Roboto", 22, "bold"),
        )
        title.pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(header, text="Ronda:").pack(side="left", padx=(18, 6))
        self.round_combo = ctk.CTkComboBox(
            header,
            values=["1", "2", "3", "4", "5"],
            variable=self.round_var,
            width=90,
            command=lambda _: self._on_round_change(),
        )
        self.round_combo.pack(side="left", padx=(0, 12), pady=8)

        self.btn_reload = ctk.CTkButton(
            header,
            text="Recargar",
            command=self._on_reload,
            height=30,
        )
        self.btn_reload.pack(side="right", padx=12)

    def _build_body(self):
        body = ctk.CTkFrame(self, corner_radius=12)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # fila superior: selector mesa + status
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(top, text="Mesa:", font=("Roboto", 14, "bold")).pack(side="left", padx=(0, 8))

        self.mesa_combo = ctk.CTkComboBox(
            top,
            values=[],
            variable=self.mesa_var,
            width=160,
            command=lambda _: self._refresh_table_detail(),
        )
        self.mesa_combo.pack(side="left")

        self.status_badge = ctk.CTkLabel(
            top,
            text="",
            corner_radius=8,
            fg_color="gray30",
            text_color="white",
            font=("Roboto", 12, "bold"),
            padx=10,
            pady=4,
        )
        self.status_badge.pack(side="left", padx=12)

        # equipos
        mid = ctk.CTkFrame(body, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=16, pady=10)

        mid.grid_columnconfigure(0, weight=1)
        mid.grid_columnconfigure(1, weight=1)

        self.teamA_box = ctk.CTkFrame(mid, corner_radius=12)
        self.teamA_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        self.teamB_box = ctk.CTkFrame(mid, corner_radius=12)
        self.teamB_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))

        self._build_team_box(self.teamA_box, "Equipo A (A + B)")
        self._build_team_box(self.teamB_box, "Equipo B (C + D)")

        # puntos + guardar
        bottom = ctk.CTkFrame(body, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 12))

        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_columnconfigure(2, weight=1)

        self.entry_points_a = ctk.CTkEntry(bottom, placeholder_text="Puntos Equipo A (A+B)")
        self.entry_points_b = ctk.CTkEntry(bottom, placeholder_text="Puntos Equipo B (C+D)")

        self.entry_points_a.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="ew")
        self.entry_points_b.grid(row=0, column=1, padx=(8, 8), pady=12, sticky="ew")

        self.btn_save = ctk.CTkButton(
            bottom,
            text="Guardar resultado",
            height=34,
            command=self._on_save,
        )
        self.btn_save.grid(row=0, column=2, padx=(8, 12), pady=12, sticky="ew")

        # ✅ NUEVO: Penalización individual (VISIBLE)
        penalty = ctk.CTkFrame(body, corner_radius=12)
        penalty.pack(fill="x", padx=16, pady=(0, 16))

        penalty.grid_columnconfigure(0, weight=1)
        penalty.grid_columnconfigure(1, weight=1)
        penalty.grid_columnconfigure(2, weight=2)
        penalty.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            penalty,
            text="Penalización / Ajuste individual",
            font=("Roboto", 14, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(10, 6))

        self.pen_player_id = ctk.CTkEntry(penalty, placeholder_text="ID Jugador (ej: 56)")
        self.pen_points = ctk.CTkEntry(penalty, placeholder_text="Puntos a restar (ej: 20)")
        self.pen_reason = ctk.CTkEntry(penalty, placeholder_text="Motivo (opcional)")

        self.pen_player_id.grid(row=1, column=0, padx=(12, 8), pady=(0, 12), sticky="ew")
        self.pen_points.grid(row=1, column=1, padx=(8, 8), pady=(0, 12), sticky="ew")
        self.pen_reason.grid(row=1, column=2, padx=(8, 8), pady=(0, 12), sticky="ew")

        self.btn_penalty = ctk.CTkButton(
            penalty,
            text="Restar",
            height=34,
            command=self._on_penalty,
        )
        self.btn_penalty.grid(row=1, column=3, padx=(8, 12), pady=(0, 12), sticky="ew")

    def _build_team_box(self, parent, title_text: str):
        title = ctk.CTkLabel(parent, text=title_text, font=("Roboto", 16, "bold"))
        title.pack(anchor="w", padx=14, pady=(12, 8))

        list_frame = ctk.CTkFrame(parent, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        lbl1 = ctk.CTkLabel(list_frame, text="-", font=("Roboto", 14))
        lbl2 = ctk.CTkLabel(list_frame, text="-", font=("Roboto", 14))
        lbl1.pack(anchor="w", pady=6)
        lbl2.pack(anchor="w", pady=6)

        parent._p1 = lbl1
        parent._p2 = lbl2

    # ---------- LÓGICA ----------

    def _on_reload(self):
        self._load_round_tables()
        self._refresh_table_detail()

    def _on_round_change(self):
        self._load_round_tables()
        self._refresh_table_detail()

    def _get_round_number(self) -> int:
        try:
            return int(self.round_var.get())
        except Exception:
            return 1

    def _get_mesa_number(self) -> int:
        text = (self.mesa_var.get() or "").strip()
        if text.lower().startswith("mesa"):
            try:
                return int(text.split()[-1])
            except Exception:
                return 0
        return 0

    def _load_round_tables(self):
        rnd = self._get_round_number()
        mesas = storage.get_round_assignments(rnd)

        values = [f"Mesa {m['mesa']}" for m in mesas]
        self.mesa_combo.configure(values=values)

        if values:
            current = self.mesa_var.get().strip()
            if current not in values:
                self.mesa_var.set(values[0])
        else:
            self.mesa_var.set("")
            self.status_badge.configure(text="", fg_color="gray30")

    def _refresh_table_detail(self):
        rnd = self._get_round_number()
        mesa_num = self._get_mesa_number()

        if mesa_num <= 0:
            self.teamA_box._p1.configure(text="-")
            self.teamA_box._p2.configure(text="-")
            self.teamB_box._p1.configure(text="-")
            self.teamB_box._p2.configure(text="-")
            self.entry_points_a.delete(0, "end")
            self.entry_points_b.delete(0, "end")
            self.status_badge.configure(text="", fg_color="gray30")
            return

        mesas = storage.get_round_assignments(rnd)
        mesa_data = next((m for m in mesas if m["mesa"] == mesa_num), None)
        if not mesa_data:
            return

        def fmt(letter: str, p: dict) -> str:
            return f"{letter}  #{p['id']}  {p['nombre']} {p['apellido']}"

        self.teamA_box._p1.configure(text=fmt("A", mesa_data["A"]))
        self.teamA_box._p2.configure(text=fmt("B", mesa_data["B"]))
        self.teamB_box._p1.configure(text=fmt("C", mesa_data["C"]))
        self.teamB_box._p2.configure(text=fmt("D", mesa_data["D"]))

        status = storage.get_table_status(rnd, mesa_num)
        if status == "finished":
            self.status_badge.configure(text="Terminado", fg_color="#b3261e")
        else:
            self.status_badge.configure(text="Jugando", fg_color="#2e7d32")

        result = storage.get_table_result(rnd, mesa_num)
        self.entry_points_a.delete(0, "end")
        self.entry_points_b.delete(0, "end")
        if result:
            self.entry_points_a.insert(0, str(result["points_a"]))
            self.entry_points_b.insert(0, str(result["points_b"]))

    def _on_save(self):
        rnd = self._get_round_number()
        mesa_num = self._get_mesa_number()

        if mesa_num <= 0:
            messagebox.showerror("Error", "Selecciona una mesa válida.")
            return

        try:
            pa = int(self.entry_points_a.get().strip() or "0")
            pb = int(self.entry_points_b.get().strip() or "0")
        except ValueError:
            messagebox.showerror("Error", "Los puntos deben ser números enteros.")
            return

        ok, msg = tournament.save_table_points(rnd, mesa_num, pa, pb)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        messagebox.showinfo("Listo", msg)
        self._refresh_table_detail()

    def _on_penalty(self):
        try:
            jugador_id = int(self.pen_player_id.get().strip())
            points = int(self.pen_points.get().strip())
        except Exception:
            messagebox.showerror("Error", "ID de jugador y puntos deben ser números.")
            return

        reason = (self.pen_reason.get().strip() or "Penalización")

        ok, msg = tournament.subtract_points_from_player(jugador_id, points, reason)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        messagebox.showinfo("Listo", msg)

        # limpiar inputs
        self.pen_player_id.delete(0, "end")
        self.pen_points.delete(0, "end")
        self.pen_reason.delete(0, "end")
