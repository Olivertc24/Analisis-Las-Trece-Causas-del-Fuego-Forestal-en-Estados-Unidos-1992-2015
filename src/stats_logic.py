"""
src/stats_logic.py
================================================================================
TODA LA LOGICA ESTADISTICA DEL APLICATIVO
================================================================================

Las paginas solo dibujan. Cada funcion de aqui devuelve un DataFrame ya listo,
de modo que la estadistica se pueda leer, revisar y corregir en un solo lugar.

LA DECISION QUE ATRAVIESA TODO EL MODULO
----------------------------------------
Casi todas las funciones reciben `solo_atribuidas`. No es un filtro mas: es la
eleccion metodologica central del trabajo.

El 26,09 % de los incendios del registro cae en `Miscellaneous` o
`Missing/Undefined`, dos categorias que no nombran ningun mecanismo. Calcular
participaciones sobre el total reparte entre las once causas reales una base
que incluye ese bloque; calcularlas sobre el subconjunto atribuido lo excluye.

Las dos lecturas son legitimas y dan resultados distintos. Por eso el aplicativo
no elige por el usuario: expone el control y muestra la distancia entre ambas.
"""

import pandas as pd

from src.query_manager import consultar

# Paleta "Brasa", la misma del banner y de los diagramas del repositorio.
PALETA = {
    "brasa":      "#F77636",
    "ambar":      "#FFB020",
    "ceniza":     "#9E7E6A",
    "humo":       "#5C3C28",
    "atribuida":  "#F77636",
    "hueco":      "#5C3C28",
    "fondo":      "#100C0A",
}

COLOR_ORIGEN = {
    "Natural":      "#FFB020",
    "Antropico":    "#F77636",
    "No atribuida": "#5C3C28",
}

COLOR_REGION = {
    "Oeste":       "#F77636",
    "Sur":         "#FFB020",
    "Medio Oeste": "#9E7E6A",
    "Noreste":     "#C4AEA2",
    "Territorio":  "#5C3C28",
}


# ==============================================================================
# CONSTRUCCION DEL FILTRO
# ==============================================================================

def _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    """
    Devuelve (clausula_where, parametros). Centralizarlo evita que una pagina
    aplique el recorte de anos y otra se olvide, que es como dos cifras del
    mismo aplicativo acaban sin cuadrar.
    """
    condiciones = ["i.anio_temporada BETWEEN ? AND ?"]
    parametros = [anio_ini, anio_fin]

    if region and region != "Todas":
        condiciones.append(f"{REGION} = ?")
        parametros.append(region)
    if ambito and ambito != "Todos":
        condiciones.append(f"{AMBITO} = ?")
        parametros.append(ambito)
    if solo_atribuidas:
        condiciones.append("c.es_atribuida = 1")

    return " AND ".join(condiciones), parametros


# AMBITO Y REGION NO ESTAN EN LA BASE NORMALIZADA, Y ES CORRECTO QUE NO ESTEN.
# La normalizada guarda lo que la fuente tiene; ambas son clasificaciones que
# decide esta investigacion. El modelo dimensional las materializa en d_agencia
# y d_estado para Tableau; aqui se expresan como SQL para que el aplicativo
# pueda leer la normalizada, que es lo que le corresponde consumir.
#
# Las dos definiciones TIENEN que coincidir con las del modelo dimensional. La
# pagina de verificacion del aplicativo lo comprueba contra `fpa_analitica` en
# lugar de confiar en que nadie las toque por separado.
AMBITO = """CASE a.codigo
    WHEN 'ST/C&L' THEN 'Estatal-Local'
    WHEN 'IA'     THEN 'Interagencial'
    WHEN 'TRIBE'  THEN 'Tribal'
    ELSE 'Federal' END"""

ORIGEN = """CASE
    WHEN c.es_atribuida = 0     THEN 'No atribuida'
    WHEN c.nombre = 'Lightning' THEN 'Natural'
    ELSE 'Antropico' END"""

