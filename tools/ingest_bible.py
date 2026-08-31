"""Ingest the World English Bible (Updated) from USFM into the corpus.

Reuses `bible/usfm.py`, the parser the print edition uses, so the archive and
the book are reading the same text through the same code. That parser already
applies the safe modernization tier as it strips the Strong's wrappers, which
is the right tier here: the World English Bible is a modern translation, and
the heavy tier's `art` -> `are` would damage it.

The thirty-nine books of the Hebrew scriptures are filed under Christianity,
in Christian order. They are NOT also filed under Judaism: that shelf carries
them in the 1917 Jewish Publication Society translation, in the Tanakh's own
order and division, so each tradition meets them in its own arrangement and
its own English. The two translations still meet on the comparison page.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bible import canon, usfm                                    # noqa: E402
from tools import corpus                                          # noqa: E402
from tools.corpus import Chapter, Work, rights                    # noqa: E402

USFM_DIR = os.path.join(corpus.ROOT, 'src', 'usfm_u')

WEB_RIGHTS = rights(
    'Dedicated to the public domain by eBible.org. The World English Bible '
    '(Updated) is free to copy, print, sell and give away.',
    'https://ebible.org/engwebu/')

# --- the Christian order --------------------------------------------------
# (usfm id, title, christian section, jewish section or None, jewish order)
OT = [
    ('GEN', 'Genesis', 'torah'), ('EXO', 'Exodus', 'torah'),
    ('LEV', 'Leviticus', 'torah'), ('NUM', 'Numbers', 'torah'),
    ('DEU', 'Deuteronomy', 'torah'),
    ('JOS', 'Joshua', 'neviim'), ('JDG', 'Judges', 'neviim'),
    ('RUT', 'Ruth', 'ketuvim'),
    ('1SA', '1 Samuel', 'neviim'), ('2SA', '2 Samuel', 'neviim'),
    ('1KI', '1 Kings', 'neviim'), ('2KI', '2 Kings', 'neviim'),
    ('1CH', '1 Chronicles', 'ketuvim'), ('2CH', '2 Chronicles', 'ketuvim'),
    ('EZR', 'Ezra', 'ketuvim'), ('NEH', 'Nehemiah', 'ketuvim'),
    ('EST', 'Esther', 'ketuvim'), ('JOB', 'Job', 'ketuvim'),
    ('PSA', 'Psalms', 'ketuvim'), ('PRO', 'Proverbs', 'ketuvim'),
    ('ECC', 'Ecclesiastes', 'ketuvim'), ('SNG', 'Song of Songs', 'ketuvim'),
    ('ISA', 'Isaiah', 'neviim'), ('JER', 'Jeremiah', 'neviim'),
    ('LAM', 'Lamentations', 'ketuvim'), ('EZK', 'Ezekiel', 'neviim'),
    ('DAN', 'Daniel', 'ketuvim'),
    ('HOS', 'Hosea', 'neviim'), ('JOL', 'Joel', 'neviim'),
    ('AMO', 'Amos', 'neviim'), ('OBA', 'Obadiah', 'neviim'),
    ('JON', 'Jonah', 'neviim'), ('MIC', 'Micah', 'neviim'),
    ('NAM', 'Nahum', 'neviim'), ('HAB', 'Habakkuk', 'neviim'),
    ('ZEP', 'Zephaniah', 'neviim'), ('HAG', 'Haggai', 'neviim'),
    ('ZEC', 'Zechariah', 'neviim'), ('MAL', 'Malachi', 'neviim'),
]

# The Tanakh's own order, which is not the Christian one: the Writings come
# last, and the twelve minor prophets are one book among the Prophets.
TANAKH_ORDER = [
    'GEN', 'EXO', 'LEV', 'NUM', 'DEU',
    'JOS', 'JDG', '1SA', '2SA', '1KI', '2KI',
    'ISA', 'JER', 'EZK',
    'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP', 'HAG',
    'ZEC', 'MAL',
    'PSA', 'PRO', 'JOB', 'SNG', 'RUT', 'LAM', 'ECC', 'EST', 'DAN',
    'EZR', 'NEH', '1CH', '2CH',
]

NT = [
    ('MAT', 'Matthew'), ('MRK', 'Mark'), ('LUK', 'Luke'), ('JHN', 'John'),
    ('ACT', 'Acts'), ('ROM', 'Romans'), ('1CO', '1 Corinthians'),
    ('2CO', '2 Corinthians'), ('GAL', 'Galatians'), ('EPH', 'Ephesians'),
    ('PHP', 'Philippians'), ('COL', 'Colossians'),
    ('1TH', '1 Thessalonians'), ('2TH', '2 Thessalonians'),
    ('1TI', '1 Timothy'), ('2TI', '2 Timothy'), ('TIT', 'Titus'),
    ('PHM', 'Philemon'), ('HEB', 'Hebrews'), ('JAS', 'James'),
    ('1PE', '1 Peter'), ('2PE', '2 Peter'), ('1JN', '1 John'),
    ('2JN', '2 John'), ('3JN', '3 John'), ('JUD', 'Jude'),
    ('REV', 'Revelation'),
]


def usfm_files():
    files = {}
    for f in os.listdir(USFM_DIR):
        if not f.endswith('.usfm'):
            continue
        path = os.path.join(USFM_DIR, f)
        bid = f.split('-', 1)[1].replace('engwebu.usfm', '') if '-' in f else ''
        if bid:
            files[bid] = path
    return files


def to_chapters(book):
    """Walk the parsed USFM blocks into chapters of verses."""
    chapters, cur, verse = [], None, None
    # A section heading is met BEFORE the verse it opens, so it waits here
    # until that verse arrives and can be named. Without this the headings
    # would carry no position and pile up at one end of the chapter.
    pending = []

    def flush_verse():
        nonlocal verse
        if verse and verse['text'].strip():
            verse['text'] = ' '.join(verse['text'].split())
            cur.verses.append(verse)
        verse = None

    for blk in book.blocks:
        if blk.style == 'c':
            flush_verse()
            num = blk.items[0].num
            cur = Chapter(num, f'Chapter {num}')
            chapters.append(cur)
            pending = []
            continue
        if cur is None:                      # front matter before chapter 1
            continue
        if blk.style in ('s1', 's2', 'ms1', 'ms2', 'd'):
            heading = ''.join(i.s for i in blk.items
                              if isinstance(i, usfm.Text)).strip()
            if heading:
                flush_verse()
                pending.append(heading)
            continue
        # A verse can run across several blocks — poetry sets each line as
        # its own \q1, and a verse often continues into the next paragraph.
        # The line break carried the separation in the source, so joining the
        # blocks needs a space put back, or the text reads "increased!Many".
        if verse is not None and verse['text'] and not verse['text'][-1].isspace():
            verse['text'] += ' '

        for it in blk.items:
            if isinstance(it, usfm.Verse):
                flush_verse()
                for heading in pending:
                    cur.blocks.append({'k': 'h', 't': heading, 'at': it.num})
                pending = []
                verse = {'n': it.num, 'text': '', 'notes': []}
            elif isinstance(it, usfm.Text):
                if verse is None:
                    verse = {'n': '', 'text': '', 'notes': []}
                verse['text'] += it.s
            elif isinstance(it, usfm.Note):
                body = ' '.join(t for _, t in it.parts).strip()
                if body and verse is not None:
                    verse['notes'].append({'ref': it.ref, 'text': body})
    flush_verse()
    return [c for c in chapters if c.verses]


def clean_sc(s):
    """Drop the small-caps sentinels the typesetter uses."""
    return s.replace('\x01', '').replace('\x02', '')


def build_work(bid, title, section, sort, files, *, canon_status='canonical',
               also_in=()):
    book = usfm.parse(files[bid])
    w = Work(id=f'webu-{bid.lower()}', title=title, religion='christianity',
             section=section, sort=sort, structure='verse',
             canon=canon_status,
             translation='World English Bible (Updated)',
             translator='eBible.org', year=2022,
             modernization='safe', rights=WEB_RIGHTS,
             provenance={'source': 'eBible.org engwebu USFM',
                         'source_file': os.path.relpath(files[bid], corpus.ROOT)},
             also_in=list(also_in))
    for c in to_chapters(book):
        for v in c.verses:
            v['text'] = clean_sc(v['text'])
            for n in v['notes']:
                n['text'] = clean_sc(n['text'])
        w.add(c)
    return w


def main():
    files = usfm_files()
    missing = [b for b, _, _ in OT] + [b for b, _ in NT]
    missing = [b for b in missing if b not in files]
    if missing:
        sys.exit(f'missing USFM for: {", ".join(missing)}')

    tanakh_pos = {b: i for i, b in enumerate(TANAKH_ORDER)}
    made = []

    # These books are NOT cross-filed into Judaism. Judaism carries the
    # Hebrew scriptures in its own translation — the 1917 Jewish Publication
    # Society text, in the Tanakh's own order — and listing a Christian
    # translation beside it would put Genesis in the shelf twice. The two
    # still meet on the comparison page, which pairs editions by title
    # across religions rather than by where they are filed.
    for i, (bid, title, _jsection) in enumerate(OT):
        made.append(build_work(bid, title, 'old-testament', i, files).save())

    for i, (bid, title) in enumerate(NT):
        made.append(build_work(bid, title, 'new-testament', i, files).save())

    # The deuterocanon and the wider apocrypha, in the order the print
    # edition sets them, several of them slices of a larger source book.
    for i, (bid, title) in enumerate(canon.DEUTEROCANONICAL):
        spec = canon.DERIVED.get(bid)
        src = spec['src'] if spec else bid
        if src not in files:
            print(f'  skip {bid}: no source')
            continue
        made.append(build_work(bid, title, 'deuterocanon', i, files,
                               canon_status='deuterocanonical',
                               ).save() if not spec else
                    _derived(bid, title, spec, 'deuterocanon', i, files,
                             'deuterocanonical'))

    for i, (bid, title) in enumerate(canon.WIDER):
        spec = canon.DERIVED.get(bid)
        if (spec['src'] if spec else bid) not in files:
            print(f'  skip {bid}: no source')
            continue
        made.append(build_work(bid, title, 'apocrypha', i, files,
                               canon_status='noncanonical').save()
                    if not spec else
                    _derived(bid, title, spec, 'apocrypha', i, files,
                             'noncanonical'))

    print(f'bible: {len(made)} works, '
          f'{sum(m["stats"]["chapters"] for m in made)} chapters, '
          f'{sum(m["stats"]["verses"] for m in made)} verses')


def _derived(bid, title, spec, section, sort, files, canon_status):
    """A book printed under its own title that is a slice of a source book."""
    from bible.build import slice_book
    book = slice_book(usfm.parse(files[spec['src']]),
                      dict(spec, id=bid, name=title))
    w = Work(id=f'webu-{bid.lower()}', title=title, religion='christianity',
             section=section, sort=sort, structure='verse',
             canon=canon_status,
             translation='World English Bible (Updated)',
             translator='eBible.org', year=2022, modernization='safe',
             rights=WEB_RIGHTS,
             provenance={'source': 'eBible.org engwebu USFM',
                         'source_file': os.path.relpath(files[spec['src']],
                                                        corpus.ROOT),
                         'note': f'the portion of {spec["src"]} printed as {title}'})
    for c in to_chapters(book):
        for v in c.verses:
            v['text'] = clean_sc(v['text'])
            for n in v['notes']:
                n['text'] = clean_sc(n['text'])
        w.add(c)
    return w.save()


if __name__ == '__main__':
    main()
