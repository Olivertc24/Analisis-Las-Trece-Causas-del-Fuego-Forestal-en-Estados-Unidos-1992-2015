# Normalización de `FPA_FOD_20170508`

De una tabla de 39 columnas sin una sola clave declarada a **una entidad y nueve
catálogos en tercera forma normal**.

```bash
cd "Base de datos"
sqlite3 fpa_normalizada.sqlite < normalizacion_3fn.sql
```

Tarda **9,4 segundos** y produce **340,6 MB** frente a los 759 MB de la fuente.

El script está organizado en siete partes —una por forma normal, más el
diagnóstico, la integridad de dominio, las exclusiones y la construcción— y cada
bloque de código dice a qué parte del razonamiento responde. Este documento sigue
el mismo orden.

---

## Parte I — Diagnóstico de la fuente

| Objeto | Filas | Columnas |
|---|---:|---:|
| `Fires` | 1.880.465 | 39 |
| `NWCG_UnitIDActive_20170109` | 5.867 | 13 |

### La clave existe, y aquí eso es una novedad

A diferencia de otras fuentes de esta serie, `Fires` sí trae una clave real:

| Columna | Valores distintos | ¿Clave? |
|---|---:|---|
| `OBJECTID` | 1.880.465 | sí |
| `FOD_ID` | 1.880.465 | sí |
| `FPA_ID` | 1.880.462 | **no — 3 duplicados** |

`FPA_ID` es el identificador que la documentación presenta como global, y no lo
es. Los tres pares colisionan, dos de ellos entre años distintos:

| `FPA_ID` | `FOD_ID` | Años |
|---|---|---|
| `FS-1452833` | 22093 · 201432072 | 2007 · 2012 |
| `ICS209_2009_KS-DDQ-128` | 1300088 · 201750002 | 2009 · 2012 |
| `SFO-2015CACDFLNU003791` | 300245030 · 300306586 | 2015 |

Se adopta `FOD_ID` como clave primaria. `FPA_ID` se conserva como atributo
descriptivo, nunca como clave alternativa.

### Una hipótesis propia, refutada

Se sospechó que `FPA_ID` era un compuesto —prefijo de sistema más número local—
y que por tanto violaba la 1FN. Se midió: **1.401.023** de 1.880.465 valores
llevan guion, pero el prefijo **no coincide nunca** con `SOURCE_SYSTEM` (cero
coincidencias en 1.401.023 casos). Los prefijos —`SFO`, `W`, `FS`, `TFS`, `IA`,
`ALS`— son etiquetas del proceso de carga, y uno solo de ellos, `SFO`, abarca
cuatro sistemas de origen distintos. La hipótesis se descarta: no hay nada que
descomponer ahí.

### Una relación que la fuente tiene y no declara

`Fires.NWCG_REPORTING_UNIT_ID` enlaza con `NWCG_UnitIDActive.UnitId` en el
**98,15 %** de las filas (1.845.708 de 1.880.465). Ese enlace no está declarado
en ninguna parte del esquema original. Integrarlo es lo que permite agrupar por
departamento, agencia y área geográfica —los niveles en que el sistema
estadounidense de fuego realmente se organiza— y sostiene el objetivo 1 de la
investigación.

---

## Parte II — Primera forma normal: atomicidad

### No hay grupos repetitivos, y conviene decirlo

En otras fuentes de esta serie sí los había: columnas numeradas del tipo
`clima1..clima4` que obligaban a crear tablas puente. **Aquí no existe ninguna.**
Las 39 columnas son monovaluadas, de modo que la cláusula de grupos repetitivos
de la 1FN se cumple de origen. Afirmarlo explícitamente evita que el lector
suponga que se pasó por alto.

### Lo que sí viola la atomicidad: las fechas y las horas

`DISCOVERY_DATE` y `CONT_DATE` no están guardadas como fechas sino como **números
de día juliano en coma flotante**:

```
DISCOVERY_DATE = 2453403.5   →   2005-02-02
```

Así almacenada, la columna no admite ninguna operación de calendario sin
convertirla antes, y cualquier comparación entre fechas es una comparación entre
flotantes. Se convierten a texto ISO `AAAA-MM-DD`.

`DISCOVERY_TIME` y `CONT_TIME` vienen como texto de cuatro caracteres, `'HHMM'`:
dos hechos —hora y minuto— en un solo campo. Se separan en columnas enteras.

---

## Parte III — Segunda forma normal

La 2FN se cumple de forma **trivial**, y conviene explicar por qué en lugar de
inventar trabajo donde no lo hay.

La clave primaria de la entidad es `FOD_ID`: una sola columna. Una dependencia
parcial exige una clave **compuesta**, porque solo de una clave compuesta se
puede depender «en parte». Con clave simple, el enunciado de la 2FN no tiene caso
que regular.

