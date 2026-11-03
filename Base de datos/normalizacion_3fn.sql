-- =============================================================================
-- NORMALIZACION DE FPA_FOD_20170508 HASTA LA TERCERA FORMA NORMAL
-- Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) - Computacion II
-- =============================================================================
--
-- ORIGEN   fpa_fod.sqlite            1 tabla de hechos, 39 columnas, 759 MB
-- DESTINO  fpa_normalizada.sqlite    1 entidad + 9 catalogos en 3FN
--
-- EJECUCION (desde esta carpeta):
--     sqlite3 fpa_normalizada.sqlite < normalizacion_3fn.sql
--
-- Este script hace UNA sola cosa: normalizar. No construye modelo dimensional,
-- no carga nada en la nube y no calcula ningun estadistico de la investigacion.
-- Esas son etapas posteriores y viven en sus propios archivos.
--
-- ORGANIZACION. Siete partes. Las partes II, III y IV son las formas normales
-- propiamente dichas. La V separa lo que la 3FN NO exige pero el dominio si
-- aconseja, para que no se confunda una cosa con la otra. La VI declara lo que
-- se deja fuera y por que. La VII construye.
--
-- TODA afirmacion numerica de los comentarios esta medida sobre la fuente. Las
-- consultas que las producen estan en NORMALIZACION.md.
--
-- =============================================================================


-- =============================================================================
-- PARTE I - DIAGNOSTICO DE LA FUENTE
-- =============================================================================
--
-- La fuente se distribuye como UNA tabla, `Fires`, de 1.880.465 filas y 39
-- columnas, acompanada de un catalogo auxiliar, `NWCG_UnitIDActive_20170109`,
-- de 5.867 unidades operativas que la mayoria de los analisis publicos ignora.
--
-- I.1  LA CLAVE EXISTE, Y ESO AQUI ES UNA NOVEDAD
-- ------------------------------------------------------------------
-- A diferencia de otras fuentes de esta serie, `Fires` SI trae una clave real:
--
--     filas       1.880.465
--     OBJECTID    1.880.465 distintos   <- clave
--     FOD_ID      1.880.465 distintos   <- clave
--     FPA_ID      1.880.462 distintos   <- NO es clave: 3 duplicados
--
-- `FPA_ID` es el identificador que la documentacion presenta como global, y no
-- lo es. Los tres pares colisionan entre anos distintos:
--
--     FS-1452833              FOD_ID 22093      (2007) y 201432072 (2012)
--     ICS209_2009_KS-DDQ-128  FOD_ID 1300088    (2009) y 201750002 (2012)
--     SFO-2015CACDFLNU003791  FOD_ID 300245030  y 300306586  (ambos 2015)
--
-- Se adopta `FOD_ID` como clave primaria. `FPA_ID` se conserva como atributo
-- descriptivo, NO como clave alternativa, y el script verifica al cierre que
-- sigue teniendo exactamente esos tres duplicados: si aparecieran mas, algo
-- habria cambiado en la fuente.
--
-- I.2  UNA HIPOTESIS PROPIA, REFUTADA
-- ------------------------------------------------------------------
-- Se sospecho que `FPA_ID` era un compuesto -prefijo de sistema mas numero
-- local- y que por tanto violaba la 1FN. Se midio: 1.401.023 de 1.880.465
-- valores llevan guion, pero el prefijo NO coincide NUNCA con `SOURCE_SYSTEM`
-- (cero coincidencias en 1.401.023 casos). Los prefijos -SFO, W, FS, TFS, IA,
-- ALS- son etiquetas del proceso de carga, y uno solo de ellos (SFO) abarca
-- cuatro sistemas de origen distintos. No hay dependencia que extraer: la
-- hipotesis se descarta y `FPA_ID` queda como cadena opaca.
--
-- I.3  UNA RELACION QUE LA FUENTE TIENE Y NO DECLARA
-- ------------------------------------------------------------------
-- `Fires.NWCG_REPORTING_UNIT_ID` enlaza con `NWCG_UnitIDActive.UnitId` en el
-- 98,15 % de las filas (1.845.708 de 1.880.465). Ese enlace no esta declarado
-- en ninguna parte del esquema original. Integrarlo es lo que permite agrupar
-- por departamento, agencia y area geografica, es decir, por los niveles en
-- que el sistema estadounidense de fuego realmente se organiza.


