-- =============================================================================
-- MODELO DIMENSIONAL: ESQUEMA EN ESTRELLA PARA LA EXPLOTACION ANALITICA
-- Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) - Computacion II
-- =============================================================================
--
-- ORIGEN   fpa_normalizada.sqlite    1 entidad + 9 catalogos en 3FN, 340,6 MB
-- DESTINO  fpa_analitica.sqlite      9 dimensiones + 1 hecho + parametros
--
-- EJECUCION (desde esta carpeta):
--     sqlite3 fpa_analitica.sqlite < modelo_dimensional.sql
--
-- POR QUE DESNORMALIZAR LO QUE SE ACABA DE NORMALIZAR
-- ------------------------------------------------------------------
-- Son objetivos opuestos. La 3FN optimiza la ESCRITURA: cada hecho vive en un
-- solo lugar, de modo que no puede contradecirse consigo mismo. A cambio,
-- responder "que proporcion de los incendios por rayo ocurre en el Oeste"
-- exige recorrer `incendios`, `causas` y `estados` con reuniones sucesivas.
--
-- El esquema en estrella optimiza la LECTURA y, sobre todo, la COMPRENSION:
-- separa lo que se mide de aquello POR LO QUE se mide. Esa separacion obliga a
-- declarar en voz alta cual es la unidad de analisis, que es justo lo que un
-- trabajo estadistico tiene que dejar explicito.
--
-- UN SOLO HECHO, UN SOLO GRANO
-- ------------------------------------------------------------------
-- Otros trabajos de esta serie necesitaron tres tablas de hechos porque tenian
-- tres granos distintos -la colision, el conductor, la victima-. Aqui NO. La
-- fuente registra un solo tipo de suceso, el incendio, y todas las preguntas
-- de la investigacion se responden a ese grano: contar incendios, sumar sus
-- acres y repartirlos por causa, por tiempo, por territorio o por organismo.
--
-- Inventar un segundo hecho agregado -por ejemplo "causa x ano"- solo anadiria
-- una copia que puede quedar desincronizada. Las agregaciones se calculan en
-- la consulta, que es donde pertenecen.
--
-- LO QUE ESTE MODELO DELIBERADAMENTE NO LLEVA
-- ------------------------------------------------------------------
-- La fuente permite calcular la DURACION de la campana de extincion a partir
-- de las fechas de descubrimiento y contencion. No se incorpora como medida:
-- ninguno de los siete objetivos la pide, y es el objeto de otro trabajo de
-- esta misma serie. Las dos fechas quedan en el hecho por si una etapa
-- posterior la necesita, pero el modelo no la precalcula ni la presenta.
--
-- LA BANDERA QUE ATRAVIESA TODO EL MODELO
-- ------------------------------------------------------------------
-- `d_causa.es_atribuida` distingue las once causas que nombran un mecanismo de
-- las dos que no lo nombran -`Miscellaneous` y `Missing/Undefined`, que suman
-- el 26,09 % del registro-. El hecho repite esa bandera como medida
-- `es_atribuido` para que la cobertura se pueda promediar y agregar
-- directamente, sin reunir con la dimension. Es el instrumento del objetivo 1.
--
-- =============================================================================

PRAGMA journal_mode = OFF;
PRAGMA synchronous  = OFF;
PRAGMA temp_store   = MEMORY;
PRAGMA cache_size   = -400000;

ATTACH DATABASE 'fpa_normalizada.sqlite' AS norm;


-- =============================================================================
-- DIMENSIONES
-- =============================================================================

-- d_tiempo: un dia por fila, del 1992-01-01 al 2015-12-31 (8.766 dias).
-- `dia_juliano` es la columna del objetivo 4: la estacionalidad de cada causa
-- se mide sobre el dia del ano, no sobre el mes, porque la ventana de fuego no
-- respeta los limites del calendario.
CREATE TABLE d_tiempo (
    fecha_id     INTEGER PRIMARY KEY,      -- AAAAMMDD
    fecha        TEXT    NOT NULL UNIQUE,
    anio         INTEGER NOT NULL,
    mes          INTEGER NOT NULL,
    nombre_mes   TEXT    NOT NULL,
    trimestre    INTEGER NOT NULL,
    dia_juliano  INTEGER NOT NULL,
    dia_semana   INTEGER NOT NULL,
    nombre_dia   TEXT    NOT NULL,
    es_fin_semana INTEGER NOT NULL,
    estacion     TEXT    NOT NULL
);
INSERT INTO d_tiempo
WITH RECURSIVE dias(f) AS (
    SELECT '1992-01-01'
    UNION ALL SELECT date(f,'+1 day') FROM dias WHERE f < '2015-12-31')
