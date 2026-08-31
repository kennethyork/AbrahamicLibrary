"""Ingest the Jewish library from Sefaria — public-domain English only.

The Tanakh comes from the 1917 Jewish Publication Society translation, which
is public domain and is the Jewish scriptures in a Jewish translation, set in
the Tanakh's own order and division. Christianity's Old Testament, ingested
separately from the World English Bible, is the same books in Christian order
and a Christian translation; the archive carries both rather than pretending
one serves for the other.

Everything here is a translation of 1877–1933, so all of it takes the full
modernization tier.
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize, sefaria                       # noqa: E402
from tools.corpus import Chapter, Work, rights                     # noqa: E402

JPS = 'The Holy Scriptures: A New Translation (JPS 1917)'

JPS_RIGHTS = rights(
    'Public domain. The Jewish Publication Society’s 1917 translation, '
    'published without a renewed copyright.',
    'https://www.sefaria.org/texts')

# (sefaria title, display title, section, order within the Tanakh)
TANAKH = [
    ('Genesis', 'Genesis', 'torah'), ('Exodus', 'Exodus', 'torah'),
    ('Leviticus', 'Leviticus', 'torah'), ('Numbers', 'Numbers', 'torah'),
    ('Deuteronomy', 'Deuteronomy', 'torah'),
    ('Joshua', 'Joshua', 'neviim'), ('Judges', 'Judges', 'neviim'),
    ('I Samuel', 'I Samuel', 'neviim'), ('II Samuel', 'II Samuel', 'neviim'),
    ('I Kings', 'I Kings', 'neviim'), ('II Kings', 'II Kings', 'neviim'),
    ('Isaiah', 'Isaiah', 'neviim'), ('Jeremiah', 'Jeremiah', 'neviim'),
    ('Ezekiel', 'Ezekiel', 'neviim'),
    ('Hosea', 'Hosea', 'neviim'), ('Joel', 'Joel', 'neviim'),
    ('Amos', 'Amos', 'neviim'), ('Obadiah', 'Obadiah', 'neviim'),
    ('Jonah', 'Jonah', 'neviim'), ('Micah', 'Micah', 'neviim'),
    ('Nahum', 'Nahum', 'neviim'), ('Habakkuk', 'Habakkuk', 'neviim'),
    ('Zephaniah', 'Zephaniah', 'neviim'), ('Haggai', 'Haggai', 'neviim'),
    ('Zechariah', 'Zechariah', 'neviim'), ('Malachi', 'Malachi', 'neviim'),
    ('Psalms', 'Psalms', 'ketuvim'), ('Proverbs', 'Proverbs', 'ketuvim'),
    ('Job', 'Job', 'ketuvim'), ('Song of Songs', 'Song of Songs', 'ketuvim'),
    ('Ruth', 'Ruth', 'ketuvim'), ('Lamentations', 'Lamentations', 'ketuvim'),
    ('Ecclesiastes', 'Ecclesiastes', 'ketuvim'), ('Esther', 'Esther', 'ketuvim'),
    ('Daniel', 'Daniel', 'ketuvim'), ('Ezra', 'Ezra', 'ketuvim'),
    ('Nehemiah', 'Nehemiah', 'ketuvim'),
    ('I Chronicles', 'I Chronicles', 'ketuvim'),
    ('II Chronicles', 'II Chronicles', 'ketuvim'),
]

# Works beyond the Tanakh, each with the public-domain English Sefaria holds.
# `section` files it in the archive; `tier` is the modernization tier.
LIBRARY = [
    # title, display, section, version, canon
    ('Pirkei Avot', 'Pirkei Avot', 'mishnah',
     'The Saying of the Jewish Fathers: Gorfinkle 1913', 'canonical'),
    ('Guide for the Perplexed', 'The Guide for the Perplexed',
     'jewish-philosophy',
     'Guide for the Perplexed, English Translation, Friedlander (1903)',
     'secondary'),
    ('Sefer Yetzirah', 'Sefer Yetzirah', 'kabbalah',
     'Sefer Yezirah, trans. by Isidor Kalisch. New York, 1877', 'secondary'),
    ('Kuzari', 'The Kuzari', 'jewish-philosophy',
     'Kitab al Khazari, translated by Hartwig Hirschfeld, 1905', 'secondary'),
]

RE_TAG = re.compile(r'<[^>]+>')
RE_FOOT = re.compile(r'<sup[^>]*>.*?</sup>|<i class="footnote">.*?</i>', re.S | re.I)


def plain(s):
    """Sefaria's text is HTML. Take the words, drop the markup."""
    if not isinstance(s, str):
        return ''
    s = RE_FOOT.sub('', s)
    s = re.sub(r'<br\s*/?>', ' ', s, flags=re.I)
    s = RE_TAG.sub('', s)
    s = html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def flatten(node):
    """Sefaria nests as deep as a work needs. Take chapters of strings."""
    if isinstance(node, str):
        return [[node]]
    if not isinstance(node, list):
        return []
    if all(isinstance(x, str) for x in node):
        return [node]
    out = []
    for child in node:
        if isinstance(child, str):
            out.append([child])
        elif isinstance(child, list) and all(isinstance(x, str) for x in child):
            out.append(child)
        else:
            out.extend(flatten(child))
    return out


