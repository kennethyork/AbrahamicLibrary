"""Strong's dictionaries, as a lexicon the archive can look words up in.

James Strong's Hebrew and Greek dictionaries of 1894 are the reference every
English Bible student has used for a century, and they are out of copyright.
archive.org holds both, scanned and marked Public Domain, and the scan is
clean enough to parse: every definition ends with the marker the scanner's own
software left behind — `SHD (6) .2` — which names the entry it belongs to more
reliably than any header could.

The useful part is the tail of each definition. Strong wrote his entries to
end with the English words the King James translators actually used for that
Hebrew or Greek word, after a `:--`. Indexed backwards, that turns into the
thing this archive had no answer for: type `mercy` and see the six different
words underneath it.

The Greek of the scan is not usable — OCR renders ἀγέλη as `ayeAn` — so the
transliteration is what is kept, which is what an English reader needs anyway.

    .venv/bin/python -m tools.ingest_strongs
"""
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import american, corpus, modernize                     # noqa: E402

DEST = os.path.join(corpus.ROOT, 'sources', 'collector', 'strongs')
DB = os.path.join(corpus.CORPUS, 'strongs.sqlite')
UA = 'AbrahamicArchive/1.0 (public-domain text collection)'

SCANS = {
    'hebrew': {
        'id': 'strongs-hebrew-dictionary-kjv-ellen-g-white-estate',
        'mark': 'SHD', 'letter': 'H', 'entries': 8674,
        'title': "Strong's Hebrew Dictionary",
    },
    'greek': {
        'id': 'strongs-greek-dictionary-kjv--ellen-g-white-estate',
        'mark': 'SGD', 'letter': 'G', 'entries': 5624,
        'title': "Strong's Greek Dictionary",
    },
}

# `(6) ‘abad [aw-bad']` — the number, the transliteration, the pronunciation.
RE_HEAD = re.compile(r'^\((\d{1,4})\)\s*(.+?)\s*$')
RE_PRON = re.compile(r'\[([^\]]{2,40})\]')


def fetch(kind):
    os.makedirs(DEST, exist_ok=True)
    path = os.path.join(DEST, f'{kind}.txt')
    if os.path.isfile(path) and os.path.getsize(path) > 500000:
        return path
    ident = SCANS[kind]['id']
    meta = urllib.request.urlopen(urllib.request.Request(
        f'https://archive.org/metadata/{ident}',
        headers={'User-Agent': UA}), timeout=120).read().decode()
    import json  # noqa: E402
    name = next(f['name'] for f in json.loads(meta)['files']
                if f['name'].endswith('_djvu.txt'))
    url = (f'https://archive.org/download/{ident}/'
           + urllib.parse.quote(name))
    print(f'  downloading {ident}…', flush=True)
    body = urllib.request.urlopen(urllib.request.Request(
        url, headers={'User-Agent': UA}), timeout=300).read()
    with open(path, 'wb') as fh:
        fh.write(body)
    return path


def parse(kind):
    """-> {number: {'word', 'pron', 'sense', 'kjv'}}

    Split on the headers, never on the end-markers. The markers look
    authoritative — every definition ends `SHD (430) .2` — and they are not:
    they carry the scanner's own paragraph count, which drifts away from
    Strong's numbering as the pages go by, so that entry 216 ends `SHD (276)`.
    Trusting them cost three hundred entries including `'owr`, `'ab` and
    `'adam`. The header `(216) ‘owr [ore]` is the only thing on the page that
    says what an entry is, so that is what is used.

    The file carries an index of every word before the dictionary itself, in
    the same header shape but with no definition under it. Keeping whichever
    copy of a number has the most text under it takes the real one.
    """
    spec = SCANS[kind]
    with open(fetch(kind), encoding='utf-8', errors='replace') as fh:
        raw = fh.read().replace('\r\n', '\n')

    noise = re.compile(re.escape(spec['mark']) + r'\s*\(\d{1,4}\)[\s.]*\d*')
    heads = list(re.finditer(r'^\((\d{1,4})\)\s*(.+?)\s*$', raw, re.M))

    out = {}
    for i, h in enumerate(heads):
        num = int(h.group(1))
        body = raw[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(raw)]
        body = noise.sub(' ', body)
        # A page number alone on a line is furniture, not text.
        body = '\n'.join(ln for ln in body.split('\n')
                         if not re.fullmatch(r'\s*\d{1,4}\s*', ln))
        sense = re.sub(r'\s+', ' ', body).strip(' ;:.')
        if len(sense) < 12:
            continue
        if num in out and len(out[num]['sense']) >= len(sense):
            continue

        kjv = ''
        if ':--' in sense:
            sense, _, kjv = sense.partition(':--')

        rest = h.group(2)
        pron = RE_PRON.search(rest)
        word = RE_PRON.sub('', rest).strip(' ,')
        if ',' in word:                      # `ayeAn, agele` — OCR'd Greek first
            word = word.split(',')[-1].strip()
        # The scanner keeps the printed page number on the headword's line.
        word = re.sub(r'[\s.]+\d{1,4}\s*$', '', word).strip(' ,.')
        if not word:
            continue

        out[num] = {
            'sense': sense.strip(' ;:'),
            'kjv': re.sub(r'\s+', ' ', kjv).strip(' .'),
            'word': word[:60],
            'pron': pron.group(1).strip() if pron else '',
        }
    return out


