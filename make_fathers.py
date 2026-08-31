#!/usr/bin/env python3
"""Build the third volume: the Apostolic Fathers, Roberts–Donaldson 1870."""
import os
import sys

from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bible import build, fathers                                 # noqa: E402
from bible.render import Renderer, register_fonts                # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'build')
SRC = os.path.join(ROOT, 'src', 'apostolic-fathers.txt')

NAME = 'The Apostolic Fathers'
SUBTITLE = 'a companion to The Lampstand Apocrypha'

NOTICE = [
    'THIS EDITION',
    '',
    'These are the writings of the generation after the apostles: Clement',
    'of Rome, Ignatius, Polycarp, the letter ascribed to Barnabas, the',
    'letter to Diognetus, the Shepherd of Hermas, and the fragments of',
    'Papias. They are not scripture in any communion, and are bound apart',
    'from the apocrypha for that reason.',
    '',
    'The translation is that of Alexander Roberts, James Donaldson and',
    'Frederick Crombie, made for the Ante-Nicene Christian Library and',
    'published at Edinburgh in 1870. It is in the public domain, and the',
    'transcription comes from Project Gutenberg.',
    '',
    'Three decisions of the editor of this volume should be stated.',
    '',
    'The letters of Ignatius survive in a shorter and a longer recension,',
    'and the 1870 edition prints them in alternating columns. Only the',
    'shorter is set here; the longer is a later expansion, and to',
    'interleave the two would make the book unreadable.',
    '',
    'The 1870 editors preface each work with an Introductory Notice of',
    'their own. Those are nineteenth-century commentary rather than the',
    'ancient text, and are not printed here.',
    '',
    'The appendix holds ten letters that the same editors print as',
    'spurious. They are kept, because the collection is more useful',
    'complete than tidy, and they are labelled as the editors labelled',
    'them rather than passed off as genuine.',
    '',
    'The English has been modernized and the spelling made American, by',
    'the same rules as the companion volumes; the sentences are the',
    'translators’ own. These works are divided into chapters but carry no',
    'verse numbers, so the running heads name the chapter alone.',
    '',
    'Set in Gentium Plus by SIL International (SIL Open Font License).',
]


def main():
    register_fonts()
    rend = Renderer()
    g = rend.g
    books = fathers.parse(SRC)
    genuine = books[:len(fathers.WORKS)]
    spurious = books[len(fathers.WORKS):]

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'The-Apostolic-Fathers.pdf')
    c = rl_canvas.Canvas(path, pagesize=(g.page_w, g.page_h))
    c.setTitle(NAME)
    c.setSubject('Public Domain; Roberts–Donaldson translation, 1870')

    pages, toc = [], []

    def add_division(title, group):
        if len(pages) % 2 == 1:
            pages.append(build.Page([], kind='blank'))
        pages.append(build.Page([], kind='part', title=title))
        toc.append(('div', title, len(pages) - 1))
        pages.append(build.Page([], kind='blank'))
        for bk in group:
            if not bk.blocks:
                continue
            cols = rend.packer.pack(rend.book_items(bk, bk.h))
            toc.append(('book', bk.h, len(pages)))
            for i in range(0, len(cols), 2):
                pages.append(build.Page(cols[i:i + 2], kind='body', book=bk.h))

    add_division('The Apostolic Fathers', genuine)
    add_division('Appendix: The Spurious Epistles', spurious)
    for i, p in enumerate(pages):
        p.number = i + 1

    # front matter
    c.setFont('Gentium-Bd', 17)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.63, NAME.upper())
    c.showPage(); c.showPage()
    c.setFont('Gentium-Bd', 19)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68, NAME.upper())
    c.setFont('Gentium', 9.5)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68 - 26,
                        'in the translation of Roberts, Donaldson and Crombie')
    c.setFont('Gentium-It', 9)
    c.drawCentredString(g.page_w / 2, g.page_h * 0.68 - 42,
                        'with the English modernized')
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(0.6)
    c.line(g.page_w / 2 - 52, g.page_h * 0.68 - 58, g.page_w / 2 + 52, g.page_h * 0.68 - 58)
    c.setFont('Gentium-It', 8.5)
    c.drawCentredString(g.page_w / 2, g.m_bot + 30, SUBTITLE)
    c.showPage()
    fm = 4                            # half-title, blank, title page are i-iii
    fm += build.draw_notice(c, rend, NOTICE, fm)
    c.showPage()
    fm += build.draw_contents(c, rend, toc, fm, fm)
    c.showPage()
    build.check_front_matter(fm - 1)

    for p in pages:
        if p.kind == 'body':
            build.draw_body_page(c, rend, p)
        elif p.kind == 'part':
            build.draw_part_page(c, rend, p)
        c.showPage()
    c.save()
    print(f"The-Apostolic-Fathers.pdf: {len(pages) + n + 4} pages "
          f"({len(genuine)} works, {len(spurious)} in the appendix)")


if __name__ == '__main__':
    main()
