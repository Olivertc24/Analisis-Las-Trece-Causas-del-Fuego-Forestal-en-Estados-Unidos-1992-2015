"""
pages/03_El_Hueco_y_las_Once.py
================================================================================
ANALISIS Y RESULTADOS
Las trece causas del fuego forestal en EE.UU., 1992-2015.
================================================================================

El titulo nombra la estructura del hallazgo: las trece categorias del registro
son ONCE causas y UN HUECO del 26,09 % repartido en dos etiquetas que no
nombran ningun mecanismo.

La seccion presenta los resultados en este orden:

    0. La cobertura de la atribucion, porque ninguna cifra posterior puede
       interpretarse sin saber sobre que fraccion del registro se calcula.
    1. El perfil comparado: frecuencia contra magnitud.
    2. La estacionalidad propia de cada causa.
    3. La firma territorial.
    4. La prueba de las dos lecturas.

EL CONTROL QUE IMPORTA. La barra lateral tiene un selector de LECTURA. No es
un filtro mas: elige el denominador de todos los porcentajes de la pagina.
Cambiarlo cambia los resultados, y esa es precisamente la demostracion.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.query_manager import estado, explicar_fallo
from src.stats_logic import (
    COLOR_ORIGEN, COLOR_REGION, PALETA,
    causa_por_region, cobertura_por, contraste_de_lecturas, curva_estacional,
    formato_numero, indicadores, lectura_automatica, muestra_geografica,
    perfil_causas, ranking_estados, reparto_por_clase, serie_anual,
    ventana_estacional,
)

st.set_page_config(page_title="Analisis y Resultados", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

diag = estado()
if not diag.get("ok"):
    st.error("El aplicativo no pudo conectarse al almacen de datos.")
    st.markdown(explicar_fallo(diag))
    st.stop()


# ==============================================================================
# BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.title("🔥 Panel de causas")

    lectura = st.radio(
        "Lectura",
        ["Sobre el registro completo", "Solo sobre las once atribuidas"],
        help="Elige el DENOMINADOR de todos los porcentajes de esta pagina. "
             "Es la decision metodologica central del trabajo.",
    )
    solo_atrib = lectura.startswith("Solo")

    st.markdown(
        f"<div style='border-left:6px solid {PALETA['brasa']}; padding:10px 14px; "
        f"background:#1C1512; border-radius:4px; margin:6px 0 14px 0;'>"
        f"<span style='color:{PALETA['brasa']}; font-weight:700;'>Denominador activo</span><br>"
        f"<span style='color:#C4AEA2; font-size:13px;'>"
        f"{'Las 11 causas atribuidas' if solo_atrib else 'Las 13 categorias, hueco incluido'}"
        f"</span></div>", unsafe_allow_html=True)

    anio_ini, anio_fin = st.select_slider(
        "Periodo", options=list(range(1992, 2016)), value=(1992, 2015),
        help="Ano de temporada declarado por la agencia reportante.")

    region_sel = st.selectbox(
        "Region censal",
        ["Todas", "Oeste", "Sur", "Medio Oeste", "Noreste", "Territorio"])

    ambito_sel = st.selectbox(
        "Ambito institucional",
        ["Todos", "Federal", "Estatal-Local", "Interagencial", "Tribal"])

    st.markdown("---")
    st.caption("Fuente: Short, K. C. (2017), FPA_FOD_20170508, 4.ª edicion.")


# ==============================================================================
# ENCABEZADO
# ==============================================================================
st.title("El hueco y las once")
st.caption("Analisis y resultados  ·  Las trece causas del fuego forestal, "
           "EE.UU. 1992-2015")

ind = indicadores(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib)
if not ind or not ind.get("incendios"):
    st.warning("Ningun incendio cumple los criterios seleccionados.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Incendios", formato_numero(ind["incendios"]))
c2.metric("Superficie (M acres)", f"{ind['acres']/1e6:,.2f}")
c3.metric("Media por evento", f"{ind['acres_medios']:,.1f} ac")
c4.metric("Mediana", f"{ind['acres_mediana']:,.2f} ac")
c5.metric("Cobertura de atribucion", f"{100*ind['cobertura']:,.2f} %",
          help="Porcentaje con causa que nombra un mecanismo. Vale 100 % "
               "cuando la lectura se restringe a las once atribuidas.")

st.info(lectura_automatica(ind, solo_atrib))
st.markdown("---")


# ==============================================================================
# 0. LA COBERTURA DE LA ATRIBUCION
# ==============================================================================
st.header("0. La cobertura de la atribucion")
st.markdown(
    "Antes de describir causas hay que responder una pregunta previa: "
    "**¿de cuantos incendios sabemos la causa?** La respuesta condiciona todo "
    "lo que sigue, porque el dato faltante no se distribuye al azar."
)

tab_amb, tab_ag, tab_anio = st.tabs(
    ["Por ambito institucional", "Por agencia reportante", "A lo largo del tiempo"])

with tab_amb:
    df = cobertura_por("ambito", anio_ini, anio_fin, region_sel, ambito_sel)
    col_g, col_t = st.columns([3, 2])
    with col_g:
        fig = px.bar(df.sort_values("cobertura_pct"), x="cobertura_pct",
                     y="categoria", orientation="h", text="cobertura_pct",
                     color="cobertura_pct",
                     color_continuous_scale=[PALETA["humo"], PALETA["brasa"], PALETA["ambar"]],
                     labels={"cobertura_pct": "Cobertura (%)", "categoria": ""},
                     title="Porcentaje de incendios con causa atribuida")
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig.update_layout(template="plotly_dark", height=380, xaxis_range=[0, 112],
                          coloraxis_showscale=False, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")
    with col_t:
        st.dataframe(df.rename(columns={
            "categoria": "Ambito", "incendios": "Incendios",
            "cobertura_pct": "Cobertura (%)", "sin_causa": "Sin causa"}),
            width="stretch", hide_index=True)

with tab_ag:
    df = cobertura_por("agencia", anio_ini, anio_fin, region_sel, ambito_sel)
    fig = px.scatter(df, x="incendios", y="cobertura_pct", text="categoria",
                     size="incendios", size_max=60, log_x=True,
                     color="cobertura_pct",
                     color_continuous_scale=[PALETA["humo"], PALETA["brasa"], PALETA["ambar"]],
                     labels={"incendios": "Incendios registrados (escala log)",
                             "cobertura_pct": "Cobertura (%)"},
                     title="Volumen frente a cobertura, por agencia reportante")
    fig.update_traces(textposition="top center")
    fig.update_layout(template="plotly_dark", height=460, coloraxis_showscale=False,
                      margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "La escala horizontal es logaritmica porque los volumenes difieren en "
        "cinco ordenes de magnitud. El cuadrante que importa es el inferior "
        "derecho: mucho volumen y poca atribucion."
    )

with tab_anio:
    df = cobertura_por("anio", anio_ini, anio_fin, region_sel, ambito_sel)
    df = df.sort_values("categoria")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["categoria"], y=df["cobertura_pct"],
                             mode="lines+markers", line=dict(color=PALETA["brasa"], width=3),
                             name="Cobertura (%)"))
    fig.update_layout(template="plotly_dark", height=400,
                      title="Cobertura de la atribucion ano a ano",
                      yaxis_title="Cobertura (%)", xaxis_title="Ano de temporada",
                      margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")

st.warning(
    "**El hueco no se reparte al azar, y ademas crece.** Las agencias federales "
    "atribuyen causa en el 84,33 % de sus incendios y los organismos estatales, "
    "de condado y locales en el 71,42 %, pese a concentrar el 73 % de los "
    "incendios del pais; los reportes interagenciales no la atribuyen "
    "practicamente nunca (0,11 %). En el tiempo, la cobertura **empeora**: el "
    "bloque sin atribuir pasa del 23,14 % en 1992 al 32,75 % en 2015."
)
st.markdown("---")


# ==============================================================================
# 1. FRECUENCIA CONTRA MAGNITUD
# ==============================================================================
st.header("1. Frecuencia contra magnitud")
st.markdown(
    "Cuantos incendios produce cada causa y cuanta superficie quema son dos "
    "preguntas distintas, y sus respuestas no coinciden."
)

perfil = perfil_causas(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib)

col_i, col_d = st.columns([3, 2])
with col_i:
    fig = go.Figure()
    fig.add_trace(go.Bar(name="% de incendios", x=perfil["causa"],
                         y=perfil["pct_incendios"], marker_color=PALETA["brasa"]))
    fig.add_trace(go.Bar(name="% de superficie", x=perfil["causa"],
                         y=perfil["pct_acres"], marker_color=PALETA["ambar"]))
    fig.update_layout(barmode="group", template="plotly_dark", height=460,
                      title="Participacion de cada causa en incendios y en superficie",
                      yaxis_title="Porcentaje (%)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                      margin=dict(l=10, r=10, t=70, b=10))
    st.plotly_chart(fig, width="stretch")

with col_d:
    fig = px.scatter(perfil, x="pct_incendios", y="acres_medios", text="causa",
                     size="acres", color="origen", color_discrete_map=COLOR_ORIGEN,
                     size_max=55, log_y=True,
                     labels={"pct_incendios": "% de los incendios",
                             "acres_medios": "Acres medios (escala log)"},
                     title="Cuantos incendios frente a que tan grandes")
    fig.update_traces(textposition="top center")
    fig.update_layout(template="plotly_dark", height=460,
                      margin=dict(l=10, r=10, t=70, b=10))
    st.plotly_chart(fig, width="stretch")

st.dataframe(
    perfil[["causa", "origen", "incendios", "pct_incendios", "acres",
            "pct_acres", "acres_medios", "acres_mediana", "indice_magnitud"]]
    .rename(columns={
        "causa": "Causa", "origen": "Origen", "incendios": "Incendios",
        "pct_incendios": "% incendios", "acres": "Acres", "pct_acres": "% acres",
        "acres_medios": "Media", "acres_mediana": "Mediana",
        "indice_magnitud": "Indice de magnitud"})
    .style.format({"Incendios": "{:,.0f}", "% incendios": "{:.2f}%",
                   "Acres": "{:,.0f}", "% acres": "{:.2f}%",
                   "Media": "{:,.1f}", "Mediana": "{:,.2f}",
                   "Indice de magnitud": "{:,.2f}"}),
    width="stretch", hide_index=True)
st.caption(
    "**Indice de magnitud** = cuota de superficie ÷ cuota de incendios. Por "
    "encima de 1, la causa quema mas de lo que su numero de incendios haria "
    "esperar; por debajo, menos. Es la forma compacta de leer el contraste."
)

with st.expander("Reparto por clase de magnitud NWCG"):
    clases = reparto_por_clase(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib)
    if not clases.empty:
        pivote = clases.pivot_table(index="causa", columns="clase",
                                    values="incendios", fill_value=0)
        pivote = 100 * pivote.div(pivote.sum(axis=1), axis=0)
        fig = px.imshow(pivote, text_auto=".1f", aspect="auto",
                        color_continuous_scale=["#1C1512", PALETA["brasa"], PALETA["ambar"]],
                        labels=dict(x="Clase NWCG", y="", color="% de la causa"),
                        title="Distribucion de cada causa entre las clases de tamano (%)")
        fig.update_layout(template="plotly_dark", height=460,
                          margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")

st.markdown("---")


# ==============================================================================
# 2. ESTACIONALIDAD
# ==============================================================================
st.header("2. La estacionalidad propia de cada causa")
st.markdown(
    "La ventana se mide sobre el **dia juliano** y no sobre el mes. Medida por "
    "meses, la ventana de `Fireworks` ocuparia «julio»; medida por dia, ocupa "
    "nueve dias."
)

ventanas = ventana_estacional(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib)
curva = curva_estacional(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib)

col_v, col_c = st.columns([2, 3])

with col_v:
    fig = go.Figure()
    for _, fila in ventanas.iterrows():
        fig.add_trace(go.Scatter(
            x=[fila["dia_p25"], fila["dia_p75"]], y=[fila["causa"], fila["causa"]],
            mode="lines", line=dict(color=PALETA["brasa"], width=9),
            showlegend=False, hovertemplate=f"{fila['causa']}: dias "
            f"{fila['dia_p25']}-{fila['dia_p75']} ({fila['amplitud_dias']} d)<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=[fila["dia_pico"]], y=[fila["causa"]], mode="markers",
            marker=dict(color=PALETA["ambar"], size=11, symbol="diamond"),
            showlegend=False, hovertemplate=f"pico: dia {fila['dia_pico']}<extra></extra>"))
    fig.update_layout(template="plotly_dark", height=480,
                      title="Ventana del 50 % central de cada causa",
                      xaxis_title="Dia del ano", xaxis_range=[0, 366],
                      margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("El rombo marca el dia mediano. La barra va del percentil 25 al 75.")

with col_c:
    causas_sel = st.multiselect(
        "Causas a superponer", options=sorted(curva["causa"].unique()),
        default=[c for c in ["Lightning", "Debris Burning", "Fireworks"]
                 if c in set(curva["causa"])])
    if causas_sel:
        sub = curva[curva["causa"].isin(causas_sel)].copy()
        sub["pct"] = 100 * sub["incendios"] / sub.groupby("causa")["incendios"].transform("sum")
        fig = px.line(sub, x="dia_juliano", y="pct", color="causa",
                      labels={"dia_juliano": "Dia del ano",
                              "pct": "% de los incendios de esa causa"},
                      title="Curva anual, normalizada por causa")
        fig.update_layout(template="plotly_dark", height=480,
                          margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")

st.dataframe(
    ventanas.rename(columns={
        "causa": "Causa", "dia_p25": "Dia 25 %", "dia_pico": "Dia mediano",
        "dia_p75": "Dia 75 %", "amplitud_dias": "Amplitud (dias)",
        "incendios": "Incendios"}),
    width="stretch", hide_index=True)

st.markdown("---")


# ==============================================================================
# 3. LA FIRMA TERRITORIAL
# ==============================================================================
st.header("3. La firma territorial")

tab_reg, tab_est, tab_mapa = st.tabs(
    ["Reparto por region", "Ranking de estados", "Distribucion espacial"])

with tab_reg:
    reg = causa_por_region(anio_ini, anio_fin, ambito_sel, solo_atrib)
    fig = px.bar(reg, x="pct_de_la_causa", y="causa", color="region",
                 orientation="h", color_discrete_map=COLOR_REGION,
                 labels={"pct_de_la_causa": "% de los incendios de la causa",
                         "causa": ""},
                 title="Como se reparte cada causa entre las cuatro regiones censales")
    fig.update_layout(template="plotly_dark", height=520, barmode="stack",
                      margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")

with tab_est:
    est = ranking_estados(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib, 15)
    fig = px.bar(est.sort_values("incendios"), x="incendios", y="estado",
                 orientation="h", color="region", color_discrete_map=COLOR_REGION,
                 hover_data=["acres", "cobertura_pct"],
                 labels={"incendios": "Incendios", "estado": ""},
                 title="Quince estados con mas incendios registrados")
    fig.update_layout(template="plotly_dark", height=520,
                      margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width="stretch")

with tab_mapa:
    n = st.slider("Tamano de la muestra", 5_000, 50_000, 25_000, step=5_000,
                  help="El mapa dibuja una muestra aleatoria. Los estadisticos "
                       "se calculan siempre sobre el universo completo.")
    mapa = muestra_geografica(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib, n)
    if not mapa.empty:
        fig = px.scatter_geo(mapa, lat="latitud", lon="longitud", color="origen",
                             color_discrete_map=COLOR_ORIGEN, scope="usa",
                             opacity=0.45, hover_data=["causa", "acres", "anio"],
                             title=f"Muestra aleatoria de {len(mapa):,} incendios")
        fig.update_layout(template="plotly_dark", height=560,
                          margin=dict(l=0, r=0, t=60, b=0))
        fig.update_geos(bgcolor="rgba(0,0,0,0)", lakecolor="#100C0A",
                        landcolor="#1C1512", subunitcolor="#5C3C28")
        st.plotly_chart(fig, width="stretch")

st.markdown("---")


# ==============================================================================
# 4. LA PRUEBA DE LAS DOS LECTURAS
# ==============================================================================
st.header("4. La prueba de las dos lecturas")
st.markdown(
    "Esta seccion **no depende del selector de lectura**: calcula las dos a la "
    "vez, porque su objeto es precisamente la distancia entre ellas."
)

contraste = contraste_de_lecturas(anio_ini, anio_fin, region_sel, ambito_sel)

if not contraste.empty:
    corte = int(contraste["corte"].iloc[0])
    col_g, col_t = st.columns([3, 2])
    with col_g:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Cambio leido sobre TODO el registro",
                             x=contraste["causa"], y=contraste["delta_todo"],
                             marker_color=PALETA["humo"]))
        fig.add_trace(go.Bar(name="Cambio leido sobre lo ATRIBUIDO",
                             x=contraste["causa"], y=contraste["delta_atrib"],
                             marker_color=PALETA["brasa"]))
        fig.add_hline(y=0, line_color="#9E7E6A", line_width=1)
        fig.update_layout(barmode="group", template="plotly_dark", height=470,
                          title=f"Cambio en puntos porcentuales: {anio_ini}-{corte} "
                                f"frente a {corte+1}-{anio_fin}",
                          yaxis_title="Puntos porcentuales",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                          margin=dict(l=10, r=10, t=80, b=10))
        st.plotly_chart(fig, width="stretch")
    with col_t:
        st.dataframe(
            contraste[["causa", "delta_todo", "delta_atrib", "espejismo"]]
            .rename(columns={"causa": "Causa", "delta_todo": "Δ sobre todo",
                             "delta_atrib": "Δ sobre atribuido",
                             "espejismo": "Espejismo"})
            .style.format({"Δ sobre todo": "{:+.2f}", "Δ sobre atribuido": "{:+.2f}",
                           "Espejismo": "{:+.2f}"}),
            width="stretch", hide_index=True)
        st.caption(
            "**Espejismo** = Δ sobre todo − Δ sobre atribuido. Es la parte del "
            "cambio aparente que no era de la causa sino del hueco creciendo "
            "por debajo."
        )

    st.success(
        "**El resultado central del trabajo.** Leido sobre el registro completo, "
        "`Lightning` cae entre los dos tramos; leido sobre lo atribuido, se "
        "mantiene practicamente plano. La caida no era del rayo: era del hueco. "
        "Y al reves, el crecimiento real de `Debris Burning` sobre lo atribuido "
        "es varias veces el que muestra el total."
    )

with st.expander("Serie anual completa por causa"):
    serie = serie_anual(anio_ini, anio_fin, region_sel, ambito_sel, solo_atrib)
    if not serie.empty:
        fig = px.area(serie, x="anio", y="pct_del_anio", color="causa",
                      labels={"anio": "Ano de temporada",
                              "pct_del_anio": "% de los incendios del ano"},
                      title="Composicion del registro, ano a ano")
        fig.update_layout(template="plotly_dark", height=520,
                          margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")
