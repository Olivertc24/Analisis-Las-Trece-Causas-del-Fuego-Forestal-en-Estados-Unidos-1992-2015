"""
src/query_manager.py
================================================================================
CONEXION AL ALMACEN EN MOTHERDUCK
================================================================================

El aplicativo no lleva datos consigo. Consulta la base normalizada alojada en
MotherDuck, de modo que el repositorio no versiona ni un solo byte de datos y
el aplicativo desplegado y el local leen exactamente lo mismo.

DE DONDE SALE EL TOKEN, EN ESTE ORDEN
-------------------------------------
  1. `st.secrets`               -> despliegue en Streamlit Community Cloud,
                                   y desarrollo local con .streamlit/secrets.toml
  2. variable de entorno        -> `motherduck_token` o `MOTHERDUCK_TOKEN`
  3. flujo de dispositivo       -> solo en local: DuckDB abre el navegador.
                                   No sirve desplegado, porque alli no hay
                                   nadie que confirme en una pantalla.

Si no hay ninguno, no se lanza una excepcion cruda: `estado()` devuelve el
diagnostico para que la interfaz explique que falta y como obtenerlo.

POR QUE `st.cache_resource` Y NO `st.cache_data`
------------------------------------------------
La conexion es un recurso vivo, no un valor serializable. Con `cache_data`
Streamlit intentaria copiarla en cada ejecucion del script -es decir, en cada
interaccion del usuario- y abriria una conexion nueva por clic.
"""

import os

import duckdb
import pandas as pd
import streamlit as st

BASE_POR_DEFECTO = "fpa_normalizada"

TABLAS_ESPERADAS = [
    "incendios", "causas", "propietarios", "clases_tamano", "agencias_nwcg",
    "estados", "sistemas_origen", "condados", "unidades_nwcg", "unidades_origen",
]


def _token_valido(valor):
    """
    Devuelve el token si parece uno de verdad, y None en caso contrario.

    POR QUE SE VALIDA LA FORMA Y NO SOLO EL MARCADOR DE LA PLANTILLA.
    MotherDuck espera un JWT: tres secciones separadas por dos puntos. Si se
    le manda cualquier otra cosa responde con un error de autenticacion que no
    distingue "token equivocado" de "token sin rellenar", y el diagnostico que
    ve el usuario acaba apuntando al sitio equivocado. Comprobando la forma
    aqui, el aplicativo puede decir exactamente cual de las dos cosas pasa.
    """
    if not valor:
        return None
    valor = str(valor).strip()
    if not valor or valor.startswith("pega_aqui"):
        return None
    if valor.count(".") != 2:          # no tiene forma de JWT
        return None
    return valor


def _secreto(clave, defecto=None):
    """Lee de st.secrets sin reventar cuando no hay archivo de secretos."""
    try:
        if clave in st.secrets:
            valor = str(st.secrets[clave]).strip()
            if valor:
                return valor
    except Exception:
        pass
    return defecto


def _token():
    """
    Busca el token en los tres origenes y devuelve el primero que sea valido.

    CUIDADO CON EL ENTORNO. Streamlit EXPORTA cada clave de `secrets.toml` como
    variable de entorno con el mismo nombre. Es decir: el fallback a
    `os.environ` NO es independiente de `st.secrets`, y un marcador sin
    rellenar entra por ahi aunque se haya filtrado al leer los secretos. Por
    eso la validacion se aplica a los tres origenes y no a uno solo.
    """
    for valor in (_secreto("motherduck_token"),
                  os.environ.get("motherduck_token"),
                  os.environ.get("MOTHERDUCK_TOKEN")):
        valido = _token_valido(valor)
        if valido:
            return valido
    return None


def _hay_marcador():
    """True si existe un token pero es el marcador de la plantilla, sin rellenar."""
    crudo = (_secreto("motherduck_token")
             or os.environ.get("motherduck_token")
             or os.environ.get("MOTHERDUCK_TOKEN") or "")
    return str(crudo).strip().startswith("pega_aqui")


