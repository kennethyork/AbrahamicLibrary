"""The citation index: who quotes what.

The Church Fathers argue by quotation. So do the rabbis, the apologists, the
Reformers and every commentary in this library — and all of them print their
references in the text: `Gen. i. 1`, `Matt. 5:9`, `Sura ii. 255`. Nineteen
million words of Fathers alone are threaded with them.

Pulled out and indexed the other way round, that thread becomes the thing a
reading app has and a study app must: open Isaiah 7 and see the forty works in
this archive that cite verse 14, and go straight to what each of them says.

A citation is stored against a canonical reference — `isaiah|7|14` — and not
against a translation, so a reference found in a Catholic commentary lights up
the same verse in the Jewish Publication Society's translation of it.

    .venv/bin/python -m tools.build_links
"""
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, parallel                                 # noqa: E402

DB = os.path.join(corpus.CORPUS, 'links.sqlite')

# --- what the books are called when they are cited -------------------------
#
# Every form the sources actually use, gathered by reading them: the full
# name, the Society of Biblical Literature abbreviation, the older English
# ones, and the ones with the stop left off.
BOOKS = {
    'genesis': ['genesis', 'gen', 'ge', 'gn'],
    'exodus': ['exodus', 'exod', 'exo', 'ex'],
    'leviticus': ['leviticus', 'lev', 'le', 'lv'],
    'numbers': ['numbers', 'num', 'nu', 'nm', 'nb'],
    'deuteronomy': ['deuteronomy', 'deut', 'deu', 'dt'],
    'joshua': ['joshua', 'josh', 'jos'],
    'judges': ['judges', 'judg', 'jdg', 'jg'],
    'ruth': ['ruth', 'rth', 'ru'],
    '1-samuel': ['1 samuel', 'i samuel', '1 sam', 'i sam', '1 sa', '1 kings' ],
    '2-samuel': ['2 samuel', 'ii samuel', '2 sam', 'ii sam', '2 sa'],
    '1-kings': ['1 kings', 'i kings', '1 kgs', 'i kgs', '3 kings'],
    '2-kings': ['2 kings', 'ii kings', '2 kgs', 'ii kgs', '4 kings'],
    '1-chronicles': ['1 chronicles', 'i chronicles', '1 chron', '1 chr'],
    '2-chronicles': ['2 chronicles', 'ii chronicles', '2 chron', '2 chr'],
    'ezra': ['ezra', 'ezr'],
    'nehemiah': ['nehemiah', 'neh', 'ne'],
    'esther': ['esther', 'esth', 'est'],
    'job': ['job', 'jb'],
    'psalms': ['psalms', 'psalm', 'psa', 'pss', 'ps'],
    'proverbs': ['proverbs', 'prov', 'pro', 'prv', 'pr'],
    'ecclesiastes': ['ecclesiastes', 'eccles', 'eccl', 'ecc', 'qoheleth'],
    'song-of-songs': ['song of songs', 'song of solomon', 'canticles', 'cant', 'song'],
    'isaiah': ['isaiah', 'isai', 'isa', 'is'],
    'jeremiah': ['jeremiah', 'jerem', 'jer', 'jr'],
    'lamentations': ['lamentations', 'lam', 'lm'],
    'ezekiel': ['ezekiel', 'ezek', 'eze', 'ezk'],
    'daniel': ['daniel', 'dan', 'dn'],
    'hosea': ['hosea', 'hos', 'ho'],
    'joel': ['joel', 'jol', 'jl'],
    'amos': ['amos', 'amo', 'am'],
    'obadiah': ['obadiah', 'obad', 'oba', 'ob'],
    'jonah': ['jonah', 'jon', 'jnh'],
    'micah': ['micah', 'mic', 'mi'],
    'nahum': ['nahum', 'nah', 'na'],
    'habakkuk': ['habakkuk', 'habak', 'hab', 'hb'],
    'zephaniah': ['zephaniah', 'zeph', 'zep'],
    'haggai': ['haggai', 'hag', 'hg'],
    'zechariah': ['zechariah', 'zech', 'zec', 'zch'],
    'malachi': ['malachi', 'mal', 'ml'],
    'matthew': ['matthew', 'matt', 'mat', 'mt'],
    'mark': ['mark', 'mrk', 'mk', 'mr'],
    'luke': ['luke', 'luk', 'lk'],
    'john': ['john', 'joh', 'jhn', 'jn'],
    'acts': ['acts of the apostles', 'acts', 'act'],
    'romans': ['romans', 'rom', 'ro', 'rm'],
    '1-corinthians': ['1 corinthians', 'i corinthians', '1 cor', 'i cor'],
    '2-corinthians': ['2 corinthians', 'ii corinthians', '2 cor', 'ii cor'],
    'galatians': ['galatians', 'gal', 'ga'],
    'ephesians': ['ephesians', 'ephes', 'eph'],
    'philippians': ['philippians', 'philip', 'phil', 'php'],
    'colossians': ['colossians', 'coloss', 'col'],
    '1-thessalonians': ['1 thessalonians', 'i thessalonians', '1 thess', '1 th'],
    '2-thessalonians': ['2 thessalonians', 'ii thessalonians', '2 thess', '2 th'],
    '1-timothy': ['1 timothy', 'i timothy', '1 tim', 'i tim'],
    '2-timothy': ['2 timothy', 'ii timothy', '2 tim', 'ii tim'],
    'titus': ['titus', 'tit', 'ti'],
    'philemon': ['philemon', 'philem', 'phlm'],
    'hebrews': ['hebrews', 'heb', 'hbr'],
    'james': ['james', 'jas', 'jm'],
    '1-peter': ['1 peter', 'i peter', '1 pet', 'i pet'],
    '2-peter': ['2 peter', 'ii peter', '2 pet', 'ii pet'],
    '1-john': ['1 john', 'i john', '1 jn', 'i jn'],
    '2-john': ['2 john', 'ii john', '2 jn'],
    '3-john': ['3 john', 'iii john', '3 jn'],
    'jude': ['jude', 'jud', 'jde'],
    'revelation': ['revelation', 'apocalypse', 'rev', 'apoc'],
    'tobit': ['tobit', 'tob'],
    'judith': ['judith', 'jdt'],
    'wisdom': ['wisdom of solomon', 'wisdom', 'wis'],
    'sirach': ['ecclesiasticus', 'sirach', 'sir'],
    'baruch': ['baruch', 'bar'],
    '1-maccabees': ['1 maccabees', 'i maccabees', '1 macc', '1 mac'],
    '2-maccabees': ['2 maccabees', 'ii maccabees', '2 macc', '2 mac'],
    'quran': ['sura', 'surah', 'sur', 'koran', 'qur’an', "qur'an", 'quran'],
}

