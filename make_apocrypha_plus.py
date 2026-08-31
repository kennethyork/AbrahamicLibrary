#!/usr/bin/env python3
"""Build Apocrypha Plus — one volume gathering everything in the project."""
import os
import sys

import reportlab.rl_config as rl_config
from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bible import build, canon, didache, eden, enoch, fathers, kdp, wake  # noqa: E402
from bible.summaries import SUMMARIES                               # noqa: E402
from bible.intros import INTROS                                     # noqa: E402
from bible.jubilees_note import TITLE as JUB_TITLE, SUBTITLE as JUB_SUB, NOTE as JUB_NOTE  # noqa: E402
from bible.render import Renderer, register_fonts                   # noqa: E402
from bible.corrections import fix_text, americanize                 # noqa: E402
from bible.usfm import Book, Block, Text                             # noqa: E402
from bible import design                                            # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'build')
NAME = 'Apocrypha Plus'

NOTICE = [
    'THIS EDITION',
    '',
    'Apocrypha Plus gathers, in one volume, the books that stand outside',
    'the sixty-six of the Protestant canon but were read, copied and',
    'argued over by the early church: the deuterocanon received by Rome',
    'and the East, the wider apocrypha beyond it, Enoch, the gospels and',
    'letters that circulated under apostolic names, and the writings of',
    'the generation that followed the apostles.',
    '',
    'Everything here is in the public domain, and so is this edition.',
    'Four translations are used, each named on the part-title page of the',
    'division it serves:',
    '',
    '    The deuterocanon and wider apocrypha, from the World English',
    '    Bible (Updated), dedicated to the public domain by eBible.org.',
    '',
    '    Enoch, from Richard Laurence’s translation of an Ethiopic',
    '    manuscript in the Bodleian Library, London, 1883.',
    '',
    '    The New Testament apocrypha, from William Wake’s translations,',
    '    as collected in The Suppressed Gospels and Epistles.',
    '',
    '    The Apostolic Fathers, from Alexander Roberts, James Donaldson',
    '    and Frederick Crombie, Edinburgh, 1870 — except the Didache,',
    '    which was found in 1873, three years after that volume went to',
    '    press, and is taken from the seventh volume of the same series,',
    '    1886.',
    '',
    'Because translators of three centuries are gathered here, the',
    'English of all of them has been brought to one standard. Spelling is',
    'American throughout. The older forms are set as present-day ones:',
    'thou, thee, thy and ye as you and your; hath, doth and saith as has,',
    'does and says; the whole -eth and -est classes — cometh, giveth,',
    'lovest, gavest — as comes, gives, love and gave; unto as to; hither,',
    'thither and whither as here, there and where; whence and thence as',
    'from where and from there; and he that, they that as he who and',
    'those who. A few constructions are turned rather than re-inflected:',
    'it came to pass becomes it happened, suffer me to go becomes allow me',
    'to go, wherewith becomes with which, and the emphatic did eat becomes',
    'ate. Each of some five hundred and sixty forms was checked in place',
    'before a rule was written for it.',
    '',
    'Two things are left as they stand. Lest keeps its old sense — every',
    'one of its hundred and fifteen uses would need the sentence rebuilt',
    'around a negation to lose it. And behold is kept because only a',
    'quarter of its uses are the exclamation; the rest are the plain verb,',
    'which no substitution survives. Beyond the forms named above, the',
    'word order is the translators’ own. No passage has been rewritten for',
    'sense or style: to recast their sentences would be to compose new',
    'translations rather than to modernize old ones, and this edition does',
    'not pretend to do that.',
    '',
    'Nothing here is claimed as scripture. The deuterocanonical books are',
    'canonical for some communions and not for others; the New Testament',
    'apocrypha are canonical for none; and the appendix holds letters',
    'their own editors judged spurious, kept for completeness and',
    'labeled as such rather than passed off as genuine.',
    '',
    'Set in Gentium Plus by SIL International (SIL Open Font License);',
    'Hebrew in Noto Serif Hebrew.',
]