-- =============================================================================
-- PARTE II - PRIMERA FORMA NORMAL: ATOMICIDAD
-- =============================================================================
--
-- 1FN: todo atributo contiene un unico valor del dominio, y no hay grupos
-- repetitivos.
--
-- II.1  NO HAY GRUPOS REPETITIVOS. HAY QUE DECIRLO.
-- ------------------------------------------------------------------
-- Conviene afirmarlo explicitamente porque en otras fuentes de esta serie si
-- los habia: columnas numeradas del tipo clima1..clima4 que obligaban a crear
-- tablas puente. Aqui NO existe ninguna. Las 39 columnas son monovaluadas.
-- La 1FN, en su clausula de grupos repetitivos, se cumple de origen.
--
-- II.2  LO QUE SI VIOLA LA ATOMICIDAD: LAS FECHAS Y LAS HORAS
-- ------------------------------------------------------------------
-- `DISCOVERY_DATE` y `CONT_DATE` no estan guardadas como fechas sino como
-- NUMEROS DE DIA JULIANO en coma flotante:
--
--     DISCOVERY_DATE = 2453403.5   ->   2005-02-02
--
-- No es un capricho de formato: asi almacenada, la columna no admite ninguna
-- operacion de calendario sin convertirla antes, y cualquier comparacion
-- directa entre fechas es una comparacion entre flotantes. Se convierten a
-- texto ISO 'AAAA-MM-DD', que es como SQLite representa una fecha.
--
-- `DISCOVERY_TIME` y `CONT_TIME` vienen como texto de cuatro caracteres,
-- 'HHMM'. Son dos hechos -hora y minuto- en un solo campo. Se separan en
-- `hora` y `minuto` enteros, conservando ademas el valor original por si el
-- analisis necesita distinguir un '0000' real de un dato ausente.


-- =============================================================================
-- PARTE III - SEGUNDA FORMA NORMAL
-- =============================================================================
--
-- 2FN: estando en 1FN, ningun atributo no clave depende de una PARTE de la
-- clave primaria.
--
-- LA 2FN SE CUMPLE DE FORMA TRIVIAL, Y CONVIENE EXPLICAR POR QUE.
-- ------------------------------------------------------------------
-- La clave primaria de la entidad es `FOD_ID`: una sola columna. Una
-- dependencia parcial exige una clave COMPUESTA, porque solo de una clave
-- compuesta se puede depender "en parte". Con clave simple, el enunciado de la
-- 2FN no tiene caso que regular: toda dependencia respecto de la clave es
-- total por construccion.
--
-- Esto no es una formalidad que se pueda saltar. Es la razon por la que en
-- esta fuente el trabajo real de normalizacion se concentra en la 3FN: no hay
-- nada que corregir en la 2FN porque la fuente, pese a su desorden, tiene una
-- clave unica bien definida.
--
-- Los catalogos que la PARTE IV crea si tienen, algunos, clave compuesta
-- -`condados` depende de (estado, codigo FIPS)-, y en ellos la 2FN se verifica
-- explicitamente: el nombre del condado depende de las DOS columnas, nunca de
-- una sola, porque el codigo FIPS de tres digitos se repite entre estados.


