#!/usr/bin/env python3
"""Build the print cover for Apocrypha Plus.

A cover is a separate file from the book block: one flat sheet carrying back
cover, spine and front cover together, with bleed all round. The spine width
depends on the page count and the paper, so it is computed rather than
guessed — get it wrong and the fold lands in the middle of the front.
"""
import argparse
import os
import subprocess
import sys

import reportlab.rl_config as rl_config
from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bible import design, kdp                                     # noqa: E402
from bible.render import register_fonts                           # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'build')
IN = 72.0
TRIM_W, TRIM_H = 5.5 * IN, 8.5 * IN      # a standard KDP trim

# --- KDP paperback ------------------------------------------------------
# Cover wrap = 2 x trim width + spine + bleed on both sides; height = trim
# plus bleed top and bottom. KDP's own cover template generator is the
# authority for a given book, and these are its inputs, so the two agree.
BLEED = 0.125 * IN          # all four outer edges
SAFE = 0.25 * IN            # keep type this far inside every trim edge
FOLD = 0.0625 * IN          # spine fold tolerance; keep spine type inside it
SPINE_TEXT_MIN = 100        # KDP prints no spine text below this page count
PAGES_MIN, PAGES_MAX = 24, 828   # black ink, 5.5 x 8.5, either paper stock

# KDP's minimum inside (gutter) margin rises with the page count. The book is
# set well above the figure for its band, but the table is here so the build
# can say so rather than leave it to be remembered.
GUTTER_MIN = [(150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75),
              (828, 0.875)]
BARCODE_W, BARCODE_H = 2.0 * IN, 1.2 * IN

# inches of thickness per page, by stock
PAPER = {'cream': 0.0025, 'white': 0.002252}

