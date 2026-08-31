"""USFM parser: turns eBible USFM into structured blocks for typesetting.

Emits, per book, a flat list of Block(style, items) where items are inline
tokens: Verse, Text (optionally words-of-Jesus) and Note (footnote / xref).
Strong's-number wrappers are stripped; the text itself is untouched.
"""
import re
from dataclasses import dataclass, field

from .corrections import fix_text, resentence


@dataclass
class Verse:
    num: str

@dataclass
class Chapter:
    num: str

@dataclass
class Text:
    s: str
    wj: bool = False          # words of Jesus
    sc: bool = False          # divine name, set in small caps
    italic: bool = False      # \qs Selah, \bk book titles

@dataclass(eq=False)          # identity, not value: two identical footnotes
class Note:                   # are still two separate occurrences
    kind: str                 # 'f' footnote | 'x' cross-reference
    ref: str                  # originating verse, e.g. "1:23"
    parts: list = field(default_factory=list)   # [(style, text)]

@dataclass
class Block:
    style: str
    items: list = field(default_factory=list)

@dataclass
class Book:
    id: str
    h: str = ""
    toc1: str = ""
    toc2: str = ""
    mt: list = field(default_factory=list)
    blocks: list = field(default_factory=list)


# --- inline cleaners -------------------------------------------------------

# \w word|strong="H1234"\w*  ->  word     (also \+w, and \w word|x-y="z"\w*)
RE_W = re.compile(r'\\\+?(w|wh|wg|wa)\s+([^|\\]*?)(?:\|[^\\]*?)?\\\+?\1\*')
# \w LORD|strong="H3068"\w*  -> sentinel-wrapped, set in small caps later
RE_DIVINE = re.compile(r'\\\+?w\s+(LORD|GOD)((?:’s)?)\|strong="(?:H3068|H3069)"[^\\]*\\\+?w\*')
SC_OPEN, SC_CLOSE = '\x01', '\x02'
RE_ND = re.compile(r'\\\+?nd\s+(.*?)\\\+?nd\*', re.S)
RE_ANY_ATTR = re.compile(r'\|[^\\]*')

PARA_STYLES = {
    'p', 'm', 'nb', 'pc', 'mi', 'pi1', 'pi2', 'li1', 'li2',
    'q1', 'q2', 'q3', 'q4', 'qc', 'qr', 'b',
    'd', 'sp', 's1', 's2', 'ms1', 'ms2', 'is1', 'ip', 'iot', 'io1', 'cl',
}


def _strip_words(s: str) -> str:
    """Remove \\w ...\\w* Strong's wrappers, keeping the word."""
    s = resentence(fix_text(s))
    s = RE_DIVINE.sub(SC_OPEN + r'\1\2' + SC_CLOSE, s)
    prev = None
    while prev != s:
        prev = s
        s = RE_W.sub(r'\2', s)
    s = RE_ND.sub(r'\1', s)
    return s


def _parse_note(body: str, kind: str):
    """Parse the inside of \\f ... \\f* / \\x ... \\x* into (ref, parts)."""
    body = _strip_words(body).strip()
    if body[:1] in '+-?' :                 # caller char, we generate our own
        body = body[1:].strip()
    parts, ref = [], ''
    # split on the note's internal markers
    toks = re.split(r'\\(fr|ft|fq|fqa|fk|fl|fv|fp|xo|xt|xq)\s*', body)
    lead = toks[0].strip()
    if lead:
        parts.append(('ft', lead))
    for i in range(1, len(toks) - 1, 2):
        mark, txt = toks[i], toks[i + 1]
        txt = re.sub(r'\\\+?\w+\*?', '', txt)       # drop nested char markers
        txt = RE_ANY_ATTR.sub('', txt).strip()
        if not txt:
            continue
        if mark in ('fr', 'xo'):
            ref = txt.rstrip(':').strip()
        else:
            parts.append((mark, txt))
    return ref, parts


def _inline(s: str, out: list, state: dict):
    """Append inline tokens for a run of USFM text to `out`."""
    s = _strip_words(s)
    # tokenise on verse markers, notes and the char styles we keep
    pat = re.compile(
        r'\\v\s+([\w\-,]+)\s?'
        r'|\\f\s(.*?)\\f\*'
        r'|\\x\s(.*?)\\x\*'
        r'|\\(wj|qs|bk|it|em|add)\*?'
        r'|\\(\+?\w+)\*?', re.S)
    pos = 0
    for m in pat.finditer(s):
        chunk = s[pos:m.start()]
        if chunk:
            out.append(Text(chunk, wj=state['wj'], italic=state['it']))
        pos = m.end()
        if m.group(1) is not None:
            out.append(Verse(m.group(1)))
        elif m.group(2) is not None:
            ref, parts = _parse_note(m.group(2), 'f')
            out.append(Note('f', ref or state['ref'], parts))
        elif m.group(3) is not None:
            ref, parts = _parse_note(m.group(3), 'x')
            out.append(Note('x', ref or state['ref'], parts))
        elif m.group(4) is not None:
            tag, closing = m.group(4), m.group(0).endswith('*')
            if tag == 'wj':
                state['wj'] = not closing
            else:
                state['it'] = not closing
        # group(5): unknown marker -> dropped
    tail = s[pos:]
    if tail:
        out.append(Text(tail, wj=state['wj'], italic=state['it']))


def parse(path: str) -> Book:
    raw = open(path, encoding='utf-8').read()
    raw = raw.replace('\u200e', '')
    book = Book(id='')
    cur = None
    state = {'wj': False, 'it': False, 'ref': ''}
    chap = '1'

    # Join continuation lines: a line not starting with \ belongs to the one above.
    lines = []
    for line in raw.split('\n'):
        if line.startswith('\\') or not lines:
            lines.append(line)
        else:
            lines[-1] += ' ' + line
    for line in lines:
        line = line.rstrip()
        if not line.startswith('\\'):
            continue
        m = re.match(r'\\(\+?[a-z0-9]+)\*?\s?(.*)$', line, re.S)
        if not m:
            continue
        tag, rest = m.group(1), m.group(2).strip()

        if tag == 'id':
            book.id = rest.split()[0] if rest else ''
        elif tag == 'h':
            book.h = rest
        elif tag == 'toc1':
            book.toc1 = rest
        elif tag == 'toc2':
            book.toc2 = rest
        elif tag in ('mt1', 'mt2', 'mt3', 'mt'):
            book.mt.append((tag, _strip_words(rest)))
        elif tag == 'c':
            chap = rest.split()[0] if rest else chap
            state['ref'] = chap
            book.blocks.append(Block('c', [Chapter(chap)]))
            cur = None
        elif tag == 'v':
            if cur is None:
                cur = Block('p')
                book.blocks.append(cur)
            _inline('\\v ' + rest, cur.items, state)
        elif tag in PARA_STYLES:
            if tag == 'b':
                book.blocks.append(Block('b'))
                cur = None
                continue
            cur = Block(tag)
            book.blocks.append(cur)
            if rest:
                _inline(rest, cur.items, state)
        elif tag in ('ide', 'rem', 'sts', 'toc3', 'usfm', 'cp', 'va', 'vp'):
            continue
        else:
            if cur is not None and rest:
                _inline(rest, cur.items, state)
    return book