SELECT CAST(replace(f,'-','') AS INTEGER), f,
       CAST(strftime('%Y',f) AS INTEGER), CAST(strftime('%m',f) AS INTEGER),
       CASE CAST(strftime('%m',f) AS INTEGER)
            WHEN 1 THEN 'Enero' WHEN 2 THEN 'Febrero' WHEN 3 THEN 'Marzo'
            WHEN 4 THEN 'Abril' WHEN 5 THEN 'Mayo' WHEN 6 THEN 'Junio'
            WHEN 7 THEN 'Julio' WHEN 8 THEN 'Agosto' WHEN 9 THEN 'Septiembre'
            WHEN 10 THEN 'Octubre' WHEN 11 THEN 'Noviembre' ELSE 'Diciembre' END,
       (CAST(strftime('%m',f) AS INTEGER)+2)/3,
       CAST(strftime('%j',f) AS INTEGER),
       CASE CAST(strftime('%w',f) AS INTEGER) WHEN 0 THEN 7
            ELSE CAST(strftime('%w',f) AS INTEGER) END,
       CASE CAST(strftime('%w',f) AS INTEGER)
            WHEN 0 THEN 'Domingo' WHEN 1 THEN 'Lunes' WHEN 2 THEN 'Martes'
            WHEN 3 THEN 'Miercoles' WHEN 4 THEN 'Jueves' WHEN 5 THEN 'Viernes'
            ELSE 'Sabado' END,
       CASE WHEN strftime('%w',f) IN ('0','6') THEN 1 ELSE 0 END,
       -- estaciones meteorologicas del hemisferio norte, no astronomicas:
       -- los trimestres completos son lo que usa la literatura de fuego.
       CASE CAST(strftime('%m',f) AS INTEGER)
            WHEN 12 THEN 'Invierno' WHEN 1 THEN 'Invierno' WHEN 2 THEN 'Invierno'
            WHEN 3 THEN 'Primavera' WHEN 4 THEN 'Primavera' WHEN 5 THEN 'Primavera'
            WHEN 6 THEN 'Verano' WHEN 7 THEN 'Verano' WHEN 8 THEN 'Verano'
            ELSE 'Otono' END
FROM dias;


-- d_causa: LA DIMENSION CENTRAL del trabajo.
--
-- Lleva dos clasificaciones que no estan en la fuente y que son decisiones
-- documentadas de esta investigacion:
--
--   es_atribuida  0 para las dos categorias que no nombran mecanismo.
--   origen        Natural / Antropico / No atribuida. Permite reproducir la
--                 agregacion habitual en la literatura -y la que uso otro
--                 trabajo de esta serie- SIN perder el detalle de las trece,
--                 y deja ver que la agregacion de dos bloques esconde un
--                 tercero del 26,09 %.
CREATE TABLE d_causa (
    causa_id     INTEGER PRIMARY KEY,
    nombre       TEXT    NOT NULL UNIQUE,
    es_atribuida INTEGER NOT NULL CHECK (es_atribuida IN (0,1)),
    origen       TEXT    NOT NULL,
    orden        INTEGER NOT NULL UNIQUE
);
INSERT INTO d_causa (causa_id, nombre, es_atribuida, origen, orden)
SELECT c.causa_id, c.nombre, c.es_atribuida,
       CASE WHEN c.es_atribuida = 0     THEN 'No atribuida'
            WHEN c.nombre = 'Lightning' THEN 'Natural'
            ELSE 'Antropico' END,
       ROW_NUMBER() OVER (ORDER BY c.es_atribuida DESC, c.nombre)
FROM norm.causas c;


CREATE TABLE d_clase_tamano (
    clase_id        INTEGER PRIMARY KEY,
    clase           TEXT    NOT NULL UNIQUE,
    etiqueta        TEXT    NOT NULL,
    hasta           REAL,
    hasta_inclusivo INTEGER NOT NULL,
    orden           INTEGER NOT NULL UNIQUE
);
INSERT INTO d_clase_tamano (clase, etiqueta, hasta, hasta_inclusivo, orden)
SELECT clase, etiqueta, hasta, hasta_inclusivo, orden FROM norm.clases_tamano
ORDER BY orden;


