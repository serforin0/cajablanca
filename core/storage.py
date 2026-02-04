# core/storage.py
import os  # ✅ nuevo (para TORNEO_DB_PATH)
import sqlite3
from pathlib import Path

# ✅ BD_PATH configurable:
# - Si existe TORNEO_DB_PATH, usa esa ruta (ideal para carpeta compartida en red)
# - Si no, usa "torneo_domino.db" local
DEFAULT_DB_PATH = Path("torneo_domino.db")
DB_PATH = Path(os.environ.get("TORNEO_DB_PATH", str(DEFAULT_DB_PATH)))


def _apply_pragmas(conn: sqlite3.Connection):
    """
    ✅ Ajustes recomendados para uso en 2 PCs:
    - WAL: reduce bloqueos de lectura/escritura
    - busy_timeout: espera si la BD está ocupada
    - foreign_keys: integridad
    - synchronous NORMAL: balance decente (especialmente en red)
    """
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("PRAGMA synchronous = NORMAL;")
    cur.execute("PRAGMA busy_timeout = 8000;")  # 8s de espera si está bloqueada
    cur.close()


def get_connection():
    # ✅ timeout para que espere en bloqueos (además del busy_timeout)
    conn = sqlite3.connect(DB_PATH, timeout=8)
    _apply_pragmas(conn)
    return conn


def init_db():
    """Crea las tablas de jugadores, asientos y estado de mesas."""
    conn = get_connection()
    cur = conn.cursor()

    # Tabla de jugadores
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT NOT NULL,
            apellido TEXT NOT NULL,
            cedula   TEXT NOT NULL,
            telefono TEXT NOT NULL,
            pago     INTEGER NOT NULL DEFAULT 5000
        );
        """
    )

    # Tabla de asientos por ronda/mesa
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS seats (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            round       INTEGER NOT NULL,
            mesa        INTEGER NOT NULL,
            letra       TEXT NOT NULL,          -- A, B, C, D
            jugador_id  INTEGER NOT NULL,
            FOREIGN KEY (jugador_id) REFERENCES players(id)
        );
        """
    )

    # ✅ BLINDAJE: una silla no puede repetirse (round+mesa+letra)
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_seats_unique_seat
        ON seats (round, mesa, letra);
        """
    )

    # ✅ BLINDAJE: un jugador NO puede aparecer 2 veces en la misma ronda
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_seats_unique_player_per_round
        ON seats (round, jugador_id);
        """
    )

    # Estado de cada mesa en una ronda
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS table_status (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            round  INTEGER NOT NULL,
            mesa   INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'playing',
            UNIQUE(round, mesa)
        );
        """
    )

    # ---------------- NUEVO: resultados por mesa ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS table_results (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            round      INTEGER NOT NULL,
            mesa       INTEGER NOT NULL,
            points_a   INTEGER NOT NULL DEFAULT 0,
            points_b   INTEGER NOT NULL DEFAULT 0,
            winner     TEXT NOT NULL DEFAULT 'draw', -- 'A', 'B', 'draw'
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(round, mesa)
        );
        """
    )

    # ---------------- NUEVO: puntos por jugador por ronda/mesa ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_round_scores (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            round         INTEGER NOT NULL,
            mesa          INTEGER NOT NULL,
            jugador_id    INTEGER NOT NULL,
            letra         TEXT NOT NULL, -- A, B, C, D
            base_points    INTEGER NOT NULL DEFAULT 0,
            penalty_points INTEGER NOT NULL DEFAULT 0,
            final_points   INTEGER NOT NULL DEFAULT 0,
            winner_pair    TEXT NOT NULL CHECK (winner_pair IN ('AC', 'BD')),
            created_at    TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(round, mesa, jugador_id),
            FOREIGN KEY (jugador_id) REFERENCES players(id)
        );
        """
    )

    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_player_round_scores_unique_seat
        ON player_round_scores (round, mesa, letra);
        """
    )

    # ---------------- NUEVO: stats por jugador ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_stats (
            jugador_id INTEGER PRIMARY KEY,
            g          INTEGER NOT NULL DEFAULT 0,
            p          INTEGER NOT NULL DEFAULT 0,
            e          INTEGER NOT NULL DEFAULT 0,
            r          INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (jugador_id) REFERENCES players(id)
        );
        """
    )

    # ---------------- NUEVO: ajustes/penalizaciones por jugador ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_adjustments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            jugador_id  INTEGER NOT NULL,
            delta_p     INTEGER NOT NULL, -- puede ser negativo (penalización) o positivo (bono)
            reason      TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (jugador_id) REFERENCES players(id)
        );
        """
    )

    conn.commit()

    # Semilla inicial de 100 jugadores demo (si la tabla está vacía)
    cur.execute("SELECT COUNT(*) FROM players;")
    (count,) = cur.fetchone()
    if count == 0:
        seed_demo_players(conn)

    conn.close()

    # Asegura que TODO jugador tenga su fila en player_stats
    ensure_player_stats_rows()
    _ensure_player_round_scores_schema()


