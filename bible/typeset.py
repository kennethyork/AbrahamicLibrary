"""A small line-breaking / column-filling typesetter for the Bible text.

ReportLab's Paragraph flowable cannot express bottom-of-column footnotes whose
height depends on which lines land in the column, so we do our own line
breaking. Text is reduced to styled atoms, atoms to justified lines, and lines
are packed into columns while footnote space is reserved iteratively.
"""
from dataclasses import dataclass, field
import pyphen

from .usfm import Verse, Chapter, Text, Note

HYPHEN = pyphen.Pyphen(lang='en_US')


# --- styles ---------------------------------------------------------------

@dataclass
class Style:
    font: str
    size: float
    rise: float = 0.0


class Sheet:
    """Named text styles, all sizes in points."""
    def __init__(self, body=8.0, leading=9.6):
        self.body_size, self.leading = body, leading
        n = 'Gentium'
        self.s = {
            'txt':    Style(n,            body),
            'sc':     Style(n,            body),   # divine name, drawn small-caps
            'wj':     Style(n,            body),
            'it':     Style(n + '-It',    body),
            'v':      Style(n + '-Bd',    body * 0.66, body * 0.40),
            'mark':   Style(n,            body * 0.66, body * 0.40),
            'note':   Style(n,            body * 0.78),
            'noteit': Style(n + '-It',    body * 0.78),
            'notebd': Style(n + '-Bd',    body * 0.78),
            'notemk': Style(n,            body * 0.55, body * 0.32),
            'head':   Style(n + '-Bd',    body * 0.85),
            'chap':   Style(n + '-Bd',    body * 2.05),
            'psalm':  Style(n + '-Bd',    body * 1.05),
            'sect':   Style(n + '-Bd',    body * 0.95),
            'desc':   Style(n + '-It',    body * 0.92),
        }

    def __getitem__(self, k):
        return self.s[k]


# --- atoms ----------------------------------------------------------------

@dataclass
class Atom:
    text: str
    style: str
    width: float = 0.0
    space_after: float = 0.0   # width of the following breakable space, 0 = none
    note: object = None        # Note attached at this point
    nobreak: bool = False      # may not start a line (note markers, punctuation)
    tight: bool = False        # closes up: no space between it and the word before
    soft: bool = False         # a hyphen this typesetter inserted, not the author's


@dataclass
class Line:
    atoms: list
    indent: float
    justify: bool
    height: float
    notes: list = field(default_factory=list)
    first_ref: tuple = None    # (chapter, verse) first reference on the line
    natural: float = 0.0       # natural width, excluding trailing space


# --- paragraph geometry ---------------------------------------------------

# style -> (first-line indent, left indent, runover extra indent, space before)
PARA_GEOM = {
    'p':   (0.9, 0.0, 0.0, 0.0),
    'm':   (0.0, 0.0, 0.0, 0.0),
    'nb':  (0.0, 0.0, 0.0, 0.0),
    'pc':  (0.0, 0.0, 0.0, 0.0),
    'pi1': (0.9, 1.2, 0.0, 0.0),
    'mi':  (0.0, 1.2, 0.0, 0.0),
    'li1': (0.0, 1.2, 0.6, 0.0),
    'q1':  (0.0, 1.1, 1.4, 0.0),
    'q2':  (0.0, 2.2, 1.4, 0.0),
    'q3':  (0.0, 3.3, 1.4, 0.0),
    'q4':  (0.0, 4.4, 1.4, 0.0),
    'qc':  (0.0, 0.0, 1.4, 0.0),
    'd':   (0.0, 0.6, 0.6, 0.25),
    'sp':  (0.0, 0.0, 0.0, 0.35),
    'ip':  (0.9, 0.0, 0.0, 0.0),
}


# --- atom building --------------------------------------------------------

def _split_divine(s):
    """Yield (text, is_divine_name) segments split on the parser's sentinels."""
    out, i = [], 0
    while True:
        a = s.find('\x01', i)
        if a < 0:
            if s[i:]:
                out.append((s[i:], False))
            return out
        if s[i:a]:
            out.append((s[i:a], False))
        b = s.find('\x02', a)
        if b < 0:
            out.append((s[a + 1:], True))
            return out
        out.append((s[a + 1:b], True))
        i = b + 1


# Punctuation that closes up against the preceding word (no space before it).
_TIGHT_LEAD = set('.,;:!?)]}’”…')
# Characters that must not begin a line, but keep whatever space precedes them.
_NOBREAK_LEAD = _TIGHT_LEAD | set('-–—')


