"""Driver: parses the USFM, paginates, and writes the printable PDF."""
import glob
import os
import re
import sys

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics

from . import canon, usfm
from .render import Renderer, register_fonts
from .corrections import manifest, WORD_FIXES, NAME_FIXES
from .layout import Geom, Item
from .typeset import Atom, Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USFM_DIR = os.path.join(ROOT, 'src', 'usfm_u')


def _vnum(v):
    """Leading integer of a verse label ('18', '18-19', '4b') -> int."""
    m = re.match(r'(\d+)', v or '')
    return int(m.group(1)) if m else None


def slice_book(bk, spec):
    """Return a new Book holding only the verses `spec` selects.

    Used for the portions that KJV-tradition apocrypha print under their own
    titles — the Song of the Three, Susanna, Bel and the Dragon, the Epistle
    of Jeremiah, the Rest of Esther. Verse numbers are left as the source has
    them so references still resolve.
    """
    sel = spec['select']
    whole = {c for c, a, _ in sel if a is None}
    spans = {c: (a, b) for c, a, b in sel if a is not None}

    def wanted(c, v):
        if c in whole:
            return True
        if c in spans:
            n = _vnum(v)
            return n is not None and spans[c][0] <= n <= spans[c][1]
        return False

    out = usfm.Book(id=spec.get('id', ''), h=spec['name'],
                    toc1=spec['title'], toc2=spec['name'])
    title_key = re.sub(r'[^a-z]', '', spec['title'].lower())
    chapter, verse, opened = None, None, set()
    for b in bk.blocks:
        if b.style == 'c':
            chapter, verse = b.items[0].num, None
            continue
        if b.style in ('s1', 's2', 'ms1', 'ms2'):
            txt = ''.join(i.s for i in b.items if isinstance(i, usfm.Text)).strip()
            # a heading that merely repeats the new book's title is redundant
            if re.sub(r'[^a-z]', '', txt.lower()) in (title_key,
                                                      title_key.replace('the', '')):
                continue
        keep = []
        for it in b.items:
            if isinstance(it, usfm.Verse):
                verse = it.num
            if wanted(chapter, verse):
                keep.append(it)
        if not keep and not (b.style in ('b',) and wanted(chapter, verse)):
            continue
        if chapter not in opened:
            opened.add(chapter)
            out.blocks.append(usfm.Block('c', [usfm.Chapter(chapter)]))
        out.blocks.append(usfm.Block(b.style, keep))
    return out


def load_book(bid, files=None):
    """Parse a book, slicing it first if it is a derived title."""
    files = files or source_files()
    spec = canon.DERIVED.get(bid)
    if not spec:
        return usfm.parse(files[bid])
    spec = dict(spec, id=bid)
    return slice_book(usfm.parse(files[spec['src']]), spec)


def source_files():
    out = {}
    for f in glob.glob(os.path.join(USFM_DIR, '*.usfm')):
        m = re.search(r'-(\w{3})eng', os.path.basename(f))
        if m:
            out[m.group(1)] = f
    return out


class Page:
    def __init__(self, cols, kind='body', book=None, title=None, subtitle=None):
        self.cols = cols            # list of Column (0-2)
        self.kind = kind            # 'body' | 'part' | 'blank' | 'front'
        self.book = book
        self.title = title
        self.subtitle = subtitle
        self.number = 0

    def ref_range(self):
        refs = []
        for col in self.cols:
            for it in col.items:
                if it.ref:
                    refs.append(it.ref)
        if not refs:
            return None
        a, b = refs[0], refs[-1]
        if a[1] is None or b[1] is None:          # chapters without verses
            return str(a[0]) if a[0] == b[0] else f"{a[0]}–{b[0]}"
        if a == b:
            return f"{a[0]}:{a[1]}"
        if a[0] == b[0]:
            return f"{a[0]}:{a[1]}–{b[1]}"
        return f"{a[0]}:{a[1]}–{b[0]}:{b[1]}"


