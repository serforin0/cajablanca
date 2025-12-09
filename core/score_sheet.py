# core/score_sheet.py
import os
from typing import Tuple

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core import storage


def generate_score_sheets_for_round(
    round_number: int,
    output_dir: str = "hojas",
) -> Tuple[int, str]:
    """
    Genera una hoja de puntuación en PDF por cada mesa de la ronda.
    Devuelve (cantidad_de_hojas, carpeta_salida)
    """
    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        raise ValueError("No hay mesas asignadas para esa ronda.")

    os.makedirs(output_dir, exist_ok=True)

    for mesa in mesas:
        mesa_num = mesa["mesa"]
        filename = os.path.join(
            output_dir,
            f"ronda{round_number}_mesa{mesa_num:02d}.pdf",
        )
        _create_sheet_for_table(round_number, mesa, filename)

    return len(mesas), os.path.abspath(output_dir)


def generate_score_sheet_for_table(
    round_number: int,
    mesa_number: int,
    output_dir: str = "hojas",
) -> str:
    """
    Genera una hoja de puntuación en PDF solo para UNA mesa.
    Devuelve la ruta absoluta del archivo.
    """
    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        raise ValueError("No hay mesas asignadas para esa ronda.")

    mesa = next((m for m in mesas if m["mesa"] == mesa_number), None)
    if mesa is None:
        raise ValueError(
            f"No se encontró la mesa {mesa_number} en la ronda {round_number}."
        )

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(
        output_dir,
        f"ronda{round_number}_mesa{mesa_number:02d}.pdf",
    )
    _create_sheet_for_table(round_number, mesa, filename)
    return os.path.abspath(filename)


def _create_sheet_for_table(round_number: int, mesa: dict, filename: str):
    """
    Crea un PDF para una mesa:
    - Muestra los 4 jugadores con sus letras A/B/C/D
    - Parejas: A-C y B-D
    - Tabla para anotar puntos
    - Campos G, P, E, R vacíos
    """
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    margin = 40

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, "Torneo de Dominó")
    c.setFont("Helvetica", 12)
    c.drawString(margin, height - margin - 20, f"Ronda: {round_number}")
    c.drawString(margin + 200, height - margin - 20, f"Mesa: {mesa['mesa']}")

    # Helper
    def full_name(p):
        return f"{p['nombre']} {p['apellido']}"

    # Jugadores
    y_top = height - margin - 60
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_top, "Jugadores (posición en la mesa):")

    c.setFont("Helvetica", 11)
    c.drawString(margin, y_top - 20, f"A (Norte): {full_name(mesa['A'])}")
    c.drawString(margin, y_top - 35, f"C (Sur):   {full_name(mesa['C'])}")
    c.drawString(
        margin + 260,
        y_top - 20,
        f"B (Este): {full_name(mesa['B'])}",
    )
    c.drawString(
        margin + 260,
        y_top - 35,
        f"D (Oeste): {full_name(mesa['D'])}",
    )

    # Parejas
    y_pairs = y_top - 70
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_pairs, "Pareja A-C:")
    c.setFont("Helvetica", 11)
    c.drawString(
        margin + 90,
        y_pairs,
        f"{full_name(mesa['A'])} / {full_name(mesa['C'])}",
    )

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_pairs - 18, "Pareja B-D:")
    c.setFont("Helvetica", 11)
    c.drawString(
        margin + 90,
        y_pairs - 18,
        f"{full_name(mesa['B'])} / {full_name(mesa['D'])}",
    )

    # Campos G, P, E, R
    y_stats = y_pairs - 50
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y_stats, "G (Ganadas): _______")
    c.drawString(margin + 150, y_stats, "P (Puntos): _______")
    c.drawString(margin + 300, y_stats, "E (Efectividad): _______")
    c.drawString(margin + 470, y_stats, "R (Ranking): _______")

    # Tabla de manos
    y_table_top = y_stats - 40
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y_table_top, "Mano")
    c.drawString(margin + 60, y_table_top, "Puntos Pareja A-C")
    c.drawString(margin + 220, y_table_top, "Puntos Pareja B-D")
    c.drawString(margin + 380, y_table_top, "Notas")

    num_rows = 12
    y = y_table_top - 10
    c.setFont("Helvetica", 10)
    for i in range(1, num_rows + 1):
        c.drawString(margin + 5, y - 12, f"{i}")
        c.line(margin, y - 15, width - margin, y - 15)
        y -= 20

    # Totales
    y_total = y - 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(
        margin,
        y_total,
        "Total Puntos Pareja A-C: __________",
    )
    c.drawString(
        margin + 260,
        y_total,
        "Total Puntos Pareja B-D: __________",
    )

    c.showPage()
    c.save()
