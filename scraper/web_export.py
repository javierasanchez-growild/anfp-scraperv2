# -*- coding: utf-8 -*-
"""
Exporta CSVs con la FORMA que consume la web, por liga.

Estructura en el repo:
  data/csv/tabla.csv, goleadores.csv, ...            -> CHILE (raíz, URLs estables)
  data/csv/<slug>/tabla.csv, goleadores.csv, ...     -> ligas internacionales
  data/csv/historico/...                             -> Chile (serie temporal)
  data/csv/historico/<slug>/...                      -> internacionales

Todo sale de Wikipedia (es), gratis. Las STATS AVANZADAS por partido (xG,
posesión, tiros) NO están en fuentes gratuitas y por eso no se generan aquí.
"""

import io
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import USER_AGENT

CSV_DIR = Path(__file__).resolve().parent.parent / "data" / "csv"
ANEXO_CHILE = ("https://es.wikipedia.org/wiki/"
               "Anexo:Estad%C3%ADsticas_de_la_Liga_de_Primera_2026")


def _tablas(html):
    return pd.read_html(io.StringIO(html))


def _limpiar(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df[[c for c in df.columns
               if not c.lower().startswith("unnamed") and c != ""]]


def _zona(pos, total):
    if pos <= 4:
        return "Libertadores/Champions"
    if pos <= 6:
        return "Internacional"
    if pos >= total - 1:
        return "Descenso"
    return "Zona media"


def construir_tabla(tablas):
    firma = {"Equipo", "Pts.", "PJ", "GF", "GC"}
    cand = [t for t in tablas
            if firma.issubset({str(c).strip() for c in t.columns})]
    if not cand:
        return None
    pos = _limpiar(max(cand, key=len))
    total = len(pos)
    try:
        pos["Zona"] = pos["Pos."].astype(int).apply(lambda p: _zona(p, total))
    except Exception:
        pass
    return pos


def _goleadores_chile():
    """Lista completa por jugador (goles + asistencias) desde el anexo chileno."""
    html = requests.get(ANEXO_CHILE, headers={"User-Agent": USER_AGENT},
                        timeout=30).text
    soup = BeautifulSoup(html, "lxml")
    filas = []
    for tb in soup.find_all("table"):
        try:
            df = pd.read_html(io.StringIO(str(tb)))[0]
        except Exception:
            continue
        cols = [str(c).strip() for c in df.columns]
        if cols[:4] == ["Jugador", "Goles", "Asistencias", "Total"]:
            equipo = None
            prev = tb
            for _ in range(8):
                prev = prev.find_previous(["h3", "h4", "p", "caption", "b", "th"])
                if prev is None:
                    break
                txt = prev.get_text(" ", strip=True)
                if txt and len(txt) < 40 and "Jugador" not in txt:
                    equipo = txt
                    break
            for _, r in df.iterrows():
                filas.append({"Jugador": r["Jugador"], "Equipo": equipo,
                              "G": int(r["Goles"]), "A": int(r["Asistencias"])})
    if not filas:
        return None
    g = pd.DataFrame(filas)
    g = g[g["G"] > 0].sort_values(["G", "A"], ascending=False).reset_index(drop=True)
    g.insert(0, "#", range(1, len(g) + 1))
    return g[["#", "Jugador", "Equipo", "G", "A"]]


def construir_goleadores(tablas, slug):
    """Chile: lista completa con asistencias. Otras ligas: tabla de goleadores
    de la página de temporada (goles; asistencias si la trae)."""
    if slug == "chile":
        try:
            g = _goleadores_chile()
            if g is not None:
                return g
        except Exception:
            pass
    gol = next((t for t in tablas
                if {"Jugador", "Equipo", "Goles", "Part."}
                .issubset({str(c).strip() for c in t.columns})), None)
    if gol is None:
        return None
    gol = _limpiar(gol).rename(columns={"Goles": "G", "Asist.": "A"})
    if "A" not in gol.columns:
        gol["A"] = ""
    gol.insert(0, "#", range(1, len(gol) + 1))
    keep = [c for c in ["#", "Jugador", "Equipo", "G", "A", "Part."] if c in gol.columns]
    return gol[keep]


def _resultados(tablas):
    matches = []
    for t in tablas:
        cols = [str(c) for c in t.columns]
        if any("Local" in c for c in cols) and any("Resultado" in c for c in cols) \
           and any("Visita" in c for c in cols):
            loc = [c for c in t.columns if "Local" in str(c)][0]
            res = [c for c in t.columns if "Resultado" in str(c)][0]
            vis = [c for c in t.columns if "Visita" in str(c)][0]
            mr = re.search(r"Fecha (\d+)", cols[0])
            rnd = int(mr.group(1)) if mr else 0
            for _, r in t.iterrows():
                mm = re.match(r"(\d+)\D+(\d+)", str(r[res]).strip())
                if mm:
                    matches.append((rnd, str(r[loc]).strip(),
                                    int(mm.group(1)), int(mm.group(2)),
                                    str(r[vis]).strip()))
    return matches


def construir_datos_momento(tablas, tabla, goleadores):
    matches = _resultados(tablas)
    rbt = defaultdict(list)
    for rnd, loc, gl, gv, vis in matches:
        rbt[loc].append((rnd, "G" if gl > gv else "E" if gl == gv else "P"))
        rbt[vis].append((rnd, "G" if gv > gl else "E" if gv == gl else "P"))

    def run(seq, target):
        s = 0
        for o in reversed(seq):
            if (target == "inv" and o in ("G", "E")) or (target == "der" and o == "P"):
                s += 1
            else:
                break
        return s

    inv, der = [], []
    for team, l in rbt.items():
        l.sort(key=lambda x: x[0])
        outs = [o for _, o in l]
        inv.append((team, run(outs, "inv")))
        der.append((team, run(outs, "der")))
    inv.sort(key=lambda x: -x[1]); der.sort(key=lambda x: -x[1])

    filas = []
    if inv:
        filas.append(["Racha invicto", inv[0][0], inv[0][1], "partidos sin perder"])
    if der:
        filas.append(["Mas derrotas seguidas", der[0][0], der[0][1], "derrotas consecutivas"])
    if tabla is not None:
        md = tabla.sort_values("GC").iloc[0]
        filas.append(["Mejor defensa", md["Equipo"], int(md["GC"]), "goles recibidos"])
        gf = tabla["GF"].astype(int).sum(); pj = tabla["PJ"].astype(int).sum()
        if pj:
            filas.append(["Promedio goles/partido", "Liga",
                          round(gf / (pj / 2), 2), "proxy de xG (no oficial)"])
    if goleadores is not None and len(goleadores):
        g0 = goleadores.iloc[0]
        filas.append(["Goleador absoluto", g0["Jugador"], g0["G"], str(g0["Equipo"])])
    filas.append(["Promedio xG/partido", "Liga", "N/D",
                  "requiere proveedor de pago (Opta/Sofascore)"])
    return pd.DataFrame(filas, columns=["Metrica", "Equipo/Jugador", "Valor", "Detalle"])


def _append_historico(histdir, nombre, df_con_fecha, fecha_captura):
    histdir.mkdir(parents=True, exist_ok=True)
    path = histdir / f"{nombre}_historico.csv"
    combinado = df_con_fecha
    if path.exists():
        try:
            prev = pd.read_csv(path)
            prev = prev[prev["fecha_captura"].astype(str) != str(fecha_captura)]
            combinado = pd.concat([prev, df_con_fecha], ignore_index=True)
        except Exception:
            combinado = df_con_fecha
    combinado.to_csv(path, index=False)


def exportar(html, fecha_captura, torneo, slug):
    """Genera los CSV de una liga. Chile en la raíz; otras en data/csv/<slug>/."""
    base = CSV_DIR if slug == "chile" else (CSV_DIR / slug)
    histdir = (CSV_DIR / "historico") if slug == "chile" else (CSV_DIR / "historico" / slug)
    base.mkdir(parents=True, exist_ok=True)
    tablas = _tablas(html)
    res = {}

    def escribir(nombre, df):
        df.to_csv(base / f"{nombre}.csv", index=False)
        _append_historico(histdir, nombre, df, fecha_captura)
        res[nombre] = len(df)

    tabla = construir_tabla(tablas)
    if tabla is not None:
        out = tabla.copy()
        out.insert(0, "torneo", torneo); out.insert(0, "fecha_captura", fecha_captura)
        escribir("tabla", out)
        avr = tabla[["Equipo", "GF", "GC"]].copy()
        avr.insert(0, "fecha_captura", fecha_captura)
        escribir("anotados_recibidos", avr)

    gol = construir_goleadores(tablas, slug)
    if gol is not None:
        out = gol.copy()
        out.insert(0, "torneo", torneo); out.insert(0, "fecha_captura", fecha_captura)
        escribir("goleadores", out)

    if slug == "chile":
        dm = construir_datos_momento(tablas, tabla, gol)
        out = dm.copy(); out.insert(0, "fecha_captura", fecha_captura)
        escribir("datos_momento", out)

    return res