# The title each canonical key is shown under.
LABEL = {k: ' '.join(w.capitalize() for w in k.split('-')) for k in BOOKS}
LABEL['song-of-songs'] = 'Song of Songs'
LABEL['quran'] = 'The Qur’an'
LABEL['1-samuel'] = '1 Samuel'

ALIAS = {}
for _key, _names in BOOKS.items():
    for _n in _names:
        ALIAS[_n] = _key

# `Gen. i. 1`, `Genesis 1:1`, `Matt. v. 9`, `Sura ii. 255`. The chapter may be
# a roman numeral, which is how the nineteenth century printed it.
NAMES = sorted(ALIAS, key=len, reverse=True)
RE_CITE = re.compile(
    r'\b(' + '|'.join(re.escape(n) for n in NAMES) + r')\.?\s*'
    r'(\d{1,3}|[ivxlcIVXLC]{1,7})\s*[:.]\s*(\d{1,3})\b', re.I)

ROMAN = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100}


def to_int(s):
    if s.isdigit():
        return int(s)
    s = s.lower()
    if not s or any(c not in ROMAN for c in s):
        return 0
    total, prev = 0, 0
    for c in reversed(s):
        v = ROMAN[c]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def cite_targets(text):
    """-> Counter of `book|chapter|verse` found in a run of text."""
    found = Counter()
    for m in RE_CITE.finditer(text):
        key = ALIAS.get(m.group(1).lower())
        c, v = to_int(m.group(2)), int(m.group(3))
        # The bounds are the real ones: 150 psalms, and Psalm 119 has 176
        # verses — but sura 2 has 286, so the Qur'an gets its own ceiling.
        # Without this every citation of Ayat al-Kursi was thrown away.
        top = 286 if key == 'quran' else 176
        if not key or not (0 < c <= 150) or not (0 < v <= top):
            continue
        found[f'{key}|{c}|{v}'] += 1
    return found


