#!/usr/bin/env python3
"""Render marketing banners for Apocrypha Plus.

Draws to a PDF canvas using the book's own visual scheme (night ground, one
lamp, Gentium Plus) so the banner matches the cover, then rasterizes it.
"""
import os
import subprocess
import sys

import reportlab.rl_config as rl_config
from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bible import design                                   # noqa: E402
from bible.render import register_fonts                    # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, 'marketing', 'img')

SIZES = {
    'social': (1200, 630, 1.0),   # X / Twitter, OG
    'square': (1080, 1080, 2.2),  # Instagram square
}


def banner(name, w, h, s):
    c = rl_canvas.Canvas(os.path.join(IMG, f'banner-{name}.pdf'), pagesize=(w, h))
    c.setTitle('Apocrypha Plus')

    # night ground with a hint of depth at the foot
    c.setFillColor(design.NIGHT)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFillColor(design.OXIDE)
    c.rect(0, 0, w, 14 * s, stroke=0, fill=1)

    # the lamp, top-left, as on the cover
    design.lamp(c, 118 * s, h - 150 * s, 72 * s)

    # title
    c.setFillColor(design.VELLUM)
    c.setFont('Gentium-Bd', 54 * s)
    c.drawCentredString(w / 2, h * 0.60, 'APOCRYPHA PLUS')
    c.setFillColor(design.LAMP)
    c.setFont('Gentium-It', 21 * s)
    c.drawCentredString(w / 2, h * 0.51, 'the books kept outside the canon')
    c.setFillColor(design.VELLUM)
    c.setFont('Gentium', 15 * s)
    c.drawCentredString(w / 2, h * 0.40,
                        '77 writings the early church read, copied and argued over')
    c.setFillColor(design.GREY)
    c.setFont('Gentium', 13 * s)
    c.drawCentredString(w / 2, h * 0.33,
                        'Enoch  ·  Apostolic Fathers  ·  deuterocanon  ·  NT apocrypha')
    c.setFillColor(design.GREY)
    c.setFont('Gentium-It', 12 * s)
    c.drawCentredString(w / 2, h * 0.12, 'in public-domain translations, modernized')

    c.save()
    subprocess.run(['pdftoppm', '-r', '72', '-singlefile', '-png',
                    os.path.join(IMG, f'banner-{name}.pdf'),
                    os.path.join(IMG, f'banner-{name}.png')], check=True)
    # pdftoppm appends .png to the -singlefile output prefix
    os.rename(os.path.join(IMG, f'banner-{name}.png.png'),
              os.path.join(IMG, f'banner-{name}.png'))


if __name__ == '__main__':
    os.makedirs(IMG, exist_ok=True)
    register_fonts()
    rl_config.canvas_basefontname = 'Gentium'
    for name, (w, h, s) in SIZES.items():
        banner(name, w, h, s)
        print(f'banner-{name}.png {w}x{h}')
