#!/usr/bin/env python3
"""Build the companion volume: the Book of Enoch, in Laurence's translation.

Kept deliberately separate from the apocrypha volume. That book is one
translation throughout; this is a different translator from a different
century, and mixing the two inside one binding would misrepresent both.
"""
import os
import sys

from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bible import build, enoch                                   # noqa: E402
from bible.render import Renderer, register_fonts                # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'build')
SRC = os.path.join(ROOT, 'src', 'enoch-laurence.txt')

NAME = 'The Book of Enoch'
SUBTITLE = 'a companion to The Lampstand Apocrypha'

NOTICE = [
    'THIS EDITION',
    '',
    'The Book of Enoch is not in the World English Bible, so this volume',
    'cannot use the translation its companion uses. The text here rests on',
    'Richard Laurence’s, made from an Ethiopic manuscript in the Bodleian',
    'Library and published in this form at London in 1883. That translation',
    'is in the public domain, and the transcription comes from Project',
    'Gutenberg. It is bound separately from the apocrypha because one book',
    'should speak with one voice, and a different translator from a',
    'different century does not share it.',
    '',
    'THE ENGLISH HAS BEEN MODERNISED. Laurence wrote in the older manner,',
    'and this edition does not: thou, thee, thy and ye are set as you and',
    'your; hath, doth and saith as has, does and says; art, hast, shalt,',
    'dost, mayest, knowest and their like as are, have, shall, do, may and',
    'know; unto as to. Spelling has been made American throughout by the',
    'same rules as the companion volume.',
    '',
    'What that means should be plain: this is Laurence’s translation',
    'altered, not Laurence’s translation. Only pronouns, verb inflections',
    'and spelling were touched — every form was checked in its place first,',
    'and nothing was changed whose sense was in doubt. The sentences',
    'themselves are his, in his order and his choice of words, and turns',
    'that would need a sentence rebuilt to modernise — whence, thence,',
    'hither — are left standing rather than rewritten, since rewriting',
    'them would be composing a new translation instead of modernising an',
    'old one.',
    '',
    'Two things follow from the source. Laurence divides the book into 104',
    'chapters, running to CV, with no chapters 11, 36 or 101 — his',
    'division, not an omission here. And his footnotes, which the',
    'transcription sets adrift in the text, are restored to the foot of',
    'the column they belong to.',
    '',
    'Set in Gentium Plus by SIL International (SIL Open Font License).',
]


def main():
    register_fonts()
    rend = Renderer()
    g = rend.g
    bk = enoch.parse(SRC)
    items = rend.book_items(bk, 'Enoch')
    cols = rend.packer.pack(items)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'The-Book-of-Enoch.pdf')
    c = rl_canvas.Canvas(path, pagesize=(g.page_w, g.page_h))
    c.setTitle(NAME)
    c.setSubject('Public Domain; translated by Richard Laurence')

    # front matter
    c.setFont('Gentium-Bd', 17)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.63, NAME.upper())
    c.showPage()
    c.showPage()
    c.setFont('Gentium-Bd', 21)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68, NAME.upper())
    c.setFont('Gentium', 9.5)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68 - 26,
                        'from the Ethiopic, in the translation of')
    c.setFont('Gentium-Bd', 11)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68 - 42, 'Richard Laurence')
    c.setFont('Gentium-It', 9)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68 - 58,
                        'with the English modernized')
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(0.6)
    c.line(g.page_w / 2 - 52, g.page_h * 0.68 - 74, g.page_w / 2 + 52, g.page_h * 0.68 - 74)
    c.setFont('Gentium-It', 8.5)
    c.drawCentredString(g.page_w / 2, g.m_bot + 30, SUBTITLE)
    c.showPage()
    build.draw_notice(c, rend, NOTICE, 4)
    c.showPage()

    pages = []
    for i in range(0, len(cols), 2):
        p = build.Page(cols[i:i + 2], kind='body', book='Enoch')
        p.number = i // 2 + 1
        pages.append(p)
    for p in pages:
        build.draw_body_page(c, rend, p)
        c.showPage()
    c.save()
    print(f"The-Book-of-Enoch.pdf: {len(pages) + 4} pages "
          f"({len(cols)} columns, {len(items)} items)")


if __name__ == '__main__':
    main()