SOURCES = {
    'The Deuterocanonical Books': 'World English Bible (Updated)',
    'The Wider Apocrypha': 'World English Bible (Updated)',
    'The Book of Enoch': 'translated by Richard Laurence, 1883',
    'The Pseudepigrapha': 'The Forgotten Books of Eden, 1926',
    'The New Testament Apocrypha': 'translated by William Wake',
    'The Apostolic Fathers': 'Ante-Nicene Christian Library, 1870 and 1886',
    'Appendix: The Spurious Epistles': 'Roberts, Donaldson and Crombie, 1870',
    'Appendix: The Books of the Bible': 'a summary of each book of the common canon',
}


def _named(bid, files):
    """Load a book and give it this edition's display name."""
    bk = build.load_book(bid, files)
    bk.h = canon.NAMES.get(bid, bk.h)
    return bk


def summary_book():
    """The appendix: a short account of each book of the common canon.

    Set as one continuous piece rather than a book apiece, so it reads as an
    appendix and does not spend a page on every entry.
    """
    bk = Book(id='SUM', h='Summaries',
              toc1='Summaries of the Books of the Bible', toc2='Summaries')
    for group, entries in SUMMARIES:
        b = Block('ms1'); b.items = [Text(group)]
        bk.blocks.append(b)
        for name, text in entries:
            h = Block('s1'); h.items = [Text(name)]
            bk.blocks.append(h)
            para = Block('p'); para.items = [Text(americanize(text))]
            bk.blocks.append(para)
    return bk


def divisions():
    files = build.source_files()
    deut = [_named(b, files) for b, _ in canon.DEUTEROCANONICAL]
    wider = [_named(b, files) for b, _ in canon.WIDER]
    eno = [enoch.parse(os.path.join(ROOT, 'src', 'enoch-laurence.txt'))]
    pse = eden.parse(os.path.join(ROOT, 'src', 'forgotten-books-eden.txt'))
    # Jubilees is described rather than printed; see bible/jubilees_note.py
    jb = Book(id='JUB', h='Jubilees', toc1=JUB_TITLE, toc2='Jubilees')
    sub = Block('d'); sub.items = [Text(JUB_SUB)]
    jb.blocks.append(sub)
    for para in JUB_NOTE:
        b = Block('p'); b.items = [Text(para)]
        jb.blocks.append(b)
    pse.append(jb)
    nt = wake.parse(os.path.join(ROOT, 'src', 'wake-nt-apocrypha.txt'))
    fa = fathers.parse(os.path.join(ROOT, 'src', 'apostolic-fathers.txt'))
    genuine, spurious = fa[:len(fathers.WORKS)], fa[len(fathers.WORKS):]
    # The Didache was found in 1873, after the 1870 volume went to press; it
    # comes from the seventh volume of the same series and stands first, as
    # the earliest of these writings.
    genuine = [didache.parse(os.path.join(ROOT, 'src', 'didache'))] + genuine
    # Four of these books are markedly harder than the rest, and the reason
    # is not the translation: a reader is dropped into Seleucid court
    # politics with no idea who anyone is. The text is left exactly as the
    # translators made it, and a page of orientation is put in front of it.
    for group in (deut, wider, genuine, spurious, nt, eno, pse):
        for bk in group:
            intro = INTROS.get(fix_text(bk.h or bk.toc2 or ''))
            if intro and bk.blocks:
                lead = []
                for para in intro:
                    b = Block('ip')
                    b.items = [Text(para)]
                    lead.append(b)
                bk.blocks = lead + bk.blocks

    return [
        ('The Deuterocanonical Books', deut),
        ('The Wider Apocrypha', wider),
        ('The Book of Enoch', eno),
        ('The Pseudepigrapha', pse),
        ('The New Testament Apocrypha', nt),
        ('The Apostolic Fathers', genuine),
        ('Appendix: The Spurious Epistles', spurious),
        ('Appendix: The Books of the Bible', [summary_book()]),
    ]


