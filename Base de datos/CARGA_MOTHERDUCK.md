# Carga en MotherDuck

Las dos bases construidas en las etapas anteriores se suben a la nube, cada una
al servicio que la va a consumir.

| Base local | Destino | La consume |
|---|---|---|
| `fpa_normalizada.sqlite` (340,6 MB) | `md:fpa_normalizada` | el aplicativo de **Streamlit** |
| `fpa_analitica.sqlite` (295,4 MB) | `md:fpa_analitica` | el tablero de **Tableau** |

El script es [`carga_motherduck.sql`](carga_motherduck.sql):

```bash
cd "Base de datos"
duckdb < carga_motherduck.sql
```

Tarda **57 segundos** para los 3,76 millones de filas de las dos bases.

---

## La autenticación, sin pegar el token en ninguna parte

Al ejecutar `ATTACH 'md:'` sin credenciales, DuckDB abre el **flujo de
dispositivo** de MotherDuck: imprime un enlace con un código de verificación,
intenta abrir el navegador y espera a que se confirme la sesión.

```
Please open this link to login into your account:
https://auth.motherduck.com/activate?user_code=XXXX-XXXX

Token successfully retrieved ✅
```

Es preferible a exportar `motherduck_token` en el entorno: el valor no queda
escrito en el historial del shell, ni en un archivo del proyecto, ni en la
documentación. El `.gitignore` del repositorio excluye además `.env` y
`.streamlit/secrets.toml` por si alguna etapa posterior necesita guardarlo.

---

## Dos tropiezos que conviene dejar anotados

**El alias no se admite.** La forma habitual de adjuntar una base en DuckDB es
`ATTACH 'origen' AS alias`. Con MotherDuck en modo *workspace* eso falla:

```
Not implemented Error: Database aliases are not yet supported
by MotherDuck in workspace mode.
```

Hay que adjuntar **sin alias** y seleccionar la base con `USE`. El detalle es
fácil de pasar por alto porque el error no detiene al cliente: las sentencias
siguientes se ejecutan igual, de modo que el script parece haber terminado bien
mientras que la mitad de lo que hizo fue a parar a otro sitio.

**El token no se puede extraer con `PRAGMA PRINT_MD_TOKEN` antes de adjuntar.**
Devuelve un error de parámetro de configuración no reconocido. Hay que adjuntar
primero. Como el flujo de dispositivo se completa solo mientras la sesión del
navegador siga autorizada, en la práctica no hace falta extraerlo.

---

## Por qué dos bases y no una con dos esquemas

Porque las consumen herramientas distintas. Tableau se conecta a
`fpa_analitica` y no necesita ver la normalizada; el aplicativo se conecta a
`fpa_normalizada` y resuelve allí sus agregaciones. Separarlas permite compartir
cada una por su cuenta sin exponer la otra.

El script es **idempotente**: usa `CREATE OR REPLACE TABLE`, de modo que puede
reejecutarse completo sin borrar nada a mano.

---

## Verificación

Conteos en la nube, contrastados contra las bases locales:

| `fpa_normalizada` | Filas | | `fpa_analitica` | Filas |
|---|---:|---|---|---:|
| `incendios` | 1.880.465 | | `h_incendios` | 1.880.465 |
| `unidades_origen` | 7.129 | | `d_tiempo` | 8.766 |
| `condados` | 2.795 | | `d_condado` | 2.796 |
| `unidades_nwcg` | 1.640 | | `d_unidad` | 1.640 |
| `estados` | 52 | | `d_estado` | 52 |
| `sistemas_origen` | 38 | | `d_sistema` | 38 |
| `propietarios` | 16 | | `d_propietario` | 17 |
| `causas` | 13 | | `d_causa` | 13 |
| `agencias_nwcg` | 11 | | `d_agencia` | 11 |
| `clases_tamano` | 7 | | `d_clase_tamano` | 7 |
| | | | `parametros` | 5 |

Todos coinciden con los locales. Las diferencias de una fila en `d_condado` y
`d_propietario` son las filas «Sin dato» que añade el modelo dimensional.

**Pero contar filas no prueba que los datos lleguen bien.** Se reejecutaron
contra la nube las consultas de los objetivos:

| Control | En la nube | En local |
|---|---:|---:|
| Suma de `tamano_acres` | 140.132.550 | 140.132.550 |
| Incendios sin atribuir | 490.528 | 490.528 |
| Huérfanos de `d_tiempo` · `d_causa` | 0 · 0 | 0 · 0 |
| Ventana del 50 % central de `Fireworks` | días 179–188 | días 179–188 |
| Ventana de `Lightning` | días 182–227 | días 182–227 |

La ventana de nueve días alrededor del 4 de julio se reproduce idéntica, que es
la comprobación que de verdad importa: no solo llegaron todas las filas, llegaron
con sus valores en su sitio.

---

La etapa siguiente es la carga de la base **original** en Supabase, para el
cuestionario SQL.