Esa es justamente la razón por la que en esta fuente el trabajo real se concentra
en la 3FN. Los catálogos que crea la parte IV sí tienen, algunos, clave
compuesta: en `condados` el nombre depende de **las dos** columnas —estado y
código FIPS—, porque el código de tres dígitos se repite entre estados.

---

## Parte IV — Tercera forma normal: dependencias transitivas

Se probaron seis dependencias candidatas contando pares distintos. Cuando el
número de pares excede el de determinantes, el mismo determinante apunta a más de
un valor y la dependencia no se sostiene.

| Dependencia | Determinantes | Valores | Pares | Veredicto |
|---|---:|---:|---:|---|
| `STAT_CAUSE_CODE → DESCR` | 13 | 13 | 13 | limpia |
| `OWNER_CODE → DESCR` | 16 | 16 | 16 | limpia |
| `NWCG_UNIT_ID → UNIT_NAME` | 1.640 | 1.635 | 1.640 | limpia |
| `(STATE, FIPS_CODE) → FIPS_NAME` | 2.795 | 1.698 | 2.798 | **sucia** |
| `SOURCE_SYSTEM → SYSTEM_TYPE` | 38 | 3 | 39 | **sucia** |
| `(SOURCE_SYSTEM, SOURCE_UNIT) → NAME` | 5.249 | 4.441 | 7.129 | **falsa** |

### La dependencia falsa: el código que no identifica nada

`SOURCE_REPORTING_UNIT` parece un código de unidad y no lo es. En el sistema
`ST-TXTXS`, el código `TXVFD` está asociado a **946 nombres distintos** de
cuerpos de bomberos voluntarios de Texas; `TXSFD`, a 369. No es un identificador:
es un cajón que significa «bomberos voluntarios de Texas, sin especificar». En
total, **407 códigos arrastran 2.287 nombres**.

Extraer un catálogo con clave `(sistema, código)` sería **inventar una
dependencia que los datos no tienen**, y colapsaría 946 cuerpos de bomberos en
uno solo. La 3FN no obliga a extraer nada aquí, porque sin dependencia transitiva
no hay violación. Pero repetir el nombre 1,88 millones de veces tampoco tiene
sentido, así que se extrae un catálogo cuya clave natural es la **terna
completa** `(sistema, código, nombre)`: 7.129 filas. Se elimina la repetición sin
afirmar nada falso sobre los datos.

### Las sucias: valor mayoritario, y la discrepancia a la vista

**`SOURCE_SYSTEM → SOURCE_SYSTEM_TYPE`.** El sistema `IA-ICS209` aparece 1.982
veces como `INTERAGCY` y **una** vez como `NONFED`.

**`(STATE, FIPS_CODE) → FIPS_NAME`.** Tres conflictos, de dos naturalezas:

| Estado | FIPS | Valores | Naturaleza |
|---|---|---|---|
| CA | 005 | Amador (591) · Douglas (1) | **error de dato** — el condado 005 de California es Amador |
| TN | 041 | DeKalb · Dekalb | mayúscula |
| VA | 810 | Virginia Beach City · Virginia Beach city | mayúscula |

En ambos casos el catálogo se construye con el valor **mayoritario**. No se
corrige la fuente ni se borra la fila discrepante: lo que se corrige es el
*catálogo*, que es donde el valor tiene que ser único para que la dependencia se
sostenga.

### Las columnas derivadas también son dependencias transitivas

Un atributo calculable a partir de otro atributo no clave depende de él, y por
tanto viola la 3FN igual que cualquier otra transitividad.

| Derivación | Discrepancias | Decisión |
|---|---:|---|
| `DISCOVERY_DOY` desde `DISCOVERY_DATE` | 0 | se elimina |
| `CONT_DOY` desde `CONT_DATE` | 0 | se elimina |
| `FIRE_SIZE_CLASS` desde `FIRE_SIZE` | 0 | pasa a catálogo |
| `FIRE_YEAR` desde `DISCOVERY_DATE` | **4** | **se conserva** |

**Sobre `FIRE_SIZE_CLASS`: el primer intento falló y el error era del
verificador.** La primera prueba dio 6 discrepancias, todas en incendios de entre
0,25 y 0,26 acres. Se había usado el umbral «menos de 0,26 acres» para la clase A
cuando la norma NWCG dice «0,25 acres o menos». Con el umbral correcto, la
derivación es exacta en los 1.880.465 registros.

