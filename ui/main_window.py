# ui/main_window.py
import customtkinter as ctk

from ui.players_view import PlayersView
from ui.tables_view import TablesView


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Gestor de Torneos de Dominó")
        self.geometry("1100x650")

        # --------- LAYOUT BÁSICO ----------
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(self)
        self.content.pack(side="right", fill="both", expand=True)

        title_label = ctk.CTkLabel(
            self.sidebar,
            text="Torneo de Dominó",
            font=("Roboto", 20, "bold"),
        )
        title_label.pack(pady=20)

        self.btn_torneo = ctk.CTkButton(
            self.sidebar,
            text="Configuración torneo",
            command=self.show_torneo_config,
        )
        self.btn_torneo.pack(pady=10, fill="x", padx=10)

        self.btn_jugadores = ctk.CTkButton(
            self.sidebar,
            text="Jugadores / Inscripción",
            command=self.show_players_view,
        )
        self.btn_jugadores.pack(pady=10, fill="x", padx=10)

        self.btn_partidas = ctk.CTkButton(
            self.sidebar,
            text="Mesas / Rondas",
            command=self.show_tables_view,
        )
        self.btn_partidas.pack(pady=10, fill="x", padx=10)

        self.btn_clasificacion = ctk.CTkButton(
            self.sidebar,
            text="Clasificación",
            command=self.show_standings_view,
        )
        self.btn_clasificacion.pack(pady=10, fill="x", padx=10)

        self.current_view = None
        self.show_players_view()  # Pantalla inicial: inscripción

    # --------- CAMBIO DE VISTAS ----------

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_torneo_config(self):
        self.clear_content()
        label = ctk.CTkLabel(
            self.content,
            text="Configuración del Torneo (pendiente de implementar)",
            font=("Roboto", 18, "bold"),
        )
        label.pack(pady=20)

    def show_players_view(self):
        self.clear_content()
        view = PlayersView(self.content)
        view.pack(fill="both", expand=True)

    def show_tables_view(self):
        self.clear_content()
        view = TablesView(self.content)
        view.pack(fill="both", expand=True)

    def show_standings_view(self):
        self.clear_content()
        label = ctk.CTkLabel(
            self.content,
            text="Clasificación y Estadísticas (pendiente de implementar)",
            font=("Roboto", 18, "bold"),
        )
        label.pack(pady=20)
