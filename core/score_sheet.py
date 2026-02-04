# core/score_sheet.py
#
# Genera hoja de puntuación por mesa (tamaño carta, estilo torneo real).
# Logos deben almacenarse en: assets/logos/

from __future__ import annotations

import os
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from core import storage


DEFAULT_TOURNAMENT_TITLE = "Torneo de Dominó"
VALID_TOURNAMENT_TYPES = {"individual", "equipo", "seleccion_12"}


def generate_score_sheet_for_table(
    round_number: int,
    mesa_number: int,
    output_path: str,
    tournament_title: str,
    tournament_type: str,
    logo_path: str | None = None,
    footer_text: str | None = None,
    players: list[dict] | None = None,
    player_stats: dict[int, dict] | None = None,
) -> str:
    output_dir: str = "hojas",
    tournament_title: str | None = None,
    footer_text: str | None = None,
) -> Tuple[int, str]:
    """
    Genera una hoja (1 página por mesa) con el layout de torneo.
    output_path incluye el nombre del archivo final.
    """
    if tournament_type not in VALID_TOURNAMENT_TYPES:
        tournament_type = "individual"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if players is None:
        mesa = _get_mesa(round_number, mesa_number)
        players = _mesa_to_players(mesa)

    if player_stats is None:
        player_stats = storage.get_player_stats_map()

    _draw_score_sheet_pdf(
        filename=output_path,
        tournament_title=tournament_title or DEFAULT_TOURNAMENT_TITLE,
        tournament_type=tournament_type,
        logo_path=logo_path,
        round_number=round_number,
        mesa_number=mesa_number,
        players=players,
        player_stats=player_stats,
        footer_text=footer_text,
    )

    return os.path.abspath(output_path)


def generate_score_sheets_for_round(
    round_number: int,
    output_dir: str,
    tournament_title: str,
    tournament_type: str,
    logo_path: str | None = None,
    footer_text: str | None = None,
) -> tuple[int, str]:
    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        raise ValueError("No hay mesas asignadas para esa ronda.")

    os.makedirs(output_dir, exist_ok=True)
    count = 0
    for mesa in mesas:
        mesa_num = mesa["mesa"]
        filename = os.path.join(output_dir, f"ronda{round_number}_mesa{mesa_num:02d}.pdf")
        generate_score_sheet_for_table(
            round_number=round_number,
            mesa_number=mesa_num,
            output_path=filename,
            tournament_title=tournament_title,
            tournament_type=tournament_type,
            logo_path=logo_path,
            footer_text=footer_text,
            players=_mesa_to_players(mesa),
        )
        count += 1
        _create_sheet_for_table(
            round_number,
            mesa,
            filename,
            tournament_title,
            footer_text=footer_text,
        )

    return count, os.path.abspath(output_dir)


def generate_sample_score_sheet(output_path: str = "hojas/sample_hoja_mesa.pdf") -> str:
def generate_score_sheet_for_table(
    round_number: int,
    mesa_number: int,
    output_dir: str = "hojas",
    tournament_title: str | None = None,
    footer_text: str | None = None,
) -> str:
    """
    Genera un PDF de muestra para validar el layout.
    """
    sample_players = [
        {"seat_letter": "A", "player_id": 12, "nombre": "Juan", "apellido": "Perez", "team_name": "La Vega"},
        {"seat_letter": "B", "player_id": 27, "nombre": "Luis", "apellido": "Rodriguez", "team_name": "Santiago"},
        {"seat_letter": "C", "player_id": 45, "nombre": "Carlos", "apellido": "Gomez", "team_name": "La Vega"},
        {"seat_letter": "D", "player_id": 88, "nombre": "Miguel", "apellido": "Diaz", "team_name": "Santiago"},
    ]

    return generate_score_sheet_for_table(
        round_number=1,
        mesa_number=64,
        output_path=output_path,
        tournament_title="1er Torneo Inter Clubes La Vega",
        tournament_type="equipo",
        logo_path=None,
        footer_text="Elaborado por: Ing. Carolina De Jesus",
        players=sample_players,
        player_stats=None,
    )


def _get_mesa(round_number: int, mesa_number: int) -> dict:
    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        raise ValueError("No hay mesas asignadas para esa ronda.")

    mesa = next((m for m in mesas if m["mesa"] == mesa_number), None)
    if mesa is None:
        raise ValueError(f"No se encontró la mesa {mesa_number} en la ronda {round_number}.")
    return mesa


def _mesa_to_players(mesa: dict) -> list[dict]:
    players = []
    for letter in ("A", "B", "C", "D"):
        p = mesa.get(letter)
        if not p:
            continue
        players.append(
            {
                "seat_letter": letter,
                "player_id": p["id"],
                "nombre": p["nombre"],
                "apellido": p["apellido"],
            }
        )
    return players


