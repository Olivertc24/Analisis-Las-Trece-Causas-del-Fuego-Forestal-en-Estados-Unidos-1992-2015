"""
pages/01_Marco_Metodologico.py
================================================================================
MARCO METODOLOGICO DE LA INVESTIGACION
Las trece causas del fuego forestal en EE.UU., 1992-2015.
================================================================================

Documenta el diseno: el problema, la pregunta que lo ordena, el nivel, la
justificacion, los objetivos, la delimitacion del universo y la
operacionalizacion de las variables.

No realiza calculos. Es la memoria metodologica del proyecto, publicada dentro
del propio aplicativo para que el lector pueda contrastar cada resultado con
las decisiones que lo hicieron posible.
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Marco Metodologico", page_icon="📐", layout="wide")

st.markdown("""
<style>
.justificado { text-align: justify; line-height: 1.65; }
.destacado   { color: #F77636; font-weight: 700; }
.tarjeta {
    background-color: #1C1512; border-left: 5px solid #F77636;
    border-radius: 6px; padding: 16px 20px; margin-bottom: 12px; height: 100%;
}
.caja-pregunta {
    background-color: #160F0C; border-top: 4px solid #F77636;
    border-bottom: 4px solid #F77636; padding: 28px; border-radius: 8px;
    margin: 30px 0;
}
</style>
""", unsafe_allow_html=True)

st.title("Marco metodologico")
st.caption("Diseno de la investigacion, objetivos y operacionalizacion")


# ==============================================================================
# 1. EL PROBLEMA
# ==============================================================================
st.header("1. Planteamiento del problema")

st.markdown("""
<div class="justificado">
La base <b>FPA FOD</b> clasifica cada uno de sus 1.880.465 incendios en una de
<b>trece causas estadisticas</b>. La literatura y la mayoria de los analisis
publicos agrupan esas trece en dos bloques -fuego humano y fuego natural-, una
simplificacion util que sin embargo esconde dos cosas.<br><br>

<b>La primera es que los trece valores no son trece causas.</b> Dos de ellos no
nombran ningun mecanismo: <code>Miscellaneous</code>, con 323.805 incendios, y
<code>Missing/Undefined</code>, con 166.723. Juntos suman
<span class="destacado">490.528 incendios, el 26,09 % del registro</span>. Mas de
uno de cada cuatro incendios del pais carece de causa utilizable.<br><br>

<b>La segunda es que ese hueco no se reparte al azar ni se mantiene estable.</b>
Por agencia reportante la atribucion varia en un factor de ocho, y a lo largo de
los 24 anos el bloque sin atribuir <b>crece</b>: del 23,14 % en 1992 al 32,75 %
en 2015, con un maximo de 35,99 % en 2008. El registro no mejora su capacidad de
atribuir causa: la pierde.
</div>
""", unsafe_allow_html=True)

st.warning(
    "**Consecuencia que ordena todo el trabajo.** Las series de causa no pueden "
    "leerse como series de comportamiento. Una causa puede «caer» entre 1992 y "
    "2015 simplemente porque el bloque sin atribuir crecio diez puntos y se la "
    "comio. Por eso cada resultado se presenta **dos veces** -sobre el registro "
    "completo y sobre el subconjunto atribuido- y la distancia entre ambas "
    "lecturas es ella misma un resultado."
)

st.markdown("""
<div class="caja-pregunta">
<b style="color:#F77636;">Pregunta de investigacion</b><br><br>
¿Como se diferencian entre si las trece causas registradas del fuego forestal en
Estados Unidos entre 1992 y 2015, en cuanto a su frecuencia, su magnitud, su
distribucion estacional y su localizacion geografica, y en que medida el grado
de cobertura de la atribucion condiciona la lectura de esas diferencias?
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. NIVEL Y DISENO
# ==============================================================================
st.header("2. Nivel y diseno de la investigacion")

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown(
        "<div class='tarjeta'><b>Nivel: descriptivo</b><br>"
        "Caracteriza y compara las causas sin postular relaciones causales ni "
        "contrastar hipotesis sobre poblaciones no observadas.</div>",
        unsafe_allow_html=True)
with col_b:
    st.markdown(
        "<div class='tarjeta'><b>Diseno: no experimental</b><br>"
        "No hay manipulacion de variables ni asignacion. Se observan registros "
        "producidos por terceros para fines operativos, no de investigacion.</div>",
        unsafe_allow_html=True)
with col_c:
    st.markdown(
        "<div class='tarjeta'><b>Fuente: documental secundaria</b><br>"
        "Registro administrativo compilado por el Forest Service. Sus silencios "
        "son datos sobre el registro, no sobre el fuego.</div>",
        unsafe_allow_html=True)

st.info(
    "**Parametros, no estimadores.** Se trabaja con el universo completo de "
    "registros y no con una muestra. Las medidas calculadas son por tanto "
    "parametros del registro: no se realizan pruebas de significacion ni "
    "inferencias mas alla del universo procesado. Donde el aplicativo dibuja una "
    "muestra -el mapa- es por limitaciones de representacion grafica, y los "
    "estadisticos que acompanan el grafico siguen calculandose sobre el total."
)


# ==============================================================================
# 3. OBJETIVOS
# ==============================================================================
st.header("3. Objetivos")

st.subheader("Objetivo general")
st.markdown("""
<div class="justificado">
Describir el perfil estadistico comparado de las trece causas registradas del
fuego forestal en Estados Unidos entre 1992 y 2015 -en frecuencia, magnitud,
estacionalidad y distribucion territorial-, estableciendo previamente el grado
de cobertura de la atribucion de causa y su efecto sobre la lectura de los
resultados.
</div>
""", unsafe_allow_html=True)

st.subheader("Objetivos especificos")
OBJETIVOS = [
    ("1", "Medir la cobertura de la atribucion",
     "Sobre el universo completo, y su variacion por agencia reportante, por "
     "estado y a lo largo de los 24 anos.", "Seccion 0"),
    ("2", "Caracterizar cada una de las trece causas",
     "En frecuencia absoluta y relativa, superficie quemada, superficie media "
     "por evento y clase de magnitud NWCG.", "Seccion 1"),
    ("3", "Contrastar frecuencia contra magnitud",
     "Identificando las causas que producen muchos incendios pequenos frente a "
     "las que producen pocos devastadores.", "Seccion 1"),
    ("4", "Describir la estacionalidad propia de cada causa",
     "Sobre el dia juliano de descubrimiento, midiendo la amplitud de su "
     "ventana anual.", "Seccion 2"),
    ("5", "Establecer la geografia de cada causa",
     "Concentracion por estado y region censal, e identificacion de las causas "
     "con firma territorial reconocible.", "Seccion 3"),
    ("6", "Evaluar la estabilidad temporal del reparto",
     "Distinguiendo el cambio real del artefacto de registro.", "Seccion 4"),
    ("7", "Construir la infraestructura de datos",
     "La fuente original en PostgreSQL, el modelo normalizado y el dimensional "
     "en MotherDuck, cada uno en el servicio que corresponde a su uso.",
     "Base de datos/"),
]
st.dataframe(
    pd.DataFrame(OBJETIVOS, columns=["N.º", "Objetivo", "Alcance", "Donde se responde"]),
    width="stretch", hide_index=True)


# ==============================================================================
# 4. DELIMITACION
# ==============================================================================
st.header("4. Delimitacion del universo")

col_1, col_2 = st.columns(2)
with col_1:
    st.markdown("""
    **Universo de registro** — 1.880.465 incendios

    Todos los registros de la base, sin excepcion. Es el universo sobre el que
    se mide la **cobertura de la atribucion** (objetivo 1) y sobre el que se
    calcula la primera de las dos lecturas.
    """)
with col_2:
    st.markdown("""
    **Universo atribuido** — 1.389.937 incendios

    El subconjunto cuya causa nombra un mecanismo: las once categorias
    distintas de `Miscellaneous` y `Missing/Undefined`. Es el **73,91 %** del
    anterior, y sobre el se calcula la segunda lectura.
    """)

st.markdown("""
<div class="justificado">
Los dos universos <b>conviven en todo el aplicativo</b>. El selector de lectura
de la barra lateral no filtra: cambia el denominador. Esa es la razon de que la
cifra de cobertura valga 100 % cuando se elige el universo atribuido: no es un
error, es la definicion.
</div>
""", unsafe_allow_html=True)

st.error(
    "**Lo que esta investigacion no podra afirmar.**\n\n"
    "- **No establece causalidad.** La base registra la causa *asignada por el "
    "organismo que reporto el incendio*, no una causa determinada pericialmente.\n"
    "- **No corrige el hueco.** No se imputan causas a los 490.528 incendios sin "
    "ella: se los cuenta, se los describe y se los deja a la vista.\n"
    "- **No compara desempeno entre agencias.** Las diferencias de atribucion "
    "reflejan practicas de registro y tipos de terreno distintos.\n"
    "- **No cubre Alaska y Hawai de forma homogenea** con el resto del pais, por "
    "la distinta composicion de organismos reportantes."
)


# ==============================================================================
# 5. OPERACIONALIZACION
# ==============================================================================
st.header("5. Operacionalizacion de las variables")

VARIABLES = [
    ("Causa", "Nominal", "causas.nombre", "13 categorias",
     "Variable central. Se acompana siempre de `es_atribuida`."),
    ("Atribucion", "Nominal dicotomica", "causas.es_atribuida", "0 / 1",
     "Construida: vale 0 en Miscellaneous y Missing/Undefined."),
    ("Origen", "Nominal", "causas.origen", "Natural / Antropico / No atribuida",
     "Construida. Permite la agregacion habitual sin perder el detalle."),
    ("Superficie", "Razon", "incendios.tamano_acres", "acres",
     "Muy asimetrica: se reportan media y mediana juntas."),
    ("Clase de magnitud", "Ordinal", "incendios.clase_tamano", "A a G",
     "Norma NWCG. Derivable de la superficie con umbral exacto."),
    ("Dia del ano", "Intervalo ciclico", "derivada de la fecha", "1 a 366",
     "Sostiene el objetivo 4. Ciclica: el dia 366 es contiguo al 1."),
    ("Ano de temporada", "Intervalo", "incendios.anio_temporada", "1992 a 2015",
     "El que imputa la agencia, no el de la fecha: difieren en 4 casos."),
    ("Region censal", "Nominal", "construida sobre estados.codigo", "4 + territorio",
     "Definicion de la Oficina del Censo. Puerto Rico queda como territorio."),
    ("Ambito institucional", "Nominal", "construida sobre agencias_nwcg.codigo",
     "Federal / Estatal-Local / Interagencial / Tribal",
     "Agrupa los once organismos reportantes del NWCG."),
]
st.dataframe(
    pd.DataFrame(VARIABLES, columns=[
        "Variable", "Escala", "Origen en el modelo", "Valores", "Nota"]),
    width="stretch", hide_index=True)

st.caption(
    "Las variables marcadas como *construidas* no existen en la fuente: son "
    "decisiones de esta investigacion. Se documentan aqui, se materializan en "
    "el modelo dimensional y se expresan como SQL en el aplicativo, con la "
    "obligacion de que las tres versiones coincidan."
)
