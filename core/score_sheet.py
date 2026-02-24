# core/score_sheet.py
#
# Genera hoja de puntuación por mesa (tamaño carta, estilo torneo real).
# Logos deben almacenarse en: assets/logos/

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

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
        # Mapa {player_id: {G,P,E,rank}}
        try:
            player_stats = storage.get_player_stats_map()
        except Exception:
            player_stats = {}

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
) -> Tuple[int, str]:
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
            player_stats=None,
        )
        count += 1

    return count, os.path.abspath(output_dir)


def generate_sample_score_sheet(output_path: str = "hojas/sample_hoja_mesa.pdf") -> str:
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
    players: list[dict] = []
    for letter in ("A", "B", "C", "D"):
        p = mesa.get(letter)
        if not p:
            continue
        players.append(
            {
                "seat_letter": letter,
                "player_id": p["id"],
                "nombre": p.get("nombre", ""),
                "apellido": p.get("apellido", ""),
                # opcional:
                "team_name": p.get("team_name", ""),
                "seleccion_name": p.get("seleccion_name", ""),
            }
        )
    return players


# ======================================================================
# DIBUJO DEL PDF
# ======================================================================

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
):
    c = canvas.Canvas(filename, pagesize=letter)
    page_w, page_h = letter

    margin_x = 36
    margin_y = 36
    usable_w = page_w - 2 * margin_x

    # -------------------------
    # Title + logo
    # -------------------------
    title_y = page_h - 36
    c.setFont("Times-Italic", 16)
    c.drawCentredString(page_w / 2, title_y, tournament_title)

    _draw_logo(c, logo_path, page_w - margin_x - 110, title_y - 30, 110, 40)

    # -------------------------
    # Header blocks (A/C left, B/D right)
    # -------------------------
    header_top = title_y - 22
    block_gap = 16
    block_w = (usable_w - block_gap) / 2.0
    left_x = margin_x
    right_x = margin_x + block_w + block_gap

    players_by_seat = {p["seat_letter"]: p for p in players}
    _draw_player_block(
        c,
        x=left_x,
        y_top=header_top,
        width=block_w,
        tournament_type=tournament_type,
        player_top=players_by_seat.get("A"),
        player_bottom=players_by_seat.get("C"),
        player_stats=player_stats,
        round_number=round_number,
    )
    _draw_player_block(
        c,
        x=right_x,
        y_top=header_top,
        width=block_w,
        tournament_type=tournament_type,
        player_top=players_by_seat.get("B"),
        player_bottom=players_by_seat.get("D"),
        player_stats=player_stats,
        round_number=round_number,
    )

    header_bottom = header_top - 86
    info_y = header_bottom - 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, info_y, f"Ronda: {round_number}")
    c.drawRightString(page_w - margin_x, info_y, f"Mesa: {mesa_number}")

    # -------------------------
    # Scoring area
    # -------------------------
    scoring_top = info_y - 14
    scoring_height = 430

    center_w = 54
    half_w = (usable_w - center_w - 10) / 2
    left_half_x = margin_x
    center_x = left_half_x + half_w + 5
    right_half_x = center_x + center_w + 5

    _draw_scoring_half(c, left_half_x, scoring_top, half_w, "Puntos Pareja A-C")
    _draw_center_grid(c, center_x, scoring_top, center_w)
    _draw_scoring_half(c, right_half_x, scoring_top, half_w, "Puntos Pareja B-D")

    # -------------------------
    # Footer
    # -------------------------
    if footer_text:
        c.setFont("Helvetica", 9)
        c.drawString(margin_x, margin_y - 6, footer_text)

    c.showPage()
    c.save()


def _draw_logo(c: canvas.Canvas, logo_path: Optional[str], x: float, y: float, w: float, h: float):
    if not logo_path:
        return
    if not os.path.exists(logo_path):
        return
    try:
        image = ImageReader(logo_path)
        iw, ih = image.getSize()
        scale = min(w / iw, h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        # align right inside the box
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
):
    # Group label
    group_label = "Individual"
    if tournament_type == "equipo":
        group_label = "Equipo"
    elif tournament_type == "seleccion_12":
        group_label = "Selección"

    def group_value(p: dict | None) -> str:
        if not p:
            return ""
        if tournament_type == "equipo":
            return p.get("team_name", "")
        if tournament_type == "seleccion_12":
            return p.get("seleccion_name", "")
        return "Individual"

    # Group line
    c.setFont("Helvetica", 8.5)
    c.drawString(x, y_top - 10, f"{group_label}: {group_value(player_top)}")

    # Table geometry
    header_h = 14
    row_h = 16
    table_top = y_top - 14
    table_h = header_h + 2 * row_h
    table_bottom = table_top - table_h

    c.setLineWidth(0.6)
    c.rect(x, table_bottom, width, table_h)

    # Column widths
    col_id = 44
    col_g = 20
    col_p = 24
    col_e = 24
    col_r = 28
    col_player = max(10, width - (col_id + col_g + col_p + col_e + col_r))

    # Column x positions
    x_id = x
    x_player = x_id + col_id
    x_g = x_player + col_player
    x_p = x_g + col_g
    x_e = x_p + col_p
    x_r = x_e + col_e
    x_end = x + width

    # Header fill
    c.setFillColor(colors.lightgrey)
    c.rect(x, table_top - header_h, width, header_h, fill=1, stroke=0)
    c.setFillColor(colors.black)

    # Header text
    c.setFont("Helvetica-Bold", 8.5)
    y_header_text = table_top - header_h + 3
    c.drawString(x_id + 2, y_header_text, "ID")
    c.drawString(x_player + 2, y_header_text, "Jugador")
    c.drawString(x_g + 6, y_header_text, "G")
    c.drawString(x_p + 6, y_header_text, "P")
    c.drawString(x_e + 6, y_header_text, "E")
    c.drawString(x_r + 4, y_header_text, "Rank")

    # Grid lines
    for vx in (x_player, x_g, x_p, x_e, x_r):
        c.line(vx, table_bottom, vx, table_top)
    c.line(x, table_top - header_h, x_end, table_top - header_h)
    c.line(x, table_top - header_h - row_h, x_end, table_top - header_h - row_h)

    # Rows
    _draw_player_row(c, x_id, table_top - header_h, row_h, player_top, player_stats, round_number)
    _draw_player_row(c, x_id, table_top - header_h - row_h, row_h, player_bottom, player_stats, round_number)

    # second group line for bottom player (like reference vibe)
    c.setFont("Helvetica", 8.5)
    c.drawString(x, table_bottom - 10, f"{group_label}: {group_value(player_bottom)}")


