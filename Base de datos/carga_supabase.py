"""
carga_supabase.py
================================================================================
CARGA DE LA TABLA ORIGINAL EN POSTGRESQL (SUPABASE)
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) - Computacion II
================================================================================

Sube `Fires` -la tabla cruda de la fuente, con sus 1.880.465 filas- a la base
PostgreSQL alojada en Supabase, que es la que responde el cuestionario SQL.

    python3 carga_supabase.py                 # carga completa, midiendo
    python3 carga_supabase.py --solo-medir    # no carga: solo informa del tamano
    python3 carga_supabase.py --limite-mb 450 # corta antes de llegar al limite

La cadena de conexion se lee de la variable de entorno SUPABASE_DB_URL o, si no
esta, de `.streamlit/secrets.toml`. Nunca se escribe en este archivo.

--------------------------------------------------------------------------------
POR QUE SIN CLAVE PRIMARIA
--------------------------------------------------------------------------------
La tabla sin la columna `Shape` ocupa en PostgreSQL unos 470 MB: 387,5 MB de
datos, 57,4 MB de cabeceras de fila y 7,2 MB de punteros, mas el relleno de
paginas. El plan gratuito de Supabase ofrece 500 MB.

Un indice primario sobre `FOD_ID` anadiria unos 40 MB que harian inviable la
carga, y no aporta nada al cuestionario: son consultas analiticas que recorren
la tabla entera, donde PostgreSQL prefiere el recorrido secuencial aunque el
indice exista. La tabla se carga por tanto SIN clave primaria, decision
documentada tambien en el README.

--------------------------------------------------------------------------------
POR QUE POR LOTES DE ANOS, MIDIENDO
--------------------------------------------------------------------------------
Porque la holgura es escasa y agotar la cuota de Supabase deja el proyecto en
modo restringido. Cargar ano a ano y consultar `pg_database_size` despues de
cada lote permite parar en el ultimo ano completo y documentarlo, en lugar de
reventar la cuota a ciegas y tener que limpiar.

--------------------------------------------------------------------------------
QUE SE EXCLUYE Y POR QUE
--------------------------------------------------------------------------------
Solo `Shape`: geometria SpatiaLite de tipo POINT, 107,6 MB, que duplica
exactamente LATITUDE y LONGITUDE -ambas conservadas- y que PostgreSQL no puede
leer sin PostGIS. Las otras 38 columnas se cargan integras, incluidas las casi
vacias, porque el cuestionario se responde contra la fuente tal como es.
"""

import argparse
import os
import pathlib
import sys
import time

import duckdb

AQUI = pathlib.Path(__file__).resolve().parent
ORIGEN = AQUI / "fpa_fod.sqlite"
TABLA = "fires"
ANIOS = range(1992, 2016)