Un segundo control reveló el error complementario, esta vez en los límites
superiores: **41.468 incendios caen exactamente sobre un límite** —35.215 con
10,0 acres declarados clase C, 4.296 con 100,0 declarados D, y así hasta 73 con
5.000,0 declarados G—. La convención «más de 10 a 100» los habría dado todos por
incoherentes. La norma define la clase C como «10 a 99,9»: el límite inferior es
inclusivo y el superior exclusivo. El catálogo guarda por eso el límite superior
y una bandera `hasta_inclusivo`, que vale 1 únicamente en la clase A.

**Sobre `FIRE_YEAR`:** cuatro incendios de Oregón declaran un año distinto al de
su fecha de descubrimiento. Tres son de 1993 descubiertos en 1994; el cuarto se
descubrió el 2009-10-10 y se contuvo el 2010-06-29, declarándose 2010.
`FIRE_YEAR` no es el año de la fecha: es el **año de temporada** al que la
agencia imputa el incendio. Lleva información propia y se conserva, renombrado
`anio_temporada` para que nadie lo confunda.

---

## Parte V — Integridad de dominio (más allá de la 3FN)

Nada de lo que sigue lo exige una forma normal. Se separa a propósito para que no
se confunda una decisión de dominio con teoría relacional.

### Las dos causas que no son causas

De los trece valores del catálogo `causas`, dos no nombran mecanismo alguno:

| Categoría | Incendios | % |
|---|---:|---:|
| `Miscellaneous` | 323.805 | 17,22 % |
| `Missing/Undefined` | 166.723 | 8,87 % |
| **Suma** | **490.528** | **26,09 %** |

El catálogo lleva por eso una bandera **`es_atribuida`**, para que ninguna
consulta pueda calcular una participación sobre el total sin haber decidido
antes, de forma explícita, qué hace con ese 26,09 %. La bandera no filtra nada:
obliga a elegir.

### Las claves foráneas se declaran

La fuente no declara ni una sola. Aquí se declaran todas, y al cierre se ejecuta
`PRAGMA foreign_key_check`. Una base que no puede verificarse no es una base
normalizada: es una base ordenada.

---

## Parte VI — Lo que se excluye, y por qué

| Columna | Motivo |
|---|---|
| `OBJECTID` | Identificador de ArcGIS, redundante con `FOD_ID`: ambos tienen 1.880.465 valores distintos sobre las mismas filas. |
| `Shape` | Geometría SpatiaLite de tipo `POINT`, **107,6 MB**. Duplica exactamente `LATITUDE` y `LONGITUDE`, que sí se conservan. |
| `DISCOVERY_DOY` | Derivada exacta de la fecha. |
| `CONT_DOY` | Derivada exacta de la fecha. |

Son **4 columnas excluidas de 39**. Las 35 restantes se cargan íntegras,
incluidas las casi vacías —`COMPLEX_NAME` tiene 5.183 valores no nulos de
1.880.465—, porque su vacío es un dato sobre el registro.

---

## Parte VII — El resultado

| Tabla | Filas | Papel |
|---|---:|---|
| `incendios` | 1.880.465 | la entidad |
| `unidades_origen` | 7.129 | terna (sistema, código, nombre) |
| `condados` | 2.795 | clave compuesta (estado, FIPS) |
| `unidades_nwcg` | 1.640 | enriquecidas con el catálogo auxiliar |
| `sistemas_origen` | 38 | |
| `propietarios` | 16 | tenencia del terreno |
| `causas` | 13 | **el catálogo central** |
| `agencias_nwcg` | 11 | |
| `estados` | 52 | |
| `clases_tamano` | 7 | rangos NWCG |

De las 1.640 unidades NWCG, **17 no aparecen** en el catálogo auxiliar; la
bandera `en_catalogo` lo deja registrado en lugar de silenciarlo.

---

## Verificación

Ejecutada sobre la base construida, contrastando contra la fuente:

| Control | Resultado |
|---|---|
| Filas en `incendios` | 1.880.465 — igual al origen |
| Suma de `tamano_acres` | 140.132.550 — **idéntica al origen** |
| Incendios sin causa atribuida | 490.528 — igual al origen |
| Clase recalculada desde los acres | **0 discrepancias** |
| `PRAGMA foreign_key_check` | sin violaciones |
| Fechas nulas tras convertir el día juliano | 0 |
| Horas fuera de 0–23 · minutos fuera de 0–59 | 0 · 0 |
| `FPA_ID` duplicados | 3 — los mismos tres del diagnóstico |

Los **678.148** incendios sin condado corresponden exactamente a los que traen
`FIPS_CODE` nulo en la fuente (1.880.465 − 1.202.317). No es una pérdida del
proceso: es un vacío del registro.

---

La etapa siguiente es la carga de esta base en **MotherDuck**, desde donde la
consumirá el aplicativo de Streamlit.