def _ensure_player_round_scores_schema():
    """Migra tabla player_round_scores si existe con nombres legacy."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='player_round_scores';
        """
    )
    if not cur.fetchone():
        conn.close()
        return

    cur.execute("PRAGMA table_info(player_round_scores);")
    columns = {row[1] for row in cur.fetchall()}

    legacy_cols = {"points_base", "penalty", "points_final", "winner_pareja"}
    new_cols = {"base_points", "penalty_points", "final_points", "winner_pair"}

    if legacy_cols.issubset(columns) and not new_cols.issubset(columns):
        cur.execute(
            """
            ALTER TABLE player_round_scores
            RENAME TO player_round_scores_legacy;
            """
        )
        cur.execute(
            """
            CREATE TABLE player_round_scores (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                round         INTEGER NOT NULL,
                mesa          INTEGER NOT NULL,
                jugador_id    INTEGER NOT NULL,
                letra         TEXT NOT NULL,
                base_points   INTEGER NOT NULL DEFAULT 0,
                penalty_points INTEGER NOT NULL DEFAULT 0,
                final_points  INTEGER NOT NULL DEFAULT 0,
                winner_pair   TEXT NOT NULL CHECK (winner_pair IN ('AC', 'BD')),
                created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(round, mesa, jugador_id),
                FOREIGN KEY (jugador_id) REFERENCES players(id)
            );
            """
        )
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_player_round_scores_unique_seat
            ON player_round_scores (round, mesa, letra);
            """
        )
        cur.execute(
            """
            INSERT INTO player_round_scores (
                id, round, mesa, jugador_id, letra,
                base_points, penalty_points, final_points, winner_pair, created_at
            )
            SELECT
                id, round, mesa, jugador_id, letra,
                points_base, penalty, points_final,
                CASE
                    WHEN winner_pareja IN ('AC','BD') THEN winner_pareja
                    ELSE 'AC'
                END,
                created_at
            FROM player_round_scores_legacy;
            """
        )
        cur.execute("DROP TABLE player_round_scores_legacy;")

    conn.commit()
    conn.close()


def seed_demo_players(conn: sqlite3.Connection):
    """Inserta 100 jugadores de ejemplo para pruebas."""
    cur = conn.cursor()
    jugadores = []

    for i in range(1, 101):
        nombre = f"Jugador {i}"
        apellido = "Demo"
        cedula = f"001-0000{i:04d}-1"
        telefono = f"809-555-{i:04d}"
        pago = 5000
        jugadores.append((nombre, apellido, cedula, telefono, pago))

    cur.executemany(
        """
        INSERT INTO players (nombre, apellido, cedula, telefono, pago)
        VALUES (?, ?, ?, ?, ?)
        """,
        jugadores,
    )
    conn.commit()


# ---------------- NUEVO: asegurar stats ----------------

def ensure_player_stats_rows():
    """Crea fila en player_stats para todo jugador que no tenga una."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO player_stats (jugador_id, g, p, e, r)
        SELECT p.id, 0, 0, 0, 0
        FROM players p
        LEFT JOIN player_stats ps ON ps.jugador_id = p.id
        WHERE ps.jugador_id IS NULL;
        """
    )

    conn.commit()
    conn.close()


# ---------- JUGADORES ----------

def get_players_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM players;")
    (count,) = cur.fetchone()
    conn.close()
    return count


def add_player(nombre: str, apellido: str, cedula: str, telefono: str, pago: int = 5000):
    """Agrega un jugador nuevo (máx. 100). Devuelve (ok, mensaje)."""
    import sqlite3 as _sqlite3

    current = get_players_count()
    if current >= 100:
        return False, "Ya hay 100 jugadores registrados. No se pueden agregar más."

    if not nombre.strip() or not apellido.strip():
        return False, "Nombre y apellido son obligatorios."
    if not cedula.strip():
        return False, "La cédula es obligatoria."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO players (nombre, apellido, cedula, telefono, pago)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre.strip(), apellido.strip(), cedula.strip(), telefono.strip(), pago),
        )
        new_id = cur.lastrowid

        # crea stats para el nuevo jugador
        cur.execute(
            "INSERT OR IGNORE INTO player_stats (jugador_id, g, p, e, r) VALUES (?,0,0,0,0);",
            (new_id,),
        )

        conn.commit()
        return True, "Jugador registrado correctamente."
    except _sqlite3.Error as e:
        return False, f"Error de base de datos: {e}"
    finally:
        conn.close()


def get_all_players():
    """Devuelve lista de dicts con todos los jugadores."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nombre, apellido, cedula, telefono, pago
        FROM players
        ORDER BY id ASC;
        """
    )
    rows = cur.fetchall()
    conn.close()

    players = []
    for row in rows:
        players.append(
            {
                "id": row[0],
                "nombre": row[1],
                "apellido": row[2],
                "cedula": row[3],
                "telefono": row[4],
                "pago": row[5],
            }
        )
    return players


# ---------- ASIGNACIONES DE MESAS / RONDAS ----------

def clear_round(round_number: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM seats WHERE round = ?;", (round_number,))
    cur.execute("DELETE FROM table_status WHERE round = ?;", (round_number,))

    conn.commit()
    conn.close()


def save_round_assignments(round_number: int, mesas: list[dict]):
    """
    Guarda en BD la asignación de mesas.
    mesas = [
      { "mesa": 1, "A": player_dict, "B": ..., "C": ..., "D": ... },
      ...
    ]
    """
    conn = get_connection()
    cur = conn.cursor()

    # Borramos todo lo de esa ronda (asientos y estado)
    cur.execute("DELETE FROM seats WHERE round = ?;", (round_number,))
    cur.execute("DELETE FROM table_status WHERE round = ?;", (round_number,))

    seat_rows = []
    status_rows = []

    for mesa in mesas:
        mesa_num = mesa["mesa"]
        for letra in ("A", "B", "C", "D"):
            jugador = mesa[letra]
            seat_rows.append((round_number, mesa_num, letra, jugador["id"]))

        # estado inicial: jugando
        status_rows.append((round_number, mesa_num, "playing"))

    # ✅ Validación extra (mensaje claro si intentan duplicar)
    seen_players = set()
    seen_seats = set()
    for rnd, mesa_num, letra, jid in seat_rows:
        key_player = (rnd, jid)
        key_seat = (rnd, mesa_num, letra)
        if key_player in seen_players:
            conn.rollback()
            conn.close()
            raise ValueError(f"Jugador #{jid} está repetido en la ronda {rnd}.")
        if key_seat in seen_seats:
            conn.rollback()
            conn.close()
            raise ValueError(f"Asiento duplicado: ronda {rnd}, mesa {mesa_num}, letra {letra}.")
        seen_players.add(key_player)
        seen_seats.add(key_seat)

    cur.executemany(
        """
        INSERT INTO seats (round, mesa, letra, jugador_id)
        VALUES (?, ?, ?, ?)
        """,
        seat_rows,
    )

    cur.executemany(
        """
        INSERT INTO table_status (round, mesa, status)
        VALUES (?, ?, ?)
        """,
        status_rows,
    )

    conn.commit()
    conn.close()


def get_round_assignments(round_number: int) -> list[dict]:
    """
    Devuelve lista de mesas con jugadores:
    [
      {
        "mesa": 1,
        "A": {id, nombre, apellido, ...},
        "B": {...},
        "C": {...},
        "D": {...},
      },
      ...
    ]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            s.mesa,
            s.letra,
            p.id,
            p.nombre,
            p.apellido,
            p.cedula,
            p.telefono,
            p.pago
        FROM seats s
        JOIN players p ON p.id = s.jugador_id
        WHERE s.round = ?
        ORDER BY
            s.mesa ASC,
            CASE s.letra
                WHEN 'A' THEN 1
                WHEN 'B' THEN 2
                WHEN 'C' THEN 3
                WHEN 'D' THEN 4
            END;
        """,
        (round_number,),
    )

    rows = cur.fetchall()
    conn.close()

    mesas_dict: dict[int, dict] = {}
    for mesa_num, letra, pid, nombre, apellido, cedula, telefono, pago in rows:
        if mesa_num not in mesas_dict:
            mesas_dict[mesa_num] = {"mesa": mesa_num}
        mesas_dict[mesa_num][letra] = {
            "id": pid,
            "nombre": nombre,
            "apellido": apellido,
            "cedula": cedula,
            "telefono": telefono,
            "pago": pago,
        }

    return [mesas_dict[m] for m in sorted(mesas_dict.keys())]


def get_round_seat_list(round_number: int) -> list[dict]:
    """Devuelve lista de asientos simples: [{jugador_id, mesa, letra}]."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT jugador_id, mesa, letra
        FROM seats
        WHERE round = ?
        ORDER BY jugador_id ASC;
        """,
        (round_number,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"jugador_id": jid, "mesa": mesa, "letra": letra} for jid, mesa, letra in rows]


def round_has_scores(round_number: int) -> bool:
    """Indica si la ronda tiene resultados guardados por jugador."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM player_round_scores WHERE round = ? LIMIT 1;",
        (round_number,),
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists


