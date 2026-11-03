# Despliegue del aplicativo

El aplicativo se publica en **Streamlit Community Cloud**. No lleva datos
consigo: los consulta en MotherDuck, de modo que lo desplegado y lo local leen
exactamente lo mismo.

---

## Antes de desplegar: el token

El despliegue **no puede usar el flujo de navegador** que sirve en local. Ese
flujo imprime un enlace y espera a que alguien lo confirme en una pantalla; un
aplicativo desplegado no tiene pantalla ni quien la mire.

Hace falta un **service token**:

1. Entrar en [app.motherduck.com](https://app.motherduck.com).
2. *Settings* → *Access tokens* → *Create token*.
3. Elegir **service token**, no el de sesión personal: el personal caduca.

---

## Desplegar

1. Entrar en [share.streamlit.io](https://share.streamlit.io) con la cuenta de
   GitHub propietaria del repositorio.
2. *Create app* → *Deploy a public app from GitHub*.
3. Rellenar:

   | Campo | Valor |
   |---|---|
   | Repository | `Olivertc24/Analisis-Las-Trece-Causas-del-Fuego-Forestal-en-Estados-Unidos-1992-2015` |
   | Branch | `main` |
   | Main file path | `app.py` |

4. Antes de pulsar *Deploy*, abrir **Advanced settings → Secrets** y pegar:

   ```toml
   motherduck_token = "EL_SERVICE_TOKEN"
   motherduck_database = "fpa_normalizada"
   ```

   Es el mismo contenido de `.streamlit/secrets.toml`, que no se versiona.
   Si se despliega sin esto, el aplicativo arranca igual pero muestra el
   diagnóstico de credenciales en lugar de los datos: está previsto, y el
   mensaje explica qué falta.

5. *Deploy*. La primera construcción instala `requirements.txt` y tarda unos
   minutos.

---

## Si hace falta cambiar el token después

*Manage app* → *Settings* → *Secrets*, pegar el nuevo contenido y guardar. El
aplicativo se reinicia solo.

---

## Lo que el aplicativo comprueba al arrancar

`app.py` no dibuja nada antes de verificar la conexión. El diagnóstico
distingue tres situaciones y en cada una dice qué hacer:

| Situación | Lo que muestra |
|---|---|
| No hay token en ningún origen | Cómo generarlo y dónde pegarlo |
| Hay token, pero es el marcador de la plantilla | Que hay que sustituirlo |
| Hay token válido pero MotherDuck lo rechaza | El error literal del motor |
| Conecta, pero a la base le faltan tablas | Qué tablas y qué script las crea |

La distinción importa: sin ella las cuatro situaciones producen el mismo error
críptico de autenticación.

---

## Una advertencia sobre `secrets.toml` y el entorno

**Streamlit exporta cada clave de `secrets.toml` como variable de entorno con
el mismo nombre.** Un `motherduck_token` sin rellenar no solo está en
`st.secrets`: también está en `os.environ`. Cualquier lógica que lea los
secretos y luego «caiga» al entorno como alternativa está leyendo dos veces lo
mismo, no dos orígenes distintos.

Por eso `src/query_manager.py` valida la **forma** del token —tres secciones
separadas por dos puntos, como exige un JWT— en los tres orígenes, en lugar de
filtrar solo el marcador al leer los secretos.
