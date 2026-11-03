"""
Motor compartido de los diagramas de esquema.

Los dos diagramas -el normalizado y el de estrella- usan el mismo formato, la
misma paleta y las mismas reglas de dibujo. Vivir en un solo modulo evita que
se separen al retocar uno de ellos.

ALTO DE LAS CAJAS. Se calcula del numero de campos, nunca se fija a mano: en
un trabajo anterior de esta serie fijarlo desbordaba el texto fuera del
recuadro en siete de nueve tablas.

ANTIALIASING. Pillow no suaviza las primitivas: se traza a triple resolucion y
se reduce al final. El texto se escribe despues, ya en tamano final.
"""

from PIL import Image, ImageDraw, ImageFont

SUPER = 3
ACENTO = (247, 118, 54)          # brasa: el hecho / lo que nace del proceso
SECUNDARIO = (158, 126, 106)     # terracota apagada: dimensiones
FONDO = (16, 12, 10)
CAJA_A = (44, 24, 14)
CAJA_B = (28, 21, 18)
BLANCO = (250, 240, 234)
GRIS = (196, 174, 162)
TENUE = (132, 110, 98)
LINEA = (92, 60, 40)

HELVETICA = "/System/Library/Fonts/HelveticaNeue.ttc"
NEGRITA, REGULAR, MEDIA = 1, 0, 10
CABECERA, CAMPO, SEPARADOR, PIE = 98, 23, 18, 18


def alto_de(campos):
    return CABECERA + PIE + sum(SEPARADOR if c == "" else CAMPO for c in campos)


def caja(tablas, clave):
    _, _, campos, (x0, y0, x1), _ = tablas[clave]
    return (x0, y0, x1, y0 + alto_de(campos))


def ancla(c, lado, desp=0):
    x0, y0, x1, y1 = c
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    return {"N": (cx, y0), "S": (cx, y1),
            "O": (x0, cy + desp), "E": (x1, cy + desp)}[lado]


def dibujar(tablas, enlaces, ancho, alto, titulo, lineas_nota, leyenda,
            destino, alturas=None, nota_xy=(70, 0), leyenda_y=None):
    alturas = alturas or {}
    s = SUPER
    lienzo = Image.new("RGB", (ancho * s, alto * s), FONDO)
    p = ImageDraw.Draw(lienzo)

    for origen, lo, destino_t, ld, grueso in enlaces:
        a = ancla(caja(tablas, origen), lo)
        b = ancla(caja(tablas, destino_t), ld, alturas.get(origen, 0))
        p.line([(a[0] * s, a[1] * s), (b[0] * s, b[1] * s)],
               fill=ACENTO if grueso else LINEA, width=(4 if grueso else 2) * s)
        r = (9 if grueso else 7) * s
        p.ellipse([b[0] * s - r, b[1] * s - r, b[0] * s + r, b[1] * s + r],
                  fill=ACENTO if grueso else SECUNDARIO)

    for clave in tablas:
        *_, destacada = tablas[clave]
        x0, y0, x1, y1 = [v * s for v in caja(tablas, clave)]
        borde = ACENTO if destacada else SECUNDARIO
        p.rounded_rectangle([x0, y0, x1, y1], radius=10 * s,
                            fill=CAJA_A if destacada else CAJA_B,
                            outline=borde, width=2 * s)
        p.rounded_rectangle([x0, y0, x1, y0 + 62 * s], radius=10 * s, fill=borde)
        p.rectangle([x0, y0 + 40 * s, x1, y0 + 62 * s], fill=borde)

    lienzo = lienzo.resize((ancho, alto), Image.LANCZOS)
    p = ImageDraw.Draw(lienzo)
    f_tit = ImageFont.truetype(HELVETICA, 23, index=NEGRITA)
    f_sub = ImageFont.truetype(HELVETICA, 14, index=REGULAR)
    f_cam = ImageFont.truetype(HELVETICA, 15, index=REGULAR)
    f_key = ImageFont.truetype(HELVETICA, 15, index=MEDIA)
    f_leg = ImageFont.truetype(HELVETICA, 16, index=REGULAR)
    f_cab = ImageFont.truetype(HELVETICA, 17, index=NEGRITA)

    for clave in tablas:
        nombre, sub, campos, _, destacada = tablas[clave]
        x0, y0, x1, y1 = caja(tablas, clave)
        p.text((x0 + 16, y0 + 11), nombre, font=f_tit, fill=(16, 20, 8))
        p.text((x0 + 16, y0 + 72), sub, font=f_sub, fill=TENUE)
        y = y0 + 98
        for campo in campos:
            if campo == "":
                p.line([(x0 + 16, y + 8), (x1 - 16, y + 8)], fill=LINEA, width=1)
                y += SEPARADOR
                continue
            es_clave = any(m in campo for m in ("PK", "FK", "UNIQUE", "degen"))
            p.text((x0 + 16, y), campo, font=f_key if es_clave else f_cam,
                   fill=BLANCO if es_clave else GRIS)
            y += CAMPO

    nx, ny = nota_xy
    p.text((nx, ny), titulo, font=f_cab, fill=ACENTO)
    for i, l in enumerate(lineas_nota):
        p.text((nx, ny + 26 + i * 20), l, font=f_sub, fill=TENUE)

    ly = leyenda_y if leyenda_y else alto - 44
    x = 70
    for color, texto in leyenda:
        p.rounded_rectangle([x, ly, x + 30, ly + 18], radius=4, fill=color)
        p.text((x + 40, ly), texto, font=f_leg, fill=GRIS)
        x += 40 + int(p.textlength(texto, font=f_leg)) + 60

    lienzo.save(destino, optimize=True)
    return destino