# ---------- ESTADO DE MESAS ----------

def get_tables_status(round_number: int) -> dict[int, str]:
    """Devuelve {mesa: status} para la ronda (status: 'playing' o 'finished')."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT mesa, status FROM table_status WHERE round = ?;", (round_number,))
    rows = cur.fetchall()
    conn.close()
    return {mesa: status for mesa, status in rows}


def get_table_status(round_number: int, mesa_number: int) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT status FROM table_status WHERE round = ? AND mesa = ?;",
        (round_number, mesa_number),
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "playing"


def set_table_status(round_number: int, mesa_number: int, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO table_status (round, mesa, status)
        VALUES (?, ?, ?)
        ON CONFLICT(round, mesa) DO UPDATE SET status = excluded.status;
        """,
        (round_number, mesa_number, status),
    )
    conn.commit()
    conn.close()


# ---------------- resultados y ranking ----------------

def save_table_result(round_number: int, mesa_number: int, points_a: int, points_b: int):
    """Guarda o actualiza el resultado de una mesa (por ronda/mesa)."""
    winner = "draw"
    if points_a > points_b:
        winner = "A"
    elif points_b > points_a:
        winner = "B"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO table_results (round, mesa, points_a, points_b, winner)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(round, mesa) DO UPDATE SET
            points_a = excluded.points_a,
            points_b = excluded.points_b,
            winner   = excluded.winner,
            created_at = datetime('now');
        """,
        (round_number, mesa_number, points_a, points_b, winner),
    )
    conn.commit()
    conn.close()


def save_table_player_scores(
    round_number: int,
    mesa_number: int,
    player_scores: list[dict],
    winner_pair: str,
):
    """
    Guarda puntos por jugador (A,B,C,D) para una mesa.
    player_scores = [
        {"jugador_id": int, "letra": "A", "base_points": int, "penalty_points": int},
        ...
    ]
    """
    conn = get_connection()
    cur = conn.cursor()

    insert_rows = []
    for row in player_scores:
        base_points = int(row.get("base_points", 0))
        penalty_points = int(row.get("penalty_points", 0))
        final_points = max(0, base_points - max(0, penalty_points))

        insert_rows.append(
            (
                round_number,
                mesa_number,
                row["jugador_id"],
                row["letra"],
                base_points,
                max(0, penalty_points),
                final_points,
                winner_pair,
            )
        )

    cur.executemany(
        """
        INSERT INTO player_round_scores (
            round, mesa, jugador_id, letra,
            base_points, penalty_points, final_points, winner_pair
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(round, mesa, jugador_id) DO UPDATE SET
            base_points = excluded.base_points,
            penalty_points = excluded.penalty_points,
            final_points = excluded.final_points,
            winner_pair = excluded.winner_pair,
            created_at = datetime('now');
        """,
        insert_rows,
    )

    conn.commit()
    conn.close()


def get_table_player_scores(round_number: int, mesa_number: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT jugador_id, letra, base_points, penalty_points, final_points, winner_pair
        FROM player_round_scores
        WHERE round = ? AND mesa = ?
        ORDER BY CASE letra
            WHEN 'A' THEN 1
            WHEN 'B' THEN 2
            WHEN 'C' THEN 3
            WHEN 'D' THEN 4
        END;
        """,
        (round_number, mesa_number),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "jugador_id": jid,
            "letra": letra,
            "base_points": base_points,
            "penalty_points": penalty_points,
            "final_points": final_points,
            "winner_pair": winner_pair,
        }
        for (jid, letra, base_points, penalty_points, final_points, winner_pair) in rows
    ]