REGION = """CASE
    WHEN e.codigo IN ('CT','ME','MA','NH','NJ','NY','PA','RI','VT') THEN 'Noreste'
    WHEN e.codigo IN ('IL','IN','IA','KS','MI','MN','MO','NE','ND','OH','SD','WI') THEN 'Medio Oeste'
    WHEN e.codigo IN ('AL','AR','DE','DC','FL','GA','KY','LA','MD','MS','NC',
                      'OK','SC','TN','TX','VA','WV') THEN 'Sur'
    WHEN e.codigo IN ('AK','AZ','CA','CO','HI','ID','MT','NV','NM','OR','UT',
                      'WA','WY') THEN 'Oeste'
    ELSE 'Territorio' END"""


# El ano sale de `anio_temporada` y NO de la fecha de descubrimiento. No es lo
# mismo: cuatro incendios de Oregon declaran una temporada distinta a la de su
# fecha, porque se imputan al ano en que se contuvieron. `anio_temporada` es el
# que usa la agencia que reporta, y es el que sostiene las cifras documentadas.
#
# El dia juliano si se calcula, porque la estacionalidad es del suceso, no de
# la temporada administrativa. Se envuelve `incendios` en una derivada para
# recorrer la tabla UNA vez en lugar de reunirla consigo misma.
_DESDE = """
FROM (SELECT *, dayofyear(CAST(fecha_descubrimiento AS DATE)) AS doy
      FROM incendios) i
JOIN causas        c ON c.causa_id   = i.causa_id
JOIN estados       e ON e.estado_id  = i.estado_id
JOIN agencias_nwcg a ON a.agencia_id = i.agencia_id
"""


# ==============================================================================
# INDICADORES DE CABECERA
# ==============================================================================

def indicadores(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    df = consultar(f"""
        SELECT COUNT(*)                        AS incendios,
               SUM(i.tamano_acres)             AS acres,
               AVG(i.tamano_acres)             AS acres_medios,
               MEDIAN(i.tamano_acres)          AS acres_mediana,
               AVG(c.es_atribuida)             AS cobertura,
               COUNT(DISTINCT c.causa_id)      AS causas
        {_DESDE} WHERE {donde}""", par)
    return df.iloc[0].to_dict() if len(df) else {}


# ==============================================================================
# OBJETIVO 1 - COBERTURA DE LA ATRIBUCION
# ==============================================================================

def cobertura_por(dimension, anio_ini, anio_fin, region, ambito):
    """`dimension` es 'ambito', 'agencia', 'region' o 'anio'."""
    columna = {"ambito": AMBITO, "agencia": "a.codigo",
               "region": REGION, "anio": "i.anio_temporada"}[dimension]
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, False)
    return consultar(f"""
        SELECT {columna}                        AS categoria,
               COUNT(*)                         AS incendios,
               100.0 * AVG(c.es_atribuida)      AS cobertura_pct,
               SUM(CASE WHEN c.es_atribuida = 0 THEN 1 ELSE 0 END) AS sin_causa
        {_DESDE} WHERE {donde}
        GROUP BY 1 HAVING COUNT(*) >= 100 ORDER BY cobertura_pct DESC""", par)


# ==============================================================================
# OBJETIVOS 2 Y 3 - PERFIL DE CADA CAUSA, FRECUENCIA CONTRA MAGNITUD
# ==============================================================================