def _draw_player_row(
    c: canvas.Canvas,
    x_left: float,
    y_top: float,
    row_h: float,
    player: dict | None,
    player_stats: dict[int, dict],
    round_number: int,
):
    if not player:
        return

    pid = int(player.get("player_id", 0))
    seat = player.get("seat_letter", "")
    full_name = f"{player.get('nombre','')} {player.get('apellido','')}".strip()

    # Column anchors (must match _draw_player_block column widths)
    # We reconstruct from fixed offsets used there:
    # ID(44) + player(remaining) + G(20) + P(24) + E(24) + Rank(28)
    # We'll position relative to x_left.
    col_id = 44
    # We don’t know the dynamic col_player here, so we place stats near the right using drawRightString
    # and rely on block grid to visually guide it. This is acceptable for now.
    y_text = y_top - row_h + 4

    c.setFont("Helvetica", 8.5)
    c.drawString(x_left + 2, y_text, f"{pid} {seat}".strip())
    c.drawString(x_left + col_id + 2, y_text, full_name)

    if round_number == 1:
        return

    stats = player_stats.get(pid, {})
    # These keys can differ; we try common ones.
    g = stats.get("G", stats.get("g", ""))
    p = stats.get("P", stats.get("p", ""))
    e = stats.get("E", stats.get("e", ""))
    r = stats.get("rank", stats.get("R", stats.get("r", "")))

    # Right aligned near row end (safe)
    # The exact x positions are handled by the grid; we place relative offsets.
    c.drawRightString(x_left + 44 + 280, y_text, str(g))  # approximate
    c.drawRightString(x_left + 44 + 310, y_text, str(p))
    c.drawRightString(x_left + 44 + 340, y_text, str(e))
    c.drawRightString(x_left + 44 + 390, y_text, str(r))


def _draw_scoring_half(c: canvas.Canvas, x: float, y_top: float, width: float, title: str):
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y_top, title)

    table_top = y_top - 14

    tarjeta_w = 74
    gap = 6
    writing_x = x + tarjeta_w + gap
    writing_w = width - tarjeta_w - gap
    writing_h = 330

    _draw_tarjeta_table(c, x, table_top, tarjeta_w)

    c.setLineWidth(0.6)
    c.rect(writing_x, table_top - writing_h, writing_w, writing_h)

    # guide lines
    c.setStrokeColor(colors.lightgrey)
    lines = 11
    spacing = writing_h / lines
    for i in range(1, lines):
        yy = table_top - i * spacing
        c.line(writing_x, yy, writing_x + writing_w, yy)
    c.setStrokeColor(colors.black)

    total_y = table_top - writing_h - 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, total_y, "Total Puntos:")
    c.line(x + 72, total_y - 2, x + width - 6, total_y - 2)


def _draw_center_grid(c: canvas.Canvas, x: float, y_top: float, width: float):
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + width / 2, y_top, "Tarjeta")

    table_top = y_top - 14
    row_h = 14
    rows = ["Negra", "Roja", "Amarilla", "Marron"]

    c.setLineWidth(0.6)
    total_h = row_h * (len(rows) + 1)
    c.rect(x, table_top - total_h, width, total_h)
    c.line(x, table_top - row_h, x + width, table_top - row_h)

    for i, label in enumerate(rows, start=1):
        y = table_top - i * row_h
        c.line(x, y - row_h, x + width, y - row_h)
        c.setFont("Helvetica", 8)
        c.drawString(x + 2, y - row_h + 4, label)
        c.drawRightString(x + width - 2, y - row_h + 4, "0")


def _draw_tarjeta_table(c: canvas.Canvas, x: float, y_top: float, width: float):
    row_h = 14
    rows = ["Tarjeta", "Negra", "Roja", "Amarilla", "Marron"]
    total_h = row_h * len(rows)

    c.setLineWidth(0.6)
    c.rect(x, y_top - total_h, width, total_h)
    c.line(x, y_top - row_h, x + width, y_top - row_h)

    split_x = x + (width * 0.62)
    c.line(split_x, y_top - row_h, split_x, y_top - total_h)

    for i, label in enumerate(rows):
        y = y_top - i * row_h
        if i == 0:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(x + 2, y - row_h + 4, label)
        else:
            c.setFont("Helvetica", 8)
            c.drawString(x + 2, y - row_h + 4, label)
            c.drawRightString(x + width - 2, y - row_h + 4, "0")
