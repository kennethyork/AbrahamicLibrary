"""Fetch from Project Gutenberg using its catalog, not its search pages.

Gutenberg publishes a complete catalog as one CSV — every book, with its
Library of Congress classification, its subject headings and its language.
Downloading that once and selecting from it locally is better than scraping
search results in every way that matters:

  * **Precise.** The LoC classification says what a book *is*. `BM` is
    Judaism, `BP` Islam, `BR`–`BX` Christianity, `BS` the Bible. No keyword
    guessing, and no more Spanish castles or Broadway musicals arriving
    because they mention "Arabian".
  * **Complete.** Search returns the first pages of results; the catalog is
    everything. It shows, for instance, that Gutenberg holds only 140 English
    Islamic texts in total — a fact worth knowing rather than guessing at.
  * **Kind.** One 21 MB download instead of thousands of search and
    bibliographic-record requests.

    .venv/bin/python -m tools.fetch_gutenberg              fetch what is missing
    .venv/bin/python -m tools.fetch_gutenberg --list       show what it would take
    .venv/bin/python -m tools.fetch_gutenberg --refresh    re-download the catalog
"""
import csv
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, nonfiction                              # noqa: E402

DEST = os.path.join(corpus.ROOT, 'sources', 'collector', 'gutenberg')
CATALOG = os.path.join(corpus.ROOT, 'sources', 'collector', 'pg_catalog.csv')
CATALOG_URL = 'https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv'
UA = 'AbrahamicArchive/1.0 (public-domain text collection)'

# Library of Congress classes -> the religion the archive files them under.
LOCC = {
    'BM': 'judaism',
    'BP': 'islam',            # Islam, Bahai, Theosophy
    'BR': 'christianity',     # Christianity
    'BS': 'christianity',     # The Bible
    'BT': 'christianity',     # Doctrinal theology
    'BV': 'christianity',     # Practical theology
    'BX': 'christianity',     # Christian denominations
    'BL': '',                 # Religions in general — decided by subject
}

# A BL book is only taken when its subjects name one of the three.
BL_KEEP = re.compile(r'islam|muslim|koran|qur.?an|muhammad|mohammed|sufi|'
                     r'jew|judaism|talmud|hebrew|rabbi|'
                     r'christian|bible|church|jesus|gospel|'
                     r'abraham|monotheis|comparative religion',
                     re.I)

_last = [0.0]


def _get(url, binary=False, pause=0.5, timeout=120):
    wait = pause - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            raw = fh.read()
        return raw if binary else raw.decode('utf-8', 'replace')
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def catalog(refresh=False):
    """The whole Gutenberg catalog, downloaded once."""
    if refresh or not os.path.isfile(CATALOG) or os.path.getsize(CATALOG) < 1e6:
        print('downloading the Gutenberg catalog…', flush=True)
        raw = _get(CATALOG_URL, binary=True, timeout=300)
        if not raw:
            sys.exit('could not download the catalog')
        os.makedirs(os.path.dirname(CATALOG), exist_ok=True)
        with open(CATALOG, 'wb') as fh:
            fh.write(raw)
    with open(CATALOG, encoding='utf-8', errors='replace') as fh:
        return list(csv.DictReader(fh))


def classes(row):
    return {c.strip()[:2] for c in re.split(r'[;,]', row.get('LoCC') or '')
            if c.strip()}


# Two shelves hold religious books filed by what they are *about* rather
# than by what they are, and the class filter is blind to both. Ibn Tufail's
# `Hai Ebn Yokdhan` and Pascal's `Pensées` are philosophy (B); Bunyan's
# `Grace Abounding` and Browne's `Religio Medici` are English literature
# (PR). Two narrow rules let them through and nothing else: a philosophy or
# ethics book whose subject headings name one of the three religions, and a
# literary work whose subject heading *opens* with a devotional one — which
# is the cataloguer saying the devotion is the point of the book and not a
# thing that happens in it.
PHILOSOPHY = {'B', 'BJ'}
NAMES_A_RELIGION = re.compile(
    r'\b(islam|islamic|muslim|koran|qur.?an|muhammad|mohammed|sufi|sufism|'
    r'judaism|jewish|jews|talmud|rabbi|cabala|kabbala|hasidism|'
    r'christian|christianity|bible|church|jesus|christ|gospel|'
    r'theology|apologetics|providence|monotheism|scholasticism|patristic)\b',
    re.I)

LITERATURE = {'PR', 'PS', 'PN'}

# Oriental languages and literature. Rumi's Mesnevi, Iqbal's Secrets of the
# Self and the Sacred Books of the East are all shelved here rather than
# under religion, and all three are primary religious literature.
ORIENTAL = {'PJ', 'PK', 'PL'}

# Josephus is filed under DS, Middle East history, with the subject heading
# `Jews -- Antiquities`. No rule is written for that heading, because the
# catalogue uses it for books about Jews as well as books by them, and the
# same rule that reaches the Antiquities reaches Henry Ford's International
# Jew. Where a heading cannot tell the difference, a person has to, so these
# are named one at a time.
ALSO_TAKE = {
    2846: 'judaism',      # The Life of Flavius Josephus
    2847: 'judaism',      # Josephus's Discourse to the Greeks
    2848: 'judaism',      # Antiquities of the Jews
    2850: 'judaism',      # The Wars of the Jews
    9793: 'judaism',      # Josephus
    64837: 'judaism',     # Selections From Josephus
    12894: 'islam',       # Sacred Books of the East
    55674: 'islam',       # Sacred Books and Early Literature of the East VI
}
DEVOTIONAL = re.compile(
    r'^(christian life|devotional literature|christian biography|'
    r'meditations|prayers|spiritual life|conversion)\b', re.I)


