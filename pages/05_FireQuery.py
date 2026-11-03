"""
pages/05_FireQuery.py
================================================================================
FIREQUERY - TERMINAL SQL Y DICCIONARIO DE DATOS
================================================================================

Abre el modelo normalizado al usuario: permite escribir y ejecutar SQL contra
`fpa_normalizada` en MotherDuck, e incorpora el diccionario completo para que
esas consultas puedan escribirse sin documentacion externa.

MEDIDAS DE ESTABILIDAD
----------------------
  * Limite de filas en el resultado mostrado, para no saturar el navegador.
  * Solo lectura: se rechazan las sentencias que modifican. La base la comparten
    el aplicativo y el tablero, y un DROP accidental la dejaria sin datos.
  * Captura de errores: una consulta mal escrita devuelve el mensaje del motor,
    nunca interrumpe el aplicativo.
"""

import pandas as pd
import streamlit as st

from src.query_manager import consultar, estado, explicar_fallo

st.set_page_config(page_title="FireQuery", page_icon="🛰️", layout="wide")

LIMITE_FILAS = 5_000

# Una sola de estas palabras al principio de una sentencia basta para rechazarla.
PROHIBIDAS = {
    "insert", "update", "delete", "drop", "create", "alter", "truncate",
    "replace", "attach", "detach", "copy", "install", "load", "set", "call",
    "export", "import", "pragma", "grant", "revoke",
}

st.title("FireQuery")
st.markdown(
    "Terminal analitica sobre el **modelo normalizado**. Las consultas se "
    "ejecutan con **DuckDB** contra `fpa_normalizada` en MotherDuck."
)

diag = estado()
if not diag.get("ok"):
    st.error("El aplicativo no pudo conectarse al almacen de datos.")
    st.markdown(explicar_fallo(diag))
    st.stop()


def es_solo_lectura(sql):
    """
    Devuelve (permitida, motivo). Se revisa CADA sentencia, no solo la primera:
    `SELECT 1; DROP TABLE incendios` empieza por SELECT y no por eso es inocua.
    """
    limpio = "\n".join(
        linea.split("--")[0] for linea in sql.splitlines()
    )
    for sentencia in limpio.split(";"):
        palabras = sentencia.strip().split()
        if not palabras:
            continue
        primera = palabras[0].lower().strip("(")
        if primera in PROHIBIDAS:
            return False, primera.upper()
    return True, None


