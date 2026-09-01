"""Ingest the Qur'an in every English translation that is free to reprint.

Four editions:

  Yusuf Ali (1934), Pickthall (1930), Shakir  — from Project Gutenberg 16955,
      which sets the three side by side, every verse numbered `sura.verse`.
      That numbering is what makes them usable in a study app: the same verse
      can be shown in three hands at once.
  Sale (1734) — the first direct English translation from the Arabic, from
      the copy already in the archive.

All four are modernized on the full tier. Pickthall and Yusuf Ali write a
deliberately archaic English — "Lo!", "ye", "hath" — as a register for
scripture; that register is exactly what this archive is for removing, and
the edition notice on every work says so.

Sale's text carries its footnote markers as bare letters stuck to the end of
a word ("the mysteriesf of faith"). They are stripped by asking the
dictionary: `mysteriesf` is not a word and `mysteries` is, so the `f` goes;
`roof` is a word, so it stays.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize                                # noqa: E402
from tools.corpus import Chapter, Work, rights                     # noqa: E402

SRC = os.path.join(corpus.ROOT, 'sources', 'collector')
PG16955 = os.path.join(SRC, 'quran', 'pg-16955.txt')
SALE = os.path.join(SRC, 'quran_sale_source.txt')

PG_RIGHTS = rights(
    'Public domain in the United States; distributed by Project Gutenberg, '
    'which clears every text it hosts for United States public-domain status. '
    'Readers outside the United States should check their own local law.',
    'https://www.gutenberg.org/ebooks/16955')

SALE_RIGHTS = rights(
    'Public domain worldwide. George Sale died in 1736 and the translation '
    'was published in 1734.',
    'https://www.gutenberg.org/ebooks/7440')

# Gutenberg 16955 sets three translations against each other. Only one of
# them can be taken.
#
# Pickthall was published in 1930 and is free in the United States from the
# first of January 2026: he died in 1936, so British copyright ran to 2006,
# so the work was still protected at home in 1996 and its American copyright
# was restored for the full ninety-five years from publication — which have
# now run.
#
# The same arithmetic condemns the other two. Yusuf Ali was published at
# Lahore in 1934 and its translator died in 1953, which under Indian and
# Pakistani law of life plus sixty kept it in copyright at home until 2013 —
# well past 1996 — so its restored American copyright stands until 2030.
# Shakir is of 1982 and there is no reading of the law under which it has
# expired. Project Gutenberg distributes all three; that is Gutenberg's
# judgement, and this archive exists to be reprinted and sold, which is a
# harder test than being read. Sale, Rodwell and Palmer carry the Qur'an
# here without needing anyone's judgement but a date.
EDITIONS = {
    'P': dict(id='quran-pickthall', translator='Marmaduke Pickthall', year=1930,
              translation='The Meaning of the Glorious Koran, translated by '
                          'Marmaduke Pickthall',
              sort=1),
}

RE_CHAP = re.compile(r'^\s*Chapter\s+(\d+):\s*$')
RE_TOTAL = re.compile(r'^\s*Total Verses:\s*(\d+)\s*Revealed At:\s*(\w+)', re.I)
RE_VNUM = re.compile(r'^\s*(\d{3})\.(\d{3})\s*$')
RE_LINE = re.compile(r'^([YPS]):\s?(.*)$')


def parse_side_by_side(path):
    """-> {sura: {'name':.., 'place':.., 'verses': {n: {'Y':..,'P':..,'S':..}}}}"""
    suras, cur, vnum = {}, None, None
    pending_name = False
    key = None
    with open(path, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().split('\n')

    for raw in lines:
        line = raw.rstrip()
        m = RE_CHAP.match(line)
        if m:
            n = int(m.group(1))
            cur = suras.setdefault(n, {'name': '', 'place': '', 'verses': {}})
            pending_name, vnum, key = True, None, None
            continue
        if cur is None:
            continue
        if pending_name and line.strip() and not RE_TOTAL.match(line):
            cur['name'] = line.strip()
            pending_name = False
            continue
        m = RE_TOTAL.match(line)
        if m:
            cur['place'] = m.group(2).title()
            continue
        m = RE_VNUM.match(line)
        if m:
            vnum, key = int(m.group(2)), None
            cur['verses'].setdefault(vnum, {})
            continue
        m = RE_LINE.match(line)
        if m and vnum is not None:
            key = m.group(1)
            cur['verses'][vnum][key] = m.group(2).strip()
            continue
        # a wrapped continuation of the line above
        if key and vnum is not None and line.strip() and not line.startswith('---'):
            cur['verses'][vnum][key] += ' ' + line.strip()
        elif not line.strip():
            key = None
    return suras


def tidy(s):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s


def build_side_by_side(report):
    suras = parse_side_by_side(PG16955)
    if len(suras) != 114:
        print(f'  warning: parsed {len(suras)} suras, expected 114')
    made = []
    for code, spec in EDITIONS.items():
        w = Work(id=spec['id'], title='The Qur’an', religion='islam',
                 section='quran', sort=spec['sort'], structure='verse',
                 canon='canonical', subtitle=f'translated by {spec["translator"]}',
                 translation=spec['translation'],
                 translator=spec['translator'], year=spec['year'],
                 modernization='full', rights=PG_RIGHTS,
                 provenance={'source': 'Project Gutenberg 16955, '
                                       'three translations side by side',
                             'source_file': os.path.relpath(PG16955, corpus.ROOT)})
        for n in sorted(suras):
            s = suras[n]
            name = s['name'] or f'Sura {n}'
            ch = Chapter(n, name)
            for vn in sorted(s['verses']):
                text = tidy(s['verses'][vn].get(code, ''))
                if not text:
                    continue
                said, src = modernize.pair(text, 'full', report)
                ch.verses.append({
                    'n': str(vn), 'text': said, 'notes': [],
                    **({'src': src} if src else {}),
                })
            if s['place']:
                ch.blocks.append({'k': 'meta', 't': f'Revealed at {s["place"]}'})
            if ch.verses:
                w.add(ch)
        made.append(w.save())
        print(f'  {spec["id"]}: {len(w.chapters)} suras, '
              f'{sum(len(c.verses) for c in w.chapters)} verses')
    return made


# --- Sale, 1734 -----------------------------------------------------------

RE_SALE_CHAP = re.compile(r'^\s*CHAPTER\s+([IVXLCDM]+)\.?\s*$')
RE_SALE_TITLE = re.compile(r'^ENTITLED,?\s*(.*)$', re.I)
RE_SALE_NOTE = re.compile(r'^\t\s*([a-z0-9]+)\s\s')
RE_MARKER = re.compile(r'\b([A-Za-z]{2,})([a-z])\b')


def roman(s):
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = vals.get(ch, 0)
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


# A marker sitting directly against punctuation, with no space: "creatures;b",
# "book;a", "A. L. M.e". A real word never follows punctuation without a space,
# so a lone letter there is always a marker.
RE_MARKER_PUNCT = re.compile(r'([;:,.!?])([a-z])(?![A-Za-z])')


def strip_markers(s):
    """Remove Sale's lettered footnote markers, asking the dictionary."""
    def repl(m):
        whole, stem = m.group(0), m.group(1)
        if modernize._is_word(whole.lower()):
            return whole                     # 'roof', 'often', 'seven'
        if modernize._is_word(stem.lower()):
            return stem                      # 'mysteriesf' -> 'mysteries'
        return whole
    s = RE_MARKER.sub(repl, s)
    s = RE_MARKER_PUNCT.sub(r'\1', s)
    return s


