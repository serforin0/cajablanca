# core/tournament.py
import random
from typing import Tuple, List, Dict, Optional

from core import storage


# ============================================================
# RONDA 1
# ============================================================

def generate_first_round() -> Tuple[bool, str]:
    """
    Mezcla todos los jugadores y los sienta en mesas de 4.
    Se sientan en sentido horario: A, B, C, D.
    Equipos:
      Equipo 1 = (A + C)
      Equipo 2 = (B + D)

    Guarda la ronda 1 en la BD.
    Garantiza que ningún jugador se repita en la ronda.
    """
    players = storage.get_all_players()
    total = len(players)

    if total < 4:
        return False, "Se necesitan al menos 4 jugadores para generar la ronda."

    if storage.round_has_scores(1):
        return False, "No se puede re-generar la ronda 1 porque ya tiene resultados guardados."

    players = players[:]  # copia
    random.shuffle(players)

    mesas = []
    mesa_num = 1
    usados = set()

    for i in range(0, total, 4):
        grupo = players[i:i + 4]
        if len(grupo) < 4:
            break  # sobran jugadores

        ids_grupo = [p["id"] for p in grupo]
        if any(pid in usados for pid in ids_grupo):
            return False, "Error interno: un jugador aparece repetido en la ronda."

        usados.update(ids_grupo)

        mesas.append({
            "mesa": mesa_num,
            "A": grupo[0],
            "B": grupo[1],
            "C": grupo[2],
            "D": grupo[3],
        })
        mesa_num += 1

    storage.save_round_assignments(1, mesas)

    # Asegura stats y recalcula (por si hay tablas/resultados previos)
    storage.ensure_player_stats_rows()
    storage.recompute_stats_from_results(win_weight=100)

    return True, f"Ronda 1 generada con {len(mesas)} mesas."


# ============================================================
# RONDA 2 (pareja anterior => enemigo)
# ============================================================

def generate_round_2() -> Tuple[bool, str]:
    """
    Regla principal ronda 2:
      - La pareja de la ronda anterior ahora debe ser tu enemigo.
    Como la pareja es:
      - R1: (A + C) son pareja
      - R1: (B + D) son pareja

    En R2, cada pareja anterior debe quedar en equipos opuestos.
    Construcción:
      - Tomamos TODAS las parejas de R1: 50 parejas (si hay 100 jugadores en R1)
      - Mezclamos parejas y agrupamos de 2 en 2 para formar mesas de 4.
      - Si pareja1 = (p,q) y pareja2 = (r,s)
        Creamos:
          Equipo1 (A+C) = (p, r)
          Equipo2 (B+D) = (q, s)
        Así p vs q (enemigos) y r vs s (enemigos).
    """
    r1 = storage.get_round_assignments(1)
    if not r1:
        return False, "No existe la Ronda 1. Genera la Ronda 1 primero."

    if storage.round_has_scores(2):
        return False, "No se puede re-generar la ronda 2 porque ya tiene resultados guardados."

    # Extraer parejas de R1: (A,C) y (B,D)
    pairs: List[Tuple[Dict, Dict]] = []
    for mesa in r1:
        # pareja 1
        pairs.append((mesa["A"], mesa["C"]))
        # pareja 2
        pairs.append((mesa["B"], mesa["D"]))

    if len(pairs) < 2:
        return False, "No hay suficientes parejas para generar la Ronda 2."

    random.shuffle(pairs)

    mesas_r2 = []
    mesa_num = 1

    # agrupar parejas de 2 en 2 => mesa de 4
    for i in range(0, len(pairs), 2):
        if i + 1 >= len(pairs):
            break

        (p, q) = pairs[i]
        (r, s) = pairs[i + 1]

        # aleatorizar quién va "del lado A/C" o "del lado B/D" dentro de cada pareja
        if random.random() < 0.5:
            p, q = q, p
        if random.random() < 0.5:
            r, s = s, r

        # Construcción garantizando que pareja anterior quede enemiga:
        # Equipo 1 = (A+C) = (p, r)
        # Equipo 2 = (B+D) = (q, s)
        mesa = {
            "mesa": mesa_num,
            "A": p,
            "B": q,
            "C": r,
            "D": s,
        }

        mesas_r2.append(mesa)
        mesa_num += 1

    if not mesas_r2:
        return False, "No se pudo generar la Ronda 2 (sin mesas)."

    storage.save_round_assignments(2, mesas_r2)

    # stats (no cambia nada si no hay resultados, pero lo mantenemos consistente)
    storage.ensure_player_stats_rows()
    storage.recompute_stats_from_results(win_weight=100)

    return True, f"Ronda 2 generada con {len(mesas_r2)} mesas (pareja anterior = enemigo)."


# ============================================================
# CAPTURA DE PUNTOS (por ronda/mesa)
# ============================================================

