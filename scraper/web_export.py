# -*- coding: utf-8 -*-
"""
Exporta CSVs con la FORMA que consume la web (La Hora de King Kong).
Replit lee estos CSVs directo desde el repo. Una hoja/CSV por sección:

  data/csv/tabla.csv               -> sección TABLA (posiciones + zona)
  data/csv/anotados_recibidos.csv  -> gráfico ANOTADOS VS RECIBIDOS
  data/csv/goleadores.csv          -> sección GOLEADORES (goles + asistencias)
  data/csv/datos_momento.csv       -> DATOS DEL MOMENTO (rachas calculadas)

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
ANEXO_URL = ("https://es.wikipedia.org/wiki/"
             "Anexo:Estad%C3%ADsticas_de_la_Liga_de_Primera_2026")
HIST_DIR = CSV_DIR / "historico"


def _tablas(html):
    return pd.read_html(io.StringIO(html))


def _limpiar(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df[[c for c in df.columns if not c.lower().startswith("unnamed") and c != ""]]


def _zona(pos, total):
    if pos <= 4:
        return "Libertadores"
    if pos <= 8:
        return "Sudamericana"
    if pos >= total - 1:
        return "Descenso"
    return "Zona media"


def construir_tabla(tablas):
    firma = {"Equipo", "Pts.", "PJ", "GF", "GC"}
    cand = [t for t in tablas if firma.issubset({str(c).strip() for c in t.columns})]
    if not cand:
        return None
    pos = _limpiar(max(cand, key=len))
    total = len(pos)
    pos["Zona"] = pos["Pos."].astype(int).apply(lambda p: _zona(p, total))
    return pos


def construir_goleadores(tablas):
    """Goleadores con goles Y asistencias reales por jugador, desde el anexo
    (lista completa por equipo). Si el anexo falla, cae a la tabla de la
    pagina de temporada (sin asistencias completas)."""
    try:
        html = requests.get(
            ANEXO_URL, headers={"User-Agent": USER_AGENT}, timeout=30
        ).text
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
        if filas:
            g = pd.DataFrame(filas)
            g = g[g["G"] > 0].sort_values(["G", "A"], ascending=False).reset_index(drop=True)
            g.insert(0, "#", range(1, len(g) + 1))
            return g[["#", "Jugador", "Equipo", "G", "A"]]
    except Exception:
        pass
    # fallback: tabla de la pagina de temporada
    gol = next((t for t in tablas if {"Jugador", "Equipo", "Goles", "Part."}
                .issubset({str(c).strip() for c in t.columns})), None)
    if gol is None:
        return None
    gol = _limpiar(gol).rename(columns={"Goles": "G"})
    gol["A"] = ""
    gol.insert(0, "#", range(1, len(gol) + 1))
    return gol[["#", "Jugador", "Equipo", "G", "A"]]


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


def _append_historico(nombre, df_con_fecha, fecha_captura):
    """Acumula la foto del dia en data/csv/historico/<nombre>_historico.csv.
    Idempotente: reemplaza las filas de ese mismo dia si ya existian."""
    HIST_DIR.mkdir(parents=True, exist_ok=True)
    path = HIST_DIR / f"{nombre}_historico.csv"
    combinado = df_con_fecha
    if path.exists():
        try:
            prev = pd.read_csv(path)
            prev = prev[prev["fecha_captura"].astype(str) != str(fecha_captura)]
            combinado = pd.concat([prev, df_con_fecha], ignore_index=True)
        except Exception:
            combinado = df_con_fecha
    combinado.to_csv(path, index=False)


def exportar(html, fecha_captura, torneo):
    """Genera todos los CSV de la web. Devuelve dict {csv: n_filas}."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    tablas = _tablas(html)
    res = {}

    tabla = construir_tabla(tablas)
    if tabla is not None:
        out = tabla.copy()
        out.insert(0, "torneo", torneo); out.insert(0, "fecha_captura", fecha_captura)
        out.to_csv(CSV_DIR / "tabla.csv", index=False)
        _append_historico("tabla", out, fecha_captura)
        res["tabla.csv"] = len(out)
        avr = tabla[["Equipo", "GF", "GC"]].copy()
        avr.insert(0, "fecha_captura", fecha_captura)
        avr.to_csv(CSV_DIR / "anotados_recibidos.csv", index=False)
        _append_historico("anotados_recibidos", avr, fecha_captura)
        res["anotados_recibidos.csv"] = len(avr)

    gol = construir_goleadores(tablas)
    if gol is not None:
        out = gol.copy()
        out.insert(0, "torneo", torneo); out.insert(0, "fecha_captura", fecha_captura)
        out.to_csv(CSV_DIR / "goleadores.csv", index=False)
        _append_historico("goleadores", out, fecha_captura)
        res["goleadores.csv"] = len(out)

    dm = construir_datos_momento(tablas, tabla, gol)
    out = dm.copy()
    out.insert(0, "fecha_captura", fecha_captura)
    out.to_csv(CSV_DIR / "datos_momento.csv", index=False)
    _append_historico("datos_momento", out, fecha_captura)
    res["datos_momento.csv"] = len(out)
    return res
