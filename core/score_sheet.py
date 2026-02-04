# core/score_sheet.py
#
# Genera hojas de puntuación por mesa, formateadas como
# la hoja de torneo (dos bloques por página, tamaño carta).
#
# Requiere:  pip install reportlab

import os
from typing import Tuple

from reportlab.lib.pagesizes import letter  # 8.5 x 11 pulgadas
from reportlab.pdfgen import canvas

from core import storage


# Título por defecto del torneo.
# Puedes cambiarlo aquí o, si quieres, exponerlo luego en una pantalla
DEFAULT_TOURNAMENT_TITLE = "Torneo de Dominó"


def generate_score_sheets_for_round(
    round_number: int,
    output_dir: str = "hojas",
    tournament_title: str | None = None,
    footer_text: str | None = None,
) -> Tuple[int, str]:
    """
    Genera una hoja de puntuación en PDF por cada mesa de la ronda.
    Cada hoja es tamaño carta, con DOS bloques (izq/der) para la misma mesa.
    Devuelve (cantidad_de_hojas, carpeta_salida).
    """
    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        raise ValueError("No hay mesas asignadas para esa ronda.")

    if tournament_title is None:
        tournament_title = DEFAULT_TOURNAMENT_TITLE

    os.makedirs(output_dir, exist_ok=True)

    for mesa in mesas:
        mesa_num = mesa["mesa"]
        filename = os.path.join(
            output_dir,
            f"ronda{round_number}_mesa{mesa_num:02d}.pdf",
        )
        _create_sheet_for_table(
            round_number,
            mesa,
            filename,
            tournament_title,
            footer_text=footer_text,
        )

    return len(mesas), os.path.abspath(output_dir)


