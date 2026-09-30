#!/usr/bin/env python3
"""Gera as 8 amostras ficticias de texto impresso do protocolo congelado
(PROTOCOLO_CONGELADO.md secao 3). Texto sintetico em portugues, sem dado
de aluno real. Cada amostra tem sua transcricao de referencia gravada
separadamente em texto simples, produzida ANTES da execucao dos candidatos.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "amostras")
os.makedirs(OUT_DIR, exist_ok=True)

# Texto base para as amostras (resposta ficticia de aluno, avaliacao de
# geografia, sem nenhuma identificacao real)
TEXTO_BASE = (
    "A capital do Brasil e Brasilia, inaugurada em 1960. "
    "Ela foi planejada pelo urbanista Lucio Costa e pelo "
    "arquiteto Oscar Niemeyer, com o objetivo de interiorizar "
    "o desenvolvimento do pais."
)

TEXTO_ACENTUACAO = (
    "A questao envolve conceitos de acao, nacao, coracao e "
    "razao. Tambem trata de fenomenos atmosfericos, como o "
    "orvalho e a neblina, alem da influencia do relevo na "
    "formacao de microclimas regionais."
)

FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/SFNS.ttf",
]


def load_font(size=28):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_text(text, size=(900, 400), font_size=28, bg=(255, 255, 255), fg=(20, 20, 20)):
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    font = load_font(font_size)
    margin = 40
    max_width = size[0] - 2 * margin
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    y = margin
    for line in lines:
        draw.text((margin, y), line, font=font, fill=fg)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + 14
    return img


def add_shadow_gradient(img):
    w, h = img.size
    overlay = Image.new("L", (w, h), 0)
    arr = np.zeros((h, w), dtype=np.uint8)
    for x in range(w):
        # gradiente da esquerda (escuro) para a direita (claro)
        val = int(120 * (1 - x / w))
        arr[:, x] = val
    overlay = Image.fromarray(arr, mode="L")
    shadow = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(shadow, img, overlay.point(lambda p: 255 - p))


def add_scribble(img):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # rasura: uma linha grossa sobre uma pequena regiao do texto
    y0 = int(h * 0.4)
    draw.line([(60, y0), (300, y0 + 10)], fill=(20, 20, 20), width=8)
    draw.line([(60, y0 + 8), (300, y0 - 2)], fill=(20, 20, 20), width=8)
    return img


def gen_imp01():
    img = render_text(TEXTO_BASE)
    img.save(os.path.join(OUT_DIR, "IMP-01_nitida.png"))


def gen_imp02():
    img = render_text(TEXTO_BASE)
    img = img.rotate(5, expand=True, fillcolor=(255, 255, 255))
    img.save(os.path.join(OUT_DIR, "IMP-02_inclinacao_leve.png"))


def gen_imp03():
    img = render_text(TEXTO_BASE)
    img = img.rotate(20, expand=True, fillcolor=(255, 255, 255))
    img.save(os.path.join(OUT_DIR, "IMP-03_inclinacao_acentuada.png"))


def gen_imp04():
    img = render_text(TEXTO_BASE)
    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    img.save(os.path.join(OUT_DIR, "IMP-04_desfocada.png"))


def gen_imp05():
    img = render_text(TEXTO_BASE)
    img = add_shadow_gradient(img)
    img.save(os.path.join(OUT_DIR, "IMP-05_iluminacao_irregular.png"))


def gen_imp06():
    img = render_text(TEXTO_ACENTUACAO)
    img.save(os.path.join(OUT_DIR, "IMP-06_acentuacao.png"))


def gen_imp07():
    img = render_text(TEXTO_BASE)
    img = add_scribble(img)
    img.save(os.path.join(OUT_DIR, "IMP-07_rasura.png"))


def gen_imp08():
    # imagem vazia/ilegivel: ruido puro, sem texto
    rng = np.random.default_rng(42)
    arr = rng.integers(0, 255, (400, 900, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    img.save(os.path.join(OUT_DIR, "IMP-08_vazia_ilegivel.png"))


def gen_referencias():
    refs = {
        "IMP-01_nitida.txt": TEXTO_BASE,
        "IMP-02_inclinacao_leve.txt": TEXTO_BASE,
        "IMP-03_inclinacao_acentuada.txt": TEXTO_BASE,
        "IMP-04_desfocada.txt": TEXTO_BASE,
        "IMP-05_iluminacao_irregular.txt": TEXTO_BASE,
        "IMP-06_acentuacao.txt": TEXTO_ACENTUACAO,
        "IMP-07_rasura.txt": TEXTO_BASE,
        "IMP-08_vazia_ilegivel.txt": "",
    }
    ref_dir = os.path.join(OUT_DIR, "referencias")
    os.makedirs(ref_dir, exist_ok=True)
    for name, text in refs.items():
        with open(os.path.join(ref_dir, name), "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    gen_imp01()
    gen_imp02()
    gen_imp03()
    gen_imp04()
    gen_imp05()
    gen_imp06()
    gen_imp07()
    gen_imp08()
    gen_referencias()
    print("8 amostras + referencias geradas em", OUT_DIR)
