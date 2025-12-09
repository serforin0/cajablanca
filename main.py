# main.py
import customtkinter as ctk

from core import storage
from ui.main_window import MainWindow


def main():
    # Inicializar BD
    storage.init_db()

    # Estilos
    ctk.set_appearance_mode("dark")      # "light" / "dark"
    ctk.set_default_color_theme("blue")  # puedes cambiar el tema

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
