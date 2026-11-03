"""
Genera el banner de cabecera del trabajo.

FORMATO. El mismo de la serie: lienzo de 1800x460, barra de acento superior,
antetitulo de la Escuela, titulo en dos lineas y las cifras al pie.

MOTIVO. Las trece causas, ordenadas por frecuencia, a escala real. Las dos
barras HUECAS son "Miscellaneous" y "Missing/Undefined": las dos categorias
que no nombran ninguna causa. Se dibujan vacias a proposito, porque juntas se
llevan el 26,09 % de los incendios del pais y esa es la primera cosa que este
trabajo tiene que decir. El motivo no es un adorno: es la tesis.

PALETA. Ambar de brasa, distinta del ambar del trabajo de respuesta operativa
y del verde del de origen del fuego, para que los tres se distingan de un
vistazo en el perfil de GitHub.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ANCHO, ALTO = 1800, 460
SUPER = 3

ACENTO = (247, 118, 54)          # brasa
ACENTO_OSCURO = (112, 44, 16)
FONDO_IZQ = (16, 12, 10)
FONDO_DER = (68, 30, 14)
BLANCO = (255, 255, 255)
GRIS_TEXTO = (214, 198, 188)

HELVETICA = "/System/Library/Fonts/HelveticaNeue.ttc"
NEGRITA, REGULAR = 1, 0

ANTETITULO = "ESCUELA DE ESTADISTICA Y CIENCIAS ACTUARIALES   ·   COMPUTACION II"
TITULO = ["Las trece causas del fuego", "forestal en Estados Unidos"]
PIE = "1.880.465 incendios   ·   140,13 millones de acres   ·   1992 - 2015"

# (causa, % de incendios, es_residual). Medido sobre la fuente.
CAUSAS = [
    ("Debris Burning",    22.81, False), ("Miscellaneous",     17.22, True),
    ("Arson",             14.97, False), ("Lightning",         14.81, False),
    ("Missing/Undefined",  8.87, True),  ("Equipment Use",      7.85, False),
    ("Campfire",           4.05, False), ("Children",           3.25, False),
    ("Smoking",            2.81, False), ("Railroad",           1.78, False),
    ("Powerline",          0.77, False), ("Fireworks",          0.61, False),
    ("Structure",          0.20, False),
]


def degradado(ancho, alto):
    lienzo = Image.new("RGB", (ancho, alto))
    pintor = ImageDraw.Draw(lienzo)
    for x in range(ancho):
        t = (x / (ancho - 1)) ** 0.75
        color = tuple(round(a + (b - a) * t) for a, b in zip(FONDO_IZQ, FONDO_DER))
        pintor.line([(x, 0), (x, alto)], fill=color)
    return lienzo


def motivo(lienzo):
    capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    pintor = ImageDraw.Draw(capa)
    s = SUPER
    # Las barras viven en la franja inferior: mas arriba chocan con el pie.
    # El eje arranca en CERO, como en el resto de la serie.
    base_y, alto_max = 452 * s, 118 * s
    margen = 62
    util = (ANCHO - 2 * margen) * s
    ancho_barra = util / (len(CAUSAS) * 1.55)
    paso = util / len(CAUSAS)
    maximo = max(v for _, v, _ in CAUSAS)

    for i, (_, valor, residual) in enumerate(CAUSAS):
        x = margen * s + i * paso + (paso - ancho_barra) / 2
        altura = (valor / maximo) * alto_max
        caja = [x, base_y - altura, x + ancho_barra, base_y]
        if residual:
            # hueca: la categoria existe en el registro pero no nombra una causa
            pintor.rectangle(caja, outline=ACENTO + (185,), width=3 * s)
        else:
            pintor.rectangle(caja, fill=ACENTO + (118,))

    pintor.line([(margen * s, base_y), ((ANCHO - margen) * s, base_y)],
                fill=ACENTO + (70,), width=2 * s)
    return Image.alpha_composite(lienzo.convert("RGBA"), capa).convert("RGB")


def texto_espaciado(pintor, xy, texto, fuente, fill, espaciado):
    x, y = xy
    for caracter in texto:
        pintor.text((x, y), caracter, font=fuente, fill=fill)
        x += pintor.textlength(caracter, font=fuente) + espaciado


def construir():
    lienzo = motivo(degradado(ANCHO * SUPER, ALTO * SUPER))
    lienzo = lienzo.resize((ANCHO, ALTO), Image.LANCZOS)
    pintor = ImageDraw.Draw(lienzo)

    for x in range(ANCHO):
        t = x / (ANCHO - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(ACENTO_OSCURO, ACENTO))
        pintor.line([(x, 0), (x, 7)], fill=color)

    f_ante = ImageFont.truetype(HELVETICA, 19, index=REGULAR)
    f_tit = ImageFont.truetype(HELVETICA, 62, index=NEGRITA)
    f_pie = ImageFont.truetype(HELVETICA, 27, index=REGULAR)

    texto_espaciado(pintor, (74, 82), ANTETITULO, f_ante, ACENTO, 1.6)
    pintor.text((72, 132), TITULO[0], font=f_tit, fill=BLANCO)
    pintor.text((72, 204), TITULO[1], font=f_tit, fill=BLANCO)
    pintor.text((74, 292), PIE, font=f_pie, fill=GRIS_TEXTO)

    destino = Path(__file__).with_name("banner_causas.png")
    lienzo.save(destino, optimize=True)
    print(f"  {destino.name}  {ANCHO}x{ALTO}  {destino.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    construir()
