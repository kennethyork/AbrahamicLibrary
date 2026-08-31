"""Reader for the pseudepigrapha in The Forgotten Books of Eden (1926).

Source: Rutherford H. Platt Jr.'s 1926 collection, which reprints earlier
translations that were themselves already public domain — Rendel Harris for
the Psalms and Odes of Solomon, Charles for the Testaments, Morfill and
Charles for 2 Enoch. Published 1926, so public domain in the United States.

The Fourth Book of Maccabees is in the collection and is passed over here:
this volume already prints it among the wider apocrypha, from the World
English Bible, which is the better text.

The file is a transcription rather than a page scan, so it is far cleaner
than the scholarly editions of the same works. What it does carry is a
systematic substitution of the pipe character for a capital I, page markers,
and a repeated attribution line, all of which are removed on load.

Each work opens with Platt's own 1926 editorial introduction. Those are not
printed: the other divisions of this book give the ancient text without a
modern editor's preface, and this one should match them.
"""
import re

from .usfm import Book, Block, Verse, Chapter, Text
from .corrections import (fix_text, americanize, modernize, resyntax,
                          resentence)

ROMAN = r'[IVXLC]+'
_VAL = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}


def _norm(s):
    # resyntax runs last as well as inside fix_text: modernize creates new
    # archaic constructions as it goes (didst bring -> did bring), and those
    # must be re-examined afterwards.
    return resentence(resyntax(modernize(americanize(fix_text(s)))))


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _roman(r):
    n = 0
    for i, ch in enumerate(r):
        v = _VAL[ch]
        n += -v if i + 1 < len(r) and _VAL[r[i + 1]] > v else v
    return n


def _deroman(s):
    """Repair a numeral the transcription damaged.

    Two faults run through them: a lower-case l stands for I (XIl for XII),
    and a lower-case letter appears where a capital belongs (XxXIll, LXxXI,
    Vi, Lil). The l is resolved before the rest is folded up, or it would
    become an L and change the value.
    """
    return s.replace('l', 'I').upper()


# (heading that opens the work, running head, printed title, division style)
#   chap  -> CHAP. I. / CHAPTER I.       roman -> a bare numeral on its own line
#   ode   -> ODE 1.
# `verse` is True where the source numbers verses, False for the poetry, which
# is set line for line.
WORKS = [
    (r'^THE FIRST BOOK OF\s*$', 'Adam and Eve I',
     'The First Book of Adam and Eve', 'chap', True),
    (r'^THE SECOND BOOK OF\s*$', 'Adam and Eve II',
     'The Second Book of Adam and Eve', 'chap', True),
    (r'^THE BOOK OF THE SECRETS OF ENOCH', '2 Enoch',
     'The Book of the Secrets of Enoch', 'roman', True),
    (r'^THE PSALMS OF SOLOMON\s*$', 'Psalms of Solomon',
     'The Psalms of Solomon', 'roman', False),
    (r'^THE ODES OF SOLOMON', 'Odes of Solomon',
     'The Odes of Solomon', 'ode', False),
    (r'^THE LETTER OF ARISTEAS\s*$', 'Aristeas',
     'The Letter of Aristeas', 'chap', True),
    (r'^FOURTH BOOK OF MACCABEES\s*$', None, None, None, None),   # boundary only
    (r'^THE STORY OF AHIKAR\s*$', 'Ahikar',
     'The Story of Ahikar', 'chap', True),
]

IDS = {
    'Adam and Eve I': 'AE1', 'Adam and Eve II': 'AE2', '2 Enoch': 'EN2',
    'Psalms of Solomon': 'PSA', 'Odes of Solomon': 'ODS',
    'Aristeas': 'ARI', 'Ahikar': 'AHI',
}

TESTAMENTS = ['REUBEN', 'SIMEON', 'LEVI', 'JUDAH', 'ISSACHAR', 'ZEBULUN',
              'DAN', 'NAPHTALI', 'GAD', 'ASHER', 'JOSEPH', 'BENJAMIN']

# Debris from the web transcription this file was taken from. The page
# markers appear in two forms, because the opening bracket is sometimes read
# as a capital I; the angle-bracket tags and the caption text are the page's
# own furniture rather than anything in the 1926 book.
_BOILER = re.compile(r'The Forgotten Books of Eden.*?sacred-texts\.com\s*|'
                     r'\(?See [Pp]age\s*<page\s*\d+>\)?\s*|'
                     r'<page\s*\d+>\s*|'
                     r'Click to enlarge\s*|'
                     r'\(See page\s*\d+\s*et seq\.?\)\s*|'
                     r'[\[I]p\.\s*[0-9ivxlc]+\]\s*|'
                     r'et seq\.\)\s*')