def main():
    register_fonts()
    # ReportLab puts Helvetica in every page's resources as the default
    # base font, and Helvetica is one of the standard 14 it does not
    # embed. KDP's preflight wants every font embedded, so the default
    # is pointed at Gentium and no unembedded font reaches the file.
    rl_config.canvas_basefontname = 'Gentium'
    rend = Renderer()
    g = rend.g
    pages, toc, works = [], [], 0

    for title, group in divisions():
        if len(pages) % 2 == 1:
            pages.append(build.Page([], kind='blank'))
        p = build.Page([], kind='part', title=title)
        p.subtitle = SOURCES.get(title)
        pages.append(p)
        toc.append(('div', title, len(pages) - 1))
        pages.append(build.Page([], kind='blank'))
        for bk in group:
            if not bk.blocks:
                continue
            works += 1
            name = fix_text(bk.h or bk.toc2)
            cols = rend.packer.pack(rend.book_items(bk, name))
            toc.append(('book', name, len(pages)))
            for i in range(0, len(cols), 2):
                pages.append(build.Page(cols[i:i + 2], kind='body', book=name))
    for i, p in enumerate(pages):
        p.number = i + 1

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'Apocrypha-Plus.pdf')
    c = rl_canvas.Canvas(path, pagesize=(g.page_w, g.page_h))
    c.setTitle(NAME)
    c.setSubject('Public Domain')
    # There is no author. These writings are anonymous or pseudonymous, and
    # the translators are named on the part-title page of each division.
    # Left empty deliberately — the library would otherwise write "anonymous",
    # which claims more than nothing does.
    c.setAuthor('')
    c.setCreator('')

    # Half-title and title are rectos, and display type on a recto centres on
    # the text block: the sheet's own centre sits 0.32 in into the gutter side.
    cx = build.optical_centre(g)

    # half-title
    c.setFont('Gentium-Bd', 18)
    c.drawCentredString(cx, g.page_h * 0.63, NAME.upper())
    design.broken_rule(c, cx - g.text_w * 0.19, cx + g.text_w * 0.19,
                       g.page_h * 0.63 - 16, design.GREY)
    c.showPage(); c.showPage()
    c.setFont('Gentium-Bd', 22)
    c.drawCentredString(cx, g.page_h * 0.70, NAME.upper())
    c.setFont('Gentium', 9.5)
    y = g.page_h * 0.70 - 28
    for ln in ['the deuterocanonical and apocryphal books,',
               'the Book of Enoch, the New Testament apocrypha,',
               'and the writings of the Apostolic Fathers']:
        c.drawCentredString(cx, y, ln)
        y -= 14
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(0.6)
    c.line(cx - 58, y - 8, cx + 58, y - 8)
    design.lamp(c, cx, y - 40, 13, design.GREY)
    c.setFont('Gentium-It', 8.5)
    c.setFillColor(design.INK)
    c.drawCentredString(cx, g.m_bot + 30,
                        'in public-domain translations, modernized')
    c.showPage()
    # half-title, its blank verso and the title page are pages i-iii; the
    # notice opens on iv and the contents on whatever the notice ends before.
    fm = 4
    fm += build.draw_notice(c, rend, NOTICE, fm)
    c.showPage()
    fm += build.draw_contents(c, rend, toc, fm, fm)
    c.showPage()
    # Body pages take their binding side from their own number, which starts
    # again at 1, so the front matter has to end on a verso.
    build.check_front_matter(fm - 1)

    for p in pages:
        if p.kind == 'body':
            build.draw_body_page(c, rend, p)
        elif p.kind == 'part':
            build.draw_part_page(c, rend, p)
        c.showPage()
    # A book is made of leaves, so the block must end on an even page;
    # otherwise the printer silently adds the blank and the count on the
    # cover — and so the spine width — is wrong.
    if c.getPageNumber() % 2 == 0:
        c.showPage()
    total = c.getPageNumber() - 1
    c.save()
    print(f"Apocrypha-Plus.pdf: {total} pages, {works} works")
    if kdp.check_block(path):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