def perfil_causas(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    df = consultar(f"""
        SELECT c.nombre                 AS causa,
               {ORIGEN}                 AS origen,
               c.es_atribuida           AS es_atribuida,
               COUNT(*)                 AS incendios,
               SUM(i.tamano_acres)      AS acres,
               AVG(i.tamano_acres)      AS acres_medios,
               MEDIAN(i.tamano_acres)   AS acres_mediana
        {_DESDE} WHERE {donde}
        GROUP BY 1,2,3 ORDER BY incendios DESC""", par)
    if df.empty:
        return df
    df["pct_incendios"] = 100 * df["incendios"] / df["incendios"].sum()
    df["pct_acres"] = 100 * df["acres"] / df["acres"].sum()
    # Razon entre la cuota de superficie y la de frecuencia: por encima de 1 la
    # causa quema mas de lo que su numero de incendios haria esperar.
    df["indice_magnitud"] = df["pct_acres"] / df["pct_incendios"]
    return df


def reparto_por_clase(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    return consultar(f"""
        SELECT c.nombre AS causa, i.clase_tamano AS clase, COUNT(*) AS incendios
        {_DESDE} WHERE {donde}
        GROUP BY 1,2 ORDER BY 1,2""", par)


# ==============================================================================
# OBJETIVO 4 - ESTACIONALIDAD
# ==============================================================================

def curva_estacional(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    return consultar(f"""
        SELECT c.nombre AS causa, i.doy AS dia_juliano, COUNT(*) AS incendios
        {_DESDE} WHERE {donde}
        GROUP BY 1,2 ORDER BY 1,2""", par)


def ventana_estacional(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    """
    Amplitud en dias del 50 % central de los eventos de cada causa.

    Se usa el rango intercuartilico sobre el DIA JULIANO y no sobre el mes:
    medida por meses, la ventana de Fireworks ocuparia "julio"; medida por dia,
    ocupa nueve dias, que es la semana del 4 de julio.
    """
    curva = curva_estacional(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    if curva.empty:
        return curva
    filas = []
    for causa, grupo in curva.groupby("causa"):
        grupo = grupo.sort_values("dia_juliano")
        acumulado = grupo["incendios"].cumsum() / grupo["incendios"].sum()
        p25 = grupo.loc[acumulado >= 0.25, "dia_juliano"].min()
        p50 = grupo.loc[acumulado >= 0.50, "dia_juliano"].min()
        p75 = grupo.loc[acumulado >= 0.75, "dia_juliano"].min()
        filas.append({"causa": causa, "dia_p25": p25, "dia_pico": p50,
                      "dia_p75": p75, "amplitud_dias": p75 - p25,
                      "incendios": int(grupo["incendios"].sum())})
    return pd.DataFrame(filas).sort_values("amplitud_dias").reset_index(drop=True)


# ==============================================================================
# OBJETIVO 5 - GEOGRAFIA
# ==============================================================================

def causa_por_region(anio_ini, anio_fin, ambito, solo_atribuidas):
    donde, par = _filtro(anio_ini, anio_fin, "Todas", ambito, solo_atribuidas)
    df = consultar(f"""
        SELECT c.nombre AS causa, {REGION} AS region, COUNT(*) AS incendios
        {_DESDE} WHERE {donde}
        GROUP BY 1,2""", par)
    if df.empty:
        return df
    df["pct_de_la_causa"] = 100 * df["incendios"] / df.groupby("causa")["incendios"].transform("sum")
    return df


def ranking_estados(anio_ini, anio_fin, region, ambito, solo_atribuidas, limite=15):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    return consultar(f"""
        SELECT e.codigo AS estado, {REGION} AS region,
               COUNT(*) AS incendios, SUM(i.tamano_acres) AS acres,
               100.0 * AVG(c.es_atribuida) AS cobertura_pct
        {_DESDE} WHERE {donde}
        GROUP BY 1,2 ORDER BY incendios DESC LIMIT {int(limite)}""", par)


def muestra_geografica(anio_ini, anio_fin, region, ambito, solo_atribuidas, n=25000):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    return consultar(f"""
        SELECT i.latitud, i.longitud, c.nombre AS causa, {ORIGEN} AS origen,
               i.tamano_acres AS acres, i.anio_temporada AS anio
        {_DESDE} WHERE {donde}
        USING SAMPLE {int(n)} ROWS""", par)


# ==============================================================================
# OBJETIVO 6 - ESTABILIDAD TEMPORAL, LEIDA DE DOS MANERAS
# ==============================================================================

def serie_anual(anio_ini, anio_fin, region, ambito, solo_atribuidas):
    donde, par = _filtro(anio_ini, anio_fin, region, ambito, solo_atribuidas)
    df = consultar(f"""
        SELECT i.anio_temporada AS anio, c.nombre AS causa, COUNT(*) AS incendios
        {_DESDE} WHERE {donde}
        GROUP BY 1,2 ORDER BY 1,2""", par)
    if df.empty:
        return df
    df["pct_del_anio"] = 100 * df["incendios"] / df.groupby("anio")["incendios"].transform("sum")
    return df


def contraste_de_lecturas(anio_ini, anio_fin, region, ambito):
    """
    El resultado central del trabajo: la misma causa, en dos tramos, leida
    sobre el registro completo y sobre el subconjunto atribuido.

    La diferencia entre ambas columnas no es ruido: es cuanto del cambio
    aparente se debe al hueco de atribucion creciendo por debajo.
    """
    corte = (anio_ini + anio_fin) // 2
    piezas = []
    for atribuidas, etiqueta in [(False, "todo"), (True, "atrib")]:
        donde, par = _filtro(anio_ini, anio_fin, region, ambito, atribuidas)
        df = consultar(f"""
            SELECT c.nombre AS causa,
                   CASE WHEN i.anio_temporada <= {corte} THEN 'primero' ELSE 'segundo' END AS tramo,
                   COUNT(*) AS incendios
            {_DESDE} WHERE {donde} AND c.es_atribuida = 1
            GROUP BY 1,2""", par)
        if df.empty:
            continue
        # el denominador cambia segun la lectura: ahi esta todo el asunto
        donde_t, par_t = _filtro(anio_ini, anio_fin, region, ambito, atribuidas)
        tot = consultar(f"""
            SELECT CASE WHEN i.anio_temporada <= {corte} THEN 'primero' ELSE 'segundo' END AS tramo,
                   COUNT(*) AS base
            {_DESDE} WHERE {donde_t} GROUP BY 1""", par_t)
        df = df.merge(tot, on="tramo")
        df[etiqueta] = 100 * df["incendios"] / df["base"]
        piezas.append(df.pivot_table(index="causa", columns="tramo",
                                     values=etiqueta).add_prefix(f"{etiqueta}_"))
    if not piezas:
        return pd.DataFrame()

    r = piezas[0].join(piezas[1], how="outer").reset_index()
    r["delta_todo"] = r["todo_segundo"] - r["todo_primero"]
    r["delta_atrib"] = r["atrib_segundo"] - r["atrib_primero"]
    # cuanto del cambio aparente era el hueco y no la causa
    r["espejismo"] = r["delta_todo"] - r["delta_atrib"]
    r["corte"] = corte
    return r.sort_values("delta_atrib", ascending=False).reset_index(drop=True)


# ==============================================================================
# LECTURA AUTOMATICA
# ==============================================================================

def formato_numero(n):
    return f"{int(n):,}".replace(",", ".")


def lectura_automatica(ind, solo_atribuidas):
    if not ind or not ind.get("incendios"):
        return "No hay incendios que cumplan los criterios seleccionados."
    cobertura = 100 * (ind.get("cobertura") or 0)
    base = ("**solo sobre las once causas atribuidas**" if solo_atribuidas
            else "**sobre el registro completo**")
    texto = (
        f"Se describen {formato_numero(ind['incendios'])} incendios, "
        f"{base}, que suman {ind['acres']/1e6:,.2f} millones de acres. "
        f"La superficie media por evento es de {ind['acres_medios']:,.1f} acres "
        f"y la mediana de {ind['acres_mediana']:,.2f}: la distancia entre ambas "
        f"mide hasta que punto unos pocos incendios concentran la superficie."
    )
    if not solo_atribuidas:
        texto += (
            f" La atribucion de causa alcanza al {cobertura:,.2f} % de este "
            f"subconjunto; el resto cae en Miscellaneous o Missing/Undefined."
        )
    return texto
