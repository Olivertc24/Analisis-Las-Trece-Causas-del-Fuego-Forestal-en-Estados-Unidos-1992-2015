"""
Diagrama del esquema en estrella.

UN SOLO HECHO. Otros trabajos de esta serie necesitaron tres tablas de hechos
porque tenian tres granos; aqui la fuente registra un solo tipo de suceso -el
incendio- y todas las preguntas se responden a ese grano. El diagrama lo
refleja: una caja central y nueve dimensiones alrededor.

d_causa se dibuja DESTACADA, con el mismo tratamiento que el hecho, porque no
es una dimension mas: es el objeto de la investigacion, y es la que lleva la
bandera `es_atribuida` que condiciona la lectura de todo lo demas.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _diagrama import ACENTO, SECUNDARIO, dibujar

IZQ, IZQ_F = 60, 500
CEN, CEN_F = 640, 1180
DER, DER_F = 1320, 1740
ANCHO, ALTO = 1800, 1440

tablas = {
    "h_incendios": ("h_incendios", "1.880.465 filas  ·  grano: el incendio", [
        "fod_id    PK   degen.",
        "fecha_id    FK",
        "causa_id    FK",
        "clase_id    FK",
        "propietario_id    FK",
        "estado_id    FK",
        "condado_id    FK",
        "agencia_id    FK",
        "unidad_id    FK",
        "sistema_id    FK",
        "",
        "tamano_acres",
        "es_atribuido  (0/1)",
        "",
        "fpa_id · nombre_fuego   degen.",
        "anio_temporada",
        "latitud · longitud",
        "fecha_contencion",
    ], (CEN, 330, CEN_F), True),

    "d_causa": ("d_causa", "13 filas  ·  EL OBJETO DEL ESTUDIO", [
        "causa_id    PK",
        "nombre",
        "es_atribuida  (0/1)",
        "origen",
        "orden",
    ], (IZQ, 50, IZQ_F), True),

    "d_tiempo": ("d_tiempo", "8.766 filas  ·  conformada", [
        "fecha_id    PK (AAAAMMDD)",
        "fecha · anio · mes",
        "nombre_mes · trimestre",
        "dia_juliano",
        "dia_semana · nombre_dia",
        "es_fin_semana",
        "estacion",
    ], (IZQ, 350, IZQ_F), False),

    "d_clase_tamano": ("d_clase_tamano", "7 filas  ·  norma NWCG", [
        "clase_id    PK",
        "clase · etiqueta",
        "hasta",
        "hasta_inclusivo",
        "orden",
    ], (IZQ, 650, IZQ_F), False),

    "d_propietario": ("d_propietario", "17 filas", [
        "propietario_id    PK",
        "etiqueta",
    ], (IZQ, 930, IZQ_F), False),

    "d_estado": ("d_estado", "52 filas  ·  conformada", [
        "estado_id    PK",
        "codigo",
        "region  (censal)",
    ], (DER, 50, DER_F), False),

    "d_condado": ("d_condado", "2.796 filas", [
        "condado_id    PK",
        "estado_id    FK",
        "fips · etiqueta",
    ], (DER, 280, DER_F), False),

    "d_agencia": ("d_agencia", "11 filas", [
        "agencia_id    PK",
        "codigo",
        "ambito",
    ], (DER, 510, DER_F), False),

    "d_unidad": ("d_unidad", "1.640 filas  ·  jerarquia NWCG", [
        "unidad_id    PK",
        "codigo · etiqueta",
        "gacc · area_geo",
        "departamento",
        "tipo_unidad",
        "en_catalogo  (0/1)",
    ], (DER, 740, DER_F), False),

    "d_sistema": ("d_sistema", "38 filas", [
        "sistema_id    PK",
        "codigo",
        "tipo",
    ], (DER, 1050, DER_F), False),
}

enlaces = [
    ("d_causa", "E", "h_incendios", "O", True),
    ("d_tiempo", "E", "h_incendios", "O", False),
    ("d_clase_tamano", "E", "h_incendios", "O", False),
    ("d_propietario", "E", "h_incendios", "O", False),
    ("d_estado", "O", "h_incendios", "E", False),
    ("d_condado", "O", "h_incendios", "E", False),
    ("d_agencia", "O", "h_incendios", "E", False),
    ("d_unidad", "O", "h_incendios", "E", False),
    ("d_sistema", "O", "h_incendios", "E", False),
]
alturas = {"d_causa": -170, "d_tiempo": -85, "d_clase_tamano": 50,
           "d_propietario": 160, "d_estado": -170, "d_condado": -85,
           "d_agencia": 0, "d_unidad": 85, "d_sistema": 170}

nota = [
    "Un solo hecho porque hay un solo grano. La fuente registra un tipo de",
    "suceso -el incendio-, y contar incendios, sumar sus acres y repartirlos",
    "por causa, tiempo, territorio u organismo son preguntas del mismo grano.",
    "Un segundo hecho agregado solo anadiria una copia desincronizable.",
    "",
    "d_causa lleva es_atribuida: vale 0 en Miscellaneous y Missing/Undefined,",
    "las dos categorias que no nombran mecanismo y que suman el 26,09 % del",
    "registro. El hecho repite la bandera como medida para que la cobertura se",
    "agregue sin reunir. Nada se filtra: se obliga a elegir que se hace con ella.",
]
leyenda = [(ACENTO, "Hecho / objeto del estudio"), (SECUNDARIO, "Dimension")]

if __name__ == "__main__":
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "esquema_estrella.png")
    dibujar(tablas, enlaces, ANCHO, ALTO, "UN HECHO, NUEVE DIMENSIONES",
            nota, leyenda, destino, alturas=alturas,
            nota_xy=(IZQ, 1130), leyenda_y=ALTO - 50)
    from PIL import Image
    im = Image.open(destino)
    print(f"  esquema_estrella.png  {im.size}  {os.path.getsize(destino)//1024} KB")