CREATE TABLE d_propietario (
    propietario_id INTEGER PRIMARY KEY,
    etiqueta       TEXT NOT NULL
);
INSERT INTO d_propietario SELECT propietario_id, nombre FROM norm.propietarios;
INSERT INTO d_propietario VALUES (-1, 'Sin dato');


-- d_estado: la region censal NO esta en la fuente. Se asigna segun la
-- definicion de las cuatro regiones de la Oficina del Censo de los Estados
-- Unidos. Puerto Rico no pertenece a ninguna: es territorio no incorporado y
-- se rotula como tal en lugar de forzarlo dentro del Sur.
CREATE TABLE d_estado (
    estado_id INTEGER PRIMARY KEY,
    codigo    TEXT NOT NULL UNIQUE,
    region    TEXT NOT NULL
);
INSERT INTO d_estado (estado_id, codigo, region)
SELECT e.estado_id, e.codigo,
  CASE
    WHEN e.codigo IN ('CT','ME','MA','NH','NJ','NY','PA','RI','VT') THEN 'Noreste'
    WHEN e.codigo IN ('IL','IN','IA','KS','MI','MN','MO','NE','ND','OH','SD','WI') THEN 'Medio Oeste'
    WHEN e.codigo IN ('AL','AR','DE','DC','FL','GA','KY','LA','MD','MS','NC',
                      'OK','SC','TN','TX','VA','WV') THEN 'Sur'
    WHEN e.codigo IN ('AK','AZ','CA','CO','HI','ID','MT','NV','NM','OR','UT',
                      'WA','WY') THEN 'Oeste'
    ELSE 'Territorio' END
FROM norm.estados e;


-- d_condado: conformada con d_estado. Clave compuesta natural (estado, FIPS).
CREATE TABLE d_condado (
    condado_id INTEGER PRIMARY KEY,
    estado_id  INTEGER NOT NULL REFERENCES d_estado (estado_id),
    fips       TEXT    NOT NULL,
    etiqueta   TEXT    NOT NULL
);
INSERT INTO d_condado SELECT condado_id, estado_id, fips, nombre FROM norm.condados;
INSERT INTO d_condado VALUES (-1, (SELECT estado_id FROM d_estado LIMIT 1), '', 'Sin dato');


-- d_agencia: el ambito institucional no esta en la fuente; agrupa los once
-- organismos reportantes del NWCG segun su naturaleza. Es la dimension con la
-- que el objetivo 1 mide el reparto desigual del hueco de atribucion.
CREATE TABLE d_agencia (
    agencia_id INTEGER PRIMARY KEY,
    codigo     TEXT NOT NULL UNIQUE,
    ambito     TEXT NOT NULL
);
INSERT INTO d_agencia (agencia_id, codigo, ambito)
SELECT a.agencia_id, a.codigo,
  CASE a.codigo
    WHEN 'ST/C&L' THEN 'Estatal-Local'
    WHEN 'IA'     THEN 'Interagencial'
    WHEN 'TRIBE'  THEN 'Tribal'
    ELSE 'Federal' END
FROM norm.agencias_nwcg a;


-- d_unidad: la jerarquia organizativa que la fuente trae en un catalogo
-- aparte y no declara. `en_catalogo` marca las 17 unidades que no aparecen en
-- el, para que su ausencia sea contable en lugar de invisible.
CREATE TABLE d_unidad (
    unidad_id    INTEGER PRIMARY KEY,
    codigo       TEXT NOT NULL UNIQUE,
    etiqueta     TEXT NOT NULL,
    gacc         TEXT,
    area_geo     TEXT,
    departamento TEXT,
    tipo_unidad  TEXT,
    en_catalogo  INTEGER NOT NULL
);
INSERT INTO d_unidad
SELECT unidad_id, codigo, nombre, gacc, area_geo, departamento, tipo_unidad,
       en_catalogo
FROM norm.unidades_nwcg;


-- d_sistema: de que sistema informatico procede el registro. Interviene en el
-- objetivo 1: parte de la variacion de la cobertura es de procedencia, no de
-- conducta de la agencia.
CREATE TABLE d_sistema (
    sistema_id INTEGER PRIMARY KEY,
    codigo     TEXT NOT NULL UNIQUE,
    tipo       TEXT NOT NULL
);
INSERT INTO d_sistema SELECT sistema_id, codigo, tipo FROM norm.sistemas_origen;


