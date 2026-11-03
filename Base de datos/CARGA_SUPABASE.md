# Carga de la tabla original en PostgreSQL (Supabase)

La tabla cruda de la fuente —`Fires`, tal como la distribuye Short (2017)— se
aloja en **PostgreSQL 17.11** sobre Supabase. Es la base contra la que se
responde el cuestionario SQL.

El script es [`carga_supabase.py`](carga_supabase.py):

```bash
cd "Base de datos"
python3 carga_supabase.py                 # carga midiendo tras cada ano
python3 carga_supabase.py --solo-medir    # informa del tamano, no carga
python3 carga_supabase.py --limite-mb 478 # corta antes de llegar al limite
```

---

## El resultado

| | |
|---|---:|
| Filas cargadas | **1.805.974** de 1.880.465 (**96,04 %**) |
| Periodo cubierto | 1992-01-01 a **2014-12-31** |
| Tamaño de la tabla | 475,7 MB |
| Tamaño total de la base | 486,2 MB de 500 |
| Espacio libre | 13,8 MB |

**El año 2015 no está.** No es un fallo del proceso: es el corte previsto. Sus
74.491 incendios necesitarían unos 19,6 MB y solo quedaban 13,8.

---

## Por qué sin clave primaria

La tabla sin la columna `Shape` ocupa en PostgreSQL unos 470 MB. El plan
gratuito de Supabase ofrece 500, de los cuales **10,3 MB ya los consume el
propio Supabase** antes de cargar nada.

Un índice primario sobre `FOD_ID` añadiría unos 40 MB que harían inviable la
carga, y **no aporta nada al cuestionario**: son consultas analíticas que
recorren la tabla entera, donde PostgreSQL prefiere el recorrido secuencial
aunque el índice exista.

---

## Por qué por lotes de años, midiendo

Porque la holgura era escasa y **agotar la cuota deja el proyecto en modo
restringido**. Cargar año a año y consultar `pg_database_size` después de cada
lote permite parar en el último año completo y documentarlo, en lugar de
reventar la cuota a ciegas y tener que limpiar.

El registro del proceso, año por año:

| Año | Filas | Acumulado | Base (MB) |
|---|---:|---:|---:|
| 1992 | 67.975 | 67.975 | 27,9 |
| 1995 | 71.472 | 277.391 | 82,3 |
| 2000 | 96.416 | 668.564 | 180,8 |
| 2005 | 88.604 | 1.056.951 | 281,8 |
| 2010 | 79.889 | 1.510.120 | 402,7 |
| 2013 | 64.780 | 1.738.221 | 466,7 |
| **2014** | 67.753 | **1.805.974** | **486,2** ← corte |

---

## Qué se excluye, y por qué

Solo **`Shape`**: geometría SpatiaLite de tipo `POINT`, 107,6 MB, que duplica
exactamente `LATITUDE` y `LONGITUDE` —ambas conservadas— y que PostgreSQL no
puede leer sin PostGIS.

Las otras **38 columnas se cargan íntegras**, incluidas las casi vacías
(`COMPLEX_NAME` tiene 5.183 valores no nulos), porque el cuestionario se
responde contra la fuente tal como es, con sus inconsistencias a la vista.

Se consideró excluir además `OBJECTID`, `DISCOVERY_DOY` y `CONT_DOY` —las tres
redundantes, y las tres excluidas del modelo normalizado por ese motivo— para
ganar los ~12,7 MB que habrían permitido cargar también 2015. **Se descartó**:
habría dejado unos 7 MB de margen sobre una cuota que, al superarse, restringe
el proyecto, y el crecimiento normal del WAL puede comérselos.

---

## Dos errores encontrados al ejecutar

**`pg_database_size` ejecutada en el cliente en vez de en el servidor.** Es una
función de PostgreSQL; invocada directamente, DuckDB la busca en su propio
catálogo y falla. Tiene que ir por `postgres_query`. El fallo apareció justo
después de insertar el primer año, con la tabla ya creada.

**Las fechas julianas retrocedían un día.** La primera versión convertía con
`to_timestamp((JD - 2440587.5) * 86400)`, que devuelve un valor **con zona
horaria**; al reducirlo a `DATE` se aplica la zona local y, estando detrás de
UTC, toda fecha perdía un día. El síntoma habría sido silencioso: fechas
plausibles, todas corridas, y la estacionalidad entera desplazada.

La versión correcta usa aritmética entera de días:

```sql
DATE '1970-01-01' + CAST(CAST(DISCOVERY_DATE AS DOUBLE) - 2440587.5 AS INTEGER)
```

Verificada por dos vías: coincide con la conversión de SQLite, y da **cero
discrepancias** frente a `DISCOVERY_DOY` en los 1.880.465 registros. Las cuatro
frente a `FIRE_YEAR` son los casos de Oregón documentados en la normalización.

---

## Verificación

Contrastada contra la fuente, restringida a los años cargados:

| Control | Fuente (≤2014) | Supabase |
|---|---:|---:|
| Filas | 1.805.974 | 1.805.974 |
| Suma de `FIRE_SIZE` | 129.914.282 | 129.914.282 |
| Causas distintas | 13 | 13 |
| Primera fecha | — | 1992-01-01 |
| Última fecha | — | 2014-12-31 |

Que la primera fecha sea exactamente `1992-01-01` confirma que la conversión
del día juliano quedó bien: con el error de zona horaria habría empezado el
1991-12-31.

---

## Una advertencia sobre el plan gratuito

**Los proyectos gratuitos de Supabase se pausan tras una semana sin
actividad.** Si el cuestionario deja de responder, el proyecto está pausado y
se reactiva con un clic desde el panel. No es un fallo del aplicativo: el
diagnóstico de la página lo distingue y lo explica.
