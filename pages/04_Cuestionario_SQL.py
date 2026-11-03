"""
pages/04_Cuestionario_SQL.py
================================================================================
CUESTIONARIO SQL - SEIS CONSULTAS ANALITICAS RESUELTAS
================================================================================

Cada apartado presenta el enunciado, la tecnica que exige, la consulta, el
resultado ejecutado EN VIVO y la interpretacion del hallazgo.

CONTRA QUE SE EJECUTA, Y POR QUE IMPORTA
----------------------------------------
No contra el modelo normalizado, sino contra la tabla CRUDA de la fuente, en
PostgreSQL. Esa eleccion es deliberada: el cuestionario demuestra que se puede
responder preguntas analiticas sobre una tabla de 38 columnas sin una sola
clave declarada, que es la situacion de partida real de casi cualquier dato
administrativo.

Las consultas se apoyan en funciones de ventana -SUM OVER, ROW_NUMBER, RANK,
LAG- y en agregacion condicional con FILTER, tecnicas que resuelven en una sola
pasada problemas que de otro modo exigirian varias consultas encadenadas.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.supabase_manager import consultar_pg, estado_pg, explicar_fallo_pg

st.set_page_config(page_title="Cuestionario SQL", page_icon="🧮", layout="wide")

BRASA, AMBAR, HUMO = "#F77636", "#FFB020", "#5C3C28"

st.title("Cuestionario SQL")
st.caption("Seis problemas analiticos resueltos sobre la tabla original, en PostgreSQL")

diag = estado_pg()
if not diag.get("ok"):
    st.error("No se pudo conectar con la base original.")
    st.markdown(explicar_fallo_pg(diag))
    st.stop()

st.info(
    f"**Conectado a PostgreSQL.** La tabla `fires` contiene "
    f"**{diag['filas']:,}** filas. ".replace(",", ".") +
    "Es la tabla cruda de la fuente: 38 columnas, sin claves declaradas, con "
    "sus inconsistencias intactas."
)

st.warning(
    "**Esta base cubre 1992-2014, no los 24 anos completos.** El ano 2015 no "
    "entro en el plan gratuito de Supabase: la tabla ocupa 475,7 MB de los 500 "
    "disponibles. El corte esta documentado en `Base de datos/"
    "CARGA_SUPABASE.md`. Por eso las cifras de esta pagina difieren levemente "
    "de las de **El Hueco y las Once**, que consulta los 24 anos en MotherDuck. "
    "La diferencia es del 3,96 % de los registros."
)


def apartado(numero, titulo, enunciado, tecnica, sql, interpretacion, grafico=None):
    """
    Renderiza un apartado completo. Centralizarlo evita repetir seis veces la
    misma estructura y garantiza que los seis se presenten igual.
    """
    st.markdown("---")
    st.header(f"{numero}. {titulo}")
    st.markdown(f"**Enunciado.** {enunciado}")
    st.caption(f"Tecnica: {tecnica}")

    with st.expander("Ver la consulta", expanded=False):
        st.code(sql, language="sql")

    try:
        df = consultar_pg(sql)
    except Exception as error:
        st.error("PostgreSQL rechazo la consulta.")
        st.code(str(error), language="text")
        return

    if df.empty:
        st.warning("La consulta no devolvio filas.")
        return

    if grafico is not None:
        col_g, col_t = st.columns([3, 2])
        with col_g:
            st.plotly_chart(grafico(df), width="stretch")
        with col_t:
            st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.dataframe(df, width="stretch", hide_index=True)

    st.success(interpretacion)


# ==============================================================================
# 1
# ==============================================================================
apartado(
    1, "El hueco de atribucion, por agencia reportante",
    "¿Que proporcion de sus incendios atribuye a una causa concreta cada "
    "organismo del NWCG, y como se ordenan entre si?",
    "agregacion condicional con FILTER · RANK() OVER",
    """SELECT nwcg_reporting_agency AS agencia,
       COUNT(*) AS incendios,
       COUNT(*) FILTER (WHERE stat_cause_descr IN ('Miscellaneous','Missing/Undefined')) AS sin_causa,
       ROUND(100.0 * COUNT(*) FILTER (
           WHERE stat_cause_descr NOT IN ('Miscellaneous','Missing/Undefined')
       ) / COUNT(*), 2) AS cobertura_pct,
       RANK() OVER (ORDER BY COUNT(*) FILTER (
           WHERE stat_cause_descr NOT IN ('Miscellaneous','Missing/Undefined')
       )::numeric / COUNT(*) DESC) AS puesto