def get_table_result(round_number: int, mesa_number: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT points_a, points_b, winner
        FROM table_results
        WHERE round = ? AND mesa = ?;
        """,
        (round_number, mesa_number),
    )
    row = cur.fetchone()
    conn.close()
    return None if not row else {"points_a": row[0], "points_b": row[1], "winner": row[2]}


def reset_player_stats():
    """Resetea stats acumuladas (G,P,E,R) de todos los jugadores."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE player_stats SET g=0, p=0, e=0, r=0, updated_at=datetime('now');")
    conn.commit()
    conn.close()


def recompute_stats_from_results(win_weight: int = 100):
    """
    Recalcula G y P por jugador usando:
    - player_round_scores: puntos individuales por ronda/mesa
    - winner_pair: define si ganó AC o BD para sumar G

    Convención:
      Pareja AC = letras A y C
      Pareja BD = letras B y D

    Fórmula:
      E = P (opción simple)
    Ranking:
      ORDER BY P desc, G desc, ID asc
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1) reset
    cur.execute("UPDATE player_stats SET g=0, p=0, e=0, r=0, updated_at=datetime('now');")

    # 2) sumar puntos y ganadas por cada jugador
    cur.execute(
        """
        SELECT round, mesa, jugador_id, letra, final_points, winner_pair
        FROM player_round_scores;
        """
    )
    results = cur.fetchall()

    for rnd, mesa, jid, letra, final_points, winner_pair in results:
        cur.execute(
            "UPDATE player_stats SET p = p + ? WHERE jugador_id = ?;",
            (final_points, jid),
        )

        if winner_pair == "AC" and letra in ("A", "C"):
            cur.execute("UPDATE player_stats SET g = g + 1 WHERE jugador_id = ?;", (jid,))
        elif winner_pair == "BD" and letra in ("B", "D"):
            cur.execute("UPDATE player_stats SET g = g + 1 WHERE jugador_id = ?;", (jid,))

    # 2.5) aplicar ajustes/penalizaciones a P
    cur.execute(
        """
        UPDATE player_stats
        SET p = p + COALESCE(
            (SELECT SUM(delta_p) FROM player_adjustments pa WHERE pa.jugador_id = player_stats.jugador_id),
            0
        ),
        updated_at = datetime('now');
        """
    )

    # 3) calcular E (opción simple: E = P). TODO: actualizar fórmula de efectividad.
    cur.execute(
        """
        UPDATE player_stats
        SET e = p,
            updated_at = datetime('now');
        """,
    )

    # 4) ranking
    cur.execute(
        """
        SELECT jugador_id
        FROM player_stats
        ORDER BY p DESC, g DESC, jugador_id ASC;
        """
    )
    ordered_ids = [row[0] for row in cur.fetchall()]

    for idx, jid in enumerate(ordered_ids, start=1):
        cur.execute("UPDATE player_stats SET r = ? WHERE jugador_id = ?;", (idx, jid))

    conn.commit()
    conn.close()


def get_ranking():
    """Devuelve ranking listo para UI: R, jugador, G, P, E."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            ps.r,
            p.id,
            p.nombre,
            p.apellido,
            ps.g,
            ps.p,
            ps.e
        FROM player_stats ps
        JOIN players p ON p.id = ps.jugador_id
        ORDER BY ps.r ASC;
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "R": r,
            "id": pid,
            "nombre": nombre,
            "apellido": apellido,
            "G": g,
            "P": puntos,
            "E": e,
        }
        for (r, pid, nombre, apellido, g, puntos, e) in rows
    ]


def get_player_stats_map() -> dict[int, dict]:
    """Devuelve {jugador_id: {G, P, E, R}}."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT jugador_id, g, p, e, r
        FROM player_stats;
        """
    )
    rows = cur.fetchall()
    conn.close()
    return {jid: {"G": g, "P": p, "E": e, "R": r} for jid, g, p, e, r in rows}


def add_player_adjustment(jugador_id: int, delta_p: int, reason: str = ""):
    """Crea un ajuste de puntos para un jugador (negativo = resta)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO player_adjustments (jugador_id, delta_p, reason)
        VALUES (?, ?, ?);
        """,
        (jugador_id, int(delta_p), reason.strip()),
    )
    conn.commit()
    conn.close()


def get_adjustments_sum_by_player() -> dict[int, int]:
    """Devuelve {jugador_id: suma_ajustes}."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT jugador_id, COALESCE(SUM(delta_p), 0)
        FROM player_adjustments
        GROUP BY jugador_id;
        """
    )
    rows = cur.fetchall()
    conn.close()
    return {jid: total for jid, total in rows}
