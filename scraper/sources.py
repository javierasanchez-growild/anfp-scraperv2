# -*- coding: utf-8 -*-
"""
Descarga de páginas y extracción de tablas (crudas y normalizadas).
"""

import io
import requests
import pandas as pd

from .config import USER_AGENT


def descargar_html(url, timeout=30):
    """Descarga el HTML de una página identificándose con un User-Agent."""
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "es-CL,es;q=0.9"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def extraer_tablas(html):
    """
    Extrae todas las tablas HTML como DataFrames.
    Devuelve [] si la página no tiene tablas (típico en páginas con datos
    cargados por JavaScript).
    """
    try:
        return pd.read_html(io.StringIO(html))
    except ValueError:
        return []


# ----------------------------------------------------------------------------
# Normalización: detecta las tablas relevantes por la FIRMA de sus columnas,
# no por un índice fijo (el índice cambia a lo largo de la temporada).
# ----------------------------------------------------------------------------

def _cols(df):
    return {str(c).strip() for c in df.columns}


def _limpiar(df):
    """Quita columnas 'Unnamed'/vacías y filas totalmente vacías."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    keep = [c for c in df.columns if not c.lower().startswith("unnamed") and c != ""]
    df = df[keep]
    df = df.dropna(how="all")
    return df


def _mejor(candidatos):
    """De varias tablas candidatas, devuelve la de más filas (la principal)."""
    return max(candidatos, key=lambda d: len(d)) if candidatos else None


def detectar_posiciones(tablas):
    """Tabla de posiciones: tiene Equipo + Pts. + PJ + GF + GC."""
    firma = {"Equipo", "Pts.", "PJ", "GF", "GC"}
    cand = [t for t in tablas if firma.issubset(_cols(t))]
    df = _mejor(cand)
    return _limpiar(df) if df is not None else None


def detectar_goleadores(tablas):
    """Goleadores: Jugador + Equipo + Goles + Part."""
    firma = {"Jugador", "Equipo", "Goles", "Part."}
    cand = [t for t in tablas if firma.issubset(_cols(t))]
    df = _mejor(cand)
    return _limpiar(df) if df is not None else None


def detectar_asistencias(tablas):
    """Asistencias (pases gol): Jugador + Equipo + Asist. + Part."""
    firma = {"Jugador", "Equipo", "Asist.", "Part."}
    cand = [t for t in tablas if firma.issubset(_cols(t))]
    df = _mejor(cand)
    return _limpiar(df) if df is not None else None


DETECTORES = {
    "posiciones": detectar_posiciones,
    "goleadores": detectar_goleadores,
    "asistencias": detectar_asistencias,
}


def tablas_normalizadas(html):
    """
    Devuelve {'posiciones': df, 'goleadores': df, 'asistencias': df}
    con solo las que se hayan podido detectar.
    """
    tablas = extraer_tablas(html)
    out = {}
    for nombre, fn in DETECTORES.items():
        df = fn(tablas)
        if df is not None and len(df):
            out[nombre] = df
    return out
# -*- coding: utf-8 -*-
"""
Descarga de páginas y extracción de tablas.
"""

import io
import requests
import pandas as pd

from .config import USER_AGENT


def descargar_html(url, timeout=30):
    """Descarga el HTML de una página identificándose con un User-Agent."""
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "es-CL,es;q=0.9"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def extraer_tablas(html):
    """
    Extrae todas las tablas HTML como DataFrames.
    Devuelve [] si la página no tiene tablas (típico en páginas con datos
    cargados por JavaScript: ahí haría falta Playwright, ver README).
    """
    try:
        return pd.read_html(io.StringIO(html))
    except ValueError:
        # ValueError = "No tables found"
        return []