-- =============================================================================
-- PARTE IV - TERCERA FORMA NORMAL: DEPENDENCIAS TRANSITIVAS
-- =============================================================================
--
-- 3FN: estando en 2FN, ningun atributo no clave depende de otro atributo no
-- clave. Cada dependencia de ese tipo se extrae a un catalogo propio.
--
-- Se probaron SEIS dependencias candidatas contando pares distintos. Cuatro
-- resultaron limpias, una sucia y una FALSA:
--
--   dependencia                        determinantes  valores  pares
--   ---------------------------------  -------------  -------  -----
--   STAT_CAUSE_CODE -> DESCR                      13       13     13   limpia
--   OWNER_CODE      -> DESCR                      16       16     16   limpia
--   NWCG_UNIT_ID    -> UNIT_NAME                1640     1635   1640   limpia
--   (STATE,FIPS_CODE) -> FIPS_NAME              2795     1698   2798   sucia
--   SOURCE_SYSTEM   -> SYSTEM_TYPE                38        3     39   sucia
--   (SOURCE_SYSTEM,SOURCE_UNIT) -> NAME         5249     4441   7129   FALSA
--
-- Cuando el numero de pares excede el de determinantes, el mismo determinante
-- apunta a mas de un valor y la dependencia no se sostiene tal cual.
--
-- IV.1  LAS LIMPIAS: SE EXTRAEN SIN MAS
-- ------------------------------------------------------------------
--   `causas`          13 filas.  Es el catalogo central de esta investigacion.
--   `propietarios`    16 filas.  Tenencia del terreno.
--   `unidades_nwcg` 1.640 filas, enriquecidas con el catalogo auxiliar.
--
-- IV.2  LA DEPENDENCIA FALSA: EL CODIGO QUE NO IDENTIFICA NADA
-- ------------------------------------------------------------------
-- `SOURCE_REPORTING_UNIT` parece un codigo de unidad y no lo es. En el sistema
-- ST-TXTXS, el codigo `TXVFD` esta asociado a 946 nombres distintos de cuerpos
-- de bomberos voluntarios de Texas; `TXSFD`, a 369. No es un identificador: es
-- un cajon que significa "bomberos voluntarios de Texas, sin especificar".
--
-- En total, 407 codigos arrastran 2.287 nombres distintos.
--
-- Extraer un catalogo con clave (sistema, codigo) seria INVENTAR una
-- dependencia que los datos no tienen, y colapsaria 946 cuerpos de bomberos en
-- uno solo. La 3FN no obliga a extraer nada aqui, porque sin dependencia
-- transitiva no hay violacion. Pero repetir el nombre 1,88 millones de veces
-- tampoco tiene sentido, asi que se extrae un catalogo cuya clave natural es
-- la TERNA COMPLETA (sistema, codigo, nombre): 7.129 filas. Se elimina la
-- repeticion sin afirmar nada falso sobre los datos.
--
-- IV.3  LAS SUCIAS: SE RESUELVEN POR MAYORIA Y SE DEJAN A LA VISTA
-- ------------------------------------------------------------------
-- (a) SOURCE_SYSTEM -> SOURCE_SYSTEM_TYPE, 39 pares para 38 sistemas.
--     El sistema `IA-ICS209` aparece 1.982 veces como 'INTERAGCY' y UNA vez
--     como 'NONFED'. Es un error de un solo registro.
--
-- (b) (STATE, FIPS_CODE) -> FIPS_NAME, 2.798 ternas para 2.795 pares.
--     Tres conflictos, de dos naturalezas distintas:
--
--       CA 005   Amador (591 filas)  vs  Douglas (1 fila)   <- error de dato
--       TN 041   DeKalb              vs  Dekalb             <- mayuscula
--       VA 810   Virginia Beach City vs  Virginia Beach city<- mayuscula
--
--     El condado 005 de California es Amador; Douglas no existe en ese estado.
--
-- En los dos casos el catalogo se construye con el valor MAYORITARIO, y la
-- entidad conserva su clave foranea hacia el. No se corrige la fuente ni se
-- borra la fila discrepante: lo que se corrige es el CATALOGO, que es donde el
-- valor tiene que ser unico para que la dependencia se sostenga.
--
-- IV.4  LAS COLUMNAS DERIVADAS TAMBIEN SON DEPENDENCIAS TRANSITIVAS
-- ------------------------------------------------------------------
-- Un atributo calculable a partir de otro atributo no clave depende de el, y
-- por tanto viola la 3FN igual que cualquier otra transitividad. Se midieron:
--
--   DISCOVERY_DOY desde DISCOVERY_DATE      0 discrepancias  -> se elimina
--   CONT_DOY      desde CONT_DATE           0 discrepancias  -> se elimina
--   FIRE_SIZE_CLASS desde FIRE_SIZE         0 discrepancias  -> se cataloga
--   FIRE_YEAR     desde DISCOVERY_DATE      4 discrepancias  -> SE CONSERVA
--
-- Sobre FIRE_SIZE_CLASS: la primera prueba dio 6 discrepancias y el error era
-- del verificador, no del dato. Se habia usado el umbral "< 0,26 acres" para
-- la clase A cuando la norma NWCG dice "0,25 acres o menos". Con el umbral
-- correcto la derivacion es exacta en los 1.880.465 registros. Queda como
-- catalogo `clases_tamano` con sus rangos declarados, no como columna.
--
-- Sobre FIRE_YEAR: cuatro incendios de Oregon declaran un ano distinto al de
-- su fecha de descubrimiento. Tres son de 1993 descubiertos en 1994; el cuarto
-- se descubrio el 2009-10-10 y se contuvo el 2010-06-29, declarandose 2010.
-- `FIRE_YEAR` no es, por tanto, el ano de la fecha: es el ano de TEMPORADA al
-- que la agencia imputa el incendio. Lleva informacion propia y se conserva.