# Captions belonging to the 1926 volume's illustration plates. They sit on
# their own lines in the middle of the text, so nothing distinguishes them
# from the words around them except that they name a picture. Listed rather
# than matched by shape, because a rule for short capitalized lines would
# also take the chapter headings.
_PLATES = {
    'FACSIMILE OF ACTUAL PAGE OF ORIGINAL GUTENBERG BIBLE.',
    'THE FIRST SUNRISE',
    "AHIKAR ANSWERS PHARAOH'S RIDDLE",
    'JUDAH REVEALS THE STORY OF HIS LIFE',
    "JOSEPH'S PREDICAMENT",
}


def _load(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    # Delete whole lines of boilerplate rather than blanking them: a blanked
    # line reads as a paragraph break and splits sentences that in fact run
    # straight on across the page turn.
    raw = '\n'.join(l for l in raw.split('\n')
                    if not _BOILER.fullmatch(l.strip())
                    and l.strip() not in _PLATES)
    # A page marker also turns up mid-line, at the end of a line of text
    # rather than on one of its own, and matching only whole lines let
    # twenty-nine of them through into the printed page. Those are removed
    # here; the line keeps its other content, so no false break is made.
    raw = _BOILER.sub(' ', raw)
    # the transcription writes a capital I as a pipe; it is never anything
    # else, bar two places where it is joined to the next letter
    raw = re.sub(r'\|(?=[a-z])', 'I', raw)
    raw = re.sub(r'(?<![A-Za-z])\|(?![A-Za-z])', 'I', raw)
    raw = raw.replace('|', 'I')
    return [l.rstrip() for l in raw.split('\n')]


# The Psalms of Solomon lost the numerals of its first two psalms in
# transcription — the first is left as a bare "I" with its period gone, the
# second has no numeral at all, only the summary line that every psalm here
# carries under its number. Both are recovered by anchoring on that summary,
# which is why the text of it appears in the code: it is the marker, not a
# quotation. The remaining sixteen run III to XVIII and need nothing.
PSALM2_ARG = 'The desecration of Jerusalem'


def _div_re(style, loose=False):
    if style == 'chap':
        return re.compile(r'^(?:CHAP\.?|CHAPTER)\s+([IVXLCivxlc]+)\.?\s*$')
    if style == 'ode':
        return re.compile(r'^ODE\s+([0-9]+)\.?\s*$')
    # a bare numeral; `loose` also accepts one whose period was dropped
    return re.compile(r'^([IVXLCivxlc]{1,9})\.\s*$' if not loose
                      else r'^([IVXLCivxlc]{1,9})\.?\s*$')   # bare numeral


def _first_chapter_start(lines, start, head_i):
    """Where an unnumbered opening chapter begins, given the next heading.

    Several works lost the numeral of their first chapter in transcription,
    so the text sits between the editor's introduction and the numeral "II".
    The introduction carries no verse numbers and the chapter does, so the
    earliest numbered verse locates it; the paragraph above that is verse
    one, which the source leaves unnumbered.
    """
    nums = [i for i in range(start, head_i)
            if re.match(r'^\d{1,3}\s+\S', lines[i].strip())]
    if not nums:
        return None
    j = nums[0] - 1
    while j > start and lines[j].strip():        # up to the blank above it
        j -= 1
    k = j - 1
    while k > start and lines[k].strip():        # over the unnumbered verse 1
        k -= 1
    return k + 1


# The Odes and Psalms of Solomon carry a line of comment under each number —
# "A strange little Ode", "One of the loveliest Odes in this unusual
# collection". Those are Platt's, written in 1926, and this edition already
# drops his introductions on the grounds that the other divisions print the
# ancient text without a modern editor in front of it. Printed under the
# number they sat in the same place, and the same italic, that this book uses
# for genuine ancient argument lines, so a reader had no way to tell them
# apart. They are suppressed for the same reason the introductions are.
_NO_ARGUMENTS = {'Odes of Solomon', 'Psalms of Solomon'}


def _body(lines, start, end, style, numbered, psalms=False, report=None,
          keep_args=True):
    """Turn one work's lines into blocks."""
    div = _div_re(style, loose=psalms)
    blocks, cur, pending, arg, n = [], None, [], None, 0
    started = False

    def value(g):
        return int(g) if style == 'ode' else _roman(_deroman(g))

    heads = [i for i in range(start, end) if div.match(lines[i].strip())]
    # An opening chapter whose numeral was lost: the first surviving one is
    # two, so the text before it is chapter one rather than introduction.
    implicit = None
    if heads and numbered:
        if value(div.match(lines[heads[0]].strip()).group(1)) == 2:
            implicit = _first_chapter_start(lines, start, heads[0])

    def flush():
        nonlocal cur, pending
        txt = _clean(' '.join(pending))
        if txt:
            if cur is None:
                cur = Block('p' if numbered else 'q1')
                blocks.append(cur)
            cur.items.append(Text(_norm(txt)))
        pending = []

    def open_div(argument=None):
        nonlocal n, cur, arg, started
        flush(); cur = None
        n += 1
        blocks.append(Block('c', [Chapter(str(n))]))
        arg = [argument] if argument else []
        started = True

    for i in range(start, end):
        s = lines[i].strip()
        if implicit is not None and i == implicit:
            open_div()
            continue
        if psalms and s.startswith(PSALM2_ARG):
            open_div(s)
            continue
        m = div.match(s)
        if m:
            # The numerals are the worst-damaged thing in the transcription:
            # XLVIII prints as XLVIIL (which reads as 95), and several lost
            # an I, so XLI, XLIII and XLVII repeat the number before them.
            # Position is reliable where the figure is not, so the chapters
            # are numbered in sequence and the figure only checked against it.
            got = value(m.group(1))
            open_div()
            if report is not None and got != n:
                report.append((n, m.group(1), got))
            continue
        if not started:
            continue                      # the editor's introduction
        if not s:
            # A blank line closes the comment slot only once something has
            # been collected. The source puts two blank lines between the
            # number and the comment under it, so closing on the first one
            # left the comment to be read as a line of the poem — which is
            # how "One of the tenets of modern physics" ended up printed
            # inside a psalm.
            if arg:
                if keep_args:
                    b = Block('d')
                    b.items = [Text(_norm(_clean(' '.join(arg))))]
                    blocks.append(b)
                arg = None
            flush(); cur = None
            continue
        if arg is not None:
            # A numbered line is the poem itself, not a comment about it, so
            # it closes the slot instead of filling it. That protects the
            # odes that carry no comment at all from losing their first line.
            if not (arg == [] and re.match(r'^\d', s)):
                arg.append(s)
                continue
            arg = None
        if numbered:
            mv = re.match(r'^(\d{1,3})\s+(.*)$', s)
            if mv:
                flush()
                cur = Block('p', [Verse(mv.group(1))])
                blocks.append(cur)
                pending.append(mv.group(2))
                continue
            pending.append(s)
        else:
            flush(); cur = None           # poetry: one line, one block
            pending.append(s)
    flush()
    return [b for b in blocks if b.style == 'c' or b.items]


REPORT = {}


def parse(path):
    lines = _load(path)

    def find(pat, after=0):
        rx = re.compile(pat)
        return next((i for i in range(after, len(lines))
                     if rx.match(lines[i].strip())), None)

    marks = []
    at = 0
    for pat, head, title, style, numbered in WORKS:
        i = find(pat, at)
        if i is None:
            continue
        marks.append((i, head, title, style, numbered))
        at = i + 1
    t_start = find(r'^(?:THE )?TESTAMENT OF ' + TESTAMENTS[0], at)
    for k, nm in enumerate(TESTAMENTS):
        i = find(r'^(?:THE )?TESTAMENT OF ' + nm, t_start if k == 0 else at)
        if i is None:
            continue
        marks.append((i, 'Testament of ' + nm.title(),
                      'The Testament of ' + nm.title(), 'chap', True))
        at = i + 1
    marks.append((len(lines), None, None, None, None))

    books = []
    for k in range(len(marks) - 1):
        start, head, title, style, numbered = marks[k]
        end = marks[k + 1][0]
        if head is None:
            continue                      # 4 Maccabees: boundary only
        # PSA is deliberate: the renderer sets a book with that id as a
        # psalter, which is how the Psalms of Solomon should be printed.
        # The biblical Psalms are not in this volume, so nothing collides.
        bid = IDS.get(head) or re.sub(r'[^A-Z]', '', head.upper())[:3]
        bk = Book(id=bid, h=head, toc1=title, toc2=head)
        bk.blocks = _body(lines, start, end, style, numbered,
                          psalms=(head == 'Psalms of Solomon'),
                          report=REPORT.setdefault(head, []),
                          keep_args=head not in _NO_ARGUMENTS)
        if bk.blocks:
            books.append(bk)
    return books
