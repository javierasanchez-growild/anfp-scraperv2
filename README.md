# Scraper diario ANFP → base de datos de fútbol

Captura todos los días (4–5 am hora Chile) las estadísticas públicas del fútbol
chileno (ANFP / Campeonato Chileno) y las acumula en una base de datos SQLite
(`anfp.db`) como serie temporal: un snapshot por día.

Corre solo en **GitHub Actions** (gratis, no necesita tu PC encendido).

## Cómo funciona

- `scraper/config.py` → lista de páginas a scrapear.
- `scraper/main.py` → descarga cada página, guarda el HTML crudo en `data/raw/`,
  extrae todas las tablas y las mete en `anfp.db` con la fecha de captura.
- `.github/workflows/scrape.yml` → lo ejecuta todos los días y guarda los datos
  de vuelta en el repositorio.

La base de datos trabaja en dos capas:

1. **Captura** (automática): cada tabla encontrada se guarda como
   `raw_<fuente>_t<n>` con columna `fecha_captura`. Robusto: nunca se cae aunque
   cambie el diseño del sitio.
2. **Normalización** (la afinas después): tablas limpias y consultables
   (posiciones, goleadores, fixture…) construidas a partir de los datos reales
   ya capturados.

## Activarlo (una sola vez)

1. Crea un repositorio nuevo en GitHub (puede ser privado).
2. Sube todos estos archivos respetando las carpetas.
3. Ve a la pestaña **Actions** y acepta habilitar los workflows.
4. Entra a "Scraping ANFP diario" y pulsa **Run workflow** para probarlo ya
   (no esperes a las 4 am).
5. Revisa que aparezca `anfp.db` y archivos en `data/raw/` en el repo.

Después de eso corre solo cada día.

## Detalles útiles

- **Hora**: el cron está en `0 8 * * *` (UTC) = 04:00 invierno / 05:00 verano
  en Chile. Para clavar las 4 am todo el año, pon dos crons (`0 7 * * *` y
  `0 8 * * *`) y agrega al inicio de `main.py` un chequeo que solo siga si la
  hora local de Santiago es las 4. Para un job nocturno normalmente no hace falta.
- **Páginas con JavaScript / widgets** (caso confirmado de la ANFP): las
  estadísticas NO vienen como tablas HTML, ni siquiera renderizando con un
  navegador real. Salen de un feed/endpoint dinámico (tipo DWOS) o de widgets
  con divs. Hay que (a) localizar ese feed mirando las peticiones de red del
  navegador, o (b) parsear los divs del widget con selectores CSS. Cowork hace
  esta "fase de descubrimiento" en vivo y deja los parsers apuntando a la
  fuente correcta.
- **Fuente de respaldo robusta**: las páginas "Anexo:Estadísticas de la Liga de
  Primera" de Wikipedia SÍ traen tablas HTML limpias (posiciones, goleadores,
  asistencias, minutaje…) y `pandas.read_html` las parsea sin problema. Sirven
  como verificación o complemento de los datos oficiales.
- **Cuando crezca la BBDD**: SQLite en el repo sirve perfecto para empezar. Si
  quieres consultarla desde otras apps, el paso siguiente es una base en la nube
  (Turso/libSQL o Supabase Postgres).

## Buenas prácticas ya incluidas

- `User-Agent` identificable (edítalo en `config.py` con tu email).
- Espera de 2 segundos entre peticiones.
- Respaldo del HTML crudo + log de cada corrida en la tabla `scrape_log`.
