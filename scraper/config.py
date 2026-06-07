# -*- coding: utf-8 -*-
"""
Configuración de fuentes.

RAW_SOURCES: páginas oficiales (solo respaldo de HTML crudo; cargan por JS).
WIKI_SOURCES: artículos de Wikipedia (es) de cada temporada. De aquí salen las
tablas normalizadas en SQLite y los CSV con forma de web. Cada liga tiene un
'slug' que define su carpeta en data/csv/<slug>/ (Chile va en la raíz para
mantener URLs estables). Para cambiar de temporada, actualiza la URL y el año.
"""

RAW_SOURCES = [
    {"nombre": "campeonato_home", "url": "https://www.campeonatochileno.cl/"},
    {"nombre": "anfp_campeonato_chileno",
     "url": "https://www.anfp.cl/categorias/campeonato-chileno/"},
]

WIKI_SOURCES = [
    {"slug": "chile", "torneo": "Liga de Primera 2026",
     "url": "https://es.wikipedia.org/wiki/Liga_de_Primera_2026"},
    {"slug": "premier", "torneo": "Premier League 2025-26",
     "url": "https://es.wikipedia.org/wiki/Premier_League_2025-26"},
    {"slug": "laliga", "torneo": "LaLiga 2025-26",
     "url": "https://es.wikipedia.org/wiki/Primera_Divisi%C3%B3n_de_Espa%C3%B1a_2025-26"},
    {"slug": "seriea", "torneo": "Serie A 2025-26",
     "url": "https://es.wikipedia.org/wiki/Serie_A_(Italia)_2025-26"},
    {"slug": "bundesliga", "torneo": "Bundesliga 2025-26",
     "url": "https://es.wikipedia.org/wiki/1._Bundesliga_2025-26"},
    {"slug": "ligue1", "torneo": "Ligue 1 2025-26",
     "url": "https://es.wikipedia.org/wiki/Ligue_1_2025-26"},
    {"slug": "brasileirao", "torneo": "Brasileirao 2026",
     "url": "https://es.wikipedia.org/wiki/Campeonato_Brasile%C3%B1o_de_F%C3%BAtbol_Serie_A_2026"},
    {"slug": "argentina", "torneo": "Primera Argentina 2026",
     "url": "https://es.wikipedia.org/wiki/Campeonato_de_Primera_Divisi%C3%B3n_2026_(Argentina)"},
]

USER_AGENT = (
    "anfp-stats-bot/1.0 (proyecto personal de base de datos de futbol; "
    "contacto: TU_EMAIL_AQUI)"
)

DELAY_SEGUNDOS = 2