-- =============================================================================
-- PARTE V - INTEGRIDAD DE DOMINIO (MAS ALLA DE LA 3FN)
-- =============================================================================
--
-- Lo que sigue NO lo exige ninguna forma normal. Son decisiones de dominio, y
-- se separan a proposito para que nadie las confunda con teoria relacional.
--
-- V.1  LAS DOS CAUSAS QUE NO SON CAUSAS
-- ------------------------------------------------------------------
-- De los trece valores de `causas`, dos no nombran mecanismo alguno:
--
--     Miscellaneous       323.805 incendios   17,22 %
--     Missing/Undefined   166.723 incendios    8,87 %
--     -------------------------------------------------
--     suman               490.528 incendios   26,09 %
--
-- El catalogo lleva por eso una bandera `es_atribuida`, para que ninguna
-- consulta pueda calcular una participacion sobre el total sin haber decidido
-- antes, de forma explicita, que hace con ese 26,09 %. La bandera no filtra
-- nada: obliga a elegir.
--
-- V.2  LAS CLAVES FORANEAS SE DECLARAN
-- ------------------------------------------------------------------
-- La fuente no declara ni una sola. Aqui se declaran todas, y al cierre se
-- ejecuta `PRAGMA foreign_key_check`. Una base que no puede verificarse no es
-- una base normalizada: es una base ordenada.


-- =============================================================================
-- PARTE VI - LO QUE SE EXCLUYE, Y POR QUE
-- =============================================================================
--
--   OBJECTID   Identificador de ArcGIS, redundante con FOD_ID: ambos tienen
--              1.880.465 valores distintos y recorren las mismas filas. Se
--              conserva FOD_ID, que es el identificador de la base y el que
--              la documentacion de Short (2017) describe.
--
--   Shape      Geometria SpatiaLite de tipo POINT, 107,6 MB. Duplica
--              exactamente LATITUDE y LONGITUDE, que si se conservan. Nada de
--              lo que esta investigacion hace necesita el tipo geometrico.
--
--   DISCOVERY_DOY, CONT_DOY   Derivadas exactas (PARTE IV.4).
--
-- Son 4 columnas excluidas de 39. Las 35 restantes se cargan integras,
-- incluidas las casi vacias -COMPLEX_NAME tiene 5.183 valores no nulos de
-- 1.880.465-, porque su vacio es un dato sobre el registro.


-- =============================================================================
-- PARTE VII - CONSTRUCCION
-- =============================================================================

PRAGMA journal_mode = OFF;
PRAGMA synchronous  = OFF;
PRAGMA temp_store   = MEMORY;
PRAGMA cache_size   = -400000;      -- 400 MB

ATTACH DATABASE 'fpa_fod.sqlite' AS src;


-- --- VII.1  catalogos de la 3FN limpia ------------------------------------

CREATE TABLE causas (
    causa_id      INTEGER PRIMARY KEY,          -- STAT_CAUSE_CODE
    nombre        TEXT    NOT NULL UNIQUE,
    es_atribuida  INTEGER NOT NULL CHECK (es_atribuida IN (0,1))
);
INSERT INTO causas
SELECT DISTINCT CAST(STAT_CAUSE_CODE AS INTEGER), STAT_CAUSE_DESCR,
       CASE WHEN STAT_CAUSE_DESCR IN ('Miscellaneous','Missing/Undefined')
            THEN 0 ELSE 1 END
FROM src.Fires;

