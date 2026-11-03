"""
pages/06_Conclusiones.py
================================================================================
CONCLUSIONES DE LA INVESTIGACION
================================================================================

Sintesis organizada en cinco bloques: la infraestructura construida, la
cobertura del registro, los hallazgos sustantivos, las limitaciones declaradas
y las lineas de continuidad.

Todas las cifras provienen de las consultas ejecutadas en las paginas
anteriores.
"""

import streamlit as st

st.set_page_config(page_title="Conclusiones", page_icon="🏁", layout="wide")

st.title("Conclusiones")
st.caption("Las trece causas del fuego forestal · EE.UU. 1992-2015")


# ==============================================================================
# 1
# ==============================================================================
st.header("1. Sobre la infraestructura de datos construida")

with st.expander("1.1. Una fuente con clave, y un identificador que no lo es",
                 expanded=True):
    st.markdown("""
    La base original se distribuye como una tabla de 39 columnas sin una sola
    clave declarada. El diagnostico encontro que **si tiene** una clave real
    -`FOD_ID`, con 1.880.465 valores distintos-, lo que la distingue de otras
    fuentes de esta serie.

    Encontro tambien que **`FPA_ID` no es unica**, pese a que la documentacion la
    presenta como el identificador global: tiene **tres duplicados**, dos de
    ellos colisionando entre anos distintos. Se conserva como atributo
    descriptivo, nunca como clave alternativa.
    """)

with st.expander("1.2. El codigo que parecia identificar y no identificaba"):
    st.markdown("""
    `SOURCE_REPORTING_UNIT` tiene forma de codigo de unidad y no lo es. En el
    sistema `ST-TXTXS`, el codigo `TXVFD` esta asociado a **946 nombres
    distintos** de cuerpos de bomberos voluntarios de Texas. No es un
    identificador: es un cajon que significa «bomberos voluntarios de Texas, sin
    especificar». En total, **407 codigos arrastran 2.287 nombres**.

    Construir un catalogo con clave `(sistema, codigo)` habria **inventado una
    dependencia que los datos no tienen** y colapsado 946 cuerpos en uno solo. Se
    opto por la terna completa como clave natural: elimina la repeticion sin
    afirmar nada falso.
    """)

with st.expander("1.3. Dos errores del verificador, no del dato"):
    st.markdown("""
    La derivacion de `FIRE_SIZE_CLASS` desde la superficie fallo dos veces, y las
    dos por culpa del control, no de la fuente:

    - Primero con **6 discrepancias**, por usar el umbral «menos de 0,26 acres»
      para la clase A cuando la norma NWCG dice «**0,25 acres o menos**».
    - Despues con **41.468**, por definir los rangos como «mas de 10 a 100»
      cuando la norma dice «**10 a 99,9**»: el limite inferior es inclusivo.

    Con los limites correctos la derivacion es **exacta en los 1.880.465
    registros**. El catalogo guarda por eso el limite superior y una bandera
    `hasta_inclusivo`, que vale 1 unicamente en la clase A.
    """)

with st.expander("1.4. Tres bases, tres servicios"):
    st.markdown("""
    La infraestructura reparte la informacion segun quien la consume: la tabla
    original en **PostgreSQL**, el modelo en 3FN y el dimensional en
    **MotherDuck**. El repositorio **no versiona ni un byte de datos**: versiona
    los scripts que reconstruyen las tres.

    La carga a la nube revelo que MotherDuck en modo *workspace* no admite
    `ATTACH ... AS alias`, y -lo que importa mas- que **ese error no detiene al
    cliente**: las sentencias siguientes se ejecutan igual y el script parece
    terminar bien mientras parte de su trabajo fue a otro sitio. Se detecto
    contando filas en destino, no confiando en la ausencia de excepcion.
    """)


# ==============================================================================
# 2
# ==============================================================================
st.header("2. Sobre la cobertura de la atribucion")

st.markdown("""
El resultado previo a todos los demas: **el 26,09 % de los incendios del pais
no tiene causa utilizable**. Son 490.528 registros repartidos entre
`Miscellaneous` (17,22 %) y `Missing/Undefined` (8,87 %).
""")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Incendios sin causa", "490.528", "26,09 % del registro",
             delta_color="inverse")
col_b.metric("Cobertura federal", "84,33 %", "477.795 incendios")
col_c.metric("Cobertura estatal-local", "71,42 %", "1.377.090 incendios",
             delta_color="off")

st.markdown("""
El hueco **no se reparte al azar**: va del 11,99 % en el Forest Service al
99,89 % en los reportes interagenciales. Y **no mejora con el tiempo**: el bloque
sin atribuir pasa del 23,14 % en 1992 al 32,75 % en 2015, con un maximo de
35,99 % en 2008.

Esa combinacion -desigual entre organismos y creciente en el tiempo- es lo que
obliga a la regla metodologica del trabajo.
""")