def build(title, display, section, version, canon_status, sort, report,
          religion='judaism', structure='verse', translator='', year=None):
    # Take the fullest free English text Sefaria holds, not simply the one
    # named above. Several of the old public-domain editions are on Sefaria
    # only in fragments — its Gorfinkle Pirkei Avot is four sections and 246
    # words, against 7,000 in the CC0 community translation — and a fragment
    # of the right edition is worth less to a reader than the whole work.
    candidates = [version] + [v['versionTitle'] for v in sefaria.pd_versions(title)]
    best, best_words, best_version = None, 0, version

    for candidate in dict.fromkeys(candidates):
        got = sefaria.text(title, candidate)
        text = got.get('text') if got else None
        if not text:
            # A work in several parts — the Guide for the Perplexed, in
            # three — cannot be fetched whole; Sefaria answers only to a
            # part-level ref.
            parts = fetch_parts(title, candidate)
            if not parts:
                continue
            got = {'text': parts, 'license': 'Public Domain', 'versionSource': ''}
        if str(got.get('license', '')).strip().lower() not in sefaria.FREE:
            continue
        words = sum(len(plain(s).split())
                    for chunk in flatten(got['text']) for s in chunk)
        if words > best_words:
            best, best_words, best_version = got, words, candidate

    if not best:
        print(f'  ! {title}: no free English text at all')
        return None
    if best_version != version:
        print(f'  … {title}: using {best_version!r} ({best_words:,} words), '
              f'which is fuller than {version!r}')
    got, version = best, best_version
    lic = str(got.get('license', '')).strip().lower()
    if lic not in sefaria.FREE:
        print(f'  ! {title}: licence is {got.get("license")!r}, skipping')
        return None

    w = Work(id='sef-' + corpus.slugify(title), title=display,
             religion=religion, section=section, sort=sort,
             structure=structure, canon=canon_status,
             translation=version, translator=translator, year=year,
             modernization='full',
             rights=rights(f'Public domain. Supplied by Sefaria as '
                           f'“{version}”.',
                           got.get('versionSource')
                           or f'https://www.sefaria.org/{urlish(title)}'),
             provenance={'source': 'Sefaria', 'sefaria_title': title,
                         'version': version})

    for i, chunk in enumerate(flatten(got['text']), 1):
        ch = Chapter(i, f'Chapter {i}')
        for j, raw in enumerate(chunk, 1):
            text = plain(raw)
            if not text:
                continue
            ch.verses.append({'n': str(j),
                              'text': modernize.modernize(text, 'full', report),
                              'notes': []})
        if ch.verses:
            w.add(ch)
    if not w.chapters:
        print(f'  ! {title}: parsed empty')
        return None
    return w.save()


def fetch_parts(title, version, limit=12):
    """Gather a work Sefaria will only serve one part at a time.

    Stops at the first part that is not there, so a three-part work costs
    four requests rather than twelve.
    """
    out = []
    for pattern in ('{t}, Part {n}', '{t} {n}', '{t}, Volume {n}'):
        found = []
        for n in range(1, limit + 1):
            got = sefaria.text(pattern.format(t=title, n=n), version)
            if not got or not got.get('text'):
                break
            found.extend(flatten(got['text']))
        if found:
            out = found
            break
    return out


def urlish(title):
    return title.replace(' ', '_')


def main():
    report = modernize.Report()
    made = []

    order = {'torah': 0, 'neviim': 1, 'ketuvim': 2}
    counters = {k: 0 for k in order}
    for title, display, section in TANAKH:
        got = sefaria.text(title, JPS)
        if not got or not got.get('text'):
            print(f'  ! {title}: no JPS text')
            continue
        sort = counters[section]
        counters[section] += 1
        w = Work(id='jps-' + corpus.slugify(title), title=display,
                 religion='judaism', section=section, sort=sort,
                 structure='verse', canon='canonical',
                 translation='The Holy Scriptures (JPS 1917)',
                 translator='Jewish Publication Society', year=1917,
                 modernization='full', rights=JPS_RIGHTS,
                 provenance={'source': 'Sefaria', 'sefaria_title': title,
                             'version': JPS})
        for ci, chunk in enumerate(flatten(got['text']), 1):
            ch = Chapter(ci, f'Chapter {ci}')
            for vi, raw in enumerate(chunk, 1):
                text = plain(raw)
                if not text:
                    continue
                ch.verses.append({'n': str(vi),
                                  'text': modernize.modernize(text, 'full', report),
                                  'notes': []})
            if ch.verses:
                w.add(ch)
        if w.chapters:
            made.append(w.save())

    print(f'  tanakh: {len(made)} books, '
          f'{sum(m["stats"]["chapters"] for m in made)} chapters, '
          f'{sum(m["stats"]["verses"] for m in made)} verses')

    for i, (title, display, section, version, canon_status) in enumerate(LIBRARY):
        m = build(title, display, section, version, canon_status, i, report)
        if m:
            made.append(m)
            print(f'  {m["id"]}: {m["stats"]["chapters"]} chapters, '
                  f'{m["stats"]["verses"]} sections')

    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'jewish.json'),
                      report.as_dict())
    d = report.as_dict()
    print(f'jewish: {len(made)} works; modernizer changed '
          f'{d["changed_occurrences"]} occurrences of {d["changed_forms"]} '
          f'forms, {d["unresolved_forms"]} unresolved')


if __name__ == '__main__':
    main()