CREATE TABLE propietarios (
    propietario_id INTEGER PRIMARY KEY,         -- OWNER_CODE
    nombre         TEXT    NOT NULL
);
INSERT INTO propietarios
SELECT DISTINCT CAST(OWNER_CODE AS INTEGER), OWNER_DESCR FROM src.Fires;

-- Rangos de la norma NWCG.
--
-- CONVENCION DE LOS LIMITES, verificada contra los datos. El catalogo guarda
-- el limite SUPERIOR de cada clase y si ese limite es inclusivo:
--
--     A   hasta 0,25   INCLUSIVO     "0,25 acres o menos"
--     B   hasta 10     exclusivo     "mas de 0,25 y menos de 10"
--     C   hasta 100    exclusivo     "10 a 99,9"
--     ...
--     G   sin limite                 "5.000 o mas"
--
-- La distincion no es cosmetica: 41.468 incendios caen EXACTAMENTE sobre un
-- limite -35.215 con 10,0 acres declarados clase C, 4.296 con 100,0 declarados
-- D, y asi hasta 73 con 5.000,0 declarados G-. Una convencion de "mas de 10 a
-- 100" los habria dado todos por incoherentes. Con los limites tal como la
-- norma los define, la derivacion desde FIRE_SIZE es exacta en los 1.880.465
-- registros.
CREATE TABLE clases_tamano (
    clase            TEXT PRIMARY KEY,
    hasta            REAL,              -- NULL en la clase abierta
    hasta_inclusivo  INTEGER NOT NULL CHECK (hasta_inclusivo IN (0,1)),
    etiqueta         TEXT NOT NULL,
    orden            INTEGER NOT NULL UNIQUE
);
INSERT INTO clases_tamano VALUES
    ('A', 0.25, 1, '0,25 acres o menos',        1),
    ('B', 10,   0, 'mas de 0,25 y menos de 10', 2),
    ('C', 100,  0, '10 a 99,9',                 3),
    ('D', 300,  0, '100 a 299,9',               4),
    ('E', 1000, 0, '300 a 999,9',               5),
    ('F', 5000, 0, '1.000 a 4.999,9',           6),
    ('G', NULL, 0, '5.000 o mas',               7);

CREATE TABLE agencias_nwcg (
    agencia_id INTEGER PRIMARY KEY,
    codigo     TEXT NOT NULL UNIQUE
);
INSERT INTO agencias_nwcg (codigo)
SELECT DISTINCT NWCG_REPORTING_AGENCY FROM src.Fires ORDER BY 1;

CREATE TABLE estados (
    estado_id INTEGER PRIMARY KEY,
    codigo    TEXT NOT NULL UNIQUE
);
INSERT INTO estados (codigo)
SELECT DISTINCT STATE FROM src.Fires ORDER BY 1;


-- --- VII.2  catalogos con dependencia sucia: valor mayoritario -------------

-- SOURCE_SYSTEM -> SOURCE_SYSTEM_TYPE. `IA-ICS209` trae 1.982 'INTERAGCY' y
-- 1 'NONFED'. Se adopta el mayoritario; la fila discrepante no se altera.
CREATE TABLE sistemas_origen (
    sistema_id INTEGER PRIMARY KEY,
    codigo     TEXT NOT NULL UNIQUE,
    tipo       TEXT NOT NULL
);
INSERT INTO sistemas_origen (codigo, tipo)
SELECT codigo, tipo FROM (
    SELECT SOURCE_SYSTEM AS codigo, SOURCE_SYSTEM_TYPE AS tipo,
           ROW_NUMBER() OVER (PARTITION BY SOURCE_SYSTEM
                              ORDER BY COUNT(*) DESC, SOURCE_SYSTEM_TYPE) AS r
    FROM src.Fires GROUP BY SOURCE_SYSTEM, SOURCE_SYSTEM_TYPE)
WHERE r = 1 ORDER BY codigo;

