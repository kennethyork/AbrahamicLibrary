"""Reader for the Didache, Ante-Nicene Fathers vol. VII (1886).

The Didache was found in 1873, three years after the Edinburgh Apostolic
Fathers went to press, so it is absent from the 1870 volume this book's
Apostolic Fathers come from. It is taken instead from the same series'
seventh volume, which is likewise in the public domain.

The source is Wikisource wikitext, one page per chapter: chapter headings
wrapped in a small-caps template, verse numbers inline, and the edition's
notes as <ref> spans. Verse numbers are only accepted when the number is the
one expected next, so an ordinary sentence ending in a numeral cannot be
mistaken for the start of a verse.
"""
import html
import os
import re

from .usfm import Book, Block, Verse, Chapter, Text, Note
from .corrections import (fix_text, americanize, modernize, resyntax,
                          resentence)

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII',
         'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI']


def _norm(s):
    # resyntax runs last as well as inside fix_text: modernize creates new
    # archaic constructions as it goes (didst bring -> did bring, hath
    # given -> has given), and those must be re-examined afterwards.
    return resentence(resyntax(modernize(americanize(fix_text(s)))))


def _strip_templates(s):
    """Reduce the wikitext templates used here to their visible text."""
    s = re.sub(r'\{\{anchor\+\|[^|]*\|2=([^}]*)\}\}', r'\1', s)
    s = re.sub(r'\{\{(?:small-caps|bbsc|sc)\|([^}]*)\}\}', r'\1', s)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    s = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'\[\[([^\]]*)\]\]', r'\1', s)
    s = s.replace("'''", '').replace("''", '')
    s = html.unescape(s)
    return s.replace('\xa0', ' ')


def _drop_header(s):
    """Remove the leading {{header ...}} block, braces balanced."""
    i = s.find('{{header')
    if i < 0:
        return s
    depth, j = 0, i
    while j < len(s):
        if s.startswith('{{', j):
            depth += 1; j += 2
        elif s.startswith('}}', j):
            depth -= 1; j += 2
            if depth == 0:
                return s[j:]
        else:
            j += 1
    return s


def parse(directory):
    bk = Book(id='DID', h='Didache', toc1='The Teaching of the Twelve Apostles',
              toc2='Didache')
    for n, roman in enumerate(ROMAN, start=1):
        path = os.path.join(directory, roman + '.txt')
        if not os.path.exists(path):
            continue
        raw = open(path, encoding='utf-8').read()
        raw = _drop_header(raw)
        raw = re.split(r'==\s*Footnotes\s*==', raw)[0]

        # lift the notes out before anything else touches the text
        notes = {}
        def take(m, _c=[0]):
            _c[0] += 1
            notes[str(_c[0])] = _norm(_strip_templates(m.group(1))).strip()
            return f'\x00{_c[0]}\x00'
        raw = re.sub(r'<ref[^>]*>(.*?)</ref>', take, raw, flags=re.S)
        raw = re.sub(r'<ref[^>]*/>', '', raw)

        text = _strip_templates(raw)
        text = re.sub(r'\s+', ' ', text).strip()

        bk.blocks.append(Block('c', [Chapter(str(n))]))

        # chapter heading: "Chapter I.—The Two Ways; The First Commandment."
        m = re.match(rf'Chapter {roman}\.\s*[—–-]\s*(.*?)(?=\s+1\.\s)', text)
        if m:
            title = m.group(1).strip().rstrip('.')
            if title:
                h = Block('s1'); h.items = [Text(_norm(title))]
                bk.blocks.append(h)
            text = text[m.end():]
        else:
            text = re.sub(rf'^Chapter {roman}\.\s*[—–-]?\s*', '', text)

        # split on verse numbers, accepting only the one expected next
        parts, expect, pos = [], 1, 0
        for m in re.finditer(r'(\d{1,3})\.\s+', text):
            if int(m.group(1)) != expect:
                continue
            if expect > 1:
                parts.append((expect - 1, text[pos:m.start()]))
            pos = m.end()
            expect += 1
        parts.append((expect - 1, text[pos:]))

        for num, chunk in parts:
            chunk = chunk.strip()
            if not chunk or num < 1:
                continue
            blk = Block('p', [Verse(str(num))])
            for piece in re.split(r'\x00(\d+)\x00', chunk):
                if piece is None:
                    continue
                if piece.isdigit() and piece in notes:
                    body = notes[piece]
                    if body:
                        blk.items.append(Note('f', f'{n}:{num}', [('ft', body)]))
                elif piece.strip():
                    blk.items.append(Text(_norm(piece)))
            bk.blocks.append(blk)
    bk.blocks = [b for b in bk.blocks if b.style == 'c' or b.items]
    return bk