def subjects_of(row):
    return [s.strip() for s in re.split(';', row.get('Subjects') or '')
            if s.strip()]


def _which(hay):
    """Which of the three a run of subject headings is talking about."""
    hay = hay.lower()
    if re.search(r'islam|muslim|koran|qur|muhammad|mohammed|sufi', hay):
        return 'islam'
    if re.search(r'jew|judaism|talmud|hebrew|rabbi|cabala|kabbala', hay):
        return 'judaism'
    return 'christianity'


def religion_of(row):
    """Which of the three this book belongs to, or '' to pass it over."""
    found = classes(row)
    for code, religion in LOCC.items():
        if code in found and religion:
            return religion
    subjects = row.get('Subjects') or ''
    title = row.get('Title') or ''
    if 'BL' in found and BL_KEEP.search(subjects + ' ' + title):
        return _which(subjects + ' ' + title)
    if found & PHILOSOPHY and NAMES_A_RELIGION.search(subjects):
        return _which(subjects)
    if found & LITERATURE and any(DEVOTIONAL.match(s)
                                  for s in subjects_of(row)):
        return _which(subjects + ' ' + title)
    if found & ORIENTAL and NAMES_A_RELIGION.search(subjects + ' ' + title):
        return _which(subjects + ' ' + title)
    try:
        return ALSO_TAKE.get(int(row['Text#']), '')
    except (KeyError, ValueError):
        return ''


def wanted(rows):
    """-> [(gutenberg id, title, religion, subjects)] worth downloading."""
    out, refused = [], {'not religion': 0, 'fiction': 0, 'not english': 0}
    for row in rows:
        if row.get('Type') != 'Text':
            continue
        if row.get('Language') != 'en':
            refused['not english'] += 1
            continue
        religion = religion_of(row)
        if not religion:
            refused['not religion'] += 1
            continue
        subjects = [s.strip() for s in
                    re.split(r';', row.get('Subjects') or '') if s.strip()]
        keep, _why = nonfiction.verdict(row.get('Title') or '', subjects)
        if not keep:
            refused['fiction'] += 1
            continue
        try:
            gid = int(row['Text#'])
        except (KeyError, ValueError):
            continue
        out.append((gid, (row.get('Title') or '').strip(), religion, subjects,
                    (row.get('Authors') or '').strip()))
    return out, refused


def download(gid, title, religion, subjects, authors):
    txt = os.path.join(DEST, f'pg-{gid}.txt')
    meta = os.path.join(DEST, f'pg-{gid}.meta.json')
    have = os.path.isfile(txt) and os.path.getsize(txt) > 2000

    if not have:
        body = None
        for url in (f'https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt',
                    f'https://www.gutenberg.org/files/{gid}/{gid}-0.txt',
                    f'https://www.gutenberg.org/ebooks/{gid}.txt.utf-8'):
            body = _get(url, binary=True)
            if body and len(body) > 2000:
                break
            body = None
        if not body:
            return False
        os.makedirs(DEST, exist_ok=True)
        with open(txt, 'wb') as fh:
            fh.write(body)

    # The metadata is rewritten either way: the catalog's subjects are better
    # than anything scraped, and the ingester classifies from them.
    corpus.write_json(meta, {
        'work_id': f'pg-{gid}',
        'gutenberg_id': gid,
        'title': title,
        'religion': religion,
        'authors': [{'name': a.strip(), 'birth_year': None, 'death_year': None}
                    for a in authors.split(';') if a.strip()],
        'subjects': subjects,
        'rights': 'Public domain in the United States (Project Gutenberg).',
        'source_url': f'https://www.gutenberg.org/ebooks/{gid}',
    })
    return not have


def main(argv):
    rows = catalog(refresh='--refresh' in argv)
    picks, refused = wanted(rows)

    from collections import Counter
    by = Counter(r for _, _, r, _, _ in picks)
    print(f'catalog: {len(rows):,} records')
    print(f'selected {len(picks):,} English religious texts — '
          + ', '.join(f'{n} {r}' for r, n in by.most_common()))
    print('passed over: '
          + ', '.join(f'{n:,} {why}' for why, n in refused.items()))

    if '--list' in argv:
        for gid, title, religion, _s, _a in picks[:40]:
            print(f'  {religion:13} {gid:6} {title[:70]}')
        print(f'  … {len(picks) - 40} more' if len(picks) > 40 else '')
        return 0

    got = 0
    for i, pick in enumerate(picks, 1):
        try:
            if download(*pick):
                got += 1
        except Exception as e:                                # noqa: BLE001
            print(f'  ! {pick[0]}: {type(e).__name__}: {e}')
        if i % 100 == 0:
            print(f'  {i}/{len(picks)} checked, {got} newly downloaded',
                  flush=True)

    print(f'{got} new texts; {len(picks)} now held')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