def scan(wid):
    """One work, in its own process. -> (wid, title, religion, {target: n})"""
    for religion in corpus.RELIGIONS:
        d = os.path.join(corpus.WORKS, religion, wid)
        meta = corpus.read_json(os.path.join(d, 'work.json'))
        if not meta:
            continue
        found = Counter()
        cdir = os.path.join(d, 'c')
        for fn in os.listdir(cdir):
            ch = corpus.read_json(os.path.join(cdir, fn)) or {}
            parts = [v['text'] for v in ch.get('verses', [])]
            parts += [b['t'] for b in ch.get('blocks', [])]
            if parts:
                found.update(cite_targets('\n'.join(parts)))
        return (wid, meta['title'], religion, meta['section'], dict(found))
    return None


def main():
    works = []
    for religion in corpus.RELIGIONS:
        base = os.path.join(corpus.WORKS, religion)
        if os.path.isdir(base):
            works += sorted(os.listdir(base))

    rows = parallel.run(scan, works, on_result=parallel.progress('links'))

    by_target = defaultdict(list)
    for wid, title, religion, section, found in rows:
        for target, n in found.items():
            by_target[target].append((wid, title, religion, section, n))

    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript("""
        PRAGMA journal_mode = OFF;
        CREATE TABLE cite (
            target   TEXT NOT NULL,   -- `isaiah|7|14`
            work     TEXT NOT NULL,
            title    TEXT NOT NULL,
            religion TEXT NOT NULL,
            section  TEXT NOT NULL,
            n        INTEGER NOT NULL
        );
        CREATE TABLE total (target TEXT PRIMARY KEY, works INTEGER, n INTEGER);
    """)
    db.executemany('INSERT INTO cite VALUES (?,?,?,?,?,?)',
                   ((t,) + row for t, rs in by_target.items() for row in rs))
    db.executemany('INSERT INTO total VALUES (?,?,?)',
                   ((t, len(rs), sum(r[4] for r in rs))
                    for t, rs in by_target.items()))
    # Which work is which book. A citation resolves to `isaiah|7|14`, and the
    # reader needs to go the other way — from the work it has open to the
    # canonical name that citations of it were filed under. Titles are matched
    # against the same alias table the scanner used, so the two can never
    # drift apart.
    db.execute('CREATE TABLE book (work TEXT PRIMARY KEY, key TEXT, label TEXT)')
    named = []
    for wid, title, religion, section, _found in rows:
        key = ALIAS.get(re.sub(r'\s+', ' ', title).strip().lower())
        if key and section in ('old-testament', 'new-testament', 'deuterocanon',
                               'torah', 'neviim', 'ketuvim', 'quran'):
            named.append((wid, key, LABEL.get(key, title)))
    db.executemany('INSERT OR REPLACE INTO book VALUES (?,?,?)', named)

    db.executescript("""
        CREATE INDEX cite_target ON cite(target, n DESC);
        CREATE INDEX cite_work ON cite(work);
    """)
    db.commit()

    citations = sum(sum(f.values()) for *_x, f in rows)
    print(f'links: {citations:,} citations to {len(by_target):,} verses, '
          f'from {sum(1 for *_x, f in rows if f):,} of {len(rows):,} works '
          f'({os.path.getsize(DB) / 1e6:.0f} MB)')
    print(f'    {len(named)} works recognised as a cited book')
    top = sorted(by_target.items(), key=lambda kv: -len(kv[1]))[:8]
    for t, rs in top:
        book, c, v = t.split('|')
        print(f'    {LABEL.get(book, book)} {c}:{v} — cited in {len(rs)} works')
    db.close()


if __name__ == '__main__':
    main()