-- =============================================================================
-- HECHO - h_incendios        grano: el incendio
-- =============================================================================
-- 1.880.465 filas, una por incendio registrado. No hay agregacion previa.

CREATE TABLE h_incendios (
    fod_id        INTEGER PRIMARY KEY,          -- degenerada: clave de la fuente
    fecha_id      INTEGER NOT NULL REFERENCES d_tiempo       (fecha_id),
    causa_id      INTEGER NOT NULL REFERENCES d_causa        (causa_id),
    clase_id      INTEGER NOT NULL REFERENCES d_clase_tamano (clase_id),
    propietario_id INTEGER NOT NULL REFERENCES d_propietario (propietario_id),
    estado_id     INTEGER NOT NULL REFERENCES d_estado       (estado_id),
    condado_id    INTEGER NOT NULL REFERENCES d_condado      (condado_id),
    agencia_id    INTEGER NOT NULL REFERENCES d_agencia      (agencia_id),
    unidad_id     INTEGER NOT NULL REFERENCES d_unidad       (unidad_id),
    sistema_id    INTEGER NOT NULL REFERENCES d_sistema      (sistema_id),
    -- medidas
    tamano_acres  REAL    NOT NULL,
    es_atribuido  INTEGER NOT NULL CHECK (es_atribuido IN (0,1)),
    -- degeneradas
    fpa_id        TEXT,
    nombre_fuego  TEXT,
    anio_temporada INTEGER NOT NULL,
    latitud       REAL NOT NULL,
    longitud      REAL NOT NULL,
    -- se conservan sin derivar nada de ellas (ver cabecera)
    fecha_contencion TEXT
);

INSERT INTO h_incendios
SELECT i.fod_id,
       CAST(replace(i.fecha_descubrimiento,'-','') AS INTEGER),
       i.causa_id, cl.clase_id,
       COALESCE(i.propietario_id, -1),
       i.estado_id, COALESCE(i.condado_id, -1),
       i.agencia_id, i.unidad_id, uo.sistema_id,
       i.tamano_acres, c.es_atribuida,
       i.fpa_id, i.nombre_fuego, i.anio_temporada,
       i.latitud, i.longitud, i.fecha_contencion
FROM norm.incendios i
JOIN norm.causas          c  ON c.causa_id = i.causa_id
JOIN d_clase_tamano       cl ON cl.clase   = i.clase_tamano
JOIN norm.unidades_origen uo ON uo.unidad_origen_id = i.unidad_origen_id;

CREATE INDEX ix_h_causa   ON h_incendios (causa_id);
CREATE INDEX ix_h_fecha   ON h_incendios (fecha_id);
CREATE INDEX ix_h_estado  ON h_incendios (estado_id);
CREATE INDEX ix_h_agencia ON h_incendios (agencia_id);
CREATE INDEX ix_h_clase   ON h_incendios (clase_id);
CREATE INDEX ix_h_atrib   ON h_incendios (es_atribuido, causa_id);


-- =============================================================================
-- PARAMETROS - lo que el script dedujo, a la vista
-- =============================================================================
CREATE TABLE parametros (clave TEXT PRIMARY KEY, valor TEXT NOT NULL, nota TEXT NOT NULL);

INSERT INTO parametros SELECT 'incendios', CAST(COUNT(*) AS TEXT),
  'Filas del hecho. Grano: el incendio.' FROM h_incendios;
INSERT INTO parametros SELECT 'acres_totales', CAST(CAST(ROUND(SUM(tamano_acres)) AS INTEGER) AS TEXT),
  'Suma de superficie quemada, en acres.' FROM h_incendios;
INSERT INTO parametros SELECT 'periodo', MIN(fecha)||' a '||MAX(fecha),
  'Primer y ultimo dia con registro.' FROM d_tiempo;
INSERT INTO parametros SELECT 'sin_atribuir', CAST(COUNT(*) AS TEXT),
  'Incendios en Miscellaneous o Missing/Undefined.' FROM h_incendios WHERE es_atribuido=0;
INSERT INTO parametros SELECT 'cobertura_atribucion',
  CAST(ROUND(100.0*AVG(es_atribuido),2) AS TEXT)||' %',
  'Porcentaje de incendios con causa que nombra un mecanismo.' FROM h_incendios;

ANALYZE;
DETACH DATABASE norm;
