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
        self.winner_var = ctk.StringVar(value="AC")

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

        # puntos por jugador + guardar
        bottom = ctk.CTkFrame(body, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 12))

        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_columnconfigure(2, weight=1)
        bottom.grid_columnconfigure(3, weight=1)
        bottom.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(
            bottom,
            text="Puntos individuales por jugador",
            font=("Roboto", 14, "bold"),
        ).grid(row=0, column=0, columnspan=5, sticky="w", padx=12, pady=(10, 6))

        ctk.CTkLabel(bottom, text="Letra", font=("Roboto", 12, "bold")).grid(
            row=1, column=0, sticky="w", padx=12
        )
        ctk.CTkLabel(bottom, text="Jugador", font=("Roboto", 12, "bold")).grid(
            row=1, column=1, sticky="w", padx=12
        )
        ctk.CTkLabel(bottom, text="Puntos", font=("Roboto", 12, "bold")).grid(
            row=1, column=2, sticky="w", padx=12
        )
        ctk.CTkLabel(bottom, text="Penalidad", font=("Roboto", 12, "bold")).grid(
            row=1, column=3, sticky="w", padx=12
        )
        ctk.CTkLabel(bottom, text="Final", font=("Roboto", 12, "bold")).grid(
            row=1, column=4, sticky="w", padx=12
        )

        self.player_entries = {}
        self.player_labels = {}
        self.player_final_labels = {}
        for idx, letra in enumerate(("A", "B", "C", "D"), start=2):
            ctk.CTkLabel(bottom, text=letra, font=("Roboto", 12, "bold")).grid(
                row=idx, column=0, sticky="w", padx=12, pady=4
            )
            lbl = ctk.CTkLabel(bottom, text="-", font=("Roboto", 12))
            lbl.grid(row=idx, column=1, sticky="w", padx=12, pady=4)
            entry_points = ctk.CTkEntry(bottom, placeholder_text="0")
            entry_penalty = ctk.CTkEntry(bottom, placeholder_text="0")
            entry_points.grid(row=idx, column=2, sticky="ew", padx=12, pady=4)
            entry_penalty.grid(row=idx, column=3, sticky="ew", padx=12, pady=4)
            final_label = ctk.CTkLabel(bottom, text="0", font=("Roboto", 12, "bold"))
            final_label.grid(row=idx, column=4, sticky="w", padx=12, pady=4)
            self.player_entries[letra] = (entry_points, entry_penalty)
            self.player_labels[letra] = lbl
            self.player_final_labels[letra] = final_label

            entry_points.bind("<KeyRelease>", lambda e, l=letra: self._update_final_points(l))
            entry_penalty.bind("<KeyRelease>", lambda e, l=letra: self._update_final_points(l))

        winner_row = 6
        ctk.CTkLabel(bottom, text="Pareja ganadora:", font=("Roboto", 12, "bold")).grid(
            row=winner_row, column=0, sticky="w", padx=12, pady=(4, 4)
        )
        self.winner_combo = ctk.CTkComboBox(
            bottom,
            values=["AC", "BD"],
            variable=self.winner_var,
            width=100,
        )
        self.winner_combo.grid(row=winner_row, column=1, sticky="w", padx=12, pady=(4, 4))

        self.btn_save = ctk.CTkButton(
            bottom,
            text="Guardar resultado",
            height=34,
            command=self._on_save,
        )
        self.btn_save.grid(row=7, column=0, columnspan=5, padx=12, pady=(10, 12), sticky="ew")

        # ✅ Ajuste adicional (opcional)
        penalty = ctk.CTkFrame(body, corner_radius=12)
        penalty.pack(fill="x", padx=16, pady=(0, 16))

        penalty.grid_columnconfigure(0, weight=1)
        penalty.grid_columnconfigure(1, weight=1)
        penalty.grid_columnconfigure(2, weight=2)
        penalty.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            penalty,
            text="Ajuste adicional individual (opcional)",
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
            for entry_points, entry_penalty in self.player_entries.values():
                entry_points.delete(0, "end")
                entry_penalty.delete(0, "end")
            for label in self.player_final_labels.values():
                label.configure(text="0")
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
        self.player_labels["A"].configure(text=fmt("A", mesa_data["A"]))
        self.player_labels["B"].configure(text=fmt("B", mesa_data["B"]))
        self.player_labels["C"].configure(text=fmt("C", mesa_data["C"]))
        self.player_labels["D"].configure(text=fmt("D", mesa_data["D"]))

        status = storage.get_table_status(rnd, mesa_num)
        if status == "finished":
            self.status_badge.configure(text="Terminado", fg_color="#b3261e")
        else:
            self.status_badge.configure(text="Jugando", fg_color="#2e7d32")

        result = storage.get_table_player_scores(rnd, mesa_num)
        for entry_points, entry_penalty in self.player_entries.values():
            entry_points.delete(0, "end")
            entry_penalty.delete(0, "end")
        for label in self.player_final_labels.values():
            label.configure(text="0")
        self.winner_var.set("AC")
        for row in result:
            entries = self.player_entries.get(row["letra"])
            if entries:
                entry_points, entry_penalty = entries
                entry_points.insert(0, str(row["base_points"]))
                entry_penalty.insert(0, str(row["penalty_points"]))
                self.player_final_labels[row["letra"]].configure(text=str(row["final_points"]))
                self.winner_var.set(row.get("winner_pair", "AC"))

    def _on_save(self):
        rnd = self._get_round_number()
        mesa_num = self._get_mesa_number()

        if mesa_num <= 0:
            messagebox.showerror("Error", "Selecciona una mesa válida.")
            return

        try:
            player_points = {}
            for letra, (entry_points, entry_penalty) in self.player_entries.items():
                player_points[letra] = {
                    "base_points": int(entry_points.get().strip() or "0"),
                    "penalty_points": int(entry_penalty.get().strip() or "0"),
                }
        except ValueError:
            messagebox.showerror("Error", "Los puntos y penalidades deben ser enteros.")
            return

        winner_pair = self.winner_var.get().strip().upper()
        ok, msg = tournament.save_table_player_scores(rnd, mesa_num, player_points, winner_pair)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        messagebox.showinfo("Listo", msg)
        self._refresh_table_detail()

    def _update_final_points(self, letra: str):
        entries = self.player_entries.get(letra)
        if not entries:
            return
        entry_points, entry_penalty = entries
        try:
            base_points = int(entry_points.get().strip() or "0")
            penalty_points = int(entry_penalty.get().strip() or "0")
        except ValueError:
            self.player_final_labels[letra].configure(text="0")
            return
        if base_points < 0 or penalty_points < 0:
            self.player_final_labels[letra].configure(text="0")
            return
        final_points = max(0, base_points - penalty_points)
        self.player_final_labels[letra].configure(text=str(final_points))

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
