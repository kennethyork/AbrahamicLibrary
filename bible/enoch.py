"""Reader for Richard Laurence's translation of 1 Enoch (Project Gutenberg).

1 Enoch is not in the World English Bible, so a companion volume needs a
different translation. Two public-domain ones are available: R. H. Charles
(1917) and Richard Laurence (1883). Charles is the better scholarship, but he
sets verse numbers inline in flowing prose, where a number cannot be told from
ordinary sentence-final digits — that parse could not be verified, and an
unverifiable parse of a sacred text is not worth shipping. Laurence marks
every chapter `CHAP. N.` and starts every verse on its own line, so his text
can be read exactly and checked.

The result is fed through the same Book/Block structures, and typeset by the
same machinery, as the World English Bible volume.
"""
import re

from .usfm import Book, Block, Verse, Chapter, Text, Note
from .corrections import (fix_text, americanize, modernize, resyntax,
                          resentence)

ROMAN = r'[IVXLCDM]+'
_VAL = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def roman_to_int(r):
    n = 0
    for i, ch in enumerate(r):
        v = _VAL[ch]
        n += -v if i + 1 < len(r) and _VAL[r[i + 1]] > v else v
    return n


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _collect_notes(lines):
    """Gather the edition's footnotes, which sit in the flow as

        Footnote 21:
        <blank>
          body text, possibly wrapped

    Returns {number: body} and the set of line indices they occupy, so the
    reading text can step over them.
    """
    notes, consumed = {}, set()
    i = 0
    while i < len(lines):
        m = re.match(r'^Footnote (\d+):\s*$', lines[i].strip())
        if not m or not lines[i].startswith('Footnote'):
            i += 1
            continue
        start, j = i, i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        body = []
        while j < len(lines) and lines[j].strip() and lines[j].startswith('  '):
            body.append(lines[j].strip())
            j += 1
        notes[m.group(1)] = _clean(' '.join(body))
        consumed.update(range(start, j))
        i = j
    return notes, consumed


def _norm(s):
    """Every reading-text transformation this volume applies, in order."""
    # resyntax runs last as well as inside fix_text: modernize creates new
    # archaic constructions as it goes (didst bring -> did bring, hath
    # given -> has given), and those must be re-examined afterwards.
    return resentence(resyntax(modernize(americanize(fix_text(s)))))


def _note_parts(body):
    """Split a footnote body into (style, text) parts, honouring _italics_."""
    parts, i = [], 0
    for m in re.finditer(r'_([^_]+)_', body):
        if m.start() > i:
            parts.append(('ft', _norm(body[i:m.start()]).strip()))
        parts.append(('fqa', _norm(m.group(1)).strip()))
        i = m.end()
    if body[i:].strip():
        parts.append(('ft', _norm(body[i:]).strip()))
    return [(k, t) for k, t in parts if t]


def _runs(s, notes=None, ref=''):
    """Split into Text runs on _italics_, turning [N] callers into Notes."""
    out = []
    for chunk in re.split(r'(\[\d+\])', s):
        m = re.fullmatch(r'\[(\d+)\]', chunk)
        if m:
            body = (notes or {}).get(m.group(1))
            if body:
                out.append(Note('f', ref, _note_parts(body)))
            continue
        i = 0
        for it in re.finditer(r'_([^_]+)_', chunk):
            if it.start() > i:
                out.append(Text(_norm(chunk[i:it.start()])))
            out.append(Text(_norm(it.group(1)), italic=True))
            i = it.end()
        if chunk[i:]:
            out.append(Text(_norm(chunk[i:])))
    return [r for r in out if not isinstance(r, Text) or r.s]


def parse(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    body = raw.split('*** START', 1)[-1].split('*** END', 1)[0]
    lines = [l.rstrip() for l in body.split('\n')]

    notes, consumed = _collect_notes(lines)

    # the text proper begins at the title line and ends at the printer's note
    start = next(i for i, l in enumerate(lines)
                 if l.strip() == 'THE BOOK OF ENOCH.' and i > 1000)
    end = next((i for i, l in enumerate(lines)
                if l.strip().startswith('PRINTED BY')), len(lines))

    bk = Book(id='ENO', h='Enoch', toc1='The Book of Enoch', toc2='Enoch')
    cur, pending = None, []
    chapter, verse = '1', '1'

    def flush():
        nonlocal cur, pending
        if pending and cur is not None:
            cur.items.extend(_runs(_clean(' '.join(pending)), notes,
                                   f'{chapter}:{verse}'))
        pending = []

    for idx in range(start + 1, end):
        if idx in consumed:            # a footnote block, not reading text
            continue
        line = lines[idx]
        s_ = line.strip()
        if not s_:
            continue
        # headings may carry the edition's bracketed section and note marks,
        # e.g. 'CHAP. XXXVII.[73] [SECT. VI.[74]]' — take the part before them
        head = s_.split('[', 1)[0].strip()
        m = re.match(rf'^CHAP\.\s+({ROMAN})\.?\s*$', head)
        if m:
            flush()
            cur = None
            chapter = str(roman_to_int(m.group(1)))
            bk.blocks.append(Block('c', [Chapter(chapter)]))
            continue
        m = re.match(r'^(\d{1,3})\.\s+(.*)$', s_)
        if m:
            flush()
            verse = m.group(1)
            cur = Block('p', [Verse(verse)])
            bk.blocks.append(cur)
            pending.append(m.group(2))
            continue
        pending.append(s_)
    flush()
    bk.blocks = [b for b in bk.blocks if b.style == 'c' or b.items]
    return bk