# -*- coding: utf-8 -*-
"""
Exporta CSVs con la FORMA que consume la web (La Hora de King Kong).
Replit lee estos CSVs directo desde el repo. Una hoja/CSV por sección:

  data/csv/tabla.csv               -> sección TABLA (posiciones + zona)
  data/csv/anotados_recibidos.csv  -> gráfico ANOTADOS VS RECIBIDOS
  data/csv/goleadores.csv          -> sección GOLEADORES (goles + asistencias)
  data/csv/datos_momento.csv       -> DATOS DEL MOMENTO (rachas calculadas)

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
ANEXO_URL = ("https://es.wikipedia.org/wiki/"
             "Anexo:Estad%C3%ADsticas_de_la_Liga_de_Primera_2026")


def _tablas(html):
    return pd.read_html(io.StringIO(html))


def _limpiar(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df[[c for c in df.columns if not c.lower().startswith("unnamed") and c != ""]]


def _zona(pos, total):
    if pos <= 4:
        return "Libertadores"
    if pos <= 8:
        return "Sudamericana"
    if pos >= total - 1:
        return "Descenso"
    return "Zona media"


def construir_tabla(tablas):
    firma = {"Equipo", "Pts.", "PJ", "GF", "GC"}
    cand = [t for t in tablas if firma.issubset({str(c).strip() for c in t.columns})]
    if not cand:
        return None
    pos = _limpiar(max(cand, key=len))
    total = len(pos)
    pos["Zona"] = pos["Pos."].astype(int).apply(lambda p: _zona(p, total))
    return pos


def construir_goleadores(tablas):
    """Goleadores con goles Y asistencias reales por jugador, desde el anexo
    (lista completa por equipo). Si el anexo falla, cae a la tabla de la
    pagina de temporada (sin asistencias completas)."""
    try:
        html = requests.get(
            ANEXO_URL, headers={"User-Agent": USER_AGENT}, timeout=30
        ).text
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
        if filas:
            g = pd.DataFrame(filas)
            g = g[g["G"] > 0].sort_values(["G", "A"], ascending=False).reset_index(drop=True)
            g.insert(0, "#", range(1, len(g) + 1))
            return g[["#", "Jugador", "Equipo", "G", "A"]]
    except Exception:
        pass
    gol = next((t for t in tablas if {"Jugador", "Equipo", "Goles", "Part."}
                .issubset({str(c).strip() for c in t.columns})), None)
    if gol is None:
        return None
    gol = _limpiar(gol).rename(columns={"Goles": "G"})
    gol["A"] = ""
    gol.insert(0, "#", range(1, len(gol) + 1))
    return gol[["#", "Jugador", "Equipo", "G", "A"]]


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


def exportar(html, fecha_captura, torneo):
    """Genera todos los CSV de la web. Devuelve dict {csv: n_filas}."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    tablas = _tablas(html)
    res = {}

    tabla = construir_tabla(tablas)
    if tabla is not None:
        out = tabla.copy()
        out.insert(0, "torneo", torneo); out.insert(0, "fecha_captura", fecha_captura)
        out.to_csv(CSV_DIR / "tabla.csv", index=False)
        res["tabla.csv"] = len(out)
        avr = tabla[["Equipo", "GF", "GC"]].copy()
        avr.insert(0, "fecha_captura", fecha_captura)
        avr.to_csv(CSV_DIR / "anotados_recibidos.csv", index=False)
        res["anotados_recibidos.csv"] = len(avr)

    gol = construir_goleadores(tablas)
    if gol is not None:
        out = gol.copy()
        out.insert(0, "torneo", torneo); out.insert(0, "fecha_captura", fecha_captura)
        out.to_csv(CSV_DIR / "goleadores.csv", index=False)
        res["goleadores.csv"] = len(out)

    dm = construir_datos_momento(tablas, tabla, gol)
    out = dm.copy()
    out.insert(0, "fecha_captura", fecha_captura)
    out.to_csv(CSV_DIR / "datos_momento.csv", index=False)
    res["datos_momento.csv"] = len(out)
    return res