def build_pages(rend, book_ids, files, progress=True):
    """Returns (pages, toc) where toc is [(kind, label, page_index)]."""
    pages, toc = [], []
    div_of = {}
    for _, testament, div_title, books in canon.DIVISIONS:
        for bid, _ in books:
            div_of[bid] = (testament, div_title)

    seen_div = set()
    for bid in book_ids:
        testament, div_title = div_of[bid]
        # part-title page, forced onto a recto
        if div_title not in seen_div:
            seen_div.add(div_title)
            if len(pages) % 2 == 1:
                pages.append(Page([], kind='blank'))
            pages.append(Page([], kind='part', title=div_title,
                              subtitle=testament))
            toc.append(('div', div_title, len(pages) - 1))
            pages.append(Page([], kind='blank'))

        book = load_book(bid, files)
        items = rend.book_items(book, canon.NAMES[bid])
        cols = rend.packer.pack(items)
        toc.append(('book', canon.NAMES[bid], len(pages)))
        for i in range(0, len(cols), 2):
            pages.append(Page(cols[i:i + 2], kind='body', book=canon.NAMES[bid]))
        if progress:
            print(f"  {canon.NAMES[bid]:<18} {len(cols):>4} cols "
                  f"-> pages {len(pages)}", file=sys.stderr)
    for i, p in enumerate(pages):
        p.number = i + 1
    return pages, toc


