# -*- coding: utf-8 -*-
"""
Configuración de fuentes.

Dos tipos de fuente:

1) RAW_SOURCES: páginas oficiales (ANFP / Campeonato Chileno). Sus estadísticas
   se cargan por JavaScript / AJAX (parámetro ?liga=ID), así que NO vienen como
   tablas HTML. Se guarda igual el HTML crudo en data/raw/ como respaldo y como
   material por si más adelante se quiere reversear ese feed dinámico.

2) WIKI_SOURCES: artículos de Wikipedia de la temporada. SÍ traen tablas HTML
   limpias (posiciones, goleadores, asistencias) que pandas.read_html parsea sin
   problema. De aquí salen las tablas NORMALIZADAS y consultables de la BBDD.
"""

# Páginas oficiales -> solo respaldo de HTML crudo.
RAW_SOURCES = [
    {
        "nombre": "campeonato_home",
        "url": "https://www.campeonatochileno.cl/",
    },
    {
        "nombre": "anfp_campeonato_chileno",
        "url": "https://www.anfp.cl/categorias/campeonato-chileno/",
    },
]

# Wikipedia -> datos normalizados (posiciones, goleadores, asistencias).
# Para cambiar de temporada, basta con actualizar el año de la URL y el torneo.
WIKI_SOURCES = [
    {
        "torneo": "Liga de Primera 2026",
        "url": "https://es.wikipedia.org/wiki/Liga_de_Primera_2026",
    },
]

# Identifícate de forma honesta ante el sitio (buena práctica de scraping).
USER_AGENT = (
    "anfp-stats-bot/1.0 (proyecto personal de base de datos de futbol chileno; "
    "contacto: TU_EMAIL_AQUI)"
)

# Segundos de espera entre una petición y otra (no golpear el sitio).
DELAY_SEGUNDOS = 2
# -*- coding: utf-8 -*-
"""
Configuración de fuentes a scrapear.

Cada fuente tiene:
  - nombre: identificador corto (se usa para nombrar tablas y archivos)
  - url:    página de donde se extraen los datos

IMPORTANTE: esta lista es un PUNTO DE PARTIDA. En la primera ejecución el
scraper guarda el HTML crudo de cada página en data/raw/, así que podrás
(o podrá Cowork) revisar qué páginas realmente traen tablas y afinar esta
lista con las URLs exactas de cada estadística (posiciones, goleadores,
fixture, asistencias, tarjetas, etc.).
"""

SOURCES = [
    {
        "nombre": "campeonato_home",
        "url": "https://www.campeonatochileno.cl/",
    },
    {
        "nombre": "campeonato_estadisticas",
        "url": "https://www.campeonatochileno.cl/estadisticas/",
    },
    {
        "nombre": "anfp_campeonato_chileno",
        "url": "https://www.anfp.cl/categorias/campeonato-chileno/",
    },
    # TODO (fase de descubrimiento): agregar URLs específicas que detectes,
    # por ejemplo tablas de posiciones por torneo, goleadores, fixture, etc.
]

# Identifícate de forma honesta ante el sitio (buena práctica de scraping).
USER_AGENT = (
    "anfp-stats-bot/1.0 (proyecto personal de base de datos de fútbol; "
    "contacto: TU_EMAIL_AQUI)"
)

# Segundos de espera entre una petición y otra (no golpear el sitio).
DELAY_SEGUNDOS = 2
