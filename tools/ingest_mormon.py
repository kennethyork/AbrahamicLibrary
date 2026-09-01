"""Ingest the Restoration scriptures: the Book of Mormon, the Doctrine and
Covenants, and the Pearl of Great Price.

These need their own ingester for two reasons.

The Book of Mormon arrived through the Gutenberg shelf, which treats every
book there as prose and hands the reader one undivided lump. It is scripture
with chapters and verses, and Gutenberg's own transcription marks every one
of them — `1:1`, `1:2` — so there was never any reason to throw that away.
Parsed properly it is fifteen books, two hundred and thirty-nine chapters and
six and a half thousand verses, and a reference like Alma 32:21 resolves.

The other two are not on Project Gutenberg at all. They come from archive.org
scans published long enough ago to be certainly free — 1891 and 1920 — which
means OCR, so they are cleaned harder: the cross-reference apparatus at the
foot of every page, the running heads, and the footnote letters the scanner
glued onto the words they were marking.

One rule runs through all three: **the printed numbers are not trusted.** The
scanner reads `SECTION 45` as `SECTION 46`, `52` as `62`, `63` as `03`. The
sections are in order and complete, so they are counted rather than read.

    .venv/bin/python -m tools.ingest_mormon
"""
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize                                # noqa: E402
from tools.corpus import Chapter, Work, rights                     # noqa: E402

GUTENBERG = os.path.join(corpus.ROOT, 'sources', 'collector', 'gutenberg')
DEST = os.path.join(corpus.ROOT, 'sources', 'collector', 'mormon')
UA = 'AbrahamicArchive/1.0 (public-domain text collection)'

TIER = 'full'

# --- the two scans -------------------------------------------------------
#
# Chosen by reading them, not by their catalog entry. Four editions of the
# Doctrine and Covenants and five of the Pearl of Great Price were downloaded
# and compared; these two are the ones whose scanner marked footnotes with a
# symbol rather than by gluing a letter onto the next word, which is the
# difference between "*my church" and "amy church" and so the difference
# between a text that can be cleaned and one that cannot.
SCANS = {
    'doctrine-and-covenants': {
        'id': 'doctrineandcove00saingoog',
        'year': 1891,
        'title': 'The Doctrine and Covenants',
        'publisher': 'Deseret News, Salt Lake City',
    },
    'pearl-of-great-price': {
        'id': 'pearlgreatprice00unkngoog',
        'year': 1920,
        'title': 'The Pearl of Great Price',
        'publisher': 'Deseret News, Salt Lake City',
    },
}

def fetch():
    """Download the two scans once. Everything else is already on disk."""
    os.makedirs(DEST, exist_ok=True)
    for key, s in SCANS.items():
        path = os.path.join(DEST, f'{key}.txt')
        if os.path.isfile(path) and os.path.getsize(path) > 100000:
            continue
        url = f'https://archive.org/download/{s["id"]}/{s["id"]}_djvu.txt'
        print(f'  downloading {s["id"]}…', flush=True)
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=300) as fh:
            body = fh.read()
        with open(path, 'wb') as out:
            out.write(body)


def read(key):
    with open(os.path.join(DEST, f'{key}.txt'), encoding='utf-8',
              errors='replace') as fh:
        return _lines(fh.read())


def _lines(text):
    """One line ending. Gutenberg ships CRLF, and a stray carriage return
    at the end of a line is enough to hide a verse marker from a regex."""
    return text.replace('\r\n', '\n').replace('\r', '\n')


# --- taking the book out of the scan -------------------------------------

# The scanner spaces every word twice and hyphenates across line ends.
RE_HYPHEN = re.compile(r'([A-Za-z])-\s*\n\s*([a-z])')
RE_SPACES = re.compile(r'[ \t]{2,}')
# The scanner sets a verse number as `1 2 .` about a hundred times over.
RE_SPACED_NUM = re.compile(r'^(\d(?:\s?\d){0,2})\s*\.')

