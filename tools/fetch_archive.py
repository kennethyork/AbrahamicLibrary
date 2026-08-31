"""Fetch Islamic texts from archive.org — only what the date proves is free.

archive.org is not a curated public-domain library. It holds plenty of
in-copyright material, and its licence fields are unreliable or absent. So
nothing here is taken on a licence claim. The single test is the publication
date: a work published in or before `PD_CUTOFF` is out of copyright in the
United States, and that date is recorded on the work's page as the evidence.

Everything else is thrown away — no date, an ambiguous date, a date too
recent, not English, no full text. That is deliberately strict, and it is the
reason this fetcher can be pointed at a library that is not itself clean.

    .venv/bin/python -m tools.fetch_archive              search and download
    .venv/bin/python -m tools.fetch_archive --dry-run    list what it would take
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

from tools import corpus, english                                  # noqa: E402

DEST = os.path.join(corpus.ROOT, 'sources', 'collector', 'archive')
UA = 'AbrahamicArchive/1.0 (public-domain text collection)'

# Copyright in the United States runs 95 years from publication, so in 2026
# everything published through 1930 is free. 1929 is used instead: one year
# of margin costs almost nothing and removes any argument about the boundary.
PD_CUTOFF = 1929

# What to look for, where it belongs, and which religion files it.
#
# archive.org has no catalogue class to filter on and no licence field worth
# trusting, so a sweep of it has to be aimed. These are aimed at the primary
# literature of each tradition and at the standard nineteenth-century
# translations of it — the editions that are old enough to be free and good
# enough to be worth having. Everything they return still has to pass the
# relevance test, the date, and the modern-reprint check below.
SEARCHES = [
    # --- Islam ----------------------------------------------------------
    ('hadith', 'islam', 'hadith'),
    ('traditions of Muhammad', 'islam', 'hadith'),
    ('sayings of Muhammad', 'islam', 'hadith'),
    ('Mishkat al-Masabih', 'islam', 'hadith'),
    ('Bukhari', 'islam', 'hadith'),

    ('life of Mahomet', 'islam', 'sira'),
    ('life of Muhammad', 'islam', 'sira'),
    ('biography of Mohammed', 'islam', 'sira'),
    ('Ibn Ishaq', 'islam', 'sira'),

    ('Masnavi Rumi', 'islam', 'sufism'),
    ('Jalaluddin Rumi', 'islam', 'sufism'),
    ('Divan Hafiz', 'islam', 'sufism'),
    ('Gulistan Saadi', 'islam', 'sufism'),
    ('Attar Persian poet', 'islam', 'sufism'),
    ('sufism mysticism islam', 'islam', 'sufism'),
    ('dervish', 'islam', 'sufism'),

    ('Ghazali', 'islam', 'islamic-law'),
    ('Hedaya Muslim law', 'islam', 'islamic-law'),
    ('Muhammadan jurisprudence', 'islam', 'islamic-law'),
    ('Islamic theology', 'islam', 'islamic-law'),
    ('Minhaj et Talibin', 'islam', 'islamic-law'),

    ('Ibn Khaldun', 'islam', 'islamic-history'),
    ('history of the caliphs', 'islam', 'islamic-history'),
    ('history of the saracens', 'islam', 'islamic-history'),
    ('Moorish Spain', 'islam', 'islamic-history'),
    ('Ottoman history', 'islam', 'islamic-history'),

    ('Koran translation', 'islam', 'quran'),
    ('Quran commentary', 'islam', 'islamic-study'),
    ('Islam introduction', 'islam', 'islamic-study'),

    # --- Judaism --------------------------------------------------------
    ('Targum Onkelos English', 'judaism', 'torah'),
    ('Hebrew Bible translation Leeser', 'judaism', 'torah'),
    ('Rashi commentary English', 'judaism', 'torah'),

    ('Mishnah English translation', 'judaism', 'mishnah'),
    ('Eighteen treatises from the Mishna', 'judaism', 'mishnah'),
    ('Pirke Aboth sayings of the fathers', 'judaism', 'mishnah'),

    ('Babylonian Talmud Rodkinson', 'judaism', 'talmud'),
    ('Talmud tractate English translation', 'judaism', 'talmud'),
    ('selections from the Talmud', 'judaism', 'talmud'),
    ('Talmud Jerusalem English', 'judaism', 'talmud'),

    ('Midrash Rabbah English', 'judaism', 'midrash'),
    ('Pirke de Rabbi Eliezer', 'judaism', 'midrash'),
    ('Midrash Tanhuma', 'judaism', 'midrash'),
    ('Haggadah of the Talmud', 'judaism', 'midrash'),

    ('Shulchan Aruch English', 'judaism', 'halakhah'),
    ('code of Jewish law', 'judaism', 'halakhah'),
    ('Mishneh Torah Maimonides English', 'judaism', 'halakhah'),

    ('works of Philo Judaeus', 'judaism', 'jewish-philosophy'),
    ('Guide for the Perplexed Maimonides', 'judaism', 'jewish-philosophy'),
    ('Kuzari Judah Halevi', 'judaism', 'jewish-philosophy'),
    ('Duties of the Heart Bahya', 'judaism', 'jewish-philosophy'),
    ('Saadia Gaon beliefs and opinions', 'judaism', 'jewish-philosophy'),
    ('Jewish ethics', 'judaism', 'jewish-philosophy'),

    ('Kabbalah unveiled', 'judaism', 'kabbalah'),
    ('Sefer Yetzirah book of formation', 'judaism', 'kabbalah'),
    ('Jewish mysticism kabbalah', 'judaism', 'kabbalah'),
    ('Zohar English', 'judaism', 'kabbalah'),
    ('Hasidism Baal Shem Tov', 'judaism', 'kabbalah'),

    ('Josephus complete works', 'judaism', 'jewish-history'),
    ('Graetz history of the Jews', 'judaism', 'jewish-history'),
    ('history of the Jewish people', 'judaism', 'jewish-history'),
    ('Jewish life in the Middle Ages', 'judaism', 'jewish-history'),

    ('Jewish daily prayer book English', 'judaism', 'liturgy'),
    ('Machzor festival prayers English', 'judaism', 'liturgy'),
    ('Passover Haggadah English', 'judaism', 'liturgy'),
    ('service of the synagogue', 'judaism', 'liturgy'),

    ('Legends of the Jews Ginzberg', 'judaism', 'jewish-study'),
    ('Jewish antiquities customs', 'judaism', 'jewish-study'),

    # --- Christianity ---------------------------------------------------
    ('Ante-Nicene Fathers', 'christianity', 'fathers'),
    ('Apostolic Fathers translation', 'christianity', 'fathers'),
    ('works of Saint Augustine', 'christianity', 'fathers'),
    ('homilies of Chrysostom', 'christianity', 'fathers'),
    ('Origen against Celsus', 'christianity', 'fathers'),
    ('Tertullian works', 'christianity', 'fathers'),
    ('Irenaeus against heresies', 'christianity', 'fathers'),
    ('Athanasius orations', 'christianity', 'fathers'),
    ('Jerome letters', 'christianity', 'fathers'),
    ('Cyprian epistles', 'christianity', 'fathers'),

    ('Book of Concord Lutheran confessions', 'christianity', 'creeds'),
    ('Westminster confession of faith', 'christianity', 'creeds'),
    ('canons and decrees council of Trent', 'christianity', 'creeds'),
    ('creeds of Christendom Schaff', 'christianity', 'creeds'),
    ('Heidelberg catechism', 'christianity', 'creeds'),

    ('Eusebius ecclesiastical history', 'christianity', 'christian-history'),
    ('Bede ecclesiastical history England', 'christianity', 'christian-history'),
    ('Foxe book of martyrs', 'christianity', 'christian-history'),
    ('history of the Reformation', 'christianity', 'christian-history'),
    ('history of the Christian church', 'christianity', 'christian-history'),
    ('lives of the saints', 'christianity', 'christian-history'),

    ('Imitation of Christ Thomas a Kempis', 'christianity', 'christian-study'),
    ('Summa Theologica Aquinas', 'christianity', 'christian-study'),
    ('Calvin Institutes of the Christian Religion', 'christianity', 'christian-study'),
    ('works of Martin Luther', 'christianity', 'christian-study'),
    ('sermons of John Wesley', 'christianity', 'christian-study'),
    ('Spurgeon sermons', 'christianity', 'christian-study'),
    ('Jonathan Edwards works', 'christianity', 'christian-study'),
    ('serious call to a devout life William Law', 'christianity', 'christian-study'),
    ('cloud of unknowing', 'christianity', 'christian-study'),
    ('Book of Common Prayer', 'christianity', 'christian-study'),
    ('Expositor\'s Bible commentary', 'christianity', 'christian-study'),
    ('Septuagint English translation', 'christianity', 'old-testament'),

    ('apocryphal gospels acts', 'christianity', 'nt-apocrypha'),
    ('Gospel of Nicodemus', 'christianity', 'nt-apocrypha'),
    ('Clementine homilies recognitions', 'christianity', 'nt-apocrypha'),

    ('book of Enoch translation', 'christianity', 'pseudepigrapha'),
    ('book of Jubilees translation', 'christianity', 'pseudepigrapha'),
    ('Apocalypse of Baruch', 'christianity', 'pseudepigrapha'),
    ('Odes and Psalms of Solomon', 'christianity', 'pseudepigrapha'),
]

RE_YEAR = re.compile(r'\b(1[0-9]{3}|20[0-2][0-9])\b')

# The item must actually be about the tradition it was searched for.
# archive.org's relevance ranking is loose enough to return the Harvard
# Classics for a search on "Bukhari", and a Dutch Republic history for one
# on "the Reformation".
RELEVANT = {
    'islam': re.compile(
        r'islam|muslim|moslem|muhammad|mohammed|mahomet|koran|qur.?an|hadith|'
        r'hadees|sunna|caliph|khalif|sufi|dervish|rumi|masnavi|hafiz|saadi|'
        r'sa.di|attar|ghazali|ghazzali|bukhari|buhari|muslim law|mishcat|'
        r'mishkat|arab|persian|ottoman|saracen|moor|shiah|shia|sunni|'
        r'muhammadan|mohammedan|mussulman|allah|prophet', re.I),
    'judaism': re.compile(
        r'jew|jewish|judaism|hebrew|israelite|talmud|mishna|midrash|torah|'
        r'rabbi|rabbinic|synagog|kabbal|cabal|qabbal|zohar|halak|hasid|'
        r'chasid|maimonid|josephus|philo|haggada|siddur|machzor|passover|'
        r'pentateuch|targum|semitic|zion|aboth|gaon|yiddish', re.I),
    'christianity': re.compile(
        r'christ|christian|church|bible|biblical|gospel|apostl|testament|'
        r'jesus|catholic|protestant|puritan|reformation|monk|monastic|'
        r'abbey|saint|theolog|creed|liturg|sermon|homil|patristic|nicene|'
        r'augustin|aquinas|calvin|luther|wesley|martyr|psalm|epistle|'
        r'scripture|papal|pope|bishop|prayer|divinity|evangel|septuagint|'
        r'apocryph|enoch|jubilees', re.I),
}

# A date of 1846 on a book that names an ISBN is a modern reprint uploaded
# under the original's date. Copyright cannot be judged from the catalogue
# alone, so the text is asked too: these markers mean a modern edition, and a
# modern edition is refused however old the work it prints.
MODERN_MARKERS = re.compile(
    r'\bISBN\b|All rights reserved|\bCopyright\s*©|©\s*(19[3-9]\d|20\d\d)|'
    r'Library of Congress Cataloging-in-Publication|'
    r'https?://|www\.[a-z]|\.com\b|\.org\b|First published in (19[3-9]\d|20\d\d)|'
    r'Printed in the United States of America',
    re.I)


def modern_reprint(text, sample=60000):
    """Evidence in the text that this is a modern edition, or ''."""
    head = text[:sample]
    hits = {m.group(0).lower() for m in MODERN_MARKERS.finditer(head)}
    # A stray URL in an OCR'd scan is noise; several markers is a pattern.
    return ', '.join(sorted(hits)[:3]) if len(hits) >= 2 else ''

_last = [0.0]


def _get(url, binary=False, pause=0.6, timeout=120):
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


def search(query, rows=60):
    """Ask archive.org, already narrowed to English texts of the right age."""
    q = (f'({query}) AND mediatype:texts AND language:(eng OR English) '
         f'AND date:[1500-01-01 TO {PD_CUTOFF}-12-31]')
    url = ('https://archive.org/advancedsearch.php?q='
           + urllib.parse.quote(q)
           + '&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=year'
           + '&fl%5B%5D=creator&fl%5B%5D=date'
           + f'&rows={rows}&page=1&output=json')
    raw = _get(url)
    if not raw:
        return []
    try:
        return json.loads(raw).get('response', {}).get('docs', [])
    except ValueError:
        return []


def published_year(meta):
    """The year a work was published, or None when it cannot be trusted.

    Several fields may carry it and several may disagree; the earliest
    plausible year wins, because that is the one that decides copyright, and
    a missing or unparseable date is a refusal rather than a guess.
    """
    years = []
    for key in ('date', 'year', 'publication_date'):
        value = meta.get(key)
        if isinstance(value, list):
            value = ' '.join(str(v) for v in value)
        if value:
            years += [int(y) for y in RE_YEAR.findall(str(value))]
    years = [y for y in years if 1400 <= y <= 2030]
    return min(years) if years else None


def item(identifier):
    raw = _get(f'https://archive.org/metadata/{urllib.parse.quote(identifier)}')
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return None


def take(identifier, religion, section, dry_run=False):
    """-> (status, year, title). Status says why it was kept or refused."""
    txt_path = os.path.join(DEST, f'ia-{identifier}.txt')
    if os.path.isfile(txt_path) and os.path.getsize(txt_path) > 5000:
        return 'already held', None, ''

    data = item(identifier)
    if not data:
        return 'no metadata', None, ''
    meta = data.get('metadata', {})
    title = str(meta.get('title', ''))[:120]

    haystack = ' '.join(str(meta.get(k, '')) for k in
                        ('title', 'creator', 'subject', 'description'))
    if not RELEVANT[religion].search(haystack):
        return f'not a {religion} text', None, title

    year = published_year(meta)
    if year is None:
        return 'no usable date', None, title
    if year > PD_CUTOFF:
        return f'published {year}, too recent', year, title

    lang = str(meta.get('language', '')).lower()
    if lang and not any(t in lang for t in ('eng', 'english')):
        return f'language {lang}', year, title

    names = [f['name'] for f in data.get('files', [])]
    full = next((n for n in names if n.endswith('_djvu.txt')), None)
    if not full:
        return 'no full text', year, title

    if dry_run:
        # The modern-reprint test needs the text, which a dry run does not
        # download, so this is the catalogue's verdict only.
        return f'WOULD TAKE ({year})', year, title

    body = _get(f'https://archive.org/download/{identifier}/'
                + urllib.parse.quote(full), binary=True, timeout=180)
    if not body or len(body) < 5000:
        return 'text too short', year, title

    text = body.decode('utf-8', 'replace')
    if not english.is_english(text):
        return 'not English', year, title
    reprint = modern_reprint(text)
    if reprint:
        return f'modern reprint ({reprint})', year, title

    os.makedirs(DEST, exist_ok=True)
    with open(txt_path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    corpus.write_json(os.path.join(DEST, f'ia-{identifier}.meta.json'), {
        'work_id': f'ia-{identifier}',
        'identifier': identifier,
        'title': title,
        'creator': meta.get('creator', ''),
        'year': year,
        'section': section,
        'religion': religion,
        'language': meta.get('language', ''),
        'rights': f'Public domain in the United States: published {year}, '
                  f'more than 95 years ago.',
        'source_url': f'https://archive.org/details/{identifier}',
    })
    return f'taken ({year})', year, title


def main(argv):
    dry_run = '--dry-run' in argv
    seen, kept = set(), 0
    refused = {}

    for query, religion, section in SEARCHES:
        hits = search(query)
        new = [h for h in hits if h.get('identifier') not in seen]
        seen.update(h.get('identifier') for h in hits)
        took = 0
        for h in new:
            ident = h.get('identifier')
            if not ident:
                continue
            try:
                status, _year, title = take(ident, religion, section, dry_run)
            except Exception as e:                                # noqa: BLE001
                status, title = f'error {type(e).__name__}', ''
            if status.startswith(('taken', 'WOULD TAKE')):
                took += 1
                kept += 1
                print(f'    + {status:22} {title[:62]}', flush=True)
            else:
                refused[status.split(',')[0]] = refused.get(
                    status.split(',')[0], 0) + 1
        print(f'  {query:28s} {len(hits):3d} found, {took:3d} taken',
              flush=True)

    print(f'\n{kept} texts taken')
    print('refused:')
    for why, n in sorted(refused.items(), key=lambda kv: -kv[1]):
        print(f'  {n:5d}  {why}')


if __name__ == '__main__':
    main(sys.argv[1:])
