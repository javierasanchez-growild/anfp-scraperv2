# -*- coding: utf-8 -*-
"""
Punto de entrada del scraper. Se ejecuta con:  python -m scraper.main

Flujo:
  A) RAW_SOURCES: descarga el HTML oficial y lo guarda en data/raw/ (respaldo).
  B) WIKI_SOURCES: descarga el artículo de Wikipedia de la temporada, detecta
     las tablas de posiciones / goleadores / asistencias y las guarda
     NORMALIZADAS en SQLite como serie temporal (una foto por día).
"""

import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from .config import RAW_SOURCES, WIKI_SOURCES, DELAY_SEGUNDOS
from . import db
from . import sources
from . import web_export

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("anfp")

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def capturar_raw(con, fecha_captura, sello):
    """Guarda el HTML crudo de las páginas oficiales (respaldo)."""
    for fuente in RAW_SOURCES:
        nombre, url = fuente["nombre"], fuente["url"]
        try:
            log.info("RAW  %s -> %s", nombre, url)
            html = sources.descargar_html(url)
            (RAW_DIR / f"{nombre}_{sello}.html").write_text(html, encoding="utf-8")
            tablas = sources.extraer_tablas(html)
            for i, dft in enumerate(tablas):
                db.guardar_tabla(con, nombre, i, dft, fecha_captura)
            con.commit()
            db.registrar_log(con, fecha_captura, nombre, url, len(tablas), "OK",
                             f"{len(tablas)} tablas crudas")
        except Exception as e:  # noqa: BLE001
            db.registrar_log(con, fecha_captura, nombre, url, 0, "ERROR", str(e))
            log.error("  ERROR RAW %s: %s", nombre, e)
        time.sleep(DELAY_SEGUNDOS)


def capturar_normalizado(con, fecha_captura):
    """Descarga Wikipedia y llena las tablas normalizadas."""
    total = 0
    for fuente in WIKI_SOURCES:
        torneo, url = fuente["torneo"], fuente["url"]
        try:
            log.info("WIKI %s -> %s", torneo, url)
            html = sources.descargar_html(url)
            normal = sources.tablas_normalizadas(html)
            try:
                web_res = web_export.exportar(html, fecha_captura, torneo)
                log.info("  CSV web -> %s", web_res)
            except Exception as e:  # noqa: BLE001
                log.error("  ERROR web_export %s: %s", torneo, e)
            detalle = []
            for nombre_tabla, df in normal.items():
                tbl, n = db.guardar_normalizada(con, nombre_tabla, df,
                                                fecha_captura, torneo)
                detalle.append(f"{tbl}={n}")
                total += n
            con.commit()
            estado = "OK" if normal else "VACIO"
            db.registrar_log(con, fecha_captura, f"wiki:{torneo}", url,
                             len(normal), estado, ", ".join(detalle) or "sin tablas")
            log.info("  -> %s", ", ".join(detalle) or "sin tablas detectadas")
        except Exception as e:  # noqa: BLE001
            db.registrar_log(con, fecha_captura, f"wiki:{torneo}", url, 0,
                             "ERROR", str(e))
            log.error("  ERROR WIKI %s: %s", torneo, e)
        time.sleep(DELAY_SEGUNDOS)
    return total


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fecha_captura = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sello = datetime.now(timezone.utc).strftime("%Y%m%d")

    con = db.conectar()
    db.inicializar(con)

    capturar_raw(con, fecha_captura, sello)
    total = capturar_normalizado(con, fecha_captura)

    con.close()
    log.info("Listo. Filas normalizadas guardadas hoy: %d", total)


if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
"""
Punto de entrada del scraper. Se ejecuta con:  python -m scraper.main

Flujo:
  A) RAW_SOURCES: descarga el HTML oficial y lo guarda en data/raw/ (respaldo).
  B) WIKI_SOURCES: descarga el artículo de Wikipedia de la temporada, detecta
     las tablas de posiciones / goleadores / asistencias y las guarda
     NORMALIZADAS en SQLite como serie temporal (una foto por día).
"""

