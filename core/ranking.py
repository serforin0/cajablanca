# core/ranking.py

WIN_WEIGHT = 100

def compute_effectiveness(g: int, p: int, win_weight: int = WIN_WEIGHT) -> int:
    # E = (G * 100) + P
    return (g * win_weight) + p

def compute_ranking(players: list, win_weight: int = WIN_WEIGHT) -> list:
    """
    players: lista de dicts u objetos con al menos: name, G, P
    Retorna la misma lista ordenada y con E y R asignados.
    """
    # 1) recalcular E
    for pl in players:
        # soporta dict o objeto
        g = pl["G"] if isinstance(pl, dict) else pl.G
        p = pl["P"] if isinstance(pl, dict) else pl.P
        e = compute_effectiveness(g, p, win_weight=win_weight)

        if isinstance(pl, dict):
            pl["E"] = e
        else:
            pl.E = e

    # 2) ordenar por E desc, P desc, G desc
    def key(pl):
        g = pl["G"] if isinstance(pl, dict) else pl.G
        p = pl["P"] if isinstance(pl, dict) else pl.P
        e = pl["E"] if isinstance(pl, dict) else pl.E
        return (-e, -p, -g)

    players.sort(key=key)

    # 3) asignar R 1..N
    for i, pl in enumerate(players):
        r = i + 1
        if isinstance(pl, dict):
            pl["R"] = r
        else:
            pl.R = r

    return players