def _draw_score_sheet_pdf(
    filename: str,
    tournament_title: str,
    tournament_type: str,
    logo_path: str | None,
    round_number: int,
    mesa_number: int,
    players: list[dict],
    player_stats: dict[int, dict],
    footer_text: str | None,
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
    c = canvas.Canvas(filename, pagesize=letter)
    page_w, page_h = letter

    margin_x = 36
    margin_y = 36
    usable_w = page_w - (2 * margin_x)

    title_y = page_h - 36
    c.setFont("Times-Italic", 16)
    c.drawCentredString(page_w / 2, title_y, tournament_title)
    margin = 32  # ~0.44"
    usable_width = width - 2 * margin
    # Dos bloques: izq/der, separados por un margen interior
    inner_margin = 24
    block_width = (usable_width - inner_margin) / 2.0

    _draw_logo(c, logo_path, page_w - margin_x - 90, title_y - 28, 90, 36)

    header_top = title_y - 24
    header_height = 86
    header_bottom = header_top - header_height

    left_block_x = margin_x
    right_block_x = margin_x + (usable_w / 2) + 10
    block_w = (usable_w / 2) - 10

    players_by_seat = {p["seat_letter"]: p for p in players}
    # Título general centrado arriba
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - margin + 4, tournament_title)

    # Llamamos a la función que dibuja un bloque completo
    top_y = height - margin - 14  # un poco debajo del título

    stats_map = storage.get_player_stats_map()

    _draw_player_block(
        c,
        x=left_block_x,
        y_top=header_top,
        width=block_w,
        tournament_type=tournament_type,
        player_top=players_by_seat.get("A"),
        player_bottom=players_by_seat.get("C"),
        player_stats=player_stats,
        round_number=round_number,
        mesa=mesa,
        stats_map=stats_map,
    )
    _draw_player_block(
        c,
        x=right_block_x,
        y_top=header_top,
        width=block_w,
        tournament_type=tournament_type,
        player_top=players_by_seat.get("B"),
        player_bottom=players_by_seat.get("D"),
        player_stats=player_stats,
        round_number=round_number,
    )

    info_y = header_bottom - 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, info_y, f"Ronda: {round_number}")
    c.drawRightString(page_w - margin_x, info_y, f"Mesa: {mesa_number}")

    scoring_top = info_y - 12
    scoring_height = 420
    scoring_bottom = scoring_top - scoring_height

    center_w = 48
    half_w = (usable_w - center_w - 10) / 2
    left_x = margin_x
    center_x = left_x + half_w + 5
    right_x = center_x + center_w + 5

    _draw_scoring_half(c, left_x, scoring_top, half_w, "Puntos Pareja A-C")
    _draw_center_grid(c, center_x, scoring_top, center_w)
    _draw_scoring_half(c, right_x, scoring_top, half_w, "Puntos Pareja B-D")

    if footer_text:
        c.setFont("Helvetica", 9)
        c.drawString(margin_x, margin_y - 6, footer_text)
        mesa=mesa,
        stats_map=stats_map,
    )

    if footer_text:
        c.setFont("Helvetica", 9)
        c.drawString(margin, margin - 4, footer_text)

    c.showPage()
    c.save()


