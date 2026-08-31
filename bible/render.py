"""Builds placeable items from parsed books and draws pages to a PDF canvas."""
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

from .usfm import Verse, Chapter, Text, Note
from .typeset import Sheet, Typesetter, Atom, Line, PARA_GEOM
from .layout import Geom, Item, Packer
from . import canon
from .corrections import book_title

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')

HEBREW = range(0x0590, 0x0600)


def register_fonts():
    faces = {
        'Gentium':      'GentiumPlus-Regular.ttf',
        'Gentium-It':   'GentiumPlus-Italic.ttf',
        'Gentium-Bd':   'GentiumPlus-Bold.ttf',
        'Gentium-BdIt': 'GentiumPlus-BoldItalic.ttf',
    }
    for name, fn in faces.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fn)))
    # Gentium has no Hebrew; fall back to a system serif that does.
    for cand in ('/usr/share/fonts/truetype/noto/NotoSerifHebrew-Regular.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
                 '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'):
        if os.path.exists(cand):
            pdfmetrics.registerFont(TTFont('Hebrew', cand))
            return cand
    return None


def is_hebrew(s):
    return any(ord(c) in HEBREW for c in s)


def shape_hebrew(s):
    """Reverse an isolated RTL run, keeping combining marks after their base."""
    import unicodedata
    clusters, cur = [], ''
    for ch in s:
        if unicodedata.combining(ch):
            cur += ch
        else:
            if cur:
                clusters.append(cur)
            cur = ch
    if cur:
        clusters.append(cur)
    return ''.join(reversed(clusters))


def sc_runs(text, size):
    """Split a divine name into (text, size) runs: cap-height initial, small caps rest."""
    i = len(text)
    while i > 0 and not text[i - 1].isupper():
        i -= 1
    caps, tail = text[:i], text[i:]
    runs = []
    if caps:
        runs.append((caps[0], size))
        if caps[1:]:
            runs.append((caps[1:], size * 0.80))
    if tail:
        runs.append((tail, size))
    return runs