# A running head: "SEC. XLV.]  COMMANDMENTS.  183", "76 PEAKL OF GIU;AT PRICK."
# The scanner's own furniture, which is mixed case and says so.
RE_DIGITISED = re.compile(
    r'Digitized by|Original from|UNIVERSITY OF|\bGoogle\b', re.I)

# A cross-reference chain: "a, 1 : 30. 5 : 14. 10 : 53—56. 11 : 16."
RE_REFCHAIN = re.compile(r'^[^A-Za-z]*$|^[\s\d.,;:—–\-]*$')

# The footnote block under a page opens with its own letter and a comma:
# "a, with civil officers, elected by themselves.   6, that the civil"
RE_FOOTSTART = re.compile(r'^\s*[A-Za-z0-9«»*^]{1,3}\s*,\s+\S')
# The leading digit is the one the scanner loses: `27.` comes back as `^7.`
RE_VERSE = re.compile(r'^\s*([^A-Za-z0-9\s]{0,2})\s*(\d{1,3})\s*\.\s+(\S.*)$')

# Footnote marks the scanner left attached to the word they hung on.
RE_MARKS = re.compile(r'[*^«»°†‡§]+')
RE_MARK_AFTER_STOP = re.compile(r'([,.;:!?])[\'"/^*?°’”]+(?=\s|$)')


def _letters(s):
    return sum(c.isalpha() for c in s)


def clean_scan(text):
    """Strip the page furniture, the apparatus and the footnote marks."""
    text = RE_HYPHEN.sub(r'\1\2', text)
    out = []
    for para in re.split(r'\n\s*\n', text):
        lines = [ln for ln in para.split('\n') if ln.strip()]
        if not lines:
            continue
        first = lines[0]
        # A footnote block, unless it is a verse — verses number with a
        # period, footnotes letter with a comma, and that is the whole test.
        if RE_FOOTSTART.match(first) and not RE_VERSE.match(first):
            continue
        kept = []
        for ln in lines:
            if RE_DIGITISED.search(ln):
                continue
            if RE_REFCHAIN.match(ln):
                continue
            # A running head — `SEC. XLV.] COMMANDMENTS. 183`, or the same
            # line after the scanner has had its way with it, `lO I»EAttL OP
            # G^EAT PRICE.` It is set in capitals and it is short, and that
            # is what identifies it. Matching the words instead would be a
            # mistake: `commandments` is an ordinary word in these books,
            # and looking for it threw away Moses 1:17.
            letters = [c for c in ln if c.isalpha()]
            if (letters and len(letters) < 40
                    and sum(c.isupper() for c in letters) > len(letters) / 2):
                continue
            ln = RE_SPACES.sub(' ', ln).strip()
            kept.append(RE_SPACED_NUM.sub(
                lambda m: m.group(1).replace(' ', '') + '.', ln))
        if kept:
            out.append('\n'.join(kept))
    text = '\n\n'.join(out)
    text = RE_MARKS.sub('', text)
    text = RE_MARK_AFTER_STOP.sub(r'\1', text)
    text = _strip_word_marks(text)
    return text


def _strip_word_marks(text):
    """Drop a trailing mark from a word only when a real word is underneath.

    `Moses/` is Moses with a footnote; `Jacob'` may be a possessive the
    scanner clipped. The dictionary decides, exactly as it does for the
    footnote letters in Sale's Koran.
    """
    def go(m):
        word = m.group(1)
        return word if modernize._is_word(word.lower()) or word[0].isupper() \
            else m.group(0)
    return re.sub(r'\b([A-Za-z]{2,})[/^*°’”?]+(?=\s|$)', go, text)


def split_lost_headings(text):
    """Cut a block where its verse numbering starts over.

    One `SECTION` heading did not survive the scan. What is left of it is a
    block whose verses run 1…17 and then begin again at 1 — two revelations
    printed as one. Numbering that starts over is the heading saying, in the
    only way it still can, that it was there.
    """
    out, cur, high = [], [], 0
    for line in text.split('\n'):
        m = RE_VERSE.match(line)
        if m:
            n = int(m.group(2))
            if n == 1 and high >= 5:
                out.append('\n'.join(cur))
                cur, high = [], 0
            high = max(high, n)
        cur.append(line)
    out.append('\n'.join(cur))
    return out