FROM fires
GROUP BY nwcg_reporting_agency
HAVING COUNT(*) >= 1000
ORDER BY cobertura_pct DESC""",
    "La cobertura va del **90,79 %** en los gobiernos tribales al **0,11 %** en "
    "los reportes interagenciales: un factor de ochocientos. Y el organismo que "
    "concentra el volumen -`ST/C&L`, con 1,32 millones de incendios- esta en "
    "**71,79 %**, por debajo de todos los federales. El hueco de atribucion no "
    "es ruido repartido al azar: tiene una estructura institucional.",
    lambda df: go.Figure(
        data=[go.Bar(x=df["cobertura_pct"], y=df["agencia"], orientation="h",
                     marker_color=BRASA,
                     text=df["cobertura_pct"].map(lambda v: f"{v:.2f}%"),
                     textposition="outside")]
    ).update_layout(template="plotly_dark", height=420, xaxis_range=[0, 112],
                    title="Cobertura de la atribucion por agencia (%)",
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=10, r=10, t=60, b=10)),
)


# ==============================================================================
# 2
# ==============================================================================
apartado(
    2, "Las trece categorias y su participacion acumulada",
    "¿Cuantas categorias hacen falta para cubrir la mitad del registro, y en "
    "que posicion de ese recuento aparecen las que no nombran causa?",
    "SUM(COUNT(*)) OVER con marco de filas acumulado",
    """SELECT stat_cause_descr AS causa,
       COUNT(*) AS incendios,
       ROUND(100.0*COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct,
       ROUND(100.0*SUM(COUNT(*)) OVER (ORDER BY COUNT(*) DESC
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(COUNT(*)) OVER (), 2) AS pct_acumulado
FROM fires
GROUP BY stat_cause_descr
ORDER BY incendios DESC""",
    "Bastan **tres categorias** para superar la mitad del registro (54,88 %), y "
    "la segunda de ellas es `Miscellaneous`, que no nombra ningun mecanismo. "
    "Sumada a `Missing/Undefined`, el bloque sin atribuir es el **25,81 %** de "
    "esta base. Cualquier porcentaje calculado sobre el total reparte entre las "
    "once causas reales una base que incluye ese cuarto.",
    lambda df: go.Figure([
        go.Bar(x=df["causa"], y=df["pct"], name="% de incendios",
               marker_color=[HUMO if c in ("Miscellaneous", "Missing/Undefined")
                             else BRASA for c in df["causa"]]),
        go.Scatter(x=df["causa"], y=df["pct_acumulado"], name="acumulado",
                   yaxis="y2", line=dict(color=AMBAR, width=3)),
    ]).update_layout(
        template="plotly_dark", height=420,
        title="Participacion individual y acumulada",
        yaxis=dict(title="% individual"),
        yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=10, r=10, t=70, b=10)),
)


# ==============================================================================
# 3
# ==============================================================================
apartado(
    3, "La causa dominante de cada estado",
    "¿Cual es la causa mas frecuente en cada estado, y que peso tiene dentro "
    "de el? Se excluyen las dos categorias sin mecanismo.",
    "ROW_NUMBER() OVER (PARTITION BY ...) para quedarse con el primero de cada grupo",
    """WITH por_estado AS (
    SELECT state AS estado, stat_cause_descr AS causa, COUNT(*) AS incendios,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY COUNT(*) DESC) AS puesto,
           ROUND(100.0*COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY state), 1) AS pct_del_estado
    FROM fires
    WHERE stat_cause_descr NOT IN ('Miscellaneous','Missing/Undefined')
    GROUP BY state, stat_cause_descr
)
SELECT estado, causa AS causa_dominante, incendios, pct_del_estado
FROM por_estado WHERE puesto = 1
ORDER BY incendios DESC LIMIT 12""",
    "El reparto es casi geografico. En el Sur manda la quema de residuos "
    "-Georgia 55,6 %, Texas 55,2 %- o el incendio provocado -Misisipi 56,1 %-; "
    "en el Oeste interior manda el rayo, y con un peso mucho mayor: **75,8 % en "
    "Colorado** y **74,0 % en Idaho**. California es la excepcion que conviene "
    "mirar: su causa dominante es `Equipment Use`, y solo con el 32,1 %.",
)


# ==============================================================================
# 4
# ==============================================================================
apartado(
    4, "La evolucion del hueco, ano a ano",
    "¿El registro mejora o empeora su capacidad de atribuir causa? Se pide "
    "ademas la variacion respecto del ano anterior.",
    "LAG() OVER para comparar cada fila con la precedente",
    """WITH por_anio AS (
    SELECT fire_year AS anio, COUNT(*) AS incendios,
           ROUND(100.0*COUNT(*) FILTER (
               WHERE stat_cause_descr IN ('Miscellaneous','Missing/Undefined')
           ) / COUNT(*), 2) AS hueco_pct
    FROM fires GROUP BY fire_year
)
SELECT anio, incendios, hueco_pct,
       LAG(hueco_pct) OVER (ORDER BY anio) AS hueco_anterior,
       ROUND(hueco_pct - LAG(hueco_pct) OVER (ORDER BY anio), 2) AS variacion