# Tipos elegidos uno a uno. Los enteros pequenos van a SMALLINT y las fechas
# julianas a DATE: la diferencia frente a dejarlo todo en TEXT y DOUBLE son
# decenas de megabytes, y aqui cada megabyte cuenta.
DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLA} (
    objectid                   INTEGER,
    fod_id                     INTEGER,
    fpa_id                     TEXT,
    source_system_type         TEXT,
    source_system              TEXT,
    nwcg_reporting_agency      TEXT,
    nwcg_reporting_unit_id     TEXT,
    nwcg_reporting_unit_name   TEXT,
    source_reporting_unit      TEXT,
    source_reporting_unit_name TEXT,
    local_fire_report_id       TEXT,
    local_incident_id          TEXT,
    fire_code                  TEXT,
    fire_name                  TEXT,
    ics_209_incident_number    TEXT,
    ics_209_name               TEXT,
    mtbs_id                    TEXT,
    mtbs_fire_name             TEXT,
    complex_name               TEXT,
    fire_year                  SMALLINT,
    discovery_date             DATE,
    discovery_doy              SMALLINT,
    discovery_time             TEXT,
    stat_cause_code            SMALLINT,
    stat_cause_descr           TEXT,
    cont_date                  DATE,
    cont_doy                   SMALLINT,
    cont_time                  TEXT,
    fire_size                  DOUBLE PRECISION,
    fire_size_class            CHAR(1),
    latitude                   DOUBLE PRECISION,
    longitude                  DOUBLE PRECISION,
    owner_code                 SMALLINT,
    owner_descr                TEXT,
    state                      TEXT,
    county                     TEXT,
    fips_code                  TEXT,
    fips_name                  TEXT
);
"""

# LAS FECHAS JULIANAS SE CONVIERTEN CON ARITMETICA ENTERA DE DIAS, NO CON
# to_timestamp(). La version con timestamp devuelve un valor CON ZONA HORARIA, y
# al reducirlo a DATE se aplica la zona local: estando detras de UTC, toda fecha
# retrocedia un dia. El sintoma era silencioso -fechas plausibles, pero todas
# corridas-. La version de abajo no toca zonas horarias y se verifico contra la
# propia fuente: cero discrepancias frente a DISCOVERY_DOY en los 1.880.465
# registros, y las cuatro frente a FIRE_YEAR son los casos de Oregon ya
# documentados en la normalizacion.
SELECT_ANIO = """
SELECT
    CAST(OBJECTID AS INTEGER), CAST(FOD_ID AS INTEGER), FPA_ID,
    SOURCE_SYSTEM_TYPE, SOURCE_SYSTEM, NWCG_REPORTING_AGENCY,
    NWCG_REPORTING_UNIT_ID, NWCG_REPORTING_UNIT_NAME,
    SOURCE_REPORTING_UNIT, SOURCE_REPORTING_UNIT_NAME,
    LOCAL_FIRE_REPORT_ID, LOCAL_INCIDENT_ID, FIRE_CODE, FIRE_NAME,
    ICS_209_INCIDENT_NUMBER, ICS_209_NAME, MTBS_ID, MTBS_FIRE_NAME,
    COMPLEX_NAME,
    CAST(FIRE_YEAR AS SMALLINT),
    DATE '1970-01-01' + CAST(CAST(DISCOVERY_DATE AS DOUBLE) - 2440587.5 AS INTEGER),
    CAST(DISCOVERY_DOY AS SMALLINT), DISCOVERY_TIME,
    CAST(STAT_CAUSE_CODE AS SMALLINT), STAT_CAUSE_DESCR,
    DATE '1970-01-01' + CAST(CAST(CONT_DATE AS DOUBLE) - 2440587.5 AS INTEGER),
    CAST(CONT_DOY AS SMALLINT), CONT_TIME,
    CAST(FIRE_SIZE AS DOUBLE), FIRE_SIZE_CLASS,
    CAST(LATITUDE AS DOUBLE), CAST(LONGITUDE AS DOUBLE),
    CAST(OWNER_CODE AS SMALLINT), OWNER_DESCR,
    STATE, COUNTY, FIPS_CODE, FIPS_NAME