-- (STATE, FIPS_CODE) -> FIPS_NAME. Tres conflictos, resueltos por mayoria.
-- Clave compuesta: el codigo FIPS de tres digitos se repite entre estados, de
-- modo que el nombre depende de las DOS columnas (verificacion de la 2FN).
CREATE TABLE condados (
    condado_id INTEGER PRIMARY KEY,
    estado_id  INTEGER NOT NULL REFERENCES estados (estado_id),
    fips       TEXT    NOT NULL,
    nombre     TEXT    NOT NULL,
    UNIQUE (estado_id, fips)
);
INSERT INTO condados (estado_id, fips, nombre)
SELECT e.estado_id, m.fips, m.nombre
FROM (SELECT estado, fips, nombre FROM (
        SELECT STATE AS estado, FIPS_CODE AS fips, FIPS_NAME AS nombre,
               ROW_NUMBER() OVER (PARTITION BY STATE, FIPS_CODE
                                  ORDER BY COUNT(*) DESC, FIPS_NAME) AS r
        FROM src.Fires WHERE FIPS_CODE IS NOT NULL AND FIPS_NAME IS NOT NULL
        GROUP BY STATE, FIPS_CODE, FIPS_NAME)
      WHERE r = 1) m
JOIN estados e ON e.codigo = m.estado
ORDER BY m.estado, m.fips;


-- --- VII.3  unidades NWCG, enriquecidas con el catalogo auxiliar -----------

CREATE TABLE unidades_nwcg (
    unidad_id    INTEGER PRIMARY KEY,
    codigo       TEXT NOT NULL UNIQUE,         -- NWCG_REPORTING_UNIT_ID
    nombre       TEXT NOT NULL,
    area_geo     TEXT,                         -- del catalogo auxiliar
    gacc         TEXT,
    tipo_unidad  TEXT,
    departamento TEXT,
    agencia      TEXT,
    estado       TEXT,
    en_catalogo  INTEGER NOT NULL CHECK (en_catalogo IN (0,1))
);
INSERT INTO unidades_nwcg
    (codigo, nombre, area_geo, gacc, tipo_unidad, departamento, agencia,
     estado, en_catalogo)
SELECT f.codigo, f.nombre,
       u.GeographicArea, u.Gacc, u.UnitType, u.Department, u.Agency, u.State,
       CASE WHEN u.UnitId IS NULL THEN 0 ELSE 1 END
FROM (SELECT DISTINCT NWCG_REPORTING_UNIT_ID AS codigo,
                      NWCG_REPORTING_UNIT_NAME AS nombre FROM src.Fires) f
LEFT JOIN src.NWCG_UnitIDActive_20170109 u ON u.UnitId = f.codigo
ORDER BY f.codigo;


-- --- VII.4  unidades de origen: clave natural = la terna completa ----------
-- No se usa (sistema, codigo) como clave porque esa dependencia es FALSA:
-- `TXVFD` arrastra 946 nombres distintos (PARTE IV.2).

CREATE TABLE unidades_origen (
    unidad_origen_id INTEGER PRIMARY KEY,
    sistema_id       INTEGER NOT NULL REFERENCES sistemas_origen (sistema_id),
    codigo           TEXT    NOT NULL,
    nombre           TEXT,
    UNIQUE (sistema_id, codigo, nombre)
);
INSERT INTO unidades_origen (sistema_id, codigo, nombre)
SELECT s.sistema_id, t.codigo, t.nombre
FROM (SELECT DISTINCT SOURCE_SYSTEM AS sistema, SOURCE_REPORTING_UNIT AS codigo,
                      SOURCE_REPORTING_UNIT_NAME AS nombre
      FROM src.Fires) t
JOIN sistemas_origen s ON s.codigo = t.sistema
ORDER BY t.sistema, t.codigo, t.nombre;


-- --- VII.5  la entidad -----------------------------------------------------
-- Las fechas julianas pasan a ISO y las horas 'HHMM' se parten en hora y
-- minuto (PARTE II.2). DISCOVERY_DOY y CONT_DOY no se cargan (PARTE IV.4).