def _draw_logo(c: canvas.Canvas, logo_path: Optional[str], x: float, y: float, w: float, h: float):
    if not logo_path:
        return
    try:
        image = ImageReader(logo_path)
        iw, ih = image.getSize()
        scale = min(w / iw, h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        c.drawImage(image, x + (w - draw_w), y, draw_w, draw_h, mask="auto")
    except Exception:
        return


def _draw_player_block(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    tournament_type: str,
    player_top: dict | None,
    player_bottom: dict | None,
    player_stats: dict[int, dict],
    round_number: int,
    mesa: dict,
    stats_map: dict[int, dict],
):
    row_h = 14
    header_h = 14
    group_h = 12

    group_label = "Individual"
    if tournament_type == "equipo":
        group_label = "Equipo"
    elif tournament_type == "seleccion_12":
        group_label = "Selección"

    def group_value(player: dict | None) -> str:
        if not player:
            return ""
        if tournament_type == "equipo":
            return player.get("team_name", "")
        if tournament_type == "seleccion_12":
            return player.get("seleccion_name", "")
        return "Individual"

    c.setFont("Helvetica", 8.5)
    c.drawString(x, y_top - 10, f"{group_label}: {group_value(player_top)}")

    table_top = y_top - group_h
    table_bottom = table_top - (header_h + (2 * row_h))

    c.setLineWidth(0.6)
    c.rect(x, table_bottom, width, header_h + (2 * row_h))

    col_id = 44
    col_player = width - (col_id + 100)
    col_g = 20
    col_p = 20
    col_e = 20
    col_r = 20

    col_x = [
        x,
        x + col_id,
        x + col_id + col_player,
        x + col_id + col_player + col_g,
        x + col_id + col_player + col_g + col_p,
        x + col_id + col_player + col_g + col_p + col_e,
        x + width,
    ]

    c.setFillColor(colors.lightgrey)
    c.rect(x, table_top - header_h, width, header_h, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.line(x, table_top - header_h, x + width, table_top - header_h)
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

    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 2, table_top - header_h + 3, "ID")
    c.drawString(col_x[1] + 2, table_top - header_h + 3, "Jugador")
    c.drawString(col_x[2] + 4, table_top - header_h + 3, "G")
    c.drawString(col_x[3] + 4, table_top - header_h + 3, "P")
    c.drawString(col_x[4] + 4, table_top - header_h + 3, "E")
    c.drawString(col_x[5] + 2, table_top - header_h + 3, "Rank")

    for cx in col_x[1:-1]:
        c.line(cx, table_bottom, cx, table_top)

    _draw_player_row(
        c, x, table_top - header_h, row_h, col_x, player_top, player_stats, round_number
    )
    _draw_player_row(
        c, x, table_top - header_h - row_h, row_h, col_x, player_bottom, player_stats, round_number
    )

    c.line(x, table_top - header_h - row_h, x + width, table_top - header_h - row_h)
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

    c.setFont("Helvetica", 8.5)
    c.drawString(x, table_bottom - 10, f"{group_label}: {group_value(player_bottom)}")

    table_right_x = x + block_width
    table_left_x = x
    for i in range(1, num_rows + 1):
        c.drawString(x + 2, y_row - 10, str(i))
        c.line(table_left_x, y_row - 12, table_right_x, y_row - 12)
        y_row -= 16
    c.line(table_left_x, y_table_top - 4, table_right_x, y_table_top - 4)

def _draw_player_row(
    c: canvas.Canvas,
    x: float,
    y: float,
    row_h: float,
    col_x: list[float],
    player: dict | None,
    player_stats: dict[int, dict],
    round_number: int,
):
    c.setFont("Helvetica", 8.5)
    if not player:
        return

    pid = player.get("player_id")
    seat = player.get("seat_letter", "")
    full_name = f"{player.get('nombre', '')} {player.get('apellido', '')}".strip()
    c.drawString(x + 2, y - row_h + 4, f"{pid} {seat}".strip())
    c.drawString(col_x[1] + 2, y - row_h + 4, full_name)

    if round_number == 1:
        return

    stats = player_stats.get(pid, {})
    c.drawRightString(col_x[3] - 2, y - row_h + 4, str(stats.get("G", "")))
    c.drawRightString(col_x[4] - 2, y - row_h + 4, str(stats.get("P", "")))
    c.drawRightString(col_x[5] - 2, y - row_h + 4, str(stats.get("E", "")))
    c.drawRightString(col_x[6] - 2, y - row_h + 4, str(stats.get("R", "")))


def _draw_scoring_half(c: canvas.Canvas, x: float, y_top: float, width: float, title: str):
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y_top, title)

    table_top = y_top - 12
    tarjeta_w = 70
    writing_x = x + tarjeta_w + 6
    writing_w = width - tarjeta_w - 6
    writing_h = 320

    _draw_tarjeta_table(c, x, table_top, tarjeta_w)

    c.setLineWidth(0.6)
    c.rect(writing_x, table_top - writing_h, writing_w, writing_h)
    line_count = 10
    line_spacing = writing_h / line_count
    for i in range(1, line_count):
        y = table_top - (i * line_spacing)
        c.setStrokeColor(colors.lightgrey)
        c.line(writing_x, y, writing_x + writing_w, y)
    c.setStrokeColor(colors.black)

    total_y = table_top - writing_h - 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, total_y, "Total Puntos:")
    c.line(x + 70, total_y - 2, x + width - 6, total_y - 2)


def _draw_center_grid(c: canvas.Canvas, x: float, y_top: float, width: float):
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + width / 2, y_top, "Tarjeta")

    table_top = y_top - 12
    row_h = 14
    rows = ["Negra", "Roja", "Amarilla", "Marron"]
    c.setLineWidth(0.6)
    c.rect(x, table_top - (row_h * (len(rows) + 1)), width, row_h * (len(rows) + 1))
    c.line(x, table_top - row_h, x + width, table_top - row_h)

    for i, label in enumerate(rows, start=1):
        y = table_top - (i * row_h)
        c.line(x, y - row_h, x + width, y - row_h)
        c.setFont("Helvetica", 8)
        c.drawString(x + 2, y - row_h + 4, label)
        c.drawRightString(x + width - 2, y - row_h + 4, "0")


def _draw_tarjeta_table(c: canvas.Canvas, x: float, y_top: float, width: float):
    row_h = 14
    rows = ["Tarjeta", "Negra", "Roja", "Amarilla", "Marron"]
    c.setLineWidth(0.6)
    c.rect(x, y_top - (row_h * len(rows)), width, row_h * len(rows))
    c.line(x, y_top - row_h, x + width, y_top - row_h)
    c.line(x + (width * 0.6), y_top - row_h, x + (width * 0.6), y_top - (row_h * len(rows)))

    for i, label in enumerate(rows):
        y = y_top - (i * row_h)
        if i == 0:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(x + 2, y - row_h + 4, label)
        else:
            c.setFont("Helvetica", 8)
            c.drawString(x + 2, y - row_h + 4, label)
            c.drawRightString(x + width - 2, y - row_h + 4, "0")