# ==============================================================================
# 3
# ==============================================================================
st.header("3. Hallazgos sustantivos")

st.subheader("3.1. Frecuencia y magnitud no coinciden")
st.markdown("""
Sobre las once causas atribuidas, `Debris Burning` produce **una de cada tres**
campanas y quema el **5,11 %** de la superficie; `Lightning` produce **una de
cada cinco** y quema el **74,40 %**. El contraste mas extremo es `Powerline`:
apenas el 1,04 % de los incendios, pero la segunda superficie media mas alta de
todas, 111,4 acres por evento.
""")

st.subheader("3.2. Cada causa tiene su propio calendario")
st.markdown("""
Medida sobre el dia juliano, la ventana del 50 % central varia en un factor de
dieciocho:

- **`Fireworks`: 9 dias**, del 179 al 188. Es la semana del 4 de julio. El
  modelo la encuentra **sin que nadie se la indique**, lo que sirve de
  validacion de la dimension temporal.
- **`Lightning`: 45 dias**, concentrada en el verano meteorologico.
- **`Arson`: 165 dias**. El incendio provocado **no tiene temporada**.
""")

st.subheader("3.3. Cada causa tiene su territorio")
st.markdown("""
`Lightning` concentra el **76,3 %** de sus incendios en el Oeste; `Debris
Burning` el **74,6 %** en el Sur; `Railroad` el **73,9 %**, tambien en el Sur.
Son firmas territoriales nitidas, y explican por que agregar todas las causas
humanas en un solo bloque pierde informacion.
""")

st.subheader("3.4. El resultado central: la distancia entre las dos lecturas")
st.success("""
**`Lightning`, leido sobre el registro completo, cae entre 1992-2003 y
2004-2015: del 16,07 % al 13,65 %. Leido sobre lo atribuido, se mantiene plano:
del 20,29 % al 19,76 %.**

La caida no era del rayo. Era del hueco creciendo por debajo.

Y al reves: el crecimiento real de `Debris Burning` sobre lo atribuido es de
**5,49 puntos**, casi seis veces el 0,95 que muestra el total.
""")

st.markdown("""
Este es el hallazgo que justifica el diseno entero del aplicativo. No es que una
de las dos lecturas sea correcta y la otra equivocada: **son dos preguntas
distintas**. La primera describe el registro tal como es; la segunda, el
fenomeno en la parte del registro donde se dejo ver. Confundirlas produce
conclusiones sobre el fuego que en realidad son conclusiones sobre la burocracia.
""")


# ==============================================================================
# 4
# ==============================================================================
st.header("4. Limitaciones declaradas")

st.error("""
- **No se establece causalidad.** La base registra la causa *asignada por el
  organismo que reporto el incendio*, no una causa determinada pericialmente.
- **No se corrige el hueco.** No se imputan causas a los 490.528 incendios sin
  ella: se los cuenta, se los describe y se los deja a la vista.
- **No se compara desempeno entre agencias.** Las diferencias de atribucion
  reflejan practicas de registro y tipos de terreno distintos, no calidad del
  trabajo.
- **La cobertura territorial no es homogenea.** Alaska y Hawai tienen una
  composicion de organismos reportantes distinta del resto del pais.
- **`Miscellaneous` y `Missing/Undefined` se agrupan, pero no son lo mismo.**
  La primera es presencia de un dato inutil; la segunda, ausencia de dato. Se
  conservan separadas en la dimension aunque se agrupen para calcular.
""")


# ==============================================================================
# 5
# ==============================================================================
st.header("5. Lineas de continuidad")

st.markdown("""
1. **Modelar la probabilidad de atribucion.** El hueco es desigual y creciente;
   caracterizar que predice que un incendio quede sin causa seria un trabajo en
   si mismo, y permitiria acotar el sesgo en lugar de solo declararlo.

2. **Cruzar con la duracion de la campana.** La fuente permite calcularla y este
   modelo la conserva sin derivarla. Preguntar si las causas con mayor
   superficie media son tambien las de contencion mas lenta conectaria este
   trabajo con el de respuesta operativa de la misma serie.

3. **Incorporar covariables climaticas.** La base no las trae. Enlazar por
   coordenada y fecha con series de sequia permitiria distinguir el componente
   meteorologico del componente de conducta en la estacionalidad de cada causa.

4. **Llevar la serie mas alla de 2015.** Las ediciones posteriores de FPA FOD
   amplian el periodo. Repetir la medicion de cobertura sobre ellas diria si la
   tendencia al deterioro continuo o se revirtio.
""")
