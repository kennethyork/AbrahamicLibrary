"""Ingest the Islamic texts fetched from archive.org.

`tools.fetch_archive` has already done the hard part — proving each text is
free by its publication date, and refusing modern reprints uploaded under an
old date. This reads what survived that and files it under Islam in the
section the search assigned.

These are scans put through OCR, not proofread transcriptions like
Gutenberg's, so the text is cleaned harder: page furniture, hyphens broken
across lines, and the running heads that OCR leaves behind.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import (corpus, english, modernize, nonfiction, parallel,   # noqa: E402
                   prose)
from tools.corpus import Chapter, Work, rights                     # noqa: E402

SRC = os.path.join(corpus.ROOT, 'sources', 'collector', 'archive')

DEFAULT_SECTION = {'islam': 'islamic-study', 'judaism': 'jewish-study',
                   'christianity': 'christian-study'}

# OCR leaves a page number alone on a line, and often a running head with it.
RE_PAGE_NUM = re.compile(r'^\s*[\[\(]?\d{1,4}[\]\)]?\s*$')
RE_OCR_JUNK = re.compile(r'^[^A-Za-z]*$')
# A word broken across a line end: "consid-\nered"
RE_HYPHEN_BREAK = re.compile(r'([A-Za-z])-\s*\n\s*([a-z])')
RE_DIGITISED = re.compile(
    r'Digitized by.*|Google\b|UNIVERSITY OF .*|Original from.*',
    re.I)


def clean_ocr(text):
    """Take the book out of the scan."""
    text = RE_HYPHEN_BREAK.sub(r'\1\2', text)
    lines = []
    for line in text.split('\n'):
        if RE_PAGE_NUM.match(line) or RE_DIGITISED.search(line):
            lines.append('')            # a break, not a word
            continue
        if RE_OCR_JUNK.match(line) and len(line.strip()) < 4:
            lines.append('')
            continue
        lines.append(line)
    return '\n'.join(lines)


def load(vid):
    txt = os.path.join(SRC, f'{vid}.txt')
    meta = corpus.read_json(os.path.join(SRC, f'{vid}.meta.json'))
    if not meta or not os.path.isfile(txt):
        return None, None
    with open(txt, encoding='utf-8', errors='replace') as fh:
        return meta, clean_ocr(fh.read())


# The fetcher's relevance test reads the description too, which is loose
# enough to let a 1913 Broadway novel through on the word "Arabian". Entry to
# the archive asks the title and the author only, which is the difference
# between a book about Islam and a book that mentions it.
# The fetcher already proved each text free by its date and checked that it
# was about the tradition it was searched for. Entry to the archive asks the
# title and the author only, which is a narrower question than the fetcher's
# and catches what its wider haystack — description and subject tags — let
# through: a 1913 Broadway novel arrived on the word "Arabian".
RELEVANT_TITLE = {
    'islam': re.compile(
        r'islam|muslim|moslem|muhammad|mohammed|mahomet|koran|qur.?an|hadith|'
        r'hadees|sunna|calif|caliph|khalif|sufi|dervish|rumi|masnavi|mesnevi|'
        r'hafiz|saadi|sa.di|gulistan|attar|ghazali|ghazzali|bukhari|buhari|'
        r'mishcat|mishkat|saracen|moorish|moslem|shiah|sunni|muhammadan|'
        r'mohammedan|mussulman|allah|arabian nights|arabic|persian poet|'
        r'ibn |al-|abu |omar khayyam|rubaiyat|divan|sheikh|imam|mecca|medina|'
        r'ottoman|turk|dervish|fakir|sacred books of the east', re.I),
    'judaism': re.compile(
        r'jew|jewish|judaism|hebrew|israelite|talmud|mishna|midrash|torah|'
        r'rabbi|rabbinic|synagog|kabbal|cabal|qabbal|zohar|halak|hasid|'
        r'chasid|maimonid|josephus|philo|haggada|siddur|machzor|passover|'
        r'pentateuch|targum|aboth|abot|gaon|ginzberg|graetz|leeser|'
        r'rodkinson|yiddish|semitic', re.I),
    'christianity': re.compile(
        r'christ|christian|church|bible|biblical|gospel|apostl|testament|'
        r'jesus|catholic|protestant|puritan|reformation|monk|monastic|'
        r'abbey|saint|st\.|theolog|creed|liturg|sermon|homil|patristic|'
        r'nicene|augustin|aquinas|calvin|luther|wesley|spurgeon|edwards|'
        r'martyr|psalm|epistle|scripture|papal|pope|bishop|prayer|'
        r'divinity|evangel|septuagint|apocryph|enoch|jubilees|kempis|'
        r'eusebius|chrysostom|origen|tertullian|irenaeus|athanasius|'
        r'jerome|cyprian|foxe|trent|concord|catechism|confession', re.I),
}

# …but never these, whatever they mention.
NOT_A_TEXT = re.compile(
    r'\bbroadway\b|\bmusical\b|\bnovel\b|\bplay in (three|four|five)\b|'
    r'\bWashington Irving\b|Harvard Classics|Books Collection|'
    r'\bwar with\b|\blancers\b|Catalog of Copyright Entries',
    re.I)


def relevant(meta):
    hay = f"{meta.get('title', '')} {creator_of(meta)}"
    rx = RELEVANT_TITLE.get(meta.get('religion') or 'islam')
    return bool(rx and rx.search(hay)) and not NOT_A_TEXT.search(hay)


def creator_of(meta):
    c = meta.get('creator')
    if isinstance(c, list):
        c = '; '.join(str(x) for x in c)
    return re.sub(r'\s+', ' ', str(c or '')).strip()[:120]


def one_text(fn):
    """Clean, modernize and save one scanned text, in its own process.

    -> ('made', meta, report) | ('setaside', title) | None
    """
    vid = fn[:-len('.meta.json')]
    meta, body = load(vid)
    if not meta or not body:
        return None
    if not relevant(meta):
        return ('setaside', meta.get('title', vid)[:70])
    keep, _why = nonfiction.verdict(meta.get('title', ''), [])
    if not keep:
        return ('setaside', meta.get('title', vid)[:70])
    if not english.is_english(body):
        return None

    chapters = prose.split_by_headings(body)
    if not chapters:
        paras = prose.paragraphs(body)
        if sum(len(p) for p in paras) < 3000:
            return None
        chapters = [('', paras)]

    report = modernize.Report()
    year = meta.get('year')
    w = Work(id=vid, title=meta.get('title', vid)[:180],
             subtitle=creator_of(meta),
             religion=meta.get('religion', 'islam'),
             section=meta.get('section') or DEFAULT_SECTION.get(
                 meta.get('religion', 'islam'), 'islamic-study'),
             sort=int(year or 0), structure='prose', canon='secondary',
             translation=meta.get('title', '')[:180],
             translator=creator_of(meta), year=year,
             modernization='full',
             rights=rights(meta.get('rights', ''), meta.get('source_url', '')),
             provenance={'source': 'archive.org',
                         'identifier': meta.get('identifier', ''),
                         'source_file': f'sources/collector/archive/{vid}.txt',
                         'note': 'Scanned and OCR\u2019d, not a proofread '
                                 'transcription; page furniture removed. '
                                 f'Public domain by its publication date '
                                 f'({year}).'})

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
        return None
    return ('made', w.save(), report.as_dict())


def main():
    if not os.path.isdir(SRC):
        sys.exit('nothing fetched yet \u2014 run tools.fetch_archive first')

    files = sorted(f for f in os.listdir(SRC) if f.endswith('.meta.json'))
    results = parallel.run(one_text, files,
                           on_result=parallel.progress('archive.org'))

    made = [r[1] for r in results if r[0] == 'made']
    merged = parallel.merge_counters([r[2] for r in results if r[0] == 'made'])
    setaside = [r[1] for r in results if r[0] == 'setaside']

    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'archive.json'),
                      merged)
    if setaside:
        print(f'  set aside as not Islamic source texts ({len(setaside)}):')
        for t in setaside[:12]:
            print(f'    - {t}')
        if len(setaside) > 12:
            print(f'    \u2026 and {len(setaside) - 12} more')
    print(f'archive.org: {len(made)} works, '
          f'{sum(m["stats"]["chapters"] for m in made)} chapters, '
          f'{sum(m["stats"]["words"] for m in made):,} words; '
          f'modernizer changed {merged["changed_occurrences"]:,} occurrences, '
          f'{merged["unresolved_forms"]} forms unresolved')


if __name__ == '__main__':
    main()