def generate_score_sheet_for_table(
    round_number: int,
    mesa_number: int,
    output_dir: str = "hojas",
    tournament_title: str | None = None,
    footer_text: str | None = None,
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

    if tournament_title is None:
        tournament_title = DEFAULT_TOURNAMENT_TITLE

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(
        output_dir,
        f"ronda{round_number}_mesa{mesa_number:02d}.pdf",
    )
    _create_sheet_for_table(
        round_number,
        mesa,
        filename,
        tournament_title,
        footer_text=footer_text,
    )
    return os.path.abspath(filename)


# ======================================================================
# DIBUJO DEL PDF
# ======================================================================

def _create_sheet_for_table(
    round_number: int,
    mesa: dict,
    filename: str,
    tournament_title: str,
    footer_text: str | None = None,
):
    """
    Crea un PDF tamaño carta (8.5 x 11") para una mesa.
    La página tiene DOS bloques (izquierda y derecha) iguales,
    cada uno con:
      - Título del torneo
      - Encabezado tipo: ID | Jugador | G | P | E | Rank
      - 4 filas (A, B, C, D) con ID = <id> <letra>
      - Tabla para anotar manos y totales (Pareja A-C vs Pareja B-D)
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    margin = 32  # ~0.44"
    usable_width = width - 2 * margin
    # Dos bloques: izq/der, separados por un margen interior
    inner_margin = 24
    block_width = (usable_width - inner_margin) / 2.0

    # Coordenadas X de cada bloque
    left_x = margin
    right_x = margin + block_width + inner_margin

    # Altura útil del bloque (lo usamos solo para orientarnos)
    block_height = height - 2 * margin

    # Título general centrado arriba
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - margin + 4, tournament_title)

    # Llamamos a la función que dibuja un bloque completo
    top_y = height - margin - 14  # un poco debajo del título

    stats_map = storage.get_player_stats_map()

    _draw_block(
        c=c,
        x=left_x,
        y_top=top_y,
        block_width=block_width,
        round_number=round_number,
        mesa=mesa,
        stats_map=stats_map,
    )

    _draw_block(
        c=c,
        x=right_x,
        y_top=top_y,
        block_width=block_width,
        round_number=round_number,
        mesa=mesa,
        stats_map=stats_map,
    )

    if footer_text:
        c.setFont("Helvetica", 9)
        c.drawString(margin, margin - 4, footer_text)

    c.showPage()
    c.save()


def _draw_block(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    block_width: float,
    round_number: int,
    mesa: dict,
    stats_map: dict[int, dict],
):
    """
    Dibuja UN bloque (la mitad izquierda o derecha de la página).
    """

    # Helper para nombre completo
    def full_name(p):
        return f"{p['nombre']} {p['apellido']}"

    # -----------------------------------------------------------
    # 1) Encabezado del bloque: info de ronda y mesa
    # -----------------------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y_top, f"Ronda: {round_number}")
    c.drawRightString(x + block_width, y_top, f"Mesa: {mesa['mesa']}")

    # -----------------------------------------------------------
    # 2) Tabla de jugadores (estilo: ID | Jugador | G | P | E | Rank)
    # -----------------------------------------------------------
    header_y = y_top - 18
    row_height = 16

    # Posiciones de columnas dentro del bloque
    id_x = x + 2
    jugador_x = x + 44
    g_x = x + block_width - 92
    p_x = g_x + 18
    e_x = p_x + 22
    r_x = e_x + 30

    # Encabezados
    c.setFont("Helvetica-Bold", 9)
    c.drawString(id_x, header_y, "ID")
    c.drawString(jugador_x, header_y, "Jugador")
    c.drawString(g_x, header_y, "G")
    c.drawString(p_x, header_y, "P")
    c.drawString(e_x, header_y, "E")
    c.drawString(r_x, header_y, "Rank")

    # Filas: A, B, C, D
    c.setFont("Helvetica", 9)
    players_order = [
        ("A", mesa["A"]),
        ("B", mesa["B"]),
        ("C", mesa["C"]),
        ("D", mesa["D"]),
    ]

    y = header_y - row_height
    for letter, player in players_order:
        player_id_text = f"{player['id']} {letter}"  # EJ: "45 C"
        c.drawString(id_x, y, player_id_text)
        c.drawString(jugador_x, y, full_name(player))
        if round_number > 1:
            stats = stats_map.get(player["id"], {})
            c.drawRightString(g_x + 10, y, str(stats.get("G", "")))
            c.drawRightString(p_x + 14, y, str(stats.get("P", "")))
            c.drawRightString(e_x + 24, y, str(stats.get("E", "")))
            c.drawRightString(r_x + 24, y, str(stats.get("R", "")))
        y -= row_height

    # Tabla (líneas finas) para jugadores
    table_top = header_y + 6
    table_bottom = y + 6
    c.setLineWidth(0.6)
    c.rect(x, table_bottom, block_width, table_top - table_bottom)
    for i in range(1, 5):
        c.line(x, table_top - (i * row_height), x + block_width, table_top - (i * row_height))
    for col_x in (jugador_x - 6, g_x - 6, p_x - 6, e_x - 6, r_x - 6):
        c.line(col_x, table_bottom, col_x, table_top)

    # -----------------------------------------------------------
    # 3) Tabla de puntos por mano (Pareja A-C vs B-D)
    # -----------------------------------------------------------
    # Títulos pareja
    y_pairs = table_bottom - 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y_pairs, "Pareja A-C:")
    c.setFont("Helvetica", 9)
    c.drawString(
        x + 70,
        y_pairs,
        f"{full_name(mesa['A'])} / {full_name(mesa['C'])}",
    )

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y_pairs - 12, "Pareja B-D:")
    c.setFont("Helvetica", 9)
    c.drawString(
        x + 70,
        y_pairs - 12,
        f"{full_name(mesa['B'])} / {full_name(mesa['D'])}",
    )

    # Campos G, P, E, R (totales de la pareja) – opcional
    y_stats = y_pairs - 30
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x, y_stats, "G (Ganadas): _______")
    c.drawString(x + 108, y_stats, "P (Puntos): _______")
    c.drawString(x + 210, y_stats, "E (Efectividad): _______")
    # Rank general lo suelen poner en otra hoja, pero dejamos el espacio
    # por si acaso quieren anotarlo aquí.
    # (Si no cabe bien por el ancho del bloque, puedes borrar esta línea)

    # -----------------------------------------------------------
    # 4) Tabla de manos
    # -----------------------------------------------------------
    y_table_top = y_stats - 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y_table_top, "Mano")
    c.drawString(x + 36, y_table_top, "Puntos A-C")
    c.drawString(x + 118, y_table_top, "Puntos B-D")
    c.drawString(x + 200, y_table_top, "Notas")

    num_rows = 12
    y_row = y_table_top - 10
    c.setFont("Helvetica", 8.5)

    table_right_x = x + block_width
    table_left_x = x
    for i in range(1, num_rows + 1):
        c.drawString(x + 2, y_row - 10, str(i))
        c.line(table_left_x, y_row - 12, table_right_x, y_row - 12)
        y_row -= 16
    c.line(table_left_x, y_table_top - 4, table_right_x, y_table_top - 4)

    # Totales al final
    y_total = y_row - 8
    c.setFont("Helvetica-Bold", 9)
    c.drawString(
        x,
        y_total,
        "Total Puntos Pareja A-C: __________",
    )
    c.drawString(
        x,
        y_total - 14,
        "Total Puntos Pareja B-D: __________",
    )