def paragraphs_to_verses(text):
    """-> [(n, text)] for a page numbered `1. … 2. …`.

    A new verse starts only where the printed number is the one that should
    come next. That single condition disposes of both ways the scan lies: a
    stray `2, 4: 13, 16, 17, 27.` left over from the apparatus does not open
    verse 3, and a sentence that happens to begin a line with `1830. He
    returned…` does not either. Anything else is more of the verse already
    open, which is what it looks like on the page.
    """
    verses, cur, want = [], None, 1
    for line in text.split('\n'):
        m = RE_VERSE.match(line)
        n = int(m.group(2)) if m else 0
        # `^7.` where verse 27 is due: what survived is the tail of the
        # number that should be there, which is enough to know it. Only
        # where something did survive in its place — a bare `7.` is a
        # footnote's number, not a damaged twenty-seven.
        if m and (want <= n <= want + 3
                  or (n < want and m.group(1)
                      and str(want).endswith(m.group(2)))):
            if cur:
                verses.append(cur)
            n = n if n >= want else want
            cur = [str(n), m.group(3).strip()]
            want = n + 1
        elif cur and line.strip():
            cur[1] += ' ' + line.strip()
    if cur:
        verses.append(cur)
    return [(n, re.sub(r'\s+', ' ', t).strip()) for n, t in verses]


# --- the Book of Mormon --------------------------------------------------

# Gutenberg's headings, in order, with the name each book is cited by and the
# number of chapters it should have. The counts are the check: a parse that
# does not reproduce them has gone wrong somewhere and says so.
BOM_BOOKS = [
    ('THE FIRST BOOK OF NEPHI', '1 Nephi', 22),
    ('THE SECOND BOOK OF NEPHI', '2 Nephi', 33),
    ('THE BOOK OF JACOB', 'Jacob', 7),
    ('THE BOOK OF ENOS', 'Enos', 1),
    ('THE BOOK OF JAROM', 'Jarom', 1),
    ('THE BOOK OF OMNI', 'Omni', 1),
    ('THE WORDS OF MORMON', 'Words of Mormon', 1),
    ('THE BOOK OF MOSIAH', 'Mosiah', 29),
    ('THE BOOK OF ALMA', 'Alma', 63),
    ('THE BOOK OF HELAMAN', 'Helaman', 16),
    ('THIRD BOOK OF NEPHI', '3 Nephi', 30),
    ('FOURTH NEPHI', '4 Nephi', 1),
    ('THE BOOK OF MORMON', 'Mormon', 9),
    ('THE BOOK OF ETHER', 'Ether', 15),
    ('THE BOOK OF MORONI', 'Moroni', 10),
]

RE_BOM_VERSE = re.compile(
    r'^(?:(?:[1-4] )?[A-Z][a-z]+ )?(\d{1,3}):(\d{1,3})(?:[ \t](.*))?$')

# Five verses in the Gutenberg text begin in the middle of a line rather
# than at the start of one — `…who had created them. 2:13 Neither did…`
# — and a parser reading line by line simply loses them.
RE_BOM_INLINE = re.compile(
    r'(?<=[.!?;:’”"])[ \t]+((?:[1-4] )?(?:[A-Z][a-z]+ )?\d{1,3}:\d{1,3})(?=\s|$)')
RE_BOM_CHAPTER = re.compile(r'^\s*[\w ]{0,20}Chapter \d+\s*$')


