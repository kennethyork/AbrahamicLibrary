"""Reader for the New Testament apocrypha in William Wake's translation.

Source: "The suppressed Gospels and Epistles of the original New Testament",
via Project Gutenberg. Public domain.

Only the nine works this collection alone supplies are taken. Its versions of
Clement, Barnabas, Ignatius, Polycarp and Hermas are passed over: those are
already in this book in the Roberts–Donaldson translation, which is the later
and better one.

Each chapter opens with an argument — a numbered summary of what follows,
indented in the source. Those are set as an italic line under the chapter
figure rather than run into the text, where their numbers would be taken for
verse numbers.
"""
import re

from .usfm import Book, Block, Verse, Chapter, Text
from .corrections import (fix_text, americanize, modernize, resyntax,
                          resentence)

ROMAN = r'[IVXLCDM]+'
_VAL = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def _roman(r):
    n = 0
    for i, ch in enumerate(r):
        v = _VAL[ch]
        n += -v if i + 1 < len(r) and _VAL[r[i + 1]] > v else v
    return n


def _norm(s):
    # resyntax runs last as well as inside fix_text: modernize creates new
    # archaic constructions as it goes (didst bring -> did bring, hath
    # given -> has given), and those must be re-examined afterwards.
    return resentence(resyntax(modernize(americanize(fix_text(s)))))


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


# (first title line in the source, running head, printed title)
WORKS = [
    ('THE GOSPEL OF THE BIRTH OF MARY', 'Birth of Mary',
     'The Gospel of the Birth of Mary'),
    ('THE GOSPEL CALLED', 'Protevangelion', 'The Protevangelion'),
    ('THE FIRST GOSPEL OF', 'I Infancy',
     'The First Gospel of the Infancy of Jesus Christ'),
    ("THE SECOND, OR ST. THOMAS'S GOSPEL OF", 'II Infancy',
     "The Second, or Thomas's Gospel of the Infancy of Jesus Christ"),
    ('THE GOSPEL OF NICODEMUS,', 'Nicodemus',
     'The Gospel of Nicodemus, formerly called the Acts of Pontius Pilate'),
    ('THE EPISTLES OF', 'Christ and Abgarus',
     'The Epistles of Jesus Christ and Abgarus King of Edessa'),
    ('THE EPISTLE OF', 'Laodiceans',
     'The Epistle of Paul the Apostle to the Laodiceans'),
    ('ST. PAUL THE APOSTLE TO SENECA, WITH', 'Paul and Seneca',
     "The Epistles of Paul the Apostle to Seneca, with Seneca's to Paul"),
    ('THE ACTS OF ST. PAUL AND THECLA', 'Paul and Thecla',
     'The Acts of Paul and Thecla'),
]


def parse(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    body = raw.split('*** START', 1)[-1].split('*** END', 1)[0]
    lines = [l.rstrip() for l in body.split('\n')]

    books = []
    used = 190
    for key, name, title in WORKS:
        start = next((i for i, l in enumerate(lines)
                      if i > used and l.strip().rstrip('.') == key.rstrip('.')), None)
        if start is None:
            continue
        end = next((i for i in range(start + 3, len(lines))
                    if lines[i].strip().startswith('REFERENCE')), len(lines))
        used = end

        bk = Book(id=name[:3].upper(), h=name, toc1=title, toc2=name)
        cur, pending, arg = None, [], None
        chapter = 0

        def flush():
            nonlocal cur, pending
            if pending:
                txt = _clean(' '.join(pending))
                if txt:
                    if cur is None:
                        cur = Block('p')
                        bk.blocks.append(cur)
                    cur.items.append(Text(_norm(txt)))
            pending = []

        for i in range(start + 1, end):
            line = lines[i]
            s = line.strip()
            indent = len(line) - len(line.lstrip()) if s else 0

            if not s:
                if arg is not None and arg:
                    b = Block('d')          # the chapter argument, set italic
                    b.items = [Text(_norm(_clean(' '.join(arg))))]
                    bk.blocks.append(b)
                    arg = None
                flush()
                cur = None
                continue

            m = re.match(rf'^CHAP(?:TER|\.)\s+({ROMAN})\.?\s*$', s)
            if m:
                flush(); cur = None
                chapter = _roman(m.group(1))
                bk.blocks.append(Block('c', [Chapter(str(chapter))]))
                arg = []                    # the argument follows the heading
                continue
            if arg is not None:
                if indent >= 5:
                    arg.append(s)
                    continue
                b = Block('d'); b.items = [Text(_norm(_clean(' '.join(arg))))]
                if arg:
                    bk.blocks.append(b)
                arg = None

            m = re.match(r'^(\d{1,3})\s+(.*)$', s)
            if m:
                flush()
                cur = Block('p', [Verse(m.group(1))])
                bk.blocks.append(cur)
                pending.append(m.group(2))
                continue
            pending.append(s)
        flush()
        bk.blocks = [b for b in bk.blocks if b.style == 'c' or b.items]
        books.append(bk)
    return books
