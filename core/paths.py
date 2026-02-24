from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Cajablanca"


def is_frozen_exe() -> bool:
    # True cuando corre empaquetado por PyInstaller
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def project_root() -> Path:
    """
    En modo normal: carpeta del proyecto (donde está main.py)
    En modo exe: carpeta donde está el .exe (no recomendado para escribir archivos)
    """
    if is_frozen_exe():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_root() -> Path:
    """
    Donde PyInstaller extrae recursos en --onefile (sys._MEIPASS),
    o la carpeta del proyecto en modo normal.
    """
    if is_frozen_exe():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return project_root()


def user_data_dir() -> Path:
    """
    Carpeta de datos del usuario (persistente).
    Recomendado para BD, PDFs, etc.
    """
    base = Path.home() / "Documents" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path() -> Path:
    return user_data_dir() / "data.db"


def hojas_dir() -> Path:
    d = user_data_dir() / "Hojas"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logos_dir() -> Path:
    """
    Carpeta de logos dentro de assets. En exe, esto está dentro de resource_root().
    """
    return resource_root() / "assets" / "logos"


def resolve_logo_path(logo_path: str | None) -> str | None:
    """
    Soporta:
    - ruta absoluta
    - ruta relativa (ej: "mi_logo.png") => assets/logos/mi_logo.png
    - None => sin logo
    """
    if not logo_path:
        return None

    p = Path(logo_path)

    # si es absoluta y existe, usarla
    if p.is_absolute() and p.exists():
        return str(p)

    # si es relativa y existe tal cual (por si viene "assets/logos/x.png")
    rel_try = (resource_root() / p).resolve()
    if rel_try.exists():
        return str(rel_try)

    # si es solo el nombre, buscar en assets/logos/
    candidate = (logos_dir() / p.name).resolve()
    if candidate.exists():
        return str(candidate)

    return None