# "ENTITLED, THE COW;d REVEALED PARTLY AT MECCA, AND PARTLY AT MEDINA."
RE_SALE_REVEALED = re.compile(r'\bREVEALED\b(.*)$', re.I)

# Words that stay lower case in a title.
_SMALL = {'of', 'the', 'a', 'an', 'and', 'or', 'to', 'in', 'at', 'for',
          'from', 'by', 'on', 'with'}


def title_case(s):
    words = s.split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        out.append(low if (i and low in _SMALL) else low[:1].upper() + low[1:])
    return ' '.join(out)


def split_sale_title(raw):
    """-> (sura name, where it was revealed)"""
    raw = strip_markers(raw.strip())
    place = ''
    m = RE_SALE_REVEALED.search(raw)
    if m:
        place = 'Revealed' + m.group(1).rstrip('. ')
        raw = raw[:m.start()]
    name = title_case(raw.strip().strip(';,. '))
    place = re.sub(r'\s+', ' ', place).strip()
    if place:
        place = place[0].upper() + place[1:].lower()
        # the lowercasing above flattens the place names too
        for proper in ('Mecca', 'Medina', 'Makka', 'Madinah', 'Jerusalem'):
            place = re.sub(rf'\b{proper.lower()}\b', proper, place)
    return name, place