def save_table_points(
    round_number: int,
    mesa_number: int,
    points_team1_ac: int,
    points_team2_bd: int
) -> Tuple[bool, str]:
    """
    Guarda/actualiza puntos de una mesa (ronda/mesa),
    marca mesa como finished y recalcula ranking.

    Equipos:
      Team1 = (A + C)
      Team2 = (B + D)
    """
    # Validaciones
    try:
        points_team1_ac = int(points_team1_ac)
        points_team2_bd = int(points_team2_bd)
    except Exception:
        return False, "Puntos inválidos (deben ser enteros)."

    if points_team1_ac < 0 or points_team2_bd < 0:
        return False, "Los puntos no pueden ser negativos."

    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        return False, f"No hay mesas generadas para la ronda {round_number}."

    if not any(m["mesa"] == mesa_number for m in mesas):
        return False, f"La mesa {mesa_number} no existe en la ronda {round_number}."

    # Guardar resultado (points_a = Team1 (A+C), points_b = Team2 (B+D))
    storage.save_table_result(round_number, mesa_number, points_team1_ac, points_team2_bd)

    # Marcar terminado
    storage.set_table_status(round_number, mesa_number, "finished")

    # Recalcular stats/ranking
    storage.ensure_player_stats_rows()
    storage.recompute_stats_from_results(win_weight=100)

    return True, "Resultado guardado correctamente."


def save_table_player_scores(
    round_number: int,
    mesa_number: int,
    player_points: dict[str, dict],
    winner_pair: str,
) -> Tuple[bool, str]:
    """
    Guarda puntos individuales por jugador (A/B/C/D).

    player_points = {
        "A": {"base_points": int, "penalty_points": int},
        "B": {"base_points": int, "penalty_points": int},
        "C": {"base_points": int, "penalty_points": int},
        "D": {"base_points": int, "penalty_points": int},
    }
    """
    winner_pair = "AC" o "BD"
    mesas = storage.get_round_assignments(round_number)
    if not mesas:
        return False, f"No hay mesas generadas para la ronda {round_number}."

    mesa_data = next((m for m in mesas if m["mesa"] == mesa_number), None)
    if not mesa_data:
        return False, f"La mesa {mesa_number} no existe en la ronda {round_number}."

    winner_pair = (winner_pair or "").upper().strip()
    if winner_pair not in ("AC", "BD"):
        return False, "Debes seleccionar la pareja ganadora (AC o BD)."

    scores_rows = []
    for letra in ("A", "B", "C", "D"):
        data = player_points.get(letra, {})
        try:
            base_points = int(data.get("base_points", 0))
            penalty_points = int(data.get("penalty_points", 0))
        except Exception:
            return False, "Puntos o penalidad inválidos (deben ser enteros)."

        if base_points < 0 or penalty_points < 0:
            return False, "Los puntos y penalidades no pueden ser negativos."

        player = mesa_data[letra]
        scores_rows.append(
            {
                "jugador_id": player["id"],
                "letra": letra,
                "base_points": base_points,
                "penalty_points": penalty_points,
            }
        )

    storage.save_table_player_scores(
        round_number,
        mesa_number,
        scores_rows,
        winner_pair,
    )

    storage.set_table_status(round_number, mesa_number, "finished")
    storage.ensure_player_stats_rows()
    storage.recompute_stats_from_results(win_weight=100)

    return True, "Resultados individuales guardados correctamente."


# ============================================================
# PENALIZACIONES (restar puntos a un jugador específico)
# ============================================================

def subtract_points_from_player(
    jugador_id: int,
    points: int,
    reason: str = "Penalización"
) -> Tuple[bool, str]:
    """
    Resta puntos a un jugador (penalización).
    Esto NO toca resultados de mesas; se aplica como ajuste acumulado.
    """
    try:
        jugador_id = int(jugador_id)
        points = int(points)
    except Exception:
        return False, "Datos inválidos."

    if points <= 0:
        return False, "Los puntos a restar deben ser > 0."

    storage.ensure_player_stats_rows()
    storage.add_player_adjustment(jugador_id, -points, reason)

    # Recalcular ranking (incluye ajustes)
    storage.recompute_stats_from_results(win_weight=100)

    return True, f"Se restaron {points} puntos al jugador #{jugador_id}."


# ============================================================
# HELPERS para UI
# ============================================================

def get_ranking():
    return storage.get_ranking()


def recompute_ranking(win_weight: int = 100):
    storage.ensure_player_stats_rows()
    storage.recompute_stats_from_results(win_weight=win_weight)


def get_table_result(round_number: int, mesa_number: int):
    return storage.get_table_result(round_number, mesa_number)


# ============================================================
# WRAPPER OPCIONAL: si tu MainWindow usa Tournament()
# ============================================================

class Tournament:
    """
    Wrapper para que puedas usar self.tournament = Tournament()
    sin romper el código ya hecho.
    """
    def generate_round1(self):
        return generate_first_round()

    def generate_round2(self):
        return generate_round_2()

    def save_table_points(self, round_number: int, mesa_number: int, pa: int, pb: int):
        return save_table_points(round_number, mesa_number, pa, pb)

    def save_table_player_scores(
        self,
        round_number: int,
        mesa_number: int,
        player_points: dict[str, dict],
        winner_pair: str,
    ):
        return save_table_player_scores(round_number, mesa_number, player_points, winner_pair)

    def subtract_points(self, jugador_id: int, points: int, reason: str = "Penalización"):
        return subtract_points_from_player(jugador_id, points, reason)

    def get_ranking(self):
        return get_ranking()
    if storage.round_has_scores(1):
        return False, "No se puede re-generar la ronda 1 porque ya tiene resultados guardados."