class Typesetter:
    MARKERS = 'abcdefghijklmnopqrstuvwxyz*'

    def __init__(self, sheet: Sheet, width_fn):
        self.sh = sheet
        self.w = width_fn                      # (text, style_name) -> points
        # The real footnote letter is only known after pagination, so reserve
        # the widest one; anything narrower simply leaves a hair more space.
        self.mark_w = max(self.w(ch, 'mark') for ch in self.MARKERS)
        self.notemk_w = max(self.w(ch, 'notemk') for ch in self.MARKERS)

    def atoms(self, items, ref_state):
        """Turn inline items into a list of Atom, splitting text into words."""
        out = []
        space_w = self.w(' ', 'txt')

        def push(text, style, note=None, nobreak=False, tight=False):
            out.append(Atom(text, style, self.w(text, style),
                            note=note, nobreak=nobreak, tight=tight))

        for it in items:
            if isinstance(it, Verse):
                ref_state['v'] = it.num
                # A verse marker opens a new USFM line, so the preceding text
                # carries no trailing space; the number needs one before it.
                if out and out[-1].space_after == 0.0 and out[-1].style != 'v':
                    out[-1].space_after = space_w
                # verse number rides ahead of the next word
                push(it.num, 'v', nobreak=False)
                out[-1].space_after = space_w * 0.42
                out[-1].ref = (ref_state['c'], it.num)
            elif isinstance(it, Note):
                # marker attaches to the previous word, never starts a line
                push('¤', 'mark', note=it, nobreak=True, tight=True)
                out[-1].width = self.mark_w
            elif isinstance(it, Text):
                base = 'it' if it.italic else ('wj' if it.wj else 'txt')
                # \x01..\x02 wraps the divine name, which is set in small caps
                for seg, sc in _split_divine(it.s):
                    style = 'sc' if sc else base
                    parts = seg.split(' ')
                    for i, wtext in enumerate(parts):
                        if wtext == '':
                            # a leading/trailing space still separates atoms
                            if out:
                                out[-1].space_after = space_w
                            continue
                        ch = wtext[0]
                        if wtext[:2] == '..':      # an ellipsis, not punctuation
                            ch = ''
                        if ch in _TIGHT_LEAD and out:
                            out[-1].space_after = 0.0
                        push(wtext, style, nobreak=ch in _NOBREAK_LEAD,
                             tight=ch in _TIGHT_LEAD)
                        if i < len(parts) - 1:
                            out[-1].space_after = space_w
        # collapse: an atom that closes up takes no space before it. A dash may
        # not start a line, but it keeps whatever space the source put there.
        for i in range(len(out) - 1):
            if out[i + 1].tight:
                out[i].space_after = 0.0
        return out

    # --- line breaking ----------------------------------------------------

    def break_lines(self, atoms, col_w, geom, leading, drop_indent=None,
                    ragged=False):
        """Greedy first-fit with hyphenation. Returns [Line].

        `drop_indent` = (extra_left, n_lines) reserves room for a drop cap on
        the first n_lines lines. `ragged` leaves the right edge unjustified,
        which is how verse lines of poetry are set.
        """
        em = self.sh.body_size
        first_in, left_in, run_in, _ = geom
        lines, i, n = [], 0, len(atoms)
        line_no = 0
        while i < n:
            indent = left_in * em + (first_in * em if line_no == 0 else run_in * em)
            if drop_indent and line_no < drop_indent[1]:
                indent += drop_indent[0]
            avail = col_w - indent
            cur, cur_w, j = [], 0.0, i
            last_break = -1          # index in cur after which we may break
            while j < n:
                a = atoms[j]
                add = a.width if not cur else a.width
                gap = cur[-1].space_after if cur else 0.0
                if cur_w + gap + add <= avail or not cur:
                    cur.append(a)
                    cur_w += gap + add
                    j += 1
                    if a.space_after > 0 and not (j < n and atoms[j].nobreak):
                        last_break = len(cur)
                else:
                    break
            if j < n and last_break > 0 and last_break < len(cur):
                # retreat to the last legal break point
                j -= (len(cur) - last_break)
                cur = cur[:last_break]
                cur_w = self._natural(cur)
            elif j < n and last_break <= 0 and len(cur) > 1:
                pass
            # try hyphenating the next word into the remaining space
            if j < n and cur:
                cur, cur_w, j = self._try_hyphen(atoms, cur, cur_w, j, avail)
            if not cur:                       # pathological: force one atom
                cur, j = [atoms[i]], i + 1
                cur_w = atoms[i].width
            notes = [a.note for a in cur if a.note is not None]
            first_ref = next((getattr(a, 'ref', None) for a in cur
                              if getattr(a, 'ref', None)), None)
            lines.append(Line(cur, indent, justify=(j < n and not ragged),
                              height=leading,
                              notes=notes, first_ref=first_ref,
                              natural=self._natural(cur)))
            i = j
            line_no += 1
            while i < n and atoms[i].text == '':
                i += 1
        if lines:
            lines[-1].justify = False
        return lines

    def _natural(self, cur):
        w = 0.0
        for k, a in enumerate(cur):
            w += a.width
            if k < len(cur) - 1:
                w += a.space_after
        return w

    def _try_hyphen(self, atoms, cur, cur_w, j, avail):
        """Split atoms[j] with a hyphen if a useful piece fits."""
        a = atoms[j]
        if a.style in ('v', 'mark') or len(a.text) < 6 or not a.text[0].isalpha():
            return cur, cur_w, j
        core = a.text.rstrip('.,;:!?)”’—')
        tail = a.text[len(core):]
        if len(core) < 6 or not core.isalpha():
            return cur, cur_w, j
        gap = cur[-1].space_after if cur else 0.0
        room = avail - cur_w - gap
        pieces = HYPHEN.inserted(core, '­').split('­')
        if len(pieces) < 2:
            return cur, cur_w, j
        head = ''
        for k in range(len(pieces) - 1):
            cand = ''.join(pieces[:k + 1])
            if len(cand) < 2 or len(core) - len(cand) < 3:
                continue
            if self.w(cand + '-', a.style) <= room:
                head = cand
            else:
                break
        if not head:
            return cur, cur_w, j
        rest = core[len(head):] + tail
        first = Atom(head + '-', a.style, self.w(head + '-', a.style))
        first.soft = True          # inserted here, so it can be undone exactly
        second = Atom(rest, a.style, self.w(rest, a.style),
                      space_after=a.space_after, note=a.note)
        if hasattr(a, 'ref'):
            second.ref = a.ref
        atoms[j] = second
        cur = cur + [first]
        return cur, cur_w + gap + first.width, j