def parse_sale():
    with open(SALE, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().split('\n')
    # the body starts at the first real chapter heading, after the contents
    start = 0
    for i, line in enumerate(lines):
        if RE_SALE_CHAP.match(line.rstrip()) and i > 5000:
            start = i
            break

    suras, cur, para = [], None, []

    def flush():
        nonlocal para
        text = tidy(' '.join(para))
        if text and cur is not None:
            cur['verses'].append(text)
        para = []

    for raw in lines[start:]:
        line = raw.rstrip()
        m = RE_SALE_CHAP.match(line)
        if m:
            flush()
            cur = {'n': roman(m.group(1)), 'title': '', 'place': '',
                   'verses': []}
            suras.append(cur)
            continue
        if cur is None:
            continue
        m = RE_SALE_TITLE.match(line.strip())
        if m and not cur['title']:
            flush()
            cur['title'], cur['place'] = split_sale_title(m.group(1))
            continue
        if RE_SALE_NOTE.match(raw):          # a footnote body: not verse text
            flush()
            continue
        if not line.strip():
            flush()
            continue
        # a new verse opens either indented or with its decade number
        if re.match(r'^\s{4,}\S', raw) or re.match(r'^\d+\t', raw):
            flush()
            para.append(re.sub(r'^\d+\t', '', raw).strip())
        elif para:
            para.append(line.strip())
    flush()
    return [s for s in suras if s['verses']]


def build_sale(report):
    suras = parse_sale()
    w = Work(id='quran-sale', title='The Qur’an', religion='islam',
             section='quran', sort=3, structure='verse', canon='canonical',
             subtitle='translated by George Sale',
             translation='The Koran, translated by George Sale',
             translator='George Sale', year=1734, modernization='full',
             rights=SALE_RIGHTS,
             provenance={'source': 'George Sale, The Koran, 1734',
                         'source_file': os.path.relpath(SALE, corpus.ROOT),
                         'note': 'Sale numbers only every tenth verse; verses '
                                 'here are numbered in sequence as they stand '
                                 'in his paragraphs.'})
    for s in suras:
        ch = Chapter(s['n'], s['title'] or f'Sura {s["n"]}')
        if s.get('place'):
            ch.blocks.append({'k': 'meta', 't': s['place']})
        for i, text in enumerate(s['verses'], 1):
            said, src = modernize.pair(strip_markers(text), 'full', report)
            ch.verses.append({'n': str(i), 'text': said, 'notes': [],
                              **({'src': src} if src else {})})
        if ch.verses:
            w.add(ch)
    m = w.save()
    print(f'  quran-sale: {len(w.chapters)} suras, '
          f'{sum(len(c.verses) for c in w.chapters)} verses')
    return m


def main():
    report = modernize.Report()
    made = build_side_by_side(report)
    if os.path.exists(SALE):
        made.append(build_sale(report))
    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'quran.json'),
                      report.as_dict())
    print(f'quran: {len(made)} editions; modernizer changed '
          f'{report.as_dict()["changed_occurrences"]} occurrences of '
          f'{report.as_dict()["changed_forms"]} forms, '
          f'{report.as_dict()["unresolved_forms"]} left unresolved')


if __name__ == '__main__':
    main()