import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from .config import RAW_SOURCES, WIKI_SOURCES, DELAY_SEGUNDOS
from . import db
from . import sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("anfp")

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def capturar_raw(con, fecha_captura, sello):
    """Guarda el HTML crudo de las páginas oficiales (respaldo)."""
    for fuente in RAW_SOURCES:
        nombre, url = fuente["nombre"], fuente["url"]
        try:
            log.info("RAW  %s -> %s", nombre, url)
            html = sources.descargar_html(url)
            (RAW_DIR / f"{nombre}_{sello}.html").write_text(html, encoding="utf-8")
            tablas = sources.extraer_tablas(html)
            for i, dft in enumerate(tablas):
                db.guardar_tabla(con, nombre, i, dft, fecha_captura)
            con.commit()
            db.registrar_log(con, fecha_captura, nombre, url, len(tablas), "OK",
                             f"{len(tablas)} tablas crudas")
        except Exception as e:  # noqa: BLE001
            db.registrar_log(con, fecha_captura, nombre, url, 0, "ERROR", str(e))
            log.error("  ERROR RAW %s: %s", nombre, e)
        time.sleep(DELAY_SEGUNDOS)


def capturar_normalizado(con, fecha_captura):
    """Descarga Wikipedia y llena las tablas normalizadas."""
    total = 0
    for fuente in WIKI_SOURCES:
        torneo, url = fuente["torneo"], fuente["url"]
        try:
            log.info("WIKI %s -> %s", torneo, url)
            html = sources.descargar_html(url)
            normal = sources.tablas_normalizadas(html)
            detalle = []
            for nombre_tabla, df in normal.items():
                tbl, n = db.guardar_normalizada(con, nombre_tabla, df,
                                                fecha_captura, torneo)
                detalle.append(f"{tbl}={n}")
                total += n
            con.commit()
            estado = "OK" if normal else "VACIO"
            db.registrar_log(con, fecha_captura, f"wiki:{torneo}", url,
                             len(normal), estado, ", ".join(detalle) or "sin tablas")
            log.info("  -> %s", ", ".join(detalle) or "sin tablas detectadas")
        except Exception as e:  # noqa: BLE001
            db.registrar_log(con, fecha_captura, f"wiki:{torneo}", url, 0,
                             "ERROR", str(e))
            log.error("  ERROR WIKI %s: %s", torneo, e)
        time.sleep(DELAY_SEGUNDOS)
    return total


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fecha_captura = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sello = datetime.now(timezone.utc).strftime("%Y%m%d")

    con = db.conectar()
    db.inicializar(con)

    capturar_raw(con, fecha_captura, sello)
    total = capturar_normalizado(con, fecha_captura)

    con.close()
    log.info("Listo. Filas normalizadas guardadas hoy: %d", total)


if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
"""
Punto de entrada del scraper. Se ejecuta con:  python -m scraper.main

Flujo por cada fuente:
  1. Descarga el HTML.
  2. Guarda el HTML crudo en data/raw/ (respaldo + material para afinar parsers).
  3. Extrae todas las tablas y las guarda en SQLite con la fecha de captura.
  4. Registra el resultado en la tabla scrape_log.
"""

import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from .config import SOURCES, DELAY_SEGUNDOS
from . import db
from . import sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("anfp")

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fecha_captura = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sello = datetime.now(timezone.utc).strftime("%Y%m%d")

    con = db.conectar()
    db.inicializar(con)

    total_tablas = 0
    for fuente in SOURCES:
        nombre, url = fuente["nombre"], fuente["url"]
        try:
            log.info("Descargando %s -> %s", nombre, url)
            html = sources.descargar_html(url)

            # Respaldo del HTML crudo.
            archivo_raw = RAW_DIR / f"{nombre}_{sello}.html"
            archivo_raw.write_text(html, encoding="utf-8")

            tablas = sources.extraer_tablas(html)
            for i, dft in enumerate(tablas):
                db.guardar_tabla(con, nombre, i, dft, fecha_captura)
            con.commit()

            total_tablas += len(tablas)
            db.registrar_log(
                con, fecha_captura, nombre, url, len(tablas), "OK",
                f"{len(tablas)} tablas guardadas",
            )
            log.info("  -> %d tablas guardadas", len(tablas))

        except Exception as e:  # noqa: BLE001
            db.registrar_log(
                con, fecha_captura, nombre, url, 0, "ERROR", str(e)
            )
            log.error("  -> ERROR en %s: %s", nombre, e)

        time.sleep(DELAY_SEGUNDOS)

    con.close()
    log.info("Listo. Total de tablas capturadas hoy: %d", total_tablas)


if __name__ == "__main__":
    main()
