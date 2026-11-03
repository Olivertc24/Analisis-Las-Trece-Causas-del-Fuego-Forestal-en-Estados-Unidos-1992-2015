"""
src/supabase_manager.py
================================================================================
CONEXION A LA BASE ORIGINAL EN POSTGRESQL (SUPABASE)
================================================================================

El cuestionario SQL no se responde contra el modelo normalizado sino contra la
tabla CRUDA, tal como la distribuye la fuente: 38 columnas, sin claves, con sus
inconsistencias a la vista. Esa tabla vive en PostgreSQL, en Supabase.

POR QUE NO SE ANADE psycopg COMO DEPENDENCIA
--------------------------------------------
DuckDB ya es dependencia del aplicativo, y su extension `postgres` abre la
conexion igual de bien. Anadir un segundo cliente de base de datos solo para
esta pagina seria peso muerto en el despliegue.

Y LO QUE IMPORTA: LA CONSULTA SE EJECUTA EN POSTGRESQL
------------------------------------------------------
`postgres_query` NO trae la tabla para filtrarla aqui: envia el texto de la
consulta al servidor y devuelve el resultado. Es PostgreSQL quien planifica y
ejecuta. Si no fuera asi, la pagina estaria mintiendo sobre lo que demuestra.

El limite de 5.000 filas se aplica DENTRO del SQL que se manda, no despues.
"""

import duckdb
import pandas as pd
import streamlit as st

from src.query_manager import _secreto

TABLA = "fires"


def _cadena():
    url = _secreto("supabase_db_url")
    if url and not str(url).startswith("pega_aqui"):
        return str(url).strip()
    return None


@st.cache_resource(show_spinner="Conectando con PostgreSQL...")
def get_conexion_pg():
    """Devuelve (conexion, diagnostico). La conexion es None si no se pudo abrir."""
    url = _cadena()
    if not url:
        return None, {"ok": False, "motivo": "sin_cadena"}
    try:
        con = duckdb.connect()
        con.execute("INSTALL postgres; LOAD postgres;")
        con.execute(f"ATTACH '{url}' AS pg (TYPE postgres, READ_ONLY)")
        filas = con.execute(
            f"SELECT * FROM postgres_query('pg', 'SELECT COUNT(*) FROM {TABLA}')"
        ).fetchone()[0]
    except Exception as error:
        return None, {"ok": False, "motivo": "conexion", "detalle": str(error)}
    return con, {"ok": True, "filas": filas}


@st.cache_data(ttl=3600, show_spinner=False)
def consultar_pg(sql):
    """
    Ejecuta la consulta EN PostgreSQL y devuelve un DataFrame.

    El texto va entre delimitadores $$ para no tener que escapar las comillas
    simples que aparecen en casi cualquier consulta con literales.
    """
    con, diag = get_conexion_pg()
    if con is None:
        return pd.DataFrame()
    limpio = sql.strip().rstrip(";")
    return con.execute(f"SELECT * FROM postgres_query('pg', $${limpio}$$)").df()


def estado_pg():
    return get_conexion_pg()[1]


def explicar_fallo_pg(diag):
    if diag.get("motivo") == "sin_cadena":
        return (
            "**No hay cadena de conexion a Supabase.**\n\n"
            "Anada `supabase_db_url` a `.streamlit/secrets.toml` (o a "
            "*Settings → Secrets* en Streamlit Community Cloud). Se obtiene en "
            "Supabase: *Connect → Direct → URI*, sustituyendo `[YOUR-PASSWORD]` "
            "por la contrasena de la base de datos."
        )
    detalle = diag.get("detalle", "")
    pistas = ""
    if "could not translate host" in detalle or "Connection refused" in detalle:
        pistas = (
            "\n\n**Probablemente el proyecto este pausado.** Los proyectos "
            "gratuitos de Supabase se pausan tras una semana sin actividad; se "
            "reactivan con un clic desde el panel del proyecto."
        )
    elif "password authentication failed" in detalle:
        pistas = (
            "\n\n**La contrasena no es la correcta.** Es la de la BASE DE DATOS, "
            "no la de la cuenta de Supabase. Se restablece en *Project Settings "
            "→ Database → Reset database password*."
        )
    return f"PostgreSQL rechazo la conexion.{pistas}\n\n```\n{detalle}\n```"
