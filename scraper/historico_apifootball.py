# -*- coding: utf-8 -*-
"""
Histórico vía API-Football (api-sports.io). Plan gratis: temporadas 2022-2024.

Baja posiciones (standings) y goleadores (topscorers) de las ligas en LEAGUES
para cada temporada en SEASONS, y los guarda como CSV en
data/csv/historico_apifootball/. Pensado para correr a mano (workflow_dispatch),
no a diario, porque el dato histórico no cambia y el plan gratis da 100 req/día.

La key NUNCA se escribe en el código: se lee del entorno (GitHub Secret
API_FOOTBALL_KEY).
"""

import os
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

import pandas as pd

KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
BASE = "https://v3.football.api-sports.io"
OUT = Path(__file__).resolve().parent.parent / "data" / "csv" / "historico_apifootball"

LEAGUES = {"chile": 265, "premier": 39, "laliga": 140, "seriea": 135,
           "bundesliga": 78, "ligue1": 61, "brasileirao": 71, "argentina": 128}
SEASONS = [2022, 2023, 2024]


def _get(path):
    req = urllib.request.Request(BASE + path, headers={"x-apisports-key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _limite(d):
    errs = d.get("errors")
    if isinstance(errs, dict):
        return any("limit" in str(k).lower() or "limit" in str(v).lower()
                   for k, v in errs.items())
    return False


def _guardar(pos_rows, gol_rows):
    OUT.mkdir(parents=True, exist_ok=True)
    if pos_rows:
        pd.DataFrame(pos_rows).to_csv(OUT / "posiciones_historico.csv", index=False)
    if gol_rows:
        pd.DataFrame(gol_rows).to_csv(OUT / "goleadores_historico.csv", index=False)
    print(f"Guardado: posiciones={len(pos_rows)} filas, goleadores={len(gol_rows)} filas")


def main():
    if not KEY:
        print("Falta API_FOOTBALL_KEY (GitHub Secret). No se ejecuta nada.")
        return
    pos_rows, gol_rows = [], []
    for slug, lid in LEAGUES.items():
        for season in SEASONS:
            try:
                d = _get("/standings?" + urllib.parse.urlencode(
                    {"league": lid, "season": season}))
                if _limite(d):
                    print("Límite diario alcanzado; guardo lo acumulado.")
                    _guardar(pos_rows, gol_rows)
                    return
                resp = d.get("response", [])
                if resp:
                    L = resp[0]["league"]
                    for t in L["standings"][0]:
                        a = t["all"]
                        pos_rows.append({
                            "liga": slug, "torneo": L["name"], "season": season,
                            "pos": t["rank"], "equipo": t["team"]["name"],
                            "pts": t["points"], "pj": a["played"], "g": a["win"],
                            "e": a["draw"], "p": a["lose"],
                            "gf": a["goals"]["for"], "gc": a["goals"]["against"],
                            "dif": t["goalsDiff"]})
                time.sleep(1)

                d = _get("/players/topscorers?" + urllib.parse.urlencode(
                    {"league": lid, "season": season}))
                if _limite(d):
                    print("Límite diario alcanzado; guardo lo acumulado.")
                    _guardar(pos_rows, gol_rows)
                    return
                for i, p in enumerate(d.get("response", []), 1):
                    st = p["statistics"][0]
                    gol_rows.append({
                        "liga": slug, "torneo": st["league"]["name"],
                        "season": season, "pos": i, "jugador": p["player"]["name"],
                        "equipo": st["team"]["name"], "goles": st["goals"]["total"],
                        "asistencias": st["goals"].get("assists"),
                        "partidos": st["games"].get("appearences")})
                time.sleep(1)
                print(f"{slug} {season}: ok")
            except Exception as e:  # noqa: BLE001
                print(f"{slug} {season}: ERROR {e}")
    _guardar(pos_rows, gol_rows)


if __name__ == "__main__":
    main()