def split_book_of_mormon(text):
    """-> [(short name, [(chapter, [(verse, text)])])]"""
    lines = RE_BOM_INLINE.sub(r'\n\1', text).split('\n')
    # The books are headed in order, so they are found in order. Two things
    # would otherwise confuse it: `THE BOOK OF MORMON` heads both the whole
    # volume and one book inside it, and the table of contents lists all
    # fifteen headings one after another. Requiring a real gap between one
    # book and the next passes over the contents and lands on the text.
    GAP = 40
    starts, pos = [], 0
    for j, (heading, _short, _n) in enumerate(BOM_BOOKS):
        for i in range(pos, len(lines)):
            if lines[i].strip().startswith(heading):
                starts.append((i, j))
                pos = i + GAP
                break
        else:
            raise SystemExit(f'book of mormon: no heading for {heading}')

    books = []
    for k, (start, j) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        _heading, short, _n = BOM_BOOKS[j]
        chapters, cur_ch, cur_v = [], None, None
        for line in lines[start:end]:
            if RE_BOM_CHAPTER.match(line):
                continue
            m = RE_BOM_VERSE.match(line)
            if m:
                # Alma 24:18 is marked at the end of its line, with the
                # verse itself beginning on the next one.
                ch, vs, body = m.group(1), m.group(2), m.group(3) or ''
                if cur_ch is None or cur_ch[0] != ch:
                    cur_ch = (ch, [])
                    chapters.append(cur_ch)
                cur_v = [vs, body]
                cur_ch[1].append(cur_v)
            elif cur_v is not None and line.strip():
                cur_v[1] += ' ' + line.strip()
            elif not line.strip():
                cur_v = None         # a blank line ends a verse
        books.append((short, [(c, [(v, re.sub(r'\s+', ' ', t).strip())
                                   for v, t in vs]) for c, vs in chapters]))
    return books


def build_book_of_mormon(report):
    path = os.path.join(GUTENBERG, 'pg-17.txt')
    if not os.path.isfile(path):
        print('  book of mormon: pg-17.txt not fetched, skipping')
        return []
    with open(path, encoding='utf-8', errors='replace') as fh:
        text = _lines(fh.read())
    body = text.split('*** START OF THE PROJECT GUTENBERG', 1)[-1]
    body = body.split('*** END OF THE PROJECT GUTENBERG', 1)[0]

    made, wrong = [], []
    for order, (short, chapters) in enumerate(split_book_of_mormon(body), 1):
        expected = dict((s, n) for _h, s, n in BOM_BOOKS)[short]
        if len(chapters) != expected:
            wrong.append(f'{short}: {len(chapters)} chapters, expected {expected}')
        w = Work(id='lds-bom-' + corpus.slugify(short),
                 title=short, religion='christianity', section='restoration',
                 sort=order, structure='verse', canon='canonical',
                 subtitle='The Book of Mormon',
                 translation='The Book of Mormon',
                 translator='Joseph Smith, Jr.', year=1830,
                 modernization=TIER,
                 rights=rights('Published in 1830, and so in the public '
                               'domain. Text from Project Gutenberg.',
                               'https://www.gutenberg.org/ebooks/17'),
                 provenance={'source': 'Project Gutenberg ebook 17',
                             'source_file': 'sources/collector/gutenberg/pg-17.txt'})
        for cn, verses in chapters:
            ch = Chapter(cn, f'{short} {cn}')
            for vn, vtext in verses:
                said, src = modernize.pair(vtext, TIER, report)
                ch.verses.append({'n': vn, 'text': said, 'notes': [],
                                  **({'src': src} if src else {})})
            w.add(ch)
        made.append(w.save())
    total_ch = sum(m['stats']['chapters'] for m in made)
    total_v = sum(m['stats']['verses'] for m in made)
    print(f'  book of mormon: {len(made)} books, {total_ch} chapters, '
          f'{total_v} verses' + (f'  ! {"; ".join(wrong)}' if wrong else ''))
    return made


# --- the Doctrine and Covenants ------------------------------------------

RE_SECTION = re.compile(r'^\s*[.,\'"]*\s*SECTION\s+[0-9IVXLCOG]+\s*\.?\s*$')
DC_SECTIONS = 136