def roman(n):
    vals = [(1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'),
            (90, 'xc'), (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'),
            (5, 'v'), (4, 'iv'), (1, 'i')]
    out = ''
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def draw_head(c, rend, page, folio):
    g = rend.g
    recto = (page.number % 2 == 1)
    y = g.page_h - g.m_top
    rng = page.ref_range()
    if page.book and rng:
        label = f"{page.book} {rng}"
        left = g.left_margin(recto)
        w = rend.small_caps(c, label, 0, -9999, rend.sh.body_size * 0.80)
        x = left + (g.text_w - w) / 2.0
        c.setFillColorRGB(0.15, 0.15, 0.15)
        rend.small_caps(c, label, x, y, rend.sh.body_size * 0.80)
        c.setFillColorRGB(0, 0, 0)
    if folio:
        c.setFont('Gentium', rend.sh.body_size * 0.85)
        if recto:
            c.drawRightString(g.page_w - g.m_out, y, folio)
        else:
            c.drawString(g.m_out, y, folio)


def assign_marks(page):
    """Per-page footnote letters, running across both columns."""
    letters = 'abcdefghijklmnopqrstuvwxyz'
    marks, i = {}, 0
    for col in page.cols:
        for nt in col.notes:
            marks[id(nt)] = letters[i % 26]
            i += 1
    return marks


def draw_body_page(c, rend, page):
    g = rend.g
    recto = (page.number % 2 == 1)
    marks = assign_marks(page)
    for ci, col in enumerate(page.cols):
        rend.draw_column(c, col, g.col_x(recto, ci), g.text_top, marks)
    draw_head(c, rend, page, str(page.number))


def optical_centre(g, recto=True):
    """The centre of the text block, not of the sheet.

    With a binding margin the two are not the same place. Display type centred
    on the sheet reads off-centre in the open book, and a wide line — "Appendix:
    The Books of the Bible" — reaches past the gutter into the binding.
    """
    return g.left_margin(recto) + g.text_w / 2.0


def draw_part_page(c, rend, page):
    g = rend.g
    cy = g.page_h * 0.60
    cx = optical_centre(g, page.number % 2 == 1)
    if page.subtitle:
        c.setFillColorRGB(0.3, 0.3, 0.3)
        w = rend.small_caps(c, page.subtitle, 0, -9999, 11)
        rend.small_caps(c, page.subtitle, cx - w / 2, cy + 46, 11)
        c.setFillColorRGB(0, 0, 0)
    c.setFont('Gentium-Bd', 19)
    c.drawCentredString(cx, cy, page.title)
    from . import design
    design.broken_rule(c, cx - 52, cx + 52, cy - 15, design.GREY)


def draw_notice(c, rend, lines, first_folio):
    """Draw the edition notice, flowing onto further pages if it outgrows one.

    `first_folio` is the physical page the notice opens on, so its parity
    decides which side the binding is on. Returns the number of pages used.
    """
    g = rend.g
    lead, top = 10.0, g.page_h * 0.78
    bottom = g.m_bot + 16                     # keep clear of the folio
    # If it no longer fits on one page, start at the top of the block instead
    # of the optical centre, which buys back another fifteen lines.
    if top - len(lines) * lead < bottom:
        top = g.text_top
    pages, i, folio = 0, 0, first_folio
    while i < len(lines):
        y = top
        left = g.left_margin(folio % 2 == 1)
        while i < len(lines) and y >= bottom:
            ln = lines[i]
            if ln == 'THIS EDITION':
                rend.small_caps(c, ln, left, y, 8.6, 'Gentium-Bd')
            elif ln:
                c.setFont('Gentium', 8.0)
                c.drawString(left, y, ln)
            y -= lead
            i += 1
        c.setFont('Gentium', rend.sh.body_size * 0.85)
        c.drawCentredString(optical_centre(g, folio % 2 == 1), g.m_bot - 2,
                            roman(folio))
        pages += 1
        folio += 1
        top = g.text_top                      # continuation pages start high
        if i < len(lines):
            c.showPage()
    return pages


def draw_front(c, rend, kind, data, folio):
    g = rend.g
    cx = optical_centre(g)                # front matter opens on a recto
    if kind == 'halftitle':
        c.setFont('Gentium-Bd', 17)
        c.drawCentredString(cx, g.page_h * 0.63, EDITION_NAME.upper())
    elif kind == 'title':
        c.setFont('Gentium-Bd', 21)
        c.drawCentredString(cx, g.page_h * 0.70, EDITION_NAME.upper())
        c.setFont('Gentium', 9.5)
        y = g.page_h * 0.70 - 26
        for ln in ['containing',
                   'THE DEUTEROCANONICAL BOOKS',
                   'and the wider apocrypha']:
            c.drawCentredString(cx, y, ln)
            y -= 14
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.6)
        c.line(cx - 52, y - 6, cx + 52, y - 6)
        if EDITION_SUBTITLE:
            c.setFont('Gentium-Bd', 12)
            c.drawCentredString(cx, y - 30, EDITION_SUBTITLE)
        c.setFont('Gentium-It', 8.5)
        c.drawCentredString(cx, g.m_bot + 30,
                            'in the translation of the World English Bible')
    elif kind == 'copyright':
        pass                      # drawn by draw_notice(), which can flow
    if folio:
        c.setFont('Gentium', rend.sh.body_size * 0.85)
        recto = True
        c.drawCentredString(cx, g.m_bot - 2, folio)


# A division heading takes at least this many of its own entries with it. One
# left alone at the foot of a column sends the reader to the wrong list: the
# entries that open the next column read as if they belonged to it.
CONTENTS_KEEP = 2

# entry size/leading, then the heading's size, leading and the air above it
C_SIZE, C_LEAD = 8.3, 10.6
C_DIV_SIZE, C_DIV_LEAD, C_DIV_AIR = 7.6, 8.8, 6.4
C_HEAD_DROP = 30.0                # space the word CONTENTS takes off the top
C_INDENT = 5.0                    # entries hang inside their division
C_LEAD_GAP = 5.2                  # clear space each side of a dotted leader


def _leaders(c, x0, x1, y, anchor, size, step=4.6):
    """A dotted leader across the gap, on a grid anchored at `anchor`.

    Every row in a column shares the anchor, so the dots stand in vertical
    file instead of dancing with the length of each title.
    """
    if x1 - x0 < step * 1.5:
        return
    c.saveState()
    c.setFont('Gentium', size)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    x = anchor
    while x > x0:
        x -= step
        if x <= x1:
            c.drawString(x, y, '.')
    c.restoreState()


def _contents_columns(g, entries, ncol=2):
    """Split entries into per-page lists of `ncol` columns.

    Heights are measured the same way they are drawn, and a heading that
    would be stranded at a column foot is pushed forward with its entries.
    """
    def height(kind, at_top):
        if kind == 'div':
            return C_DIV_LEAD + (0.0 if at_top else C_DIV_AIR)
        return C_LEAD

    sheets, i = [], 0
    while i < len(entries):
        cap = g.text_top - g.text_bot - (C_HEAD_DROP if not sheets else 0.0)
        sheet = []
        while len(sheet) < ncol and i < len(entries):
            col, used = [], 0.0
            while i < len(entries):
                need = height(entries[i][0], not col)
                if col and used + need > cap:
                    break
                col.append(entries[i])
                used += need
                i += 1
            if i < len(entries):
                divs = [k for k, e in enumerate(col) if e[0] == 'div']
                # only push back if something is left in the column to hold it
                if divs and divs[-1] > 0 and len(col) - divs[-1] - 1 < CONTENTS_KEEP:
                    i -= len(col) - divs[-1]
                    col = col[:divs[-1]]
            sheet.append(col)
        sheets.append(sheet)
    return sheets


def check_front_matter(n):
    """The front matter must occupy an even number of pages.

    Body pages carry their own numbering from 1 and take their binding side
    from it, so page 1 has to fall on a recto. If the front matter runs to an
    odd count every leaf in the book is mirrored the wrong way and the gutter
    lands on the outer edge — the whole block prints into the spine.
    """
    if n % 2:
        raise SystemExit(
            f"front matter is {n} pages, an odd count: body page 1 would fall "
            f"on a verso and every gutter in the book would be on the wrong "
            f"side. Add a blank leaf to the front matter.")
    return n


def draw_contents(c, rend, toc, first_folio=None, first_page_no=1):
    """Table of contents; returns the number of pages drawn.

    `first_page_no` is the physical page the contents opens on. Its parity
    decides which side the binding is on: laid out as a recto on a verso, the
    text block sits over the gutter, which at this thickness is the one thing
    a print-on-demand preflight rejects.
    """
    g = rend.g
    entries = [(kind, label, idx + 1) for kind, label, idx in toc]
    sheets = _contents_columns(g, entries)
    num_w = pdfmetrics.stringWidth('000', 'Gentium', C_SIZE)

    for pi, sheet in enumerate(sheets):
        recto = (first_page_no + pi) % 2 == 1
        top = g.text_top
        cx = optical_centre(g, recto)
        if pi == 0:
            c.setFont('Gentium-Bd', 12.5)
            c.drawCentredString(cx, top - 6, 'CONTENTS')
            top -= C_HEAD_DROP
        for ci, col in enumerate(sheet):
            x = g.col_x(recto, ci)
            right = x + g.col_w
            y = top
            for n, (kind, label, pno) in enumerate(col):
                if kind == 'div':
                    if n:                       # never indent the column top
                        y -= C_DIV_AIR
                    c.setFillColorRGB(0.25, 0.25, 0.25)
                    rend.small_caps(c, label, x, y, C_DIV_SIZE, 'Gentium-Bd')
                    c.setFillColorRGB(0, 0, 0)
                    y -= C_DIV_LEAD
                else:
                    num = str(pno)
                    c.setFont('Gentium', C_SIZE)
                    c.drawString(x + C_INDENT, y, label)
                    c.drawRightString(right, y, num)
                    lx = x + C_INDENT + pdfmetrics.stringWidth(
                        label, 'Gentium', C_SIZE)
                    _leaders(c, lx + C_LEAD_GAP, right - num_w - C_LEAD_GAP,
                             y, right - num_w, C_SIZE)
                    y -= C_LEAD
        if first_folio is not None:
            c.setFont('Gentium', rend.sh.body_size * 0.85)
            c.drawCentredString(cx, g.m_bot - 2, roman(first_folio + pi))
        if pi < len(sheets) - 1:
            c.showPage()
    return len(sheets)


# The title page identity. The text as printed differs from the World English
# Bible (see corrections.py), so per the publisher's request it carries its own
# name and credits the WEB as its source rather than claiming to be it.
EDITION_NAME = 'The Lampstand Apocrypha'
EDITION_SUBTITLE = ''


def applied_corrections():
    """Which corrections actually occur in the books being printed.

    The notice must describe this volume, not the project: a correction to a
    book that is not printed here has no business on its copyright page.
    """
    import re as _re
    from .corrections import BOOK_TITLES
    files = source_files()
    raw = []
    for bid in canon.ORDER:
        if bid in files:
            raw.append(open(files[bid], encoding='utf-8').read())
    text = '\n'.join(raw)
    words = set(w.lower() for w in _re.findall(r"[A-Za-z]+", text))
    spell = {a: b for a, b in sorted(WORD_FIXES.items()) if a.lower() in words}
    names = {a: b for a, b in sorted(NAME_FIXES.items()) if a.lower() in words}
    titles = [b for b in BOOK_TITLES if b in canon.ORDER]
    return spell, names, titles


def edition_notice():
    import textwrap
    spell, names, titles = applied_corrections()
    lines = [
        'THIS EDITION',
        '',
        'The text is that of the World English Bible (Updated), which its',
        'publishers dedicated to the public domain. Eighteen books are set',
        'here: first those received as canonical by the Catholic and Orthodox',
        'churches, then the wider apocrypha preserved alongside them. The',
        'translators’ footnotes and cross-references are kept throughout.',
        '',
        'The portions that apocrypha in the King James tradition print under',
        'their own titles are set that way here. The Rest of Esther, the',
        'Epistle of Jeremiah, the Song of the Three Holy Children, Susanna,',
        'and Bel and the Dragon stand as books rather than lying buried in',
        'Greek Esther, Baruch and Greek Daniel. Their verse numbers are left',
        'as the source gives them, so a reference still points where it',
        'always did, and no protocanonical text is printed: the Hebrew of',
        'Esther and of Daniel is not here.',
        '',
    ]
    if titles:
        lines += ['Book titles as received have been corrected:', '']
        for book, was, now in manifest():
            lines.append(f'    {book:<16}“{was}”  →  “{now}”')
        lines.append('')
    if spell:
        lines += [
            'Spelling has been made consistently American where the source',
            'varied from itself, the American form being the one it uses',
            'elsewhere:',
            '',
        ]
        pairs = ', '.join(f'{a} → {b}' for a, b in spell.items())
        lines += ['    ' + w for w in textwrap.wrap(pairs + '.', 62)]
        lines.append('')
    if names:
        lines += [
            'Proper names follow American practice, the Latin digraph',
            'simplified: ' + ', '.join(sorted(names.values())[:6]) + ' and',
            'others. Names ending -aeus keep the spelling American Bibles',
            'give them, and Hebrew names in -ael (Ishmael, Raphael) are',
            'untouched, as are words that merely look British: Tyre the city,',
            'spelt the grain, smelt the ore, the burnt offering.',
            '',
        ]
    lines += [
        'Because the printed text differs from the text as received, this',
        'edition is not called the World English Bible, a trademark of',
        'eBible.org. Beyond the corrections above, nothing has been altered.',
        '',
        'The World English Bible is in the public domain and may be freely',
        'copied, printed, sold and given away, and so may this edition.',
        '',
        'Source text: engwebu, obtained from eBible.org.',
        'Set in Gentium Plus by SIL International (SIL Open Font License);',
        'Hebrew in Noto Serif Hebrew.',
    ]
    return lines


def render_pdf(out_path, book_ids=None, title_note=None, body=8.0, leading=9.6,
               trim='5.5x8.5'):
    register_fonts()
    rend = Renderer(body, leading, trim)
    files = source_files()
    ids = book_ids or canon.ORDER
    print(f"paginating {len(ids)} books...", file=sys.stderr)
    pages, toc = build_pages(rend, ids, files)
    g = rend.g

    c = rl_canvas.Canvas(out_path, pagesize=(g.page_w, g.page_h))
    c.setTitle(EDITION_NAME + (f' — {EDITION_SUBTITLE}' if EDITION_SUBTITLE else ''))
    c.setSubject('Public Domain; text of the World English Bible (Updated)')

    # --- front matter (roman folios)
    fm = 1
    draw_front(c, rend, 'halftitle', None, None); c.showPage(); fm += 1
    c.showPage(); fm += 1                                   # blank verso
    draw_front(c, rend, 'title', None, None); c.showPage(); fm += 1
    fm += draw_notice(c, rend, edition_notice(), fm)
    c.showPage()
    n = draw_contents(c, rend, toc, fm, fm)
    fm += n
    c.showPage()
    # The body numbers itself from 1 and draws its gutter from that number, so
    # the front matter has to end on a verso or every leaf after it is mirrored
    # the wrong way round. See check_front_matter().
    check_front_matter(fm - 1)

    # --- body
    for p in pages:
        if p.kind == 'body':
            draw_body_page(c, rend, p)
        elif p.kind == 'part':
            draw_part_page(c, rend, p)
        c.showPage()
    c.save()
    return len(pages), len(pages) + 4 + n
