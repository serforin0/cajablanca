# ui/main_window.py
import customtkinter as ctk

from ui.players_view import PlayersView
from ui.tables_view import TablesView

from ui.score_capture_view import ScoreCaptureView
from ui.ranking_view import RankingView


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Gestor de Torneos de Dominó")
        self.geometry("1100x650")

        # Colores para el menú
        self.MENU_BG = "#1e272e"
        self.MENU_BTN_NORMAL = "#1f538d"
        self.MENU_BTN_HOVER = "#14375e"
        self.MENU_BTN_ACTIVE = "#2196f3"
        self.MENU_BTN_ACTIVE_HOVER = "#1976d2"

        # --------- LAYOUT PRINCIPAL ----------
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=16,
            fg_color=self.MENU_BG,
        )
        self.sidebar.pack(side="left", fill="y", padx=12, pady=12)

        self.content_outer = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color="#11171b",
        )
        self.content_outer.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        self.content = ctk.CTkFrame(
            self.content_outer,
            corner_radius=14,
            fg_color="#171f24",
        )
        self.content.pack(fill="both", expand=True, padx=18, pady=18)

        # --------- MENÚ LATERAL ----------
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="Torneo de Dominó",
            font=("Roboto", 22, "bold"),
        )
        title_label.pack(pady=(18, 24), padx=16, anchor="w")

        self.menu_buttons: dict[str, ctk.CTkButton] = {}

        self.btn_torneo = ctk.CTkButton(
            self.sidebar,
            text="Configuración torneo",
            command=self.show_torneo_config,
            fg_color=self.MENU_BTN_NORMAL,
            hover_color=self.MENU_BTN_HOVER,
        )
        self.btn_torneo.pack(fill="x", padx=16, pady=6)
        self.menu_buttons["torneo"] = self.btn_torneo

        self.btn_jugadores = ctk.CTkButton(
            self.sidebar,
            text="Jugadores / Inscripción",
            command=self.show_players_view,
            fg_color=self.MENU_BTN_NORMAL,
            hover_color=self.MENU_BTN_HOVER,
        )
        self.btn_jugadores.pack(fill="x", padx=16, pady=6)
        self.menu_buttons["jugadores"] = self.btn_jugadores

        self.btn_partidas = ctk.CTkButton(
            self.sidebar,
            text="Mesas / Rondas",
            command=self.show_tables_view,
            fg_color=self.MENU_BTN_NORMAL,
            hover_color=self.MENU_BTN_HOVER,
        )
        self.btn_partidas.pack(fill="x", padx=16, pady=6)
        self.menu_buttons["mesas"] = self.btn_partidas

        self.btn_captura = ctk.CTkButton(
            self.sidebar,
            text="Captura de puntos",
            command=self.show_score_capture_view,
            fg_color=self.MENU_BTN_NORMAL,
            hover_color=self.MENU_BTN_HOVER,
        )
        self.btn_captura.pack(fill="x", padx=16, pady=6)
        self.menu_buttons["captura"] = self.btn_captura

        self.btn_ranking = ctk.CTkButton(
            self.sidebar,
            text="Ranking",
            command=self.show_ranking_view,
            fg_color=self.MENU_BTN_NORMAL,
            hover_color=self.MENU_BTN_HOVER,
        )
        self.btn_ranking.pack(fill="x", padx=16, pady=6)
        self.menu_buttons["ranking"] = self.btn_ranking

        self.btn_clasificacion = ctk.CTkButton(
            self.sidebar,
            text="Clasificación",
            command=self.show_ranking_view,
            fg_color=self.MENU_BTN_NORMAL,
            hover_color=self.MENU_BTN_HOVER,
        )
        self.btn_clasificacion.pack(fill="x", padx=16, pady=6)
        self.menu_buttons["clasificacion"] = self.btn_clasificacion

        # Vista inicial
        self._set_active_menu("jugadores")
        self.show_players_view()

    # --------- UTILIDAD: MENÚ ACTIVO ----------

    def _set_active_menu(self, key: str):
        for name, btn in self.menu_buttons.items():
            if name == key:
                btn.configure(fg_color=self.MENU_BTN_ACTIVE, hover_color=self.MENU_BTN_ACTIVE_HOVER)
            else:
                btn.configure(fg_color=self.MENU_BTN_NORMAL, hover_color=self.MENU_BTN_HOVER)

    # --------- CAMBIO DE VISTAS ----------

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_torneo_config(self):
        self._set_active_menu("torneo")
        self.clear_content()

        inner = ctk.CTkFrame(self.content, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        title = ctk.CTkLabel(inner, text="Configuración del Torneo", font=("Roboto", 20, "bold"))
        title.pack(anchor="w", pady=(0, 16))

        info = ctk.CTkLabel(inner, text="(Pendiente de implementar)", font=("Roboto", 14))
        info.pack(anchor="w")

    def show_players_view(self):
        self._set_active_menu("jugadores")
        self.clear_content()

        view = PlayersView(self.content)
        view.pack(fill="both", expand=True, padx=24, pady=24)

    def show_tables_view(self):
        self._set_active_menu("mesas")
        self.clear_content()

        # TablesView actualmente recibe SOLO (master) en tu código
        view = TablesView(self.content)
        view.pack(fill="both", expand=True, padx=24, pady=24)

    def show_score_capture_view(self):
        self._set_active_menu("captura")
        self.clear_content()

        # ScoreCaptureView debe ser (master) SIN tournament
        view = ScoreCaptureView(self.content)
        view.pack(fill="both", expand=True, padx=24, pady=24)

    def show_ranking_view(self):
        self._set_active_menu("ranking")
        self.clear_content()

        # RankingView debe ser (master) SIN tournament
        view = RankingView(self.content)
        view.pack(fill="both", expand=True, padx=24, pady=24)

    def show_standings_view(self):
        self.show_ranking_view()
