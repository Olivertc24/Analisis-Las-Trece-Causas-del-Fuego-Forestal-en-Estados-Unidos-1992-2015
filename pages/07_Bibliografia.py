"""
pages/07_Bibliografia.py
================================================================================
REFERENCIAS BIBLIOGRAFICAS Y FUENTES CONSULTADAS
================================================================================
"""

import streamlit as st

st.set_page_config(page_title="Bibliografia", page_icon="📖", layout="wide")

st.title("Referencias bibliograficas")
st.caption("Fuentes de datos, literatura cientifica y documentacion tecnica")

st.header("Fuente de datos primaria")
st.markdown("""
- Short, K. C. (2017). *Spatial wildfire occurrence data for the United States,
  1992-2015 [FPA_FOD_20170508]* (4.ª ed.). Fort Collins, CO: Forest Service
  Research Data Archive. https://doi.org/10.2737/RDS-2013-0009.4

- Tatman, R. (2020). *1.88 Million US Wildfires* [Conjunto de datos]. Kaggle.
  https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires
""")

st.info("""
**Licencia y cita obligatoria.** El conjunto de datos se distribuye bajo
licencia **CC0 (dominio publico)**. Fue producido con financiamiento del
Gobierno de Estados Unidos y puede utilizarse sin permisos ni tarifas
adicionales. La documentacion de la fuente exige, no obstante, citar el trabajo
de Short (2017) en toda publicacion, presentacion o producto de investigacion
que lo emplee. Esta investigacion cumple dicho requisito.
""")

st.header("Literatura cientifica sobre el fenomeno")
st.markdown("""
- Balch, J. K., Bradley, B. A., Abatzoglou, J. T., Nagy, R. C., Fusco, E. J., y
  Mahood, A. L. (2017). Human-started wildfires expand the fire niche across the
  United States. *Proceedings of the National Academy of Sciences*, 114(11),
  2946-2951. https://doi.org/10.1073/pnas.1617394114

- Short, K. C. (2014). A spatial database of wildfires in the United States,
  1992-2011. *Earth System Science Data*, 6(1), 1-27.
  https://doi.org/10.5194/essd-6-1-2014

- Abatzoglou, J. T., y Williams, A. P. (2016). Impact of anthropogenic climate
  change on wildfire across western US forests. *Proceedings of the National
  Academy of Sciences*, 113(42), 11770-11775.
  https://doi.org/10.1073/pnas.1607171113
""")

st.header("Normativa y documentacion institucional")
st.markdown("""
- National Wildfire Coordinating Group. *NWCG Glossary of Wildland Fire*
  (PMS 205). Clasificacion de causas estadisticas y clases de tamano A-G.
  https://www.nwcg.gov/glossary/a-z

- National Wildfire Coordinating Group. *NWCG Standards for Wildland Fire
  Reporting*. Estandar bajo el que los organismos federales, estatales y locales
  reportan a la base FPA FOD.

- U.S. Census Bureau. *Census Regions and Divisions of the United States*.
  Definicion de las cuatro regiones censales empleadas en el objetivo 5.
  https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf
""")

st.header("Fundamentos de modelado de datos")
st.markdown("""
- Codd, E. F. (1971). Further normalization of the data base relational model.
  *IBM Research Report RJ909*. Formulacion de la segunda y tercera formas
  normales.

- Date, C. J. (2019). *Database Design and Relational Theory: Normal Forms and
  All That Jazz* (2.ª ed.). Apress.

- Kimball, R., y Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive
  Guide to Dimensional Modeling* (3.ª ed.). Wiley. Esquema en estrella,
  dimensiones conformadas y dimensiones degeneradas.
""")

st.header("Documentacion tecnica de las herramientas")
st.markdown("""
- DuckDB Foundation. *DuckDB Documentation*. https://duckdb.org/docs/

- Raasveldt, M., y Muhleisen, H. (2019). DuckDB: An embeddable analytical
  database. *Proceedings of the 2019 International Conference on Management of
  Data (SIGMOD '19)*, 1981-1984. https://doi.org/10.1145/3299869.3320212

- MotherDuck. *MotherDuck Documentation*. https://motherduck.com/docs/

- Supabase. *Supabase Documentation*. https://supabase.com/docs

- Streamlit Inc. *Streamlit Documentation*. https://docs.streamlit.io/

- Plotly Technologies. *Plotly Python Open Source Graphing Library*.
  https://plotly.com/python/
""")

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de "
    "Venezuela · Material academico de la asignatura Computacion II."
)
