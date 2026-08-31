"""Page geometry, column packing with bottom-of-column footnotes, and drawing."""
from dataclasses import dataclass, field

from .typeset import Line, Atom

PT = 1.0
IN = 72.0


# Named trim sizes: (width, height, top, bottom, inner/gutter, outer) in inches
TRIMS = {
    '5.5x8.5': (5.5, 8.5, 0.47, 0.52, 1.00, 0.35),
    '6x9':     (6.0, 9.0, 0.55, 0.60, 0.70, 0.50),
}


class Geom:
    """Mirrored margins with a binding gutter, sized to a named trim."""
    head_gap = 13.0
    col_gap = 13.0

    def __init__(self, trim='5.5x8.5'):
        w, h, mt, mb, mi, mo = TRIMS[trim]
        self.trim = trim
        self.page_w, self.page_h = w * IN, h * IN
        self.m_top, self.m_bot = mt * IN, mb * IN
        self.m_in, self.m_out = mi * IN, mo * IN
        self.text_w = self.page_w - self.m_in - self.m_out
        self.col_w = (self.text_w - self.col_gap) / 2.0
        self.text_top = self.page_h - self.m_top - self.head_gap
        self.text_bot = self.m_bot
        self.col_h = self.text_top - self.text_bot

    def left_margin(self, recto: bool) -> float:
        return self.m_in if recto else self.m_out

    def col_x(self, recto: bool, col: int) -> float:
        return self.left_margin(recto) + col * (self.col_w + self.col_gap)


# --- placeable items ------------------------------------------------------

@dataclass
class Item:
    """One thing that can sit in a column."""
    kind: str                  # 'line' | 'space' | 'rule' | 'drop'
    line: Line = None
    height: float = 0.0
    keep_next: int = 0         # lines that must follow in the same column
    drop: tuple = None         # (chapter_number, size, n_lines) drop cap
    align: str = 'body'        # 'body' | 'center'
    ref: tuple = None          # (chapter, verse) for running heads
    book_start: bool = False


@dataclass
class Column:
    items: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    height: float = 0.0


class Packer:
    """Fills columns, reserving bottom space for the footnotes they contain."""

    def __init__(self, geom: Geom, note_h_fn, note_leading, rule_gap=4.5):
        self.g = geom
        self.note_h = note_h_fn        # [Note] -> total height of the block
        self.note_leading = note_leading
        self.rule_gap = rule_gap

    def pack(self, items):
        """Greedily split `items` into columns. Returns [Column]."""
        cols, i, n = [], 0, len(items)
        while i < n:
            col, used, notes = [], 0.0, []
            j = i
            while j < n:
                it = items[j]
                if it.kind == 'space' and not col:
                    j += 1                      # never open a column with space
                    i = j
                    continue
                new_notes = notes + [nt for nt in (it.line.notes if it.line else [])]
                reserve = self.note_h(new_notes)
                if used + it.height + reserve > self.g.col_h and col:
                    break
                col.append(it)
                used += it.height
                notes = new_notes
                j += 1
            if not col:                          # single oversized item
                col, j = [items[i]], i + 1
                notes = list(items[i].line.notes) if items[i].line else []
            # honour keep-together: pull trailing orphans forward
            if j < n:
                back = 0
                while (len(col) - back) > 1:
                    tail = col[len(col) - back - 1]
                    need = tail.keep_next
                    if need and (back < need):
                        back += 1
                    else:
                        break
                if back:
                    for it in col[len(col) - back:]:
                        for nt in (it.line.notes if it.line else []):
                            if nt in notes:
                                notes.remove(nt)
                    col = col[:len(col) - back]
                    j -= back
                # never end a column with trailing space/rule
                while col and col[-1].kind == 'space':
                    col.pop()
                    j -= 1
            cols.append(Column(col, notes, sum(x.height for x in col)))
            i = j
        return cols