def _nombre_base():
    return _secreto("motherduck_database", BASE_POR_DEFECTO)


@st.cache_resource(show_spinner="Conectando con MotherDuck...")
def get_conexion():
    """
    Devuelve (conexion, diagnostico). La conexion es None si no se pudo abrir;
    el diagnostico explica por que, en lenguaje que la interfaz pueda mostrar.
    """
    token = _token()
    base = _nombre_base()

    try:
        if token:
            con = duckdb.connect(f"md:{base}?motherduck_token={token}")
            origen = "token"
        else:
            # Sin token: DuckDB abre el flujo de dispositivo. Util en local,
            # inviable desplegado. Si no hay quien confirme, falla aqui.
            con = duckdb.connect(f"md:{base}")
            origen = "flujo de dispositivo"
    except Exception as error:
        return None, {
            "ok": False,
            "motivo": "conexion",
            "detalle": str(error),
            "base": base,
            "con_token": bool(token),
            "marcador": _hay_marcador(),
        }

    faltantes = _tablas_faltantes(con)
    if faltantes:
        return con, {
            "ok": False, "motivo": "tablas", "faltantes": faltantes,
            "base": base, "origen": origen,
        }

    return con, {"ok": True, "base": base, "origen": origen}


def _tablas_faltantes(con):
    try:
        presentes = {f[0] for f in con.execute(
            "SELECT table_name FROM information_schema.tables").fetchall()}
    except Exception:
        return list(TABLAS_ESPERADAS)
    return [t for t in TABLAS_ESPERADAS if t not in presentes]


@st.cache_data(ttl=3600, show_spinner=False)
def consultar(sql, parametros=None):
    """
    Ejecuta una consulta y devuelve un DataFrame.

    Se cachea por el TEXTO de la consulta: dos llamadas con el mismo SQL y los
    mismos parametros no vuelven a la nube. Es lo que hace tolerable que cada
    interaccion del usuario reejecute el script entero.
    """
    con, estado = get_conexion()
    if con is None:
        return pd.DataFrame()
    return con.execute(sql, parametros or []).df()


def estado():
    """Diagnostico de la conexion, para que la interfaz lo muestre."""
    return get_conexion()[1]


def explicar_fallo(diagnostico):
    """Texto en Markdown que explica un fallo de conexion y como resolverlo."""
    if diagnostico.get("motivo") == "tablas":
        return (
            f"La base **`{diagnostico['base']}`** respondio, pero le faltan "
            f"tablas: `{'`, `'.join(diagnostico['faltantes'])}`.\n\n"
            "Ejecute la carga desde la carpeta `Base de datos/`:\n\n"
            "```bash\nduckdb < carga_motherduck.sql\n```"
        )
    if diagnostico.get("con_token"):
        return (
            "El token existe pero MotherDuck lo rechazo o la base no esta "
            "disponible.\n\n"
            f"Detalle del motor:\n\n```\n{diagnostico.get('detalle','')}\n```"
        )
    if diagnostico.get("marcador"):
        return (
            "**El archivo `.streamlit/secrets.toml` existe pero conserva el "
            "marcador de la plantilla.** Sustituya el valor de "
            "`motherduck_token` por un token real.\n\n"
            "Se genera en app.motherduck.com → *Settings → Access tokens*, y "
            "debe ser un **service token**: el de sesion personal caduca y no "
            "sirve para un aplicativo desplegado."
        )
    return (
        "**No hay token de MotherDuck.**\n\n"
        "En local, copie la plantilla y pegue su token:\n\n"
        "```bash\ncp .streamlit/secrets.toml.example .streamlit/secrets.toml\n```\n\n"
        "En Streamlit Community Cloud, pegue ese mismo contenido en "
        "*Settings → Secrets*.\n\n"
        "El token se genera en app.motherduck.com → *Settings → Access tokens*. "
        "Debe ser un **service token**: el de sesion personal caduca y no sirve "
        "para un aplicativo desplegado."
    )