# ==============================================================================
# CONSULTAS DE EJEMPLO
# ==============================================================================
EJEMPLOS = {
    "— elegir un ejemplo —": "",
    "Las trece categorias, con su bandera de atribucion": """
SELECT c.causa_id, c.nombre, c.es_atribuida,
       COUNT(*)                        AS incendios,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (), 2) AS pct
FROM incendios i
JOIN causas c ON c.causa_id = i.causa_id
GROUP BY 1,2,3
ORDER BY incendios DESC""".strip(),

    "Cobertura de la atribucion, ano a ano": """
SELECT i.anio_temporada                        AS anio,
       COUNT(*)                                AS incendios,
       ROUND(100.0*AVG(c.es_atribuida), 2)     AS cobertura_pct
FROM incendios i
JOIN causas c ON c.causa_id = i.causa_id
GROUP BY 1
ORDER BY 1""".strip(),

    "Frecuencia contra magnitud, solo causas atribuidas": """
SELECT c.nombre                               AS causa,
       COUNT(*)                               AS incendios,
       ROUND(SUM(i.tamano_acres)/1e6, 2)      AS millones_acres,
       ROUND(AVG(i.tamano_acres), 1)          AS acres_medios,
       ROUND(MEDIAN(i.tamano_acres), 2)       AS acres_mediana
FROM incendios i
JOIN causas c ON c.causa_id = i.causa_id
WHERE c.es_atribuida = 1
GROUP BY 1
ORDER BY millones_acres DESC""".strip(),

    "Ventana estacional con funciones de ventana": """
WITH por_dia AS (
    SELECT c.nombre AS causa,
           dayofyear(CAST(i.fecha_descubrimiento AS DATE)) AS doy,
           COUNT(*) AS n
    FROM incendios i
    JOIN causas c ON c.causa_id = i.causa_id
    WHERE c.es_atribuida = 1
    GROUP BY 1,2
), acumulado AS (
    SELECT causa, doy,
           SUM(n) OVER (PARTITION BY causa ORDER BY doy)::DOUBLE
             / SUM(n) OVER (PARTITION BY causa) AS p
    FROM por_dia
)
SELECT causa,
       MIN(CASE WHEN p >= 0.25 THEN doy END) AS dia_p25,
       MIN(CASE WHEN p >= 0.75 THEN doy END) AS dia_p75,
       MIN(CASE WHEN p >= 0.75 THEN doy END)
         - MIN(CASE WHEN p >= 0.25 THEN doy END) AS amplitud_dias
FROM acumulado
GROUP BY causa
ORDER BY amplitud_dias""".strip(),

    "Las unidades NWCG sin enlace al catalogo auxiliar": """
SELECT u.codigo, u.nombre, COUNT(i.fod_id) AS incendios
FROM unidades_nwcg u
LEFT JOIN incendios i ON i.unidad_id = u.unidad_id
WHERE u.en_catalogo = 0
GROUP BY 1,2
ORDER BY incendios DESC""".strip(),

    "El codigo de unidad que no identifica nada": """
SELECT s.codigo AS sistema, u.codigo AS unidad,
       COUNT(*) AS nombres_distintos
FROM unidades_origen u
JOIN sistemas_origen s ON s.sistema_id = u.sistema_id
GROUP BY 1,2
HAVING COUNT(*) > 1
ORDER BY nombres_distintos DESC
LIMIT 10""".strip(),
}

eleccion = st.selectbox("Consultas de ejemplo", list(EJEMPLOS.keys()))
if eleccion != "— elegir un ejemplo —":
    st.session_state["sql"] = EJEMPLOS[eleccion]

sql = st.text_area(
    "Consulta SQL", key="sql", height=240,
    placeholder="SELECT nombre, es_atribuida FROM causas ORDER BY causa_id",
)

col_ej, col_lim = st.columns([1, 3])
ejecutar = col_ej.button("Ejecutar", type="primary", width="stretch")
limite = col_lim.slider("Filas a mostrar", 100, LIMITE_FILAS, 500, step=100)

if ejecutar and sql and sql.strip():
    permitida, motivo = es_solo_lectura(sql)
    if not permitida:
        st.error(
            f"Sentencia **{motivo}** rechazada. Esta terminal es de solo "
            "lectura: la base la comparten el aplicativo y el tablero."
        )
    else:
        try:
            with st.spinner("Consultando MotherDuck..."):
                df = consultar(f"SELECT * FROM ({sql.rstrip().rstrip(';')}) "
                               f"LIMIT {int(limite)}")
            st.success(f"{len(df):,} filas devueltas (limite {limite:,}).")
            st.dataframe(df, width="stretch", hide_index=True)
            if not df.empty:
                st.download_button(
                    "Descargar como CSV", df.to_csv(index=False).encode("utf-8"),
                    "firequery.csv", "text/csv")
        except Exception as error:
            st.error("El motor rechazo la consulta.")
            st.code(str(error), language="text")

st.markdown("---")


# ==============================================================================
# DICCIONARIO DE DATOS
# ==============================================================================
st.header("Diccionario del modelo normalizado")

