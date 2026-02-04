# core/round_assignment_sheet.py
#
# Genera PDF de asignación "ID / Mesa" por ronda (para pegar en el club).

import os
from typing import Tuple

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from core import storage


DEFAULT_TOURNAMENT_TITLE = "Torneo de Dominó"


def generate_round_assignment_sheet(
    round_number: int,
    output_dir: str = "hojas",
    tournament_title: str | None = None,
) -> Tuple[str, str]:
    """
    Genera PDF con listado ID | Mesa en columnas repetidas.
    Devuelve (ruta_absoluta_pdf, carpeta_salida).
    """
    seats = storage.get_round_seat_list(round_number)
    if not seats:
        raise ValueError("No hay mesas asignadas para esa ronda.")

    if tournament_title is None:
        tournament_title = DEFAULT_TOURNAMENT_TITLE

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"ronda{round_number}_asignacion.pdf")

    _draw_round_assignment_pdf(
        filename=filename,
        round_number=round_number,
        tournament_title=tournament_title,
        seats=seats,
    )

    return os.path.abspath(filename), os.path.abspath(output_dir)


def _draw_round_assignment_pdf(
    filename: str,
    round_number: int,
    tournament_title: str,
    seats: list[dict],
):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    margin_x = 36
    margin_y = 40
    usable_width = width - 2 * margin_x

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - margin_y + 8, tournament_title)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width / 2.0, height - margin_y - 10, f"RONDA: {round_number}")

    # Preparar data (ordenada por ID)
    rows = sorted(seats, key=lambda r: r["jugador_id"])

    # Configuración de columnas
    columns = 4
    col_width = usable_width / columns
    header_y = height - margin_y - 36
    row_height = 16
    max_rows_per_col = int((header_y - margin_y) / row_height) - 1
    if max_rows_per_col < 10:
        max_rows_per_col = 10

    def draw_headers():
        c.setFont("Helvetica-Bold", 10)
        for col in range(columns):
            x = margin_x + (col * col_width)
            c.drawString(x, header_y, "ID")
            c.drawString(x + 36, header_y, "Mesa")

    draw_headers()
    c.setFont("Helvetica", 10)

    col = 0
    row_in_col = 0
    y = header_y - row_height

    for item in rows:
        x = margin_x + (col * col_width)
        c.drawString(x, y, str(item["jugador_id"]))
        c.drawString(x + 36, y, str(item["mesa"]))

        row_in_col += 1
        y -= row_height

        if row_in_col >= max_rows_per_col:
            col += 1
            row_in_col = 0
            y = header_y - row_height

            if col >= columns:
                c.showPage()
                col = 0
                y = header_y - row_height
                draw_headers()
                c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