FROM src.Fires
WHERE FIRE_YEAR = ?
"""


def cadena_de_conexion():
    url = os.environ.get("SUPABASE_DB_URL")
    if url:
        return url.strip()
    secretos = AQUI.parent / ".streamlit" / "secrets.toml"
    if secretos.exists():
        import tomllib
        datos = tomllib.loads(secretos.read_text())
        url = str(datos.get("supabase_db_url", "")).strip()
        if url and not url.startswith("pega_aqui"):
            return url
    sys.exit(
        "No hay cadena de conexion.\n\n"
        "  export SUPABASE_DB_URL='postgresql://...'\n\n"
        "o anada `supabase_db_url` a .streamlit/secrets.toml.\n"
        "Se obtiene en Supabase: Project Settings -> Database -> Connection "
        "string, pestana URI."
    )


def tamano_mb(con):
    return con.execute(
        "SELECT pg_database_size(current_database()) / 1048576.0"
    ).fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite-mb", type=float, default=460.0,
                    help="Corta la carga al superar este tamano. Por defecto 460, "
                         "que deja 40 MB de margen bajo el limite de 500.")
    ap.add_argument("--solo-medir", action="store_true")
    args = ap.parse_args()

    if not ORIGEN.exists():
        sys.exit(f"No se encuentra {ORIGEN}")

    url = cadena_de_conexion()
    con = duckdb.connect()
    con.execute("INSTALL sqlite; LOAD sqlite; INSTALL postgres; LOAD postgres;")
    con.execute("SET GLOBAL sqlite_all_varchar=true")
    con.execute(f"ATTACH '{ORIGEN}' AS src (TYPE sqlite, READ_ONLY)")
    con.execute(f"ATTACH '{url}' AS pg (TYPE postgres)")

    if args.solo_medir:
        print(f"  tamano actual de la base: {tamano_mb(con):.1f} MB")
        filas = con.execute(f"SELECT COUNT(*) FROM pg.{TABLA}").fetchone()[0]
        print(f"  filas en {TABLA}: {filas:,}")
        return

    print("  creando la tabla (sin clave primaria)...")
    con.execute(f"CALL postgres_execute('pg', $${DDL}$$)")
    con.execute(f"CALL postgres_execute('pg', 'TRUNCATE TABLE {TABLA}')")

    total = 0
    t0 = time.time()
    print(f"\n  {'ano':>5}  {'filas':>9}  {'acumulado':>10}  {'base (MB)':>10}  {'seg':>6}")
    print(f"  {'-'*5}  {'-'*9}  {'-'*10}  {'-'*10}  {'-'*6}")

    for anio in ANIOS:
        t1 = time.time()
        con.execute(f"INSERT INTO pg.{TABLA} {SELECT_ANIO}", [anio])
        n = con.execute("SELECT COUNT(*) FROM src.Fires WHERE FIRE_YEAR = ?",
                        [anio]).fetchone()[0]
        total += n
        mb = tamano_mb(con)
        print(f"  {anio:>5}  {n:>9,}  {total:>10,}  {mb:>10.1f}  {time.time()-t1:>6.1f}")

        if mb > args.limite_mb:
            print(f"\n  CORTE EN {anio}: la base alcanzo {mb:.1f} MB, por encima "
                  f"del limite de {args.limite_mb:.0f} MB.")
            print(f"  Cargados {total:,} de 1.880.465 incendios "
                  f"({100*total/1880465:.2f} %), de 1992 a {anio}.")
            print("  Esto NO es un fallo: es el corte documentado que evita "
                  "agotar la cuota.")
            break
    else:
        print(f"\n  CARGA COMPLETA: {total:,} filas en {time.time()-t0:.0f} s.")
        print(f"  Tamano final: {tamano_mb(con):.1f} MB.")

    print("\n  verificacion contra la fuente:")
    origen = con.execute("SELECT COUNT(*) FROM src.Fires").fetchone()[0]
    destino = con.execute(f"SELECT COUNT(*) FROM pg.{TABLA}").fetchone()[0]
    print(f"    filas en la fuente : {origen:,}")
    print(f"    filas en PostgreSQL: {destino:,}")
    acres_o = con.execute("SELECT ROUND(SUM(FIRE_SIZE)) FROM src.Fires "
                          "WHERE FIRE_YEAR <= ?", [anio]).fetchone()[0]
    acres_d = con.execute(f"SELECT ROUND(SUM(fire_size)) FROM pg.{TABLA}").fetchone()[0]
    print(f"    acres en la fuente (hasta {anio}): {acres_o:,.0f}")
    print(f"    acres en PostgreSQL              : {acres_d:,.0f}")


if __name__ == "__main__":
    main()
