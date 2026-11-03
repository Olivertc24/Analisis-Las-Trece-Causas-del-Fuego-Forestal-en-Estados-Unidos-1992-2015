-- =============================================================================
-- CARGA DE LAS DOS BASES EN MOTHERDUCK
-- Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) - Computacion II
-- =============================================================================
--
-- Sube a la nube las dos bases construidas en las etapas anteriores:
--
--     fpa_normalizada.sqlite  ->  md:fpa_normalizada   consumida por Streamlit
--     fpa_analitica.sqlite    ->  md:fpa_analitica     consumida por Tableau
--
-- EJECUCION (desde esta carpeta):
--     duckdb < carga_motherduck.sql
--
-- AUTENTICACION. No hace falta pegar ningun token: al ejecutar `ATTACH 'md:'`
-- sin credenciales, DuckDB abre el flujo de dispositivo de MotherDuck, imprime
-- un enlace con un codigo y espera a que se confirme en el navegador. Es
-- preferible a exportar `motherduck_token` en el entorno, porque el valor no
-- queda escrito en el historial del shell ni en ningun archivo del proyecto.
--
-- UNA ADVERTENCIA SOBRE EL ALIAS. En modo workspace, MotherDuck NO admite
-- `ATTACH 'md:' AS algo`: responde "Database aliases are not yet supported".
-- Hay que adjuntar sin alias y seleccionar la base con `USE`.
--
-- POR QUE DOS BASES Y NO UNA CON DOS ESQUEMAS. Porque las consumen herramientas
-- distintas con permisos distintos. Tableau se conecta a `fpa_analitica` y no
-- necesita ver la normalizada; el aplicativo se conecta a `fpa_normalizada` y
-- resuelve sus agregaciones alli. Separarlas permite compartir cada una por su
-- cuenta sin exponer la otra.
--
-- IDEMPOTENCIA. `CREATE OR REPLACE TABLE` permite reejecutar el script completo
-- sin borrar nada a mano: cada tabla se reemplaza por su version actual.
--
-- =============================================================================

INSTALL sqlite;
LOAD sqlite;

ATTACH 'md:';


-- --- 1. la base normalizada: insumo del aplicativo de Streamlit -------------

ATTACH 'fpa_normalizada.sqlite' AS norm (TYPE sqlite, READ_ONLY);
CREATE DATABASE IF NOT EXISTS fpa_normalizada;
USE fpa_normalizada;

CREATE OR REPLACE TABLE causas          AS SELECT * FROM norm.causas;
CREATE OR REPLACE TABLE propietarios    AS SELECT * FROM norm.propietarios;
CREATE OR REPLACE TABLE clases_tamano   AS SELECT * FROM norm.clases_tamano;
CREATE OR REPLACE TABLE agencias_nwcg   AS SELECT * FROM norm.agencias_nwcg;
CREATE OR REPLACE TABLE estados         AS SELECT * FROM norm.estados;
CREATE OR REPLACE TABLE sistemas_origen AS SELECT * FROM norm.sistemas_origen;
CREATE OR REPLACE TABLE condados        AS SELECT * FROM norm.condados;
CREATE OR REPLACE TABLE unidades_nwcg   AS SELECT * FROM norm.unidades_nwcg;
CREATE OR REPLACE TABLE unidades_origen AS SELECT * FROM norm.unidades_origen;
CREATE OR REPLACE TABLE incendios       AS SELECT * FROM norm.incendios;

DETACH norm;


-- --- 2. el modelo dimensional: insumo del tablero de Tableau ----------------

ATTACH 'fpa_analitica.sqlite' AS dim (TYPE sqlite, READ_ONLY);
CREATE DATABASE IF NOT EXISTS fpa_analitica;
USE fpa_analitica;

CREATE OR REPLACE TABLE d_tiempo       AS SELECT * FROM dim.d_tiempo;
CREATE OR REPLACE TABLE d_causa        AS SELECT * FROM dim.d_causa;
CREATE OR REPLACE TABLE d_clase_tamano AS SELECT * FROM dim.d_clase_tamano;
CREATE OR REPLACE TABLE d_propietario  AS SELECT * FROM dim.d_propietario;
CREATE OR REPLACE TABLE d_estado       AS SELECT * FROM dim.d_estado;
CREATE OR REPLACE TABLE d_condado      AS SELECT * FROM dim.d_condado;
CREATE OR REPLACE TABLE d_agencia      AS SELECT * FROM dim.d_agencia;
CREATE OR REPLACE TABLE d_unidad       AS SELECT * FROM dim.d_unidad;
CREATE OR REPLACE TABLE d_sistema      AS SELECT * FROM dim.d_sistema;
CREATE OR REPLACE TABLE parametros     AS SELECT * FROM dim.parametros;
CREATE OR REPLACE TABLE h_incendios    AS SELECT * FROM dim.h_incendios;

DETACH dim;


-- --- 3. verificacion -------------------------------------------------------
-- Los conteos deben coincidir con los de las bases locales.

SELECT database_name, table_name, estimated_size AS filas
FROM duckdb_tables()
WHERE database_name IN ('fpa_normalizada','fpa_analitica')
ORDER BY database_name, filas DESC;