def build_doctrine_and_covenants(report):
    raw = read('doctrine-and-covenants')
    lines = raw.split('\n')
    starts = [i for i, ln in enumerate(lines) if RE_SECTION.match(ln)]
    spec = SCANS['doctrine-and-covenants']
    w = Work(id='lds-doctrine-and-covenants',
             title='The Doctrine and Covenants',
             religion='christianity', section='restoration', sort=20,
             structure='verse', canon='canonical',
             subtitle='The revelations given to Joseph Smith',
             translation=spec['title'], translator='Joseph Smith, Jr.',
             year=spec['year'], modernization=TIER,
             rights=rights(f'Published in {spec["year"]} by '
                           f'{spec["publisher"]}, and so in the public domain '
                           f'in the United States.',
                           f'https://archive.org/details/{spec["id"]}'),
             provenance={'source': f'archive.org {spec["id"]} ({spec["year"]})',
                         'note': 'Sections are numbered in the order they '
                                 'stand; the scan misreads several of the '
                                 'printed numbers.'})
    # One heading did not survive the scan — section 61's. It shows as a
    # block whose verse numbering runs to the end of one section and then
    # starts again at 1, which is the signature of a lost heading and the
    # place to cut. Sections are then numbered by where they fall.
    blocks = []
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        whole = clean_scan('\n'.join(lines[start + 1:end]))
        for j, block in enumerate(split_lost_headings(whole)):
            paras = [p.strip() for p in block.split('\n\n') if p.strip()]
            verses = paragraphs_to_verses(block)
            if not verses and len(paras) > 1 and _letters(block) > 80:
                # Section 13 is a single sentence and is printed without a
                # verse number, because there is nothing to number it
                # against. It is still a verse.
                verses = [('1', re.sub(r'\s+', ' ', ' '.join(paras[1:])))]
            if verses:
                blocks.append((verses, paras[0] if j == 0 and paras else ''))

    for n, (verses, head) in enumerate(blocks, 1):
        ch = Chapter(str(n), f'Section {n}')
        # What is printed above verse 1 says when and where the revelation
        # was given, which is the reader's whole bearing on it.
        if head and not RE_VERSE.match(head) and _letters(head) > 20:
            ch.blocks.append({'k': 'meta',
                              't': modernize.modernize(
                                  re.sub(r'\s+', ' ', head), TIER, report)})
        for vn, vtext in verses:
            said, src = modernize.pair(vtext, TIER, report)
            ch.verses.append({'n': vn, 'text': said, 'notes': [],
                              **({'src': src} if src else {})})
        w.add(ch)
    m = w.save()
    note = '' if m['stats']['chapters'] == DC_SECTIONS else \
        f'  ! expected {DC_SECTIONS}'
    print(f'  doctrine and covenants: {m["stats"]["chapters"]} sections, '
          f'{m["stats"]["verses"]} verses ({len(starts)} headings in the '
          f'scan){note}')
    return [m]


# --- the Pearl of Great Price --------------------------------------------
#
# Five books in three printed divisions: the two long ones head themselves,
# and the last three sit under `WRITINGS OF JOSEPH SMITH` divided only by a
# roman numeral on a line of its own.
PGP_PARTS = [
    ('The Book of Moses', 'Moses', 8, 30,
     r'^\s*THE BOOK OF MOSES\.?\s*$', None),
    ('The Book of Abraham', 'Abraham', 5, 31,
     r'^\s*THE BOOK OF ABRAHAM\.?\s*$', None),
    ('Joseph Smith—Matthew', 'Joseph Smith—Matthew', 1, 32,
     r'^\s*WRITINGS OF JOSEPH SMITH\.?\s*$', r'^\s*II\.\s*$'),
    ('Joseph Smith—History', 'Joseph Smith—History', 1, 33,
     r'^\s*II\.\s*$', r'^\s*III\.\s*$'),
    ('The Articles of Faith', 'The Articles of Faith', 1, 34,
     r'^\s*III\.\s*$', None),
]

# `CHAPTER` comes off the scanner as CHAPTEE, CHAPTEK, and its numeral as JV
# for IV or IIL for III. The word is matched by how far it is from the right
# one rather than by spelling it out, and the numeral is then ignored — the
# chapters are counted, like everything else here.
RE_HEADING_SHAPE = re.compile(
    r'^\s*([A-Za-z]{7})[,.]?\s*([IVXLCTJ0-9OG]{1,6})\s*[.,«»^*\'\"]*\s*$')


