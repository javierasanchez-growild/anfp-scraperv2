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
