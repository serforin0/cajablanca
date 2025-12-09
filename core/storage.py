# core/storage.py
import sqlite3
from pathlib import Path

DB_PATH = Path("torneo_domino.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Crea las tablas de jugadores y asientos (mesas/rondas)."""
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

    conn.commit()

    # Semilla inicial de 100 jugadores demo (si la tabla está vacía)
    cur.execute("SELECT COUNT(*) FROM players;")
    (count,) = cur.fetchone()
    if count == 0:
        seed_demo_players(conn)

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

    cur.execute("DELETE FROM seats WHERE round = ?;", (round_number,))

    rows = []
    for mesa in mesas:
        mesa_num = mesa["mesa"]
        for letra in ("A", "B", "C", "D"):
            jugador = mesa[letra]
            rows.append((round_number, mesa_num, letra, jugador["id"]))

    cur.executemany(
        """
        INSERT INTO seats (round, mesa, letra, jugador_id)
        VALUES (?, ?, ?, ?)
        """,
        rows,
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

    # Ordenar por número de mesa
    mesas = [mesas_dict[m] for m in sorted(mesas_dict.keys())]
    return mesas