FROM por_anio ORDER BY anio""",
    "El hueco **crece**: parte del 23,14 % en 1992 y llega al 27,56 % en 2014, "
    "con un maximo de 35,99 % en 2008. No es una deriva suave sino escalones: "
    "+8,17 puntos en 2003 y +8,37 en 2005. Esos saltos sugieren cambios en el "
    "conjunto de organismos que reportan, no un cambio en el fuego. Es la razon "
    "de que las series de causa no puedan leerse como series de comportamiento.",
    lambda df: go.Figure([
        go.Scatter(x=df["anio"], y=df["hueco_pct"], mode="lines+markers",
                   line=dict(color=BRASA, width=3), name="hueco (%)"),
        go.Bar(x=df["anio"], y=df["variacion"], name="variacion anual",
               marker_color=AMBAR, opacity=0.55, yaxis="y2"),
    ]).update_layout(
        template="plotly_dark", height=420,
        title="Porcentaje sin causa atribuida, y su variacion",
        yaxis=dict(title="% sin causa"),
        yaxis2=dict(title="variacion (p.p.)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=10, r=10, t=70, b=10)),
)


# ==============================================================================
# 5
# ==============================================================================
apartado(
    5, "La concentracion extrema de la superficie",
    "¿Cuantos incendios hacen falta para acumular el 25, 50, 75 y 90 % de toda "
    "la superficie quemada?",
    "suma acumulada con SUM() OVER ordenada · CROSS JOIN con una lista de umbrales",
    """WITH ordenados AS (
    SELECT fire_size,
           SUM(fire_size) OVER (ORDER BY fire_size DESC, fod_id) AS acres_acum,
           ROW_NUMBER() OVER (ORDER BY fire_size DESC, fod_id) AS n,
           SUM(fire_size) OVER () AS acres_total,
           COUNT(*) OVER () AS total
    FROM fires
)
SELECT umbral AS pct_superficie,
       MIN(n) AS incendios_necesarios,
       ROUND(100.0*MIN(n)/MAX(total), 4) AS pct_de_los_incendios
FROM ordenados
CROSS JOIN (VALUES (25),(50),(75),(90)) AS u(umbral)
WHERE acres_acum >= acres_total * umbral / 100.0
GROUP BY umbral ORDER BY umbral""",
    "**802 incendios -el 0,0444 % del registro- acumulan la mitad de toda la "
    "superficie quemada.** Ciento cincuenta y tres acumulan la cuarta parte. La "
    "distribucion de la magnitud del fuego no solo es asimetrica: esta "
    "concentrada en una cola practicamente puntual. Es la razon de que la media "
    "de superficie por evento sea un estadistico engañoso y haya que "
    "acompanarla siempre de la mediana.",
    lambda df: go.Figure(
        data=[go.Bar(x=df["pct_superficie"].astype(str) + " %",
                     y=df["incendios_necesarios"], marker_color=BRASA,
                     text=df["incendios_necesarios"], textposition="outside")]
    ).update_layout(template="plotly_dark", height=420, yaxis_type="log",
                    title="Incendios necesarios para acumular cada % de superficie",
                    xaxis_title="porcentaje de la superficie",
                    yaxis_title="numero de incendios (escala log)",
                    margin=dict(l=10, r=10, t=60, b=10)),
)


# ==============================================================================
# 6
# ==============================================================================
apartado(
    6, "La ventana estacional de cada causa",
    "¿En cuantos dias del ano se concentra el 50 % central de los incendios de "
    "cada causa?",
    "PERCENTILE_CONT ... WITHIN GROUP, funcion de agregacion ordenada",
    """SELECT stat_cause_descr AS causa,
       COUNT(*) AS incendios,
       PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY discovery_doy)::int AS dia_p25,
       PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY discovery_doy)::int AS dia_mediano,
       PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY discovery_doy)::int AS dia_p75,
       (PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY discovery_doy)
        - PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY discovery_doy))::int AS amplitud
FROM fires
WHERE stat_cause_descr NOT IN ('Miscellaneous','Missing/Undefined')
GROUP BY stat_cause_descr ORDER BY amplitud""",
    "La amplitud varia en un factor de dieciocho. `Fireworks` concentra su 50 % "
    "central en **nueve dias**, del 179 al 188: es la semana del 4 de julio, y "
    "la consulta la encuentra sin que nadie se la indique. `Lightning` ocupa 45 "
    "dias de verano. En el extremo opuesto, `Arson` se reparte por **165 dias**: "
    "el incendio provocado no tiene temporada. Este resultado coincide con el "
    "que calcula el aplicativo sobre MotherDuck, lo que verifica de paso que "
    "las dos bases dicen lo mismo.",
    lambda df: go.Figure([
        go.Bar(y=df["causa"], x=df["amplitud"], orientation="h",
               base=df["dia_p25"], marker_color=BRASA, name="ventana",
               hovertemplate="dias %{base} a %{x}<extra></extra>"),
    ]).update_layout(template="plotly_dark", height=460,
                     title="Ventana del 50 % central, en dias del ano",
                     xaxis=dict(title="dia del ano", range=[0, 366]),
                     yaxis=dict(autorange="reversed"),
                     margin=dict(l=10, r=10, t=60, b=10)),
)

st.markdown("---")
st.caption(
    "Las seis consultas se ejecutan EN PostgreSQL: `postgres_query` envia el "
    "texto al servidor y devuelve el resultado. Es PostgreSQL quien planifica "
    "y ejecuta, no el cliente."
)
