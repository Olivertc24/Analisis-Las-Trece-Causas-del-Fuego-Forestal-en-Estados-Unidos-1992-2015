"""
pages/02_Marco_Teorico.py
================================================================================
MARCO TEORICO DE LA INVESTIGACION
Las trece causas del fuego forestal en EE.UU., 1992-2015.
================================================================================

Reune los antecedentes, el origen institucional del registro, el significado de
las trece categorias de causa y los fundamentos tecnicos de la arquitectura de
datos empleada.
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Marco Teorico", page_icon="📚", layout="wide")

st.markdown("""
<style>
.justificado { text-align: justify; line-height: 1.65; }
.destacado   { color: #F77636; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("Marco teorico")
st.caption("Origen del registro, significado de las categorias y fundamentos tecnicos")


# ==============================================================================
# 1. ANTECEDENTES
# ==============================================================================
st.header("1. Antecedentes")

st.subheader("1.1. La base FPA FOD como registro operativo, no cientifico")
st.markdown("""
<div class="justificado">
La <b>Fire Program Analysis fire-occurrence database</b> (FPA FOD) fue construida
para alimentar el sistema federal de analisis de programas de fuego de Estados
Unidos. Su cuarta edicion, compilada por <b>Karen C. Short (2017)</b>, integra
los reportes de organismos federales, estatales y locales bajo el estandar del
<b>National Wildfire Coordinating Group (NWCG)</b>.<br><br>

El matiz importa para leer sus silencios. La base <b>no se construyo para
investigar</b>: se construyo para planificar presupuesto y recursos. Un campo
vacio no es un fallo del compilador, es un campo que el organismo reportante no
necesitaba llenar para su proposito. De ahi que la cobertura de la atribucion de
causa varie tanto entre organismos: para el Forest Service la causa determina el
programa de prevencion; para un cuerpo de bomberos municipal que reporta un
conato, no determina nada.
</div>
""", unsafe_allow_html=True)

st.subheader("1.2. El nicho de fuego humano")
st.markdown("""
<div class="justificado">
<b>Balch y colaboradores (2017)</b> mostraron, sobre esta misma base, que el
fuego de origen humano <i>expande el nicho del fuego</i>: triplica la duracion
de la temporada y desplaza la ignicion hacia meses y lugares donde el rayo es
practicamente inexistente. Ese trabajo es el antecedente directo de los
objetivos 4 y 5 de esta investigacion.<br><br>

La diferencia de enfoque es deliberada. Balch y su equipo agregan todas las
causas humanas en un bloque; aqui se <b>desagregan las once</b>, porque un
incendio provocado, una quema de residuos y un uso de maquinaria no comparten ni
estacionalidad, ni magnitud tipica, ni geografia.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. LAS TRECE CATEGORIAS
# ==============================================================================
st.header("2. Que significan las trece categorias")

st.markdown("""
<div class="justificado">
El campo <code>STAT_CAUSE_DESCR</code> toma trece valores. Conviene leerlos con
cuidado, porque no son trece elementos del mismo tipo logico: once nombran un
<b>mecanismo de ignicion</b> y dos son <b>categorias residuales</b>.
</div>
""", unsafe_allow_html=True)

CAUSAS = [
    ("1", "Lightning", "Natural", "Descarga electrica atmosferica. Unica causa no humana del catalogo."),
    ("2", "Equipment Use", "Antropico", "Maquinaria agricola, forestal o de construccion: chispas, escapes, frenos."),
    ("3", "Smoking", "Antropico", "Material de fumar desechado encendido."),
    ("4", "Campfire", "Antropico", "Fogata recreativa mal extinguida o fuera de control."),
    ("5", "Debris Burning", "Antropico", "Quema de residuos vegetales o domesticos que escapa. La mas frecuente."),
    ("6", "Railroad", "Antropico", "Chispas de frenos y ruedas en el derecho de via ferroviario."),
    ("7", "Arson", "Antropico", "Ignicion deliberada con intencion de dano."),
    ("8", "Children", "Antropico", "Ignicion por menores, sin intencion delictiva imputable."),
    ("9", "Miscellaneous", "NO ATRIBUIDA", "«Otras». El organismo identifico algo, pero fuera del catalogo."),
    ("10", "Fireworks", "Antropico", "Articulos pirotecnicos."),
    ("11", "Powerline", "Antropico", "Fallo o contacto de linea electrica aerea."),
    ("12", "Structure", "Antropico", "Incendio estructural que se propaga a vegetacion."),
    ("13", "Missing/Undefined", "NO ATRIBUIDA", "Sin dato. El campo llego vacio o ilegible."),
]
st.dataframe(
    pd.DataFrame(CAUSAS, columns=["Codigo", "Categoria", "Origen", "Que recoge"]),
    width="stretch", hide_index=True)

st.warning(
    "**La diferencia entre las dos residuales no es menor, y el aplicativo no "
    "la borra.** `Missing/Undefined` es ausencia de dato: nadie lleno el campo. "
    "`Miscellaneous` es presencia de un dato inutil: alguien determino la causa "
    "y decidio que no encajaba en el catalogo. La primera habla de la "
    "diligencia del registro; la segunda, de la suficiencia del catalogo. Se "
    "agrupan bajo `es_atribuida = 0` porque para calcular participaciones se "
    "comportan igual, pero se conservan separadas en la dimension."
)


# ==============================================================================
# 3. LA ARQUITECTURA INSTITUCIONAL
# ==============================================================================
st.header("3. Quien reporta: la arquitectura del NWCG")

st.markdown("""
<div class="justificado">
El NWCG coordina a organismos de naturaleza muy distinta. Esta investigacion los
agrupa en cuatro <b>ambitos</b>, porque la cobertura de la atribucion varia
sistematicamente entre ellos.
</div>
""", unsafe_allow_html=True)

AMBITOS = [
    ("Federal", "FS, BIA, BLM, NPS, FWS, DOD, BOR, DOE",
     "477.795", "Gestionan terreno federal. La causa alimenta su programa de prevencion."),
    ("Estatal-Local", "ST/C&L", "1.377.090",
     "Agencias estatales, de condado y municipales. Concentran el 73 % del registro."),
    ("Interagencial", "IA", "21.841",
     "Reportes de incidentes coordinados entre organismos."),
    ("Tribal", "TRIBE", "3.739", "Gobiernos tribales reconocidos federalmente."),
]
st.dataframe(
    pd.DataFrame(AMBITOS, columns=["Ambito", "Organismos", "Incendios", "Naturaleza"]),
    width="stretch", hide_index=True)

st.info(
    "**El catalogo que casi nadie usa.** La fuente se distribuye con una segunda "
    "tabla, `NWCG_UnitIDActive`, de **5.867 unidades operativas** con su "
    "departamento, su agencia, su tipo y su centro de coordinacion geografica "
    "(GACC). Ese enlace **no esta declarado** en el esquema original, pero "
    "resuelve el **98,15 %** de los registros. Integrarlo es lo que permite "
    "analizar la cobertura por nivel organizativo real y no solo por sigla."
)


# ==============================================================================
# 4. FUNDAMENTOS TECNICOS
# ==============================================================================
st.header("4. Fundamentos de la arquitectura de datos")

st.subheader("4.1. Por que normalizar y despues desnormalizar")
st.markdown("""
<div class="justificado">
No es un paso atras: son objetivos opuestos. La <b>tercera forma normal</b>
optimiza la escritura -cada hecho vive en un solo lugar, de modo que no puede
contradecirse consigo mismo- y es lo que garantiza que el dato sea coherente. El
<b>esquema en estrella</b> optimiza la lectura y la comprension: separa lo que se
mide de aquello por lo que se mide.<br><br>

Se construyen los dos porque sirven a cosas distintas. El aplicativo consulta el
<b>normalizado</b>, donde las once causas y sus catalogos viven sin redundancia;
el tablero consulta el <b>dimensional</b>, que es la forma que una herramienta de
tablero espera encontrar.
</div>
""", unsafe_allow_html=True)

st.subheader("4.2. Por que DuckDB y no un motor transaccional")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("""
    **Almacenamiento columnar**

    Una consulta que agrupa 1,88 millones de filas por causa solo necesita dos
    columnas. Un motor orientado a filas lee las treinta y cinco; uno columnar
    lee dos. La misma tabla ocupa **113 MB** en formato columnar frente a los
    **470 MB** que ocuparia en PostgreSQL.
    """)
with col_b:
    st.markdown("""
    **Ejecucion vectorizada**

    DuckDB procesa lotes de valores en lugar de fila a fila. Para agregaciones
    sobre millones de registros la diferencia es de orden de magnitud, y es lo
    que permite que el aplicativo recalcule la pagina entera al mover un
    control sin que el usuario perciba espera.
    """)

st.subheader("4.3. Por que la nube, y por que repartida")
st.markdown("""
<div class="justificado">
El repositorio <b>no versiona ni un byte de datos</b>. Las tres bases viven en
servicios gestionados, y lo que se versiona son los scripts que las construyen.
Eso garantiza que lo desplegado y lo local lean exactamente lo mismo, y que el
trabajo sea replicable sin descargar 759 MB.<br><br>

El reparto en tres destinos no es un capricho: cada herramienta recibe la forma
de datos que sabe aprovechar, y ninguna ve mas de lo que necesita.
</div>
""", unsafe_allow_html=True)

st.dataframe(pd.DataFrame([
    ("PostgreSQL (Supabase)", "La tabla original integra, 37 columnas",
     "Cuestionario SQL", "Motor relacional cliente-servidor, con la fuente cruda y sus inconsistencias a la vista."),
    ("MotherDuck · fpa_normalizada", "1 entidad + 9 catalogos en 3FN",
     "Aplicativo Streamlit", "OLAP embebido: las agregaciones se resuelven en la nube, no en el cliente."),
    ("MotherDuck · fpa_analitica", "9 dimensiones + 1 hecho",
     "Tablero Tableau", "Un esquema en estrella es lo que una herramienta de tablero espera."),
], columns=["Servicio", "Que aloja", "Quien lo consume", "Por que ahi"]),
    width="stretch", hide_index=True)
