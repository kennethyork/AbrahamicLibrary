"""Hand-picked texts that the automatic collectors cannot reach.

Everything else in this archive arrives by a rule: a Library of Congress
class, a licence field, a publication date. That works for thousands of
books and leaves specific, well-known holes — the whole New Testament
apocrypha shelf stood empty, and there was no Jewish prayer book in a
library that holds two hundred Talmud volumes. The books that fill those
holes exist and are free; they are simply not where a rule would look.

So this list is chosen by hand, one entry at a time, each with the edition
and the year that makes it free. Every item here was found by searching
archive.org, opening the scan and reading it. The year is the evidence: all
of it was published in or before 1929 and so is out of copyright in the
United States.

What is *not* here matters too, and is recorded at the foot of this file:
several works were looked for and left out because no free English edition
of them exists.

    .venv/bin/python -m tools.ingest_curated
    .venv/bin/python -m tools.ingest_curated --check    fetch and report only
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, english, ingest_archive, modernize, prose  # noqa: E402
from tools.corpus import Chapter, Work, rights                       # noqa: E402

DEST = os.path.join(corpus.ROOT, 'sources', 'collector', 'curated')
UA = 'AbrahamicArchive/1.0 (public-domain text collection)'
PD_CUTOFF = 1929


def item(archive, title, author, year, religion, section, sort, **kw):
    return dict(archive=archive, title=title, author=author, year=year,
                religion=religion, section=section, sort=sort, **kw)


ITEMS = [
    # --- the New Testament apocrypha, which had no shelf at all -----------
    item('apocryphalnewtes0000unse_b9n3',
         'The Apocryphal New Testament', 'M. R. James', 1924,
         'christianity', 'nt-apocrypha', 1,
         note='The standard collection: the infancy gospels, the Gospel of '
              'Peter, the Acts of John, Paul, Peter, Andrew and Thomas, the '
              'Apocalypse of Peter, and the rest.'),
    item('lostbooksofbible0000unse_a7y5',
         'The Lost Books of the Bible', '', 1926,
         'christianity', 'nt-apocrypha', 2),
    item('forgottenbooksof0000unse',
         'The Forgotten Books of Eden', '', 1927,
         'christianity', 'nt-apocrypha', 3),
    item('thedidache00alleuoft',
         'The Didache', 'Willoughby Charles Allen', 1903,
         'christianity', 'nt-apocrypha', 4,
         note='The Teaching of the Twelve Apostles — the earliest church '
              'order there is, older than most of the Fathers.'),

    # --- the pseudepigrapha, which had one work and it was the wrong one --
    item('apocryphapseudep01charuoft',
         'The Apocrypha of the Old Testament', 'R. H. Charles', 1913,
         'christianity', 'pseudepigrapha', 10,
         note='Volume I of Charles’s edition.'),
    item('apocryphapseudep02charuoft',
         'The Pseudepigrapha of the Old Testament', 'R. H. Charles', 1913,
         'christianity', 'pseudepigrapha', 11,
         note='Volume II of Charles’s edition: Jubilees, the Letter of '
              'Aristeas, the Books of Adam and Eve, Enoch, the Testaments '
              'of the Twelve Patriarchs, the Sibylline Oracles, 2 Baruch, '
              '4 Ezra and the Psalms of Solomon.'),
    item('testamentsoftwel00char',
         'The Testaments of the Twelve Patriarchs', 'R. H. Charles', 1917,
         'christianity', 'pseudepigrapha', 12),
    item('sibyllineoracles00terruoft',
         'The Sibylline Oracles', 'Milton S. Terry', 1890,
         'christianity', 'pseudepigrapha', 13),

    # --- one classic of Christian mysticism that was simply absent -------
    item('darknightofsoul00sain',
         'The Dark Night of the Soul', 'St John of the Cross', 1908,
         'christianity', 'christian-study', 20),

    # --- Judaism: the mystical text, and the prayer book -----------------
    item('kabbaladenudata00rosegoog',
         'The Kabbalah Unveiled', 'S. L. MacGregor Mathers', 1912,
         'judaism', 'kabbalah', 1,
         note='The three books of the Zohar that Knorr von Rosenroth put '
              'into Latin, here in English. No complete English Zohar is '
              'free: the Sperling and Simon translation is of 1931.'),
    item('authoriseddailyp00sing',
         'The Authorised Daily Prayer Book', 'Simeon Singer', 1904,
         'judaism', 'liturgy', 1,
         note='The siddur of the United Hebrew Congregations — the prayer '
              'book itself, which this library held two hundred Talmud '
              'volumes without.'),
    item('unionhaggadahhom00cent',
         'The Union Haggadah', 'Central Conference of American Rabbis', 1923,
         'judaism', 'liturgy', 2,
         note='The home service for Passover.'),

    # --- Philo, in the translation whose date can be checked --------------
    #
    # Sefaria carries Philo in the Loeb Classical Library and marks it public
    # domain. Six of those volumes are of 1932 to 1941 and are not: a licence
    # field saying `Public Domain` is a claim that a copyright expired, and
    # the date on a Harvard University Press book of 1941 says it has not.
    # Yonge's translation is of 1854, is complete, and needs no one's word.
    item('worksofphilojuda01phil', 'The Works of Philo Judaeus, Volume I',
         'C. D. Yonge', 1854, 'judaism', 'jewish-philosophy', 40),
    item('worksofphilojuda0002phil', 'The Works of Philo Judaeus, Volume II',
         'C. D. Yonge', 1854, 'judaism', 'jewish-philosophy', 41),
    item('worksofphilojuda03phil', 'The Works of Philo Judaeus, Volume III',
         'C. D. Yonge', 1855, 'judaism', 'jewish-philosophy', 42),
    item('worksofphilojuda04phil', 'The Works of Philo Judaeus, Volume IV',
         'C. D. Yonge', 1855, 'judaism', 'jewish-philosophy', 43),

    # --- Islam: a fifth Qur’an, and the second hadith collection ---------
    # Five scans of Palmer were compared. Two of them are the second volume
    # filed under a name that says the first, and one of those has a scanner
    # that reads every `c` as an `e` — "graee", "eame", "elouds". The two
    # taken here were checked by counting the openings: fifteen in the first
    # volume, ninety-eight in the second.
    item('qurn0000unse_o3d6',
         'The Qur’ân, Part I', 'E. H. Palmer', 1880,
         'islam', 'quran', 20,
         note='Palmer’s translation for the Sacred Books of the East, '
              'suras 1–16.'),
    item('thequraan09unknuoft',
         'The Qur’ân, Part II', 'E. H. Palmer', 1880,
         'islam', 'quran', 21,
         note='Palmer’s translation for the Sacred Books of the East, '
              'suras 17–114.'),
    item('dli.csl.6689',
         'Mishcat-ul-Masabih', 'A. N. Matthews', 1810,
         'islam', 'hadith', 10,
         note='The second great hadith collection to reach English, and '
              'the only one besides Bukhari that is free: the standard '
              'translations of Sahih Muslim are all modern.'),
    item('bim_eighteenth-century_sentences-of-ali-son-in-_ali-ibn-abi-talib-cali_1717',
         'The Sentences of Ali', '', 1717,
         'islam', 'islamic-law', 20,
         note='Maxims attributed to Ali. The Nahj al-Balagha itself has no '
              'free English translation; this is the pre-copyright remnant '
              'of the same material.'),
]

# Looked for and not taken, so that the gap is a decision and not an
# oversight. Each of these was searched for on archive.org and on Project
# Gutenberg with a cutoff of 1929, and no free English edition came back.
NOT_FREE = {
    'Sahih Muslim': 'no English translation before 1929; the pre-1929 scans '
                    'are Urdu (the Al-Moallim Tarjuma).',
    'Muwatta of Malik': 'no English translation before 1929.',
    'Nawawi’s Forty Hadith': 'no English translation before 1929.',
    'Nahj al-Balagha': 'no English translation before 1929; the Sentences '
                       'of Ali (1717) is taken instead.',
    'Ibn Ishaq, Sirat Rasul Allah': 'Guillaume’s translation is of 1955. '
                                    'Muir’s Life of Mahomet, which quotes it '
                                    'at length, is already held.',
    'Ibn Khaldun, Muqaddimah': 'the only pre-1929 full translation is de '
                               'Slane’s French; Rosenthal’s English is 1958.',
    'Attar, The Conference of the Birds': 'Garcin de Tassy’s is French; '
                                          'FitzGerald’s Bird Parliament '
                                          'exists only inside his collected '
                                          'Literary Remains.',
    'The Zohar, complete': 'Sperling and Simon is of 1931. Mathers’s three '
                           'books are taken instead.',
    'The Tanya': 'first English translation 1962.',
}


# --- fetching -------------------------------------------------------------

_last = [0.0]


def _get(url, binary=False, timeout=300, pause=0.5):
    wait = pause - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            raw = fh.read()
        return raw if binary else raw.decode('utf-8', 'replace')
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            OSError):
        return None


def text_url(identifier):
    """The plain text of a scan, wherever the item happens to keep it.

    `<id>_djvu.txt` is the usual name and is tried first because it costs
    one request; where it is missing the item's own file list is asked.
    """
    direct = f'https://archive.org/download/{identifier}/{identifier}_djvu.txt'
    meta = _get(f'https://archive.org/metadata/{identifier}', timeout=60)
    if not meta:
        return direct
    try:
        files = json.loads(meta).get('files', [])
    except ValueError:
        return direct
    names = [f['name'] for f in files if f.get('name', '').endswith('.txt')]
    if not names:
        return direct
    names.sort(key=lambda n: (not n.endswith('_djvu.txt'), len(n)))
    return f'https://archive.org/download/{identifier}/{urllib.parse.quote(names[0])}'


def fetch(spec):
    path = os.path.join(DEST, spec['archive'] + '.txt')
    if os.path.isfile(path) and os.path.getsize(path) > 20000:
        return path
    body = _get(text_url(spec['archive']), binary=True)
    if not body or len(body) < 20000:
        return None
    os.makedirs(DEST, exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(body)
    return path


# --- ingesting ------------------------------------------------------------

# Google prefixes its scans with two pages about Google. The last line of it
# names the search service one final time, and the book starts after that.
# The URL comes off the scanner as `http: //books .google .com/`, spaced and
# broken, so it is matched with the spaces allowed for.
RE_GOOGLE_END = re.compile(
    r'^.*http\s*:\s*/\s*/\s*books\s*\.\s*google\s*\.\s*com.*$', re.M | re.I)
RE_GOOGLE_START = re.compile(r'\bThis is a digital c?opy of a book\b', re.I)


def strip_scanner_notice(text):
    """The book, without the two pages the scanner put in front of it."""
    if not RE_GOOGLE_START.search(text[:4000]):
        return text
    ends = list(RE_GOOGLE_END.finditer(text[:20000]))
    return text[ends[-1].end():] if ends else text



def build(spec, path, report):
    with open(path, encoding='utf-8', errors='replace') as fh:
        raw = fh.read().replace('\r\n', '\n').replace('\r', '\n')
    body = ingest_archive.clean_ocr(strip_scanner_notice(raw))
    if not english.is_english(body):
        return None, 'not English'

    chapters = prose.split_by_headings(body)
    if not chapters:
        paras = prose.paragraphs(body)
        if sum(len(p) for p in paras) < 3000:
            return None, 'too little text'
        chapters = [('', paras)]

    wid = 'cur-' + corpus.slugify(spec['archive'])
    w = Work(id=wid, title=spec['title'], subtitle=spec['author'],
             religion=spec['religion'], section=spec['section'],
             sort=spec['sort'], structure='prose', canon='secondary',
             translation=spec['title'], translator=spec['author'],
             year=spec['year'], modernization='full',
             rights=rights(f'Published in {spec["year"]}, and so in the '
                           f'public domain in the United States.',
                           f'https://archive.org/details/{spec["archive"]}'),
             provenance={'source': 'archive.org',
                         'identifier': spec['archive'],
                         'source_file':
                             f'sources/collector/curated/{spec["archive"]}.txt',
                         'note': (spec.get('note', '') + ' ' if spec.get('note')
                                  else '') +
                                 'Chosen by hand; scanned and OCR’d, not a '
                                 'proofread transcription.'})
    for i, (heading, paras) in enumerate(chapters, 1):
        # The heading gets the same tier as the text under it. Modernizing
        # the body and leaving `Of the Vanity of Him that Hath Riches`
        # over the top of it is the one place archaic English survived
        # a full-tier book.
        ch = Chapter(i, modernize.modernize(heading, 'full') or f'Part {i}')
        for p in paras:
            ch.blocks.append({'k': 'p',
                              't': modernize.modernize(p, 'full', report)})
        w.add(ch)
    if not w.chapters:
        return None, 'no chapters'
    return w.save(), ''


def main():
    check = '--check' in sys.argv
    report = modernize.Report()
    made, failed = [], []
    for spec in ITEMS:
        if spec['year'] > PD_CUTOFF:                     # belt and braces
            failed.append((spec['title'], f'published {spec["year"]}'))
            continue
        path = fetch(spec)
        if not path:
            failed.append((spec['title'], 'no text at archive.org'))
            continue
        if check:
            print(f'  {os.path.getsize(path):>9,}  {spec["title"]}')
            continue
        m, why = build(spec, path, report)
        if not m:
            failed.append((spec['title'], why))
            continue
        made.append(m)
        print(f'  {spec["religion"]:<13} {spec["section"]:<15} '
              f'{m["stats"]["words"]:>8,} words  {spec["title"]}')
    if check:
        return
    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'curated.json'),
                      report.as_dict())
    for title, why in failed:
        print(f'  ! {title}: {why}')
    print(f'curated: {len(made)} works, '
          f'{sum(m["stats"]["words"] for m in made):,} words; '
          f'{len(NOT_FREE)} works looked for and not free')


if __name__ == '__main__':
    main()