def is_chapter_heading(line):
    m = RE_HEADING_SHAPE.match(line)
    if not m:
        return False
    # All caps, or it is the word `chapter` inside a sentence.
    return (m.group(1).isupper()
            and sum(a != b for a, b in zip(m.group(1), 'CHAPTER')) <= 2)


def _find(lines, pattern, after=0):
    rx = re.compile(pattern)
    for i in range(after, len(lines)):
        if rx.match(lines[i]):
            return i
    return -1


def build_pearl_of_great_price(report):
    lines = read('pearl-of-great-price').split('\n')
    spec = SCANS['pearl-of-great-price']
    # Everything before the body is the contents, which lists the same
    # headings; the body starts at the last `THE BOOK OF MOSES`.
    body_at = max(i for i, ln in enumerate(lines)
                  if re.match(r'^\s*THE BOOK OF MOSES\.?\s*$', ln))

    # Where each part opens, so that each can be closed at the next.
    opens_at, pos = [], body_at
    for part in PGP_PARTS:
        at = _find(lines, part[4], pos)
        if at < 0:
            print(f'  ! pearl of great price: no heading for {part[0]}')
        opens_at.append(at)
        pos = max(pos, at + 1)

    made = []
    for k, (title, short, expected, sort, _opens, closes) in enumerate(PGP_PARTS):
        start = opens_at[k]
        if start < 0:
            continue
        later = [a for a in opens_at[k + 1:] if a > start]
        end = min(later) if later else len(lines)
        if closes:
            shut = _find(lines, closes, start + 1)
            if 0 <= shut < end:
                end = shut
        block_lines = lines[start + 1:end]
        marks = [i for i, ln in enumerate(block_lines)
                 if is_chapter_heading(ln)]
        spans = ([(marks[i] + 1, marks[i + 1] if i + 1 < len(marks)
                   else len(block_lines)) for i in range(len(marks))]
                 if marks else [(0, len(block_lines))])

        # The em dash in `Joseph Smith—History` slugifies into a run-on;
        # it is a separator, so it is spelt as one before slugifying.
        w = Work(id='lds-pgp-' + corpus.slugify(short.replace('—', ' ')),
                 title=title, religion='christianity', section='restoration',
                 sort=sort, structure='verse', canon='canonical',
                 subtitle='The Pearl of Great Price',
                 translation=spec['title'], translator='Joseph Smith, Jr.',
                 year=spec['year'], modernization=TIER,
                 rights=rights(f'Published in {spec["year"]} by '
                               f'{spec["publisher"]}, and so in the public '
                               f'domain in the United States.',
                               f'https://archive.org/details/{spec["id"]}'),
                 provenance={'source': f'archive.org {spec["id"]} '
                                       f'({spec["year"]})'})
        for n, (a, b) in enumerate(spans, 1):
            block = clean_scan('\n'.join(block_lines[a:b]))
            verses = paragraphs_to_verses(block)
            if not verses:
                continue
            ch = Chapter(str(n), f'{short} {n}' if len(spans) > 1 else title)
            for vn, vtext in verses:
                said, src = modernize.pair(vtext, TIER, report)
                ch.verses.append({'n': vn, 'text': said, 'notes': [],
                                  **({'src': src} if src else {})})
            w.add(ch)
        if len(w.chapters) != expected:
            print(f'  ! {title}: {len(w.chapters)} chapters, '
                  f'expected {expected}')
        if w.chapters:
            m = w.save()
            made.append(m)
            print(f'    {title}: {m["stats"]["chapters"]} ch, '
                  f'{m["stats"]["verses"]} verses')
    total = sum(m['stats']['verses'] for m in made)
    print(f'  pearl of great price: {len(made)} books, {total} verses')
    return made


def main():
    fetch()
    report = modernize.Report()
    made = build_book_of_mormon(report)
    made += build_doctrine_and_covenants(report)
    made += build_pearl_of_great_price(report)
    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'mormon.json'),
                      report.as_dict())
    words = sum(m['stats']['words'] for m in made)
    print(f'mormon: {len(made)} works, {words:,} words')


if __name__ == '__main__':
    main()