BLURB = [
    ('h', 'Seventy-six writings the early church read,'),
    ('h', 'copied and argued over — and then set aside.'),
    ('', ''),
    ('b', 'The deuterocanonical books received by Rome and the East, with'),
    ('b', 'the Rest of Esther, the Epistle of Jeremiah, the Song of the'),
    ('b', 'Three, Susanna, and Bel and the Dragon standing under their own'),
    ('b', 'titles. The wider apocrypha beyond them: 1 and 2 Esdras, the'),
    ('b', 'Prayer of Manasseh, Psalm 151, 3 and 4 Maccabees. The Book of'),
    ('b', 'Enoch entire, and the pseudepigrapha around it — the books of'),
    ('b', 'Adam and Eve, the Secrets of Enoch, the Psalms and Odes of'),
    ('b', 'Solomon, Aristeas, Ahikar, and the Testaments of the Twelve'),
    ('b', 'Patriarchs. The gospels and letters that circulated under'),
    ('b', 'apostolic names — the Protevangelion, the infancy gospels,'),
    ('b', 'Nicodemus, Laodiceans, Paul and Thecla. And the writings of the'),
    ('b', 'generation after the apostles, from the Didache to the Shepherd'),
    ('b', 'of Hermas.'),
    ('', ''),
    ('b', 'Five public-domain sources across three centuries, brought to'),
    ('b', 'one modern American standard: spelling, pronouns and verb forms'),
    ('b', 'made present-day, the sentences left as the translators wrote'),
    ('b', 'them. Every departure from the source texts is listed inside,'),
    ('b', 'and each division names the translation it uses.'),
    ('', ''),
    ('b', 'Nothing here is claimed as scripture. Some of these books are'),
    ('b', 'canonical for some communions and not for others; some are'),
    ('b', 'canonical for none; and the appendix keeps ten letters their own'),
    ('b', 'editors judged spurious, labeled as such. A summary of each'),
    ('b', 'book of the common canon closes the volume.'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=int, default=0,
                    help='page count of the block (read from the PDF if omitted)')
    ap.add_argument('--paper', default='cream', choices=sorted(PAPER))
    a = ap.parse_args()

    pages = a.pages
    if not pages:
        block = os.path.join(OUT, 'Apocrypha-Plus.pdf')
        out = subprocess.run(['pdfinfo', block], capture_output=True, text=True)
        pages = int([l for l in out.stdout.splitlines()
                     if l.startswith('Pages:')][0].split()[1])

    problems = []
    if pages % 2:
        problems.append(f'page count {pages} is odd; a sheet has two sides')
    if not PAGES_MIN <= pages <= PAGES_MAX:
        problems.append(f'page count {pages} is outside KDP\'s range for '
                        f'this trim, {PAGES_MIN}-{PAGES_MAX}')
    if problems:
        for x in problems:
            print('ERROR: ' + x, file=sys.stderr)
        raise SystemExit(1)

    spine = pages * PAPER[a.paper] * IN
    W = TRIM_W * 2 + spine + BLEED * 2
    H = TRIM_H + BLEED * 2
    back_l = BLEED
    spine_l = BLEED + TRIM_W
    front_l = spine_l + spine

    register_fonts()
    # ReportLab puts Helvetica in every page's resources as the default
    # base font, and Helvetica is one of the standard 14 it does not
    # embed. KDP's preflight wants every font embedded, so the default
    # is pointed at Gentium and no unembedded font reaches the file.
    rl_config.canvas_basefontname = 'Gentium'
    path = os.path.join(OUT, 'Apocrypha-Plus-Cover.pdf')
    c = rl_canvas.Canvas(path, pagesize=(W, H))
    c.setTitle('Apocrypha Plus — cover')
    c.setAuthor('')

    # the whole wrap, bleed included, is the night ground
    c.setFillColor(design.NIGHT)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- front ---------------------------------------------------------
    fx = front_l + TRIM_W / 2
    design.lamp(c, fx, BLEED + TRIM_H * 0.62, 32)
    c.setFillColor(design.VELLUM)
    c.setFont('Gentium-Bd', 30)
    c.drawCentredString(fx, BLEED + TRIM_H * 0.44, 'APOCRYPHA')
    c.drawCentredString(fx, BLEED + TRIM_H * 0.44 - 34, 'PLUS')
    design.broken_rule(c, fx - TRIM_W * 0.22, fx + TRIM_W * 0.22,
                       BLEED + TRIM_H * 0.355)
    c.setFillColor(design.LAMP)
    c.setFont('Gentium-It', 11)
    c.drawCentredString(fx, BLEED + TRIM_H * 0.30,
                        'the books kept outside the canon')
    c.setFillColor(design.VELLUM)
    c.setFont('Gentium', 8.4)
    c.drawCentredString(fx, BLEED + SAFE + 6,
                        'in public-domain translations, modernized')

    # --- spine ---------------------------------------------------------
    if pages >= SPINE_TEXT_MIN:                # KDP's threshold for spine text
        sx = spine_l + spine / 2
        c.saveState()
        c.translate(sx, BLEED + TRIM_H / 2)
        c.rotate(-90)
        c.setFillColor(design.VELLUM)
        c.setFont('Gentium-Bd', 13)
        c.drawCentredString(30, -4.6, 'APOCRYPHA PLUS')
        c.restoreState()
        design.lamp(c, sx, BLEED + SAFE + 26, 9)

    # --- back ----------------------------------------------------------
    bx = back_l + SAFE + 6
    y = BLEED + TRIM_H - SAFE - 40
    for kind, line in BLURB:
        if kind == 'h':
            c.setFillColor(design.LAMP)
            c.setFont('Gentium-Bd', 11)
            c.drawString(bx, y, line)
            y -= 15
        elif kind == 'b':
            c.setFillColor(design.VELLUM)
            c.setFont('Gentium', 8.6)
            c.drawString(bx, y, line)
            y -= 11.4
        else:
            y -= 7
    design.broken_rule(c, bx, back_l + TRIM_W - SAFE - 6, y - 6, design.LAMP)
    c.setFillColor(design.LAMP)
    c.setFont('Gentium-It', 8.2)
    c.drawString(bx, y - 24,
                 'Every text in this book is in the public domain,')
    c.drawString(bx, y - 35, 'and so is this edition of it.')

    # clear space for the barcode, which the printer prints over
    bw, bh = BARCODE_W, BARCODE_H
    c.setFillColorRGB(1, 1, 1)
    c.rect(back_l + TRIM_W - SAFE - bw, BLEED + SAFE, bw, bh, stroke=0, fill=1)

    c.save()
    if kdp.check_cover(path, TRIM_W, TRIM_H, spine, BLEED, SAFE, FOLD):
        raise SystemExit(1)
    print(f"Apocrypha-Plus-Cover.pdf")
    print(f"  block {pages} pages on {a.paper} stock")
    print(f"  spine {spine/IN:.4f} in ({spine:.2f} pt)")
    print(f"  wrap  {W/IN:.3f} x {H/IN:.3f} in, {BLEED/IN:.3f} in bleed")
    need = next(g for lim, g in GUTTER_MIN if pages <= lim)
    print(f"  KDP   5.5 x 8.5 paperback, black ink")
    print(f"        gutter required {need:.3f} in at {pages} pages")
    print(f"        type {SAFE/IN:.2f} in inside trim, spine type "
          f"{FOLD/IN:.4f} in inside the fold")
    print(f"        barcode clear {BARCODE_W/IN:.1f} x {BARCODE_H/IN:.1f} in, "
          f"{SAFE/IN:.2f} in off the trim edge")


if __name__ == '__main__':
    main()