# --- modernizing a lexicon, carefully ------------------------------------
#
# Strong's prose is Victorian and belongs in modern American English like
# everything else here: `worshipper` should be `worshiper`, and `nay, i.e.
# truly` should read `no, i.e. truly`.
#
# But a dictionary entry is not all prose. It carries pronunciation in braces
# and brackets, and the modernizer cannot tell a phonetic spelling from an
# archaic verb: turned loose on this file it rewrites `{o-doth’}` as
# `{o-does’}`, `{bats-leeth’}` as `{bats-lees’}` and `{min-nay’}` as
# `{min-no’}` — the `-eth` rule and the `nay -> no` swap firing inside
# somebody's guide to saying a Hebrew word. So the guides are hidden first
# and put back afterwards, and only the English between them is touched.
RE_GUIDE = re.compile(r'\{[^}]*\}|\[[^\]]*\]')
KEEP = '\x01'


def polish(text, report=None):
    """Modernize the English of an entry and leave the phonetics alone."""
    if not text:
        return text
    kept = []

    def hide(m):
        kept.append(m.group(0))
        return f'{KEEP}{len(kept) - 1}{KEEP}'

    masked = RE_GUIDE.sub(hide, text)
    out = modernize.modernize(masked, 'full', report)
    for i, original in enumerate(kept):
        out = out.replace(f'{KEEP}{i}{KEEP}', original)
    return out


RE_TOKEN = re.compile(r"[A-Za-z'‘’]{3,}")


def bare(w):
    return re.sub(r"[^a-z]", '', w.lower())


def centrality(entries):
    """How many other entries are derived from each one.

    Strong builds his dictionary out of itself: `from 'owr' ('owr);
    illumination`. A root that dozens of other entries are traced back to is
    the central word of its family, and that is exactly the entry a reader
    who typed `light` wants first — where the position of the word inside a
    list of renderings, which is all the printed page offers, puts obscure
    compounds on top instead.
    """
    by_word = {}
    for n, e in entries.items():
        key = bare(e['word'])
        if key:
            by_word.setdefault(key, n)
    hits = {}
    for n, e in entries.items():
        seen = set()
        for tok in RE_TOKEN.findall(e['sense']):
            target = by_word.get(bare(tok))
            if target is not None and target != n and target not in seen:
                seen.add(target)
                hits[target] = hits.get(target, 0) + 1
    return hits


# The English words a definition ends with, which is how a reader gets in.
RE_KJV_SPLIT = re.compile(r'[,;]')
RE_CLEAN = re.compile(r'[^a-z\' ]+')


# Strong lists the renderings in order, the commonest first. That order is
# the only ranking available without a tagged text, and it is a good one: it
# is the lexicographer saying which sense the word usually carries.
def kjv_words(kjv):
    out = {}
    for i, part in enumerate(RE_KJV_SPLIT.split(kjv or '')):
        part = RE_CLEAN.sub(' ', part.lower())
        for w in part.split():
            if len(w) > 2 and w not in ('the', 'and', 'for', 'that', 'with'):
                out.setdefault(w, i)
    return out


def main():
    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript("""
        CREATE TABLE entry (
            id     TEXT PRIMARY KEY,   -- H430, G26
            lang   TEXT, num INTEGER, word TEXT, pron TEXT,
            sense  TEXT, kjv TEXT, refs INTEGER
        );
        CREATE TABLE english (word TEXT, id TEXT, rank INTEGER, kjvn INTEGER);
        CREATE INDEX english_word ON english(word, rank, kjvn);
        CREATE INDEX entry_word ON entry(word);
    """)
    total = 0
    report = modernize.Report()
    for kind, spec in SCANS.items():
        got = parse(kind)
        # The definitions are prose and are brought to modern American
        # English like the rest of the archive. The list of renderings is
        # not: it is a record of the words the King James translators
        # actually used, and rewriting `shew` to `show` there would be
        # putting words in their mouths. It is indexed under both instead,
        # so a reader coming from a modernized text still finds it.
        for e in got.values():
            e['sense'] = polish(e['sense'], report)
        refs = centrality(got)
        rows = [(f'{spec["letter"]}{n}', kind, n, e['word'], e.get('pron', ''),
                 e['sense'], e['kjv'], refs.get(n, 0))
                for n, e in sorted(got.items())]
        db.executemany('INSERT OR REPLACE INTO entry VALUES (?,?,?,?,?,?,?,?)', rows)
        # How many English words the entry is rendered by, as well as where
        # this one falls among them. A word that is first in a list of one is
        # the core sense — `'owr` is simply `light` — while a word that is
        # first in a list of forty is a corner of a much larger meaning.
        # Ordering by the two together puts the word a reader wants on top.
        pairs, both = [], 0
        for n, e in got.items():
            words = kjv_words(e['kjv'])
            eid = f'{spec["letter"]}{n}'
            for w, r in words.items():
                pairs.append((w, eid, r, len(words)))
                modern = american.americanize(w)
                if modern != w and modern not in words:
                    pairs.append((modern, eid, r, len(words)))
                    both += 1
        db.executemany('INSERT INTO english VALUES (?,?,?,?)', pairs)
        total += len(rows)
        print(f'  {spec["title"]}: {len(rows):,} of {spec["entries"]:,} entries, '
              f'{len(pairs):,} English words indexed back to them'
              + (f' ({both} of them a modern spelling of one)' if both else ''))
    db.commit()
    db.close()
    r = report.as_dict()
    print(f'  modernizer changed {r["changed_occurrences"]:,} occurrences of '
          f'{r["changed_forms"]} forms in the definitions')
    print(f'strongs: {total:,} entries ({os.path.getsize(DB) / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
