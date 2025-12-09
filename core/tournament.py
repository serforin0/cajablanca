# core/tournament.py
import random
from typing import Tuple

from core import storage


def generate_first_round() -> Tuple[bool, str]:
    """
    Mezcla todos los jugadores y los sienta en mesas de 4.
    A, B, C, D en sentido de las agujas del reloj.
    A frente a C, B frente a D.
    Guarda la ronda 1 en la BD.
    """
    players = storage.get_all_players()
    total = len(players)

    if total < 4:
        return False, "Se necesitan al menos 4 jugadores para generar la ronda."

    random.shuffle(players)

    mesas = []
    mesa_num = 1

    for i in range(0, total, 4):
        grupo = players[i:i + 4]
        if len(grupo) < 4:
            # Si sobra gente (no múltiplo de 4), los dejamos fuera de esta ronda
            break

        # Orden: A, B, C, D (reloj) -> A frente a C, B frente a D
        mesa = {
            "mesa": mesa_num,
            "A": grupo[0],
            "B": grupo[1],
            "C": grupo[2],
            "D": grupo[3],
        }
        mesas.append(mesa)
        mesa_num += 1

    storage.save_round_assignments(1, mesas)
    return True, f"Ronda 1 generada con {len(mesas)} mesas."