CREATE TABLE incendios (
    fod_id               INTEGER PRIMARY KEY,
    fpa_id               TEXT,
    anio_temporada       INTEGER NOT NULL,      -- FIRE_YEAR, no derivable
    fecha_descubrimiento TEXT    NOT NULL,      -- AAAA-MM-DD
    hora_descubrimiento  INTEGER,
    minuto_descubrimiento INTEGER,
    fecha_contencion     TEXT,
    hora_contencion      INTEGER,
    minuto_contencion    INTEGER,
    causa_id             INTEGER NOT NULL REFERENCES causas (causa_id),
    tamano_acres         REAL    NOT NULL,
    clase_tamano         TEXT    NOT NULL REFERENCES clases_tamano (clase),
    latitud              REAL    NOT NULL,
    longitud             REAL    NOT NULL,
    propietario_id       INTEGER REFERENCES propietarios (propietario_id),
    estado_id            INTEGER NOT NULL REFERENCES estados (estado_id),
    condado_id           INTEGER REFERENCES condados (condado_id),
    agencia_id           INTEGER NOT NULL REFERENCES agencias_nwcg (agencia_id),
    unidad_id            INTEGER NOT NULL REFERENCES unidades_nwcg (unidad_id),
    unidad_origen_id     INTEGER NOT NULL REFERENCES unidades_origen (unidad_origen_id),
    -- identificadores locales y de interoperabilidad, casi siempre nulos
    reporte_local_id     TEXT,
    incidente_local_id   TEXT,
    codigo_fuego         TEXT,
    nombre_fuego         TEXT,
    ics209_numero        TEXT,
    ics209_nombre        TEXT,
    mtbs_id              TEXT,
    mtbs_nombre          TEXT,
    nombre_complejo      TEXT
);

INSERT INTO incendios
SELECT
    f.FOD_ID, f.FPA_ID, f.FIRE_YEAR,
    date(f.DISCOVERY_DATE),
    CASE WHEN LENGTH(f.DISCOVERY_TIME)=4 THEN CAST(SUBSTR(f.DISCOVERY_TIME,1,2) AS INTEGER) END,
    CASE WHEN LENGTH(f.DISCOVERY_TIME)=4 THEN CAST(SUBSTR(f.DISCOVERY_TIME,3,2) AS INTEGER) END,
    date(f.CONT_DATE),
    CASE WHEN LENGTH(f.CONT_TIME)=4 THEN CAST(SUBSTR(f.CONT_TIME,1,2) AS INTEGER) END,
    CASE WHEN LENGTH(f.CONT_TIME)=4 THEN CAST(SUBSTR(f.CONT_TIME,3,2) AS INTEGER) END,
    CAST(f.STAT_CAUSE_CODE AS INTEGER),
    f.FIRE_SIZE, f.FIRE_SIZE_CLASS, f.LATITUDE, f.LONGITUDE,
    CAST(f.OWNER_CODE AS INTEGER),
    e.estado_id, c.condado_id, a.agencia_id, un.unidad_id, uo.unidad_origen_id,
    f.LOCAL_FIRE_REPORT_ID, f.LOCAL_INCIDENT_ID, f.FIRE_CODE, f.FIRE_NAME,
    f.ICS_209_INCIDENT_NUMBER, f.ICS_209_NAME, f.MTBS_ID, f.MTBS_FIRE_NAME,
    f.COMPLEX_NAME
FROM src.Fires f
JOIN estados        e  ON e.codigo = f.STATE
JOIN agencias_nwcg  a  ON a.codigo = f.NWCG_REPORTING_AGENCY
JOIN unidades_nwcg  un ON un.codigo = f.NWCG_REPORTING_UNIT_ID
JOIN sistemas_origen s ON s.codigo = f.SOURCE_SYSTEM
JOIN unidades_origen uo ON uo.sistema_id = s.sistema_id
                       AND uo.codigo = f.SOURCE_REPORTING_UNIT
                       AND (uo.nombre IS f.SOURCE_REPORTING_UNIT_NAME)
LEFT JOIN condados  c  ON c.estado_id = e.estado_id AND c.fips = f.FIPS_CODE;


-- --- VII.6  indices --------------------------------------------------------

CREATE INDEX ix_inc_causa    ON incendios (causa_id);
CREATE INDEX ix_inc_anio     ON incendios (anio_temporada);
CREATE INDEX ix_inc_estado   ON incendios (estado_id);
CREATE INDEX ix_inc_agencia  ON incendios (agencia_id);
CREATE INDEX ix_inc_fecha    ON incendios (fecha_descubrimiento);
CREATE INDEX ix_inc_clase    ON incendios (clase_tamano);

DETACH DATABASE src;
