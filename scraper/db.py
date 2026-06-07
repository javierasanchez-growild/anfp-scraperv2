# -*- coding: utf-8 -*-
"""
Manejo de la base de datos SQLite (anfp.db).

Dos capas:
  1) CAPA DE CAPTURA (raw): respaldo + log de cada corrida. Nunca se cae.
  2) CAPA NORMALIZADA: tablas limpias y consultables (posiciones, goleadores,
     asistencias) como serie temporal: una foto por día (fecha_captura).
"""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "anfp.db"


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    return con


def inicializar(con):
    """Crea las tablas base si no existen."""
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS scrape_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_captura TEXT,
            fuente        TEXT,
            url           TEXT,
            tablas        INTEGER,
            estado        TEXT,
            mensaje       TEXT
        )
        """
    )
    con.commit()


def _nombre_seguro(texto):
    """Convierte un nombre en algo válido para una tabla SQL."""
    limpio = re.sub(r"[^a-zA-Z0-9_]", "_", str(texto).lower())
    return re.sub(r"_+", "_", limpio).strip("_")


def guardar_tabla(con, fuente, indice, df, fecha_captura):
    """Guarda un DataFrame crudo como 'raw_<fuente>_t<indice>' (histórico)."""
    df = df.copy()
    df.columns = [
        _nombre_seguro(str(c)) or f"col_{i}" for i, c in enumerate(df.columns)
    ]
    df.insert(0, "fecha_captura", fecha_captura)
    nombre_tabla = f"raw_{_nombre_seguro(fuente)}_t{indice}"
    df.to_sql(nombre_tabla, con, if_exists="append", index=False)
    return nombre_tabla


def _tabla_existe(con, nombre):
    cur = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (nombre,)
    )
    return cur.fetchone() is not None


def guardar_normalizada(con, nombre_tabla, df, fecha_captura, torneo):
    """
    Guarda una tabla normalizada (posiciones/goleadores/asistencias) como serie
    temporal. Agrega columnas fecha_captura y torneo. Idempotente: si ya hay
    filas de ese mismo día y torneo, las reemplaza (re-correr no duplica).
    """
    df = df.copy()
    df.columns = [
        _nombre_seguro(str(c)) or f"col_{i}" for i, c in enumerate(df.columns)
    ]
    df.insert(0, "torneo", torneo)
    df.insert(0, "fecha_captura", fecha_captura)

    nombre = _nombre_seguro(nombre_tabla)
    if _tabla_existe(con, nombre):
        con.execute(
            f"DELETE FROM {nombre} WHERE fecha_captura=? AND torneo=?",
            (fecha_captura, torneo),
        )
        con.commit()
    df.to_sql(nombre, con, if_exists="append", index=False)
    return nombre, len(df)


def registrar_log(con, fecha_captura, fuente, url, tablas, estado, mensaje):
    con.execute(
        "INSERT INTO scrape_log "
        "(fecha_captura, fuente, url, tablas, estado, mensaje) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (fecha_captura, fuente, url, tablas, estado, mensaje),
    )
    con.commit()
# -*- coding: utf-8 -*-
"""
Manejo de la base de datos SQLite (anfp.db).

Diseño en dos capas:
  1) CAPA DE CAPTURA: cada tabla encontrada en una página se guarda tal cual,
     con una columna 'fecha_captura'. Así nunca se pierde nada y la BBDD queda
     como una serie temporal (un snapshot por día).
  2) CAPA NORMALIZADA: tablas limpias y consultables (posiciones, goleadores,
     partidos...). Esta capa la afinas con datos reales una vez que sepas la
     estructura exacta de cada página.
"""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "anfp.db"


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    return con


def inicializar(con):
    """Crea las tablas base si no existen."""
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS scrape_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_captura TEXT,
            fuente        TEXT,
            url           TEXT,
            tablas        INTEGER,
            estado        TEXT,
            mensaje       TEXT
        )
        """
    )
    con.commit()


def _nombre_seguro(texto):
    """Convierte un nombre en algo válido para una tabla SQL."""
    limpio = re.sub(r"[^a-zA-Z0-9_]", "_", texto.lower())
    return re.sub(r"_+", "_", limpio).strip("_")


def guardar_tabla(con, fuente, indice, df, fecha_captura):
    """
    Guarda un DataFrame como tabla 'raw_<fuente>_t<indice>', agregando la
    columna fecha_captura para mantener el histórico día a día.
    """
    df = df.copy()
    # Nombres de columna seguros y únicos.
    df.columns = [
        _nombre_seguro(str(c)) or f"col_{i}" for i, c in enumerate(df.columns)
    ]
    df.insert(0, "fecha_captura", fecha_captura)

    nombre_tabla = f"raw_{_nombre_seguro(fuente)}_t{indice}"
    df.to_sql(nombre_tabla, con, if_exists="append", index=False)
    return nombre_tabla


def registrar_log(con, fecha_captura, fuente, url, tablas, estado, mensaje):
    con.execute(
        "INSERT INTO scrape_log "
        "(fecha_captura, fuente, url, tablas, estado, mensaje) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (fecha_captura, fuente, url, tablas, estado, mensaje),
    )
    con.commit()
