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