ESQUEMA = {
    "incendios": [
        ("fod_id", "INTEGER", "PK. Identificador de la fuente."),
        ("fpa_id", "TEXT", "Identificador global de la fuente. NO es unico: 3 duplicados."),
        ("anio_temporada", "INTEGER", "Ano que imputa la agencia. Difiere de la fecha en 4 casos."),
        ("fecha_descubrimiento", "TEXT", "AAAA-MM-DD. Convertida del dia juliano original."),
        ("hora_descubrimiento", "INTEGER", "0-23. Separada del campo 'HHMM' original."),
        ("minuto_descubrimiento", "INTEGER", "0-59."),
        ("fecha_contencion", "TEXT", "AAAA-MM-DD. Nula en el 47 % de los casos."),
        ("causa_id", "INTEGER", "FK -> causas."),
        ("tamano_acres", "REAL", "Superficie final quemada."),
        ("clase_tamano", "TEXT", "FK -> clases_tamano. Derivable exactamente del tamano."),
        ("latitud / longitud", "REAL", "Coordenadas del punto de origen."),
        ("propietario_id", "INTEGER", "FK -> propietarios. Tenencia del terreno."),
        ("estado_id", "INTEGER", "FK -> estados."),
        ("condado_id", "INTEGER", "FK -> condados. Nulo en 678.148 registros."),
        ("agencia_id", "INTEGER", "FK -> agencias_nwcg."),
        ("unidad_id", "INTEGER", "FK -> unidades_nwcg."),
        ("unidad_origen_id", "INTEGER", "FK -> unidades_origen."),
    ],
    "causas": [
        ("causa_id", "INTEGER", "PK. Codigo STAT_CAUSE_CODE de la fuente, 1 a 13."),
        ("nombre", "TEXT", "Etiqueta original en ingles."),
        ("es_atribuida", "INTEGER", "0 en Miscellaneous y Missing/Undefined; 1 en las once restantes."),
    ],
    "clases_tamano": [
        ("clase", "TEXT", "PK. A a G, norma NWCG."),
        ("hasta", "REAL", "Limite superior. Nulo en la clase abierta G."),
        ("hasta_inclusivo", "INTEGER", "Vale 1 solo en la clase A: '0,25 acres o menos'."),
        ("etiqueta", "TEXT", "Rango en lenguaje natural."),
        ("orden", "INTEGER", "Para ordenar sin depender del alfabeto."),
    ],
    "unidades_nwcg": [
        ("unidad_id", "INTEGER", "PK."),
        ("codigo", "TEXT", "NWCG_REPORTING_UNIT_ID."),
        ("nombre", "TEXT", "Denominacion de la unidad."),
        ("gacc / area_geo", "TEXT", "Centro de coordinacion y area. Del catalogo auxiliar."),
        ("departamento / agencia", "TEXT", "Jerarquia organizativa."),
        ("en_catalogo", "INTEGER", "0 en las 17 unidades que no aparecen en el catalogo auxiliar."),
    ],
    "unidades_origen": [
        ("unidad_origen_id", "INTEGER", "PK."),
        ("sistema_id", "INTEGER", "FK -> sistemas_origen."),
        ("codigo", "TEXT", "SOURCE_REPORTING_UNIT. NO identifica la unidad: TXVFD cubre 946 nombres."),
        ("nombre", "TEXT", "Denominacion. La clave natural es la terna completa."),
    ],
    "condados": [
        ("condado_id", "INTEGER", "PK."),
        ("estado_id", "INTEGER", "FK -> estados."),
        ("fips", "TEXT", "Codigo FIPS de 3 digitos. Se repite entre estados."),
        ("nombre", "TEXT", "Resuelto por mayoria en 3 conflictos documentados."),
    ],
    "propietarios · estados · agencias_nwcg · sistemas_origen": [
        ("*_id", "INTEGER", "PK."),
        ("codigo / nombre", "TEXT", "Etiqueta."),
        ("tipo", "TEXT", "Solo en sistemas_origen: ambito del sistema de procedencia."),
    ],
}

for tabla, columnas in ESQUEMA.items():
    with st.expander(f"`{tabla}`"):
        st.dataframe(pd.DataFrame(columnas, columns=["Columna", "Tipo", "Descripcion"]),
                     width="stretch", hide_index=True)

st.info(
    "**Lo que no esta aqui y hay que construir.** `ambito` institucional y "
    "`region` censal no son columnas: son clasificaciones de esta "
    "investigacion. El aplicativo las expresa como `CASE` sobre "
    "`agencias_nwcg.codigo` y `estados.codigo`. Si las necesita en una consulta, "
    "escribalas igual, o consulte `fpa_analitica`, donde si estan "
    "materializadas en `d_agencia` y `d_estado`."
)
