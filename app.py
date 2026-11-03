"""
app.py
================================================================================
PORTADA DEL APLICATIVO
Investigacion: Las trece causas del fuego forestal en Estados Unidos
1992-2015. 1.880.465 incendios, 140,13 millones de acres.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) - Computacion II
================================================================================

Esta pagina es la entrada: presenta la investigacion, enuncia la pregunta que
la ordena y orienta hacia la seccion que el lector busca.

NO CONTIENE ANALISIS. Todos los estadisticos viven en
`pages/03_El_Hueco_y_las_Once.py`, de modo que el recorrido del aplicativo
reproduzca el de un trabajo escrito.

Lo unico que ejecuta es la verificacion de la conexion con MotherDuck, para que
un fallo de credenciales se reporte aqui y no a mitad de un grafico.
"""

import streamlit as st

from src.query_manager import estado, explicar_fallo

st.set_page_config(
    page_title="Las trece causas | EE.UU. 1992-2015",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.justificado { text-align: justify; line-height: 1.65; }
.caja-pregunta {
    background-color: #160F0C;
    border-top: 4px solid #F77636;
    border-bottom: 4px solid #F77636;
    padding: 26px 30px; border-radius: 8px; margin: 26px 0;
}
.tarjeta {
    background-color: #1C1512; border-left: 5px solid #F77636;
    border-radius: 6px; padding: 14px 18px; margin-bottom: 12px; height: 100%;
}
.tarjeta b { color: #F77636; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# VERIFICACION DE LA CONEXION
# ==============================================================================
diag = estado()

with st.sidebar:
    st.title("🔥 Panel de causas")
    if diag.get("ok"):
        st.success(f"Conectado a `{diag['base']}`")
        st.caption(f"Autenticacion: {diag['origen']}.")
    else:
        st.error("Sin conexion con MotherDuck")
    st.caption(
        "Los controles del universo de analisis estan en **El Hueco y las "
        "Once**, que es donde se calculan los estadisticos."
    )
    st.markdown("---")
    st.caption(
        "Fuente: Short, K. C. (2017). *Spatial wildfire occurrence data for "
        "the United States, 1992-2015* (FPA_FOD_20170508), 4.ª edicion. "
        "Forest Service Research Data Archive."
    )

st.image("assets/banner_causas.png", width="stretch")

if not diag.get("ok"):
    st.error("El aplicativo no pudo conectarse al almacen de datos.")
    st.markdown(explicar_fallo(diag))
    st.stop()

st.markdown("#### Perfil comparado de cada causa y cobertura de la atribucion, 1992-2015")

st.markdown("""
<div class="justificado">
Investigacion estadistica descriptiva sobre <b>1.880.465 incendios forestales
geo-referenciados</b> ocurridos en Estados Unidos entre 1992 y 2015, que suman
<b>140,13 millones de acres</b> de superficie quemada.<br><br>

El registro federal clasifica cada incendio en <b>trece causas estadisticas</b>.
Este trabajo las describe una por una -frecuencia, magnitud, estacionalidad y
geografia- y, antes de eso, mide <b>cuantas de esas trece nombran realmente una
causa</b>.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="caja-pregunta">
<b style="color:#F77636;">Pregunta de investigacion</b><br><br>
¿Como se diferencian entre si las trece causas registradas del fuego forestal en
Estados Unidos entre 1992 y 2015, en cuanto a su frecuencia, su magnitud, su
distribucion estacional y su localizacion geografica, y en que medida el grado
de cobertura de la atribucion condiciona la lectura de esas diferencias?
</div>
""", unsafe_allow_html=True)

st.warning(
    "**Dos de las trece no son causas.** `Miscellaneous` (17,22 %) y "
    "`Missing/Undefined` (8,87 %) no nombran ningun mecanismo: suman el "
    "**26,09 %** del registro. Por eso cada resultado de esta investigacion se "
    "presenta **dos veces** -sobre el registro completo y sobre el subconjunto "
    "atribuido- y la distancia entre ambas lecturas es ella misma un resultado."
)


# ==============================================================================
# GUIA DE NAVEGACION
# ==============================================================================
st.markdown("---")
st.header("Como recorrer este aplicativo")
st.markdown(
    "El aplicativo reproduce la estructura de un trabajo de investigacion "
    "escrito. Cada seccion del menu lateral corresponde a una parte del informe."
)

SECCIONES = [
    ("1", "Marco Metodologico",
     "El problema, el nivel de la investigacion, los objetivos y la "
     "operacionalizacion de las variables."),
    ("2", "Marco Teorico",
     "El registro FPA FOD, la arquitectura institucional del NWCG y los "
     "fundamentos tecnicos de la infraestructura de datos."),
    ("3", "El Hueco y las Once",
     "<b>Analisis y resultados.</b> La cobertura de la atribucion, el perfil "
     "comparado de cada causa, su estacionalidad, su geografia y la prueba de "
     "las dos lecturas. Es la seccion de evidencia."),
    ("4", "Cuestionario SQL",
     "Seis problemas analiticos resueltos contra la base <b>original</b>, "
     "alojada en PostgreSQL."),
    ("5", "FireQuery",
     "Terminal SQL abierta contra el modelo normalizado, con el diccionario "
     "de datos."),
    ("6", "Conclusiones",
     "Sintesis, limitaciones declaradas y lineas de continuidad."),
    ("7", "Bibliografia", "Fuente de datos, literatura y documentacion tecnica."),
]

for fila in range(0, len(SECCIONES), 2):
    columnas = st.columns(2)
    for columna, (num, titulo, desc) in zip(columnas, SECCIONES[fila:fila + 2]):
        with columna:
            st.markdown(
                f"<div class='tarjeta'><b>{num}. {titulo}</b><br>"
                f"<span style='color:#C4AEA2; font-size:14px;'>{desc}</span></div>",
                unsafe_allow_html=True)


# ==============================================================================
# FICHA TECNICA
# ==============================================================================
st.markdown("---")
st.header("Ficha tecnica")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("La fuente")
    st.markdown("""
    - **Base**: Fire Program Analysis fire-occurrence database (FPA FOD), 4.ª ed.
    - **Compilacion**: Karen C. Short (2017), Forest Service Research Data Archive.
    - **Cobertura**: 24 anos completos, 1992-2015.
    - **Volumen original**: 759 MB, una tabla de 39 columnas.
    - **Licencia**: CC0, con cita obligatoria a Short (2017).
    """)
    st.caption(
        "El catalogo de 5.867 unidades operativas del NWCG que acompana a la "
        "fuente -y que la mayoria de los analisis publicos ignora- si se "
        "integra en este modelo: enlaza con el 98,15 % de los registros."
    )

with col_b:
    st.subheader("La arquitectura en la nube")
    st.markdown("""
    - **PostgreSQL / Supabase**: la tabla original integra, para el cuestionario SQL.
    - **MotherDuck** · `fpa_normalizada`: 1 entidad + 9 catalogos en 3FN. **Lo que lee este aplicativo.**
    - **MotherDuck** · `fpa_analitica`: 9 dimensiones + 1 hecho. Lo consume Tableau.
    - **DuckDB**: motor OLAP; las agregaciones se resuelven en la nube.
    """)
    st.caption(
        "El repositorio no versiona ni un byte de datos: las tres bases se "
        "reconstruyen con los scripts de `Base de datos/`."
    )

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de "
    "Venezuela · Material academico de la asignatura Computacion II."
)