class Renderer:
    def __init__(self, body=8.0, leading=9.6, trim='5.5x8.5'):
        self.g = Geom(trim)
        self.sh = Sheet(body, leading)
        self.leading = leading
        self.ts = Typesetter(self.sh, self.width)
        self._note_cache = {}
        self.packer = Packer(self.g, self.note_block_height, leading * 0.80)

    # --- metrics ---------------------------------------------------------
    def width(self, text, style):
        st = self.sh[style]
        if is_hebrew(text):
            return pdfmetrics.stringWidth(text, 'Hebrew', st.size)
        if style == 'sc':
            return sum(pdfmetrics.stringWidth(t, st.font, sz)
                       for t, sz in sc_runs(text, st.size))
        return pdfmetrics.stringWidth(text, st.font, st.size)

    # --- footnotes -------------------------------------------------------
    def note_lines(self, note):
        """Wrap one note into lines of (atoms). Cached by identity."""
        key = id(note)
        if key in self._note_cache:
            return self._note_cache[key]
        atoms = [Atom('§', 'notemk', self.ts.notemk_w)]
        atoms[-1].space_after = self.width(' ', 'note') * 0.5
        if note.ref:
            atoms.append(Atom(note.ref, 'notebd', self.width(note.ref, 'notebd')))
            atoms[-1].space_after = self.width(' ', 'note')
        for kind, txt in note.parts:
            style = 'noteit' if kind in ('fq', 'fqa', 'fl', 'xt', 'fk') else 'note'
            words = txt.split(' ')
            for i, wd in enumerate(words):
                if not wd:
                    continue
                atoms.append(Atom(wd, style, self.width(wd, style)))
                atoms[-1].space_after = self.width(' ', style)
            if atoms:
                atoms[-1].space_after = self.width(' ', 'note')
        if atoms:
            atoms[-1].space_after = 0.0
        geom = (0.0, 0.0, 0.7, 0.0)
        saved = self.sh.body_size
        lines = self.ts.break_lines(atoms, self.g.col_w, geom,
                                    self.leading * 0.80)
        self._note_cache[key] = lines
        return lines

    def note_block_height(self, notes):
        if not notes:
            return 0.0
        h = self.packer.rule_gap + 3.0
        for nt in notes:
            h += len(self.note_lines(nt)) * self.leading * 0.80
        return h + 2.0

    # --- building items from a parsed book -------------------------------
    def book_items(self, book, name):
        em = self.sh.body_size
        items = []
        single_chapter = sum(1 for b in book.blocks if b.style == 'c') <= 1
        # the Apostolic Fathers are divided into chapters but carry no verse
        # numbers, so their running heads name the chapter only
        has_verses = any(isinstance(i, Verse)
                         for b in book.blocks for i in b.items)
        is_psalms = book.id == 'PSA'
        ref_state = {'c': '1', 'v': '1'}
        pending_drop = None
        first_para_of_chapter = False

        def add_lines(lines, keep_first=0, align='body'):
            for k, ln in enumerate(lines):
                items.append(Item('line', line=ln, height=ln.height,
                                  align=align, ref=ln.first_ref,
                                  keep_next=max(0, keep_first - k)))

        def centered(text, style, space_before, space_after, keep=5, notes=()):
            if space_before:
                items.append(Item('space', height=space_before))
            rows = self._wrap_centered(text, style)
            h = self.leading * 1.15
            for k, row in enumerate(rows):
                carry = list(notes) if k == len(rows) - 1 else []
                for nt in carry:
                    row = row + [Atom('¤', 'mark', self.ts.mark_w,
                                      note=nt, nobreak=True, tight=True)]
                ln = Line(row, 0.0, False, h, notes=carry)
                items.append(Item('line', line=ln, height=h, align='center',
                                  keep_next=keep if k == 0 else 0))
            if space_after:
                items.append(Item('space', height=space_after))

        # -- book title
        items.append(Item('space', height=self.leading * 0.6, book_start=True))
        title = book_title(book.id, book.toc1 or name)
        for part in self._wrap_centered(title, 'psalm'):
            ln = Line(part, 0.0, False, self.leading * 1.35)
            items.append(Item('line', line=ln, height=self.leading * 1.35,
                              align='center', keep_next=4))
        items.append(Item('space', height=self.leading * 0.9))

        for blk in book.blocks:
            st = blk.style
            if st == 'c':
                ref_state['c'] = blk.items[0].num
                ref_state['v'] = '1'
                if is_psalms:
                    centered('PSALM ' + ref_state['c'], 'psalm',
                             self.leading * 0.9, self.leading * 0.35)
                elif not single_chapter:
                    pending_drop = ref_state['c']
                first_para_of_chapter = True
                continue
            if st == 'b':
                items.append(Item('space', height=self.leading * 0.45))
                continue
            if st in ('ms1', 'ms2', 's1', 's2', 'is1'):
                txt = ''.join(i.s for i in blk.items if isinstance(i, Text)).strip()
                heads = [i for i in blk.items if isinstance(i, Note)]
                if txt:
                    big = st.startswith('ms')
                    centered(txt, 'sect' if not big else 'psalm',
                             self.leading * (1.0 if big else 0.7),
                             self.leading * 0.35, notes=heads)
                continue
            if st == 'cl':
                continue

            geom = PARA_GEOM.get(st, PARA_GEOM['p'])
            atoms = self.ts.atoms(blk.items, ref_state)
            if not atoms:
                continue
            # the chapter drop cap swallows the verse-1 number
            drop = None
            if pending_drop and first_para_of_chapter:
                if atoms and atoms[0].style == 'v' and atoms[0].text == '1':
                    atoms = atoms[1:]
                size = self.leading * 2 * 0.80
                dw = pdfmetrics.stringWidth(pending_drop, 'Gentium-Bd', size) + 3.2
                drop = (dw, 2)
                geom = (0.0,) + tuple(geom[1:])      # drop cap replaces the indent
            if st in ('d', 'sp'):
                for a in atoms:
                    if a.style == 'txt':
                        a.style = 'it'
                        a.width = self.width(a.text, 'it')
            lead = self.leading
            if geom[3]:
                items.append(Item('space', height=self.leading * geom[3]))
            # verse lines of poetry are set ragged right, never justified
            ragged = st[0] == 'q' or st in ('d', 'sp')
            lines = self.ts.break_lines(atoms, self.g.col_w, geom, lead,
                                        drop_indent=drop, ragged=ragged)
            if drop:
                add_lines(lines, keep_first=2)
                head = items[len(items) - len(lines)]
                head.drop = (pending_drop, size, 2)
                head.ref = head.ref or (ref_state['c'],
                                        '1' if has_verses else None)
                pending_drop = None
            else:
                add_lines(lines, keep_first=1 if st.startswith('q') else 0)
            first_para_of_chapter = False
        return items

    def _wrap_centered(self, text, style):
        """Break a title into centered lines of atoms."""
        words = text.split()
        out, cur, cw = [], [], 0.0
        sp = self.width(' ', style)
        for wd in words:
            w = self.width(wd, style)
            if cur and cw + sp + w > self.g.col_w:
                out.append(cur)
                cur, cw = [], 0.0
            a = Atom(wd, style, w)
            a.space_after = sp
            cur.append(a)
            cw += (sp if cw else 0) + w
        if cur:
            cur[-1].space_after = 0.0
            out.append(cur)
        for ln in out:
            ln[-1].space_after = 0.0
        return out

    # --- drawing ---------------------------------------------------------
    def draw_atoms(self, c, atoms, x, y, avail, justify, align='body'):
        natural = 0.0
        for k, a in enumerate(atoms):
            natural += a.width + (a.space_after if k < len(atoms) - 1 else 0.0)
        gaps = [k for k in range(len(atoms) - 1) if atoms[k].space_after > 0]
        extra = 0.0
        if justify and gaps and natural < avail:
            extra = (avail - natural) / len(gaps)
            if extra > self.width(' ', 'txt') * 2.6:      # too loose: leave ragged
                extra = 0.0
        if align == 'center':
            x += max(0.0, (avail - natural) / 2.0)
        cx = x
        for k, a in enumerate(atoms):
            st = self.sh[a.style]
            if a.style == 'sc':
                sx = cx
                for t, sz in sc_runs(a.text, st.size):
                    c.setFont(st.font, sz)
                    c.drawString(sx, y + st.rise, t)
                    sx += pdfmetrics.stringWidth(t, st.font, sz)
            else:
                font = 'Hebrew' if is_hebrew(a.text) else st.font
                txt = shape_hebrew(a.text) if is_hebrew(a.text) else a.text
                c.setFont(font, st.size)
                c.drawString(cx, y + st.rise, txt)
            cx += a.width
            if k < len(atoms) - 1:
                cx += a.space_after + (extra if a.space_after > 0 else 0.0)
        return cx

    def draw_column(self, c, col, x, top, marks):
        """Draw one packed column. `marks` maps id(note) -> marker letter."""
        y = top - self.leading * 0.78
        pending_drop = None
        drop_lines = 0
        for it in col.items:
            if it.kind == 'space':
                y -= it.height
                continue
            ln = it.line
            if it.drop:
                pending_drop = it.drop
                drop_lines = 0
            # substitute real marker letters for the placeholder
            for a in ln.atoms:
                if a.note is not None:
                    a.text = marks.get(id(a.note), '*')
                    a.width = self.ts.mark_w
            self.draw_atoms(c, ln.atoms, x + ln.indent, y,
                            self.g.col_w - ln.indent, ln.justify, it.align)
            if pending_drop is not None:
                drop_lines += 1
                if drop_lines == 2:
                    num, size, _ = pending_drop
                    c.setFont('Gentium-Bd', size)
                    c.drawString(x, y, num)
                    pending_drop = None
            y -= ln.height
        # footnotes, anchored to the foot of the column
        if col.notes:
            h = self.note_block_height(col.notes)
            ry = self.g.text_bot + h - self.packer.rule_gap
            c.setStrokeColorRGB(0.45, 0.45, 0.45)
            c.setLineWidth(0.35)
            c.line(x, ry, x + self.g.col_w * 0.38, ry)
            ny = ry - self.packer.rule_gap - self.leading * 0.62
            for nt in col.notes:
                for ln in self.note_lines(nt):
                    for a in ln.atoms:
                        if a.style == 'notemk':
                            a.text = marks.get(id(nt), '*')
                            a.width = self.ts.notemk_w
                    self.draw_atoms(c, ln.atoms, x + ln.indent, ny,
                                    self.g.col_w - ln.indent, False)
                    ny -= self.leading * 0.80

    def small_caps(self, c, text, x, y, size, font='Gentium', align='left'):
        """Fake small caps: caps at full size, lowercase as reduced caps."""
        runs, cur, up = [], '', None
        for ch in text:
            u = ch.isupper() or not ch.isalpha()
            if up is None or u == up:
                cur += ch
            else:
                runs.append((cur, up))
                cur = ch
            up = u
        if cur:
            runs.append((cur, up))
        total = sum(pdfmetrics.stringWidth(t.upper(), font,
                                           size if u else size * 0.82)
                    for t, u in runs)
        if align == 'right':
            x -= total
        for t, u in runs:
            s = size if u else size * 0.82
            c.setFont(font, s)
            c.drawString(x, y, t.upper())
            x += pdfmetrics.stringWidth(t.upper(), font, s)
        return total
