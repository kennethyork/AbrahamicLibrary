"""Ingest the Project Gutenberg shelf into the archive.

Two passes.

The Douay-Rheims Bible is handled on its own, because Gutenberg publishes it
one book per file and those seventy-three files are a complete second English
Bible. Titled by their book names, they line up with the World English Bible
and the 1917 Tanakh, so Genesis can be read in three translations at once.

Everything else is classified by its Gutenberg subject headings and title into
a religion and a section. The shelf is mostly Christian commentary, history
and study — that is what Gutenberg holds — so most of it lands in those
sections rather than among the scriptures.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import (corpus, english, modernize, nonfiction, parallel,   # noqa: E402
                   prose)
from tools.corpus import Chapter, Work, rights                     # noqa: E402

SRC = os.path.join(corpus.ROOT, 'sources', 'collector', 'gutenberg')

PG_RIGHTS_TEXT = (
    'Public domain in the United States; distributed by Project Gutenberg. '
    'Readers outside the United States should check their own local law.')

# --- the Douay-Rheims, one Gutenberg book per book of the Bible -----------

DR_RANGE = range(8301, 8374)
DR_SKIP = {1581, 1582, 1609, 1610, 8300}        # the combined volumes

# The Book of Mormon is scripture with chapters and verses, and Gutenberg
# marks every one of them. `tools.ingest_mormon` reads it properly; this
# shelf would file it as one long prose lump.
OWNED_ELSEWHERE = {
    17,        # the Book of Mormon — `tools.ingest_mormon` reads it properly
    16955,     # three Qur’ans in parallel — `tools.ingest_quran` takes the
               # one of them that is free, and as verses rather than prose
}

RE_DR = re.compile(r'^The Bible, Douay-Rheims, Book (\d+):\s*(.+?)(?::\s*The Challoner Revision)?$')

# The Douay-Rheims names several books differently; the modern name is given
# so the volume lines up with the other translations for comparison.
DR_NAMES = {
    'Josue': 'Joshua', '1 Kings': '1 Samuel', '2 Kings': '2 Samuel',
    '3 Kings': '1 Kings', '4 Kings': '2 Kings',
    '1 Paralipomenon': '1 Chronicles', '2 Paralipomenon': '2 Chronicles',
    '1 Esdras': 'Ezra', '2 Esdras': 'Nehemiah', 'Tobias': 'Tobit',
    'Canticle of Canticles': 'Song of Songs', 'Ecclesiasticus': 'Sirach',
    'Isaias': 'Isaiah', 'Jeremias': 'Jeremiah',
    'Lamentations of Jeremias': 'Lamentations', 'Ezechiel': 'Ezekiel',
    'Osee': 'Hosea', 'Abdias': 'Obadiah', 'Jonas': 'Jonah',
    'Micheas': 'Micah', 'Habacuc': 'Habakkuk', 'Sophonias': 'Zephaniah',
    'Aggeus': 'Haggai', 'Zacharias': 'Zechariah', 'Malachias': 'Malachi',
    '1 Machabees': '1 Maccabees', '2 Machabees': '2 Maccabees',
    'Apocalypse': 'Revelation', 'Paralipomenon': 'Chronicles',
}

DR_DEUTERO = {'Tobit', 'Judith', 'Wisdom', 'Sirach', 'Baruch',
              '1 Maccabees', '2 Maccabees'}

# '1:1. In the beginning God created heaven, and earth.'
RE_DR_VERSE = re.compile(r'^(\d{1,3}):(\d{1,3})\.\s+(.*)$', re.S)

# --- classification -------------------------------------------------------
#
# Ordered: the first rule that matches a book's subjects or title wins.
RULES = [
    (r'\bkoran|qur.?an\b',                       'islam', 'quran'),
    (r'\bhadith|sunnah\b',                       'islam', 'hadith'),
    (r'\bmohammed|muhammad|prophet of islam\b',  'islam', 'sira'),
    (r'\bsufi|dervish|rumi|masnavi|omar khayyam\b', 'islam', 'sufism'),
    (r'\bislam|muslim|moslem|mahometan|caliph\b', 'islam', 'islamic-history'),

    (r'\btalmud\b',                              'judaism', 'talmud'),
    (r'\bmishna\b',                              'judaism', 'mishnah'),
    (r'\bmidrash|haggada\b',                     'judaism', 'midrash'),
    (r'\bkabbala|cabala|zohar\b',                'judaism', 'kabbalah'),
    (r'\bjosephus\b',                            'judaism', 'jewish-history'),
    (r'\bjews|jewish|judaism|hebrew(?!\s+bible)|rabbi|synagogue|yiddish\b',
                                                 'judaism', 'jewish-history'),

    (r'\bapocrypha|deuterocanonical\b',      'christianity', 'deuterocanon'),
    (r'\bpseudepigrapha|book of enoch|jubilees\b',
                                             'christianity', 'pseudepigrapha'),
    (r'\bapostolic fathers|ante-nicene|church fathers|patristic\b',
                                             'christianity', 'fathers'),
    (r'\bcreed|council of (nicaea|trent)|catechism\b',
                                             'christianity', 'creeds'),
    (r'\bchurch history|history of the church|reformation|martyr|missions?\b',
                                             'christianity', 'christian-history'),
]

FALLBACK = ('christianity', 'christian-study')

# Books that are not religious texts at all, however they were collected.
JUNK = re.compile(
    r'\b(lancers|south africa|hungarian|finnish|dutch|german\)|french\)|'
    r'kroatien|maatiede|mesek)\b', re.I)


# The Restoration scriptures have their own shelf; everything else written
# by or about the Latter-day Saints is history or study like anyone else's.
RESTORATION = (r'\bbook of mormon\b|\bdoctrine and covenants\b|'
               r'\bpearl of great price\b')

# Gutenberg files scripture commentary under headings like `Bible. John --
# Criticism, interpretation, etc.` or `Bible. N.T. -- Introductions`, which
# says which testament far better than any word in the title does.
NT_BOOKS = (r'\bbible\. ?(?:n\.? ?t\.?|gospels?|matthew|mark|luke|john|acts|'
            r'romans|corinthians|galatians|ephesians|philippians|colossians|'
            r'thessalonians|timothy|titus|philemon|hebrews|james|peter|jude|'
            r'revelation)\b')
OT_BOOKS = (r'\bbible\. ?(?:o\.? ?t\.?|genesis|exodus|leviticus|numbers|'
            r'deuteronomy|joshua|judges|ruth|samuel|kings|chronicles|ezra|'
            r'nehemiah|esther|job|psalms|proverbs|ecclesiastes|song of|'
            r'isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|'
            r'obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|'
            r'malachi|pentateuch)\b')


# Sections within a religion, chosen from the subject headings. The religion
# itself comes from the Library of Congress class in the catalog, which is
# authoritative; only the shelf within it is guessed at.
SECTIONS = {
    'islam': [
        (r'\bkoran|qur.?an\b', 'quran'),
        (r'\bhadith|sunnah\b', 'hadith'),
        (r'\bmuhammad|mohammed|prophet\b', 'sira'),
        (r'\bsufi|dervish|rumi|masnavi|khayyam|persian poetry\b', 'sufism'),
        (r'\blaw|jurisprudence|theolog|creed\b', 'islamic-law'),
        (r'\bhistory|caliph|empire|turkey|crusade\b', 'islamic-history'),
    ],
    'judaism': [
        (r'\btalmud\b', 'talmud'),
        (r'\bmishna\b', 'mishnah'),
        (r'\bmidrash|haggada\b', 'midrash'),
        (r'\bkabbala|cabala|zohar|mystic\b', 'kabbalah'),
        (r'\bliturg|prayer|festival\b', 'liturgy'),
        (r'\blaw\b', 'halakhah'),
        (r'\bhistory|josephus|persecut\b', 'jewish-history'),
        (r'\bphilosoph|ethic\b', 'jewish-philosophy'),
    ],
    'christianity': [
        (RESTORATION, 'restoration'),
        # Enoch, Jubilees and the Books of Adam and Eve are all catalogued
        # under `Apocryphal books (Old Testament)`, the same heading Tobit
        # and Judith get, so the narrower rule has to be asked first or
        # they end up on the deuterocanonical shelf beside them.
        (r'\bpseudepigrapha|enoch|jubilees|adam and eve|'
         r'twelve patriarchs|sibylline\b', 'pseudepigrapha'),
        (r'\bapocrypha|deuterocanonical\b', 'deuterocanon'),
        (r'\bfathers|ante-nicene|patristic\b', 'fathers'),
        (r'\bcreed|council|catechism|confession\b', 'creeds'),
        (r'\bnew testament\b|\bepistle|' + NT_BOOKS, 'new-testament'),
        (r'\bold testament\b|\bpentateuch\b|' + OT_BOOKS, 'old-testament'),
        # `gospel` on its own is not a shelf. It is in the title of every
        # revival sermon ever preached — "The Hope of the Gospel", "Gospel
        # Themes: A Treatise on Salient Features of Mormonism" — and it put
        # fifty-nine such books, nine of them Latter-day Saint, next to the
        # Gospel of John. Only the plural, or `gospel of`/`according to`,
        # names the books themselves.
        (r'\bgospels\b|\bgospel (?:of|according to)\b', 'new-testament'),
        (r'\bhistory|reformation|martyr|mission|church history\b',
         'christian-history'),
    ],
}

DEFAULT_SECTION = {'islam': 'islamic-study', 'judaism': 'jewish-study',
                   'christianity': 'christian-study'}


def classify(meta):
    """-> (religion, section).

    The religion comes from the catalog's Library of Congress class, which
    states what a book is; only where that is missing does it fall back to
    reading the title, which is what the whole catalog approach replaced.
    """
    hay = ' '.join([meta.get('title', '')] + list(meta.get('subjects', []))).lower()

    religion = meta.get('religion')
    if religion in SECTIONS:
        for pattern, section in SECTIONS[religion]:
            if re.search(pattern, hay):
                return religion, section
        return religion, DEFAULT_SECTION[religion]

    for pattern, religion, section in RULES:
        if re.search(pattern, hay):
            return religion, section
    return FALLBACK


def year_of(meta):
    for a in meta.get('authors', []):
        if a.get('death_year'):
            return int(a['death_year'])
    return None


def tier_for(meta):
    """The full tier, for everything on this shelf.

    Gutenberg only holds what is out of copyright, so every book here is old
    enough to be written in an English worth modernizing — and the ones that
    are not still quote the King James Bible at length, which is exactly what
    a reader of this archive should not have to stumble over. The one word
    that made the full tier unsafe for later prose was `art`, and that is now
    resolved by context rather than by tier, so "a work of art" survives.
    """
    return 'full'


def load(vid):
    txt = os.path.join(SRC, f'{vid}.txt')
    meta = corpus.read_json(os.path.join(SRC, f'{vid}.meta.json'))
    if not meta or not os.path.isfile(txt):
        return None, None
    with open(txt, encoding='utf-8', errors='replace') as fh:
        return meta, prose.strip_gutenberg(fh.read())


# --- the Douay-Rheims -----------------------------------------------------

def douay(report):
    made, order = [], 0
    for gid in DR_RANGE:
        meta, body = load(f'pg-{gid}')
        if not meta:
            continue
        # The catalog writes a title over two lines — `Book 19: Esther` and
        # then `The Challoner Revision` — and a regex anchored with `$` does
        # not match across that. When the metadata was rewritten from the
        # catalog, every one of the seventy-three books stopped matching and
        # the Douay-Rheims quietly stopped being rebuilt.
        m = RE_DR.match(re.sub(r'\s+', ' ', meta.get('title', '')).strip())
        if not m:
            continue
        booknum, name = int(m.group(1)), m.group(2).strip()
        name = DR_NAMES.get(name, name)

        section = ('new-testament' if booknum >= 47 else
                   'deuterocanon' if name in DR_DEUTERO else 'old-testament')

        w = Work(id=f'dr-{corpus.slugify(name)}', title=name,
                 religion='christianity', section=section, sort=booknum,
                 structure='verse',
                 canon='deuterocanonical' if section == 'deuterocanon' else 'canonical',
                 subtitle='Douay-Rheims, Challoner revision',
                 translation='The Douay-Rheims Bible, Challoner revision',
                 translator='Richard Challoner', year=1752,
                 modernization='full',
                 rights=rights(PG_RIGHTS_TEXT,
                               f'https://www.gutenberg.org/ebooks/{gid}'),
                 provenance={'source': f'Project Gutenberg {gid}',
                             'source_file': f'sources/collector/gutenberg/pg-{gid}.txt'})

        for chapter_n, chunk in split_dr_chapters(body):
            ch = Chapter(chapter_n, f'Chapter {chapter_n}')
            for vn, text, notes in chunk:
                said, src = modernize.pair(text, 'full', report)
                ch.verses.append({
                    'n': vn, 'text': said,
                    'notes': [{'ref': f'{chapter_n}:{vn}',
                               'text': modernize.modernize(n, 'full', report)}
                              for n in notes],
                    **({'src': src} if src else {}),
                })
            if ch.verses:
                w.add(ch)

        if w.chapters:
            made.append(w.save())
            order += 1
    print(f'  douay-rheims: {len(made)} books, '
          f'{sum(m["stats"]["chapters"] for m in made)} chapters, '
          f'{sum(m["stats"]["verses"] for m in made)} verses')
    return made


def split_dr_chapters(body):
    """Group the Douay-Rheims by its `chapter:verse.` markers.

    The text is set as paragraphs opening `1:1. In the beginning...`, with
    Challoner's own annotations standing between them as ordinary paragraphs.
    Keying on the markers rather than on the chapter headings picks the verses
    up exactly and leaves the annotations identifiable: an unmarked paragraph
    belongs to the verse above it, and is kept as a note on it.

    -> [(chapter, [(verse, text, [note, ...]), ...]), ...]
    """
    chapters, order = {}, []
    cur_ch = cur_v = None
    buf, notes = [], []

    def flush():
        if cur_ch is None or cur_v is None:
            return
        text = ' '.join(' '.join(buf).split())
        if text:
            chapters[cur_ch].append((cur_v, text, list(notes)))

    for para in re.split(r'\n\s*\n', body):
        para = para.strip()
        if not para:
            continue
        m = RE_DR_VERSE.match(para)
        if m:
            flush()
            cur_ch, cur_v = m.group(1), m.group(2)
            if cur_ch not in chapters:
                chapters[cur_ch] = []
                order.append(cur_ch)
            buf, notes = [m.group(3)], []
        elif cur_v is not None:
            # Challoner's annotation on the verse just given
            notes.append(' '.join(para.split()))
    flush()

    return [(ch, chapters[ch]) for ch in order if chapters[ch]]


# --- everything else ------------------------------------------------------

# Gutenberg gives three different Korans the same title, `The Koran
# (Al-Qur'an)`, and the difference between them — Rodwell, Sale — is only in
# the author field, with its cataloguing role attached. Pulled out and put
# under the title, it tells the reader which book they are looking at.
RE_ROLE = re.compile(r'\s*\[[^\]]*\]\s*$')


def byline(meta):
    names = []
    for a in meta.get('authors', []):
        name = RE_ROLE.sub('', (a.get('name') or '').strip())
        if not name or name == 'Anonymous':
            continue
        # `Rodwell, J. M. (John Medows), 1808-1900` -> `J. M. Rodwell`,
        # and `Smith, Joseph, Jr.` -> `Joseph Smith, Jr.` — the suffix is
        # part of the name and belongs at the end of it, not the middle.
        name = re.sub(r',\s*\d{0,4}\??\s*-\s*\d{0,4}\??$', '', name)
        name = re.sub(r'\s*\([^)]*\)', '', name).strip().rstrip(',')
        parts = [x.strip() for x in name.split(',') if x.strip()]
        if len(parts) > 1:
            suffix = ''
            if re.fullmatch(r'(?:jr|sr|[ivx]+)\.?', parts[-1], re.I):
                suffix, parts = ', ' + parts[-1], parts[:-1]
            name = ' '.join(parts[1:] + parts[:1]) + suffix
        if name not in names:
            names.append(name)
    return ', '.join(names[:3])[:120]


def one_book(vid):
    """Parse, modernize and save one Gutenberg book.

    Runs in its own process, so it takes only a string and returns only
    plain data. -> ('made', meta, report) | ('fiction', title, why) | None
    """
    gid = int(vid.split('-')[1]) if '-' in vid and vid.split('-')[1].isdigit() else 0
    meta, body = load(vid)
    if not meta or not body:
        return None
    title = (meta.get('title') or '').strip()
    if not title or JUNK.search(title):
        return None
    # Gutenberg's search returns every language, and its language field is
    # not always set. The text itself is the reliable witness.
    if not english.is_english(body):
        return None
    # A library of sources, not of stories about them: the Arabian Nights,
    # fairy tales, adventure novels and the Rubaiyat parodies are all
    # refused here on their own subject headings.
    keep, why = nonfiction.verdict(title, meta.get('subjects', []))
    if not keep:
        return ('fiction', title[:64], why)

    religion, section = classify(meta)
    tier = tier_for(meta)
    authors = ', '.join(a['name'] for a in meta.get('authors', [])
                        if a.get('name') and a['name'] != 'Anonymous')

    chapters = prose.split_by_headings(body)
    if not chapters:
        paras = prose.paragraphs(body)
        if sum(len(p) for p in paras) < 2000:
            return None
        chapters = [('', paras)]

    report = modernize.Report()
    # The catalog runs a title over several lines and marks the subtitle
    # with a MARC `$b`. Neither belongs on a page.
    shown = re.sub(r'\s+', ' ', re.sub(r'\s*:\s*\$b\s*', ': ', title)).strip()
    w = Work(id=f'pg-{gid}', title=shown[:180],
             subtitle=byline(meta),
             religion=religion, section=section, sort=gid,
             structure='prose', canon='secondary',
             translation=shown[:180], translator=authors, year=year_of(meta),
             modernization=tier,
             rights=rights(PG_RIGHTS_TEXT,
                           f'https://www.gutenberg.org/ebooks/{gid}'),
             provenance={'source': f'Project Gutenberg {gid}',
                         'source_file': f'sources/collector/gutenberg/{vid}.txt',
                         'subjects': meta.get('subjects', []),
                         'note': 'Chapters recovered from the headings in '
                                 'the plain text.'})

    for i, (heading, paras) in enumerate(chapters, 1):
        # The heading gets the same tier as the text under it. Modernizing
        # the body and leaving `Of the Vanity of Him that Hath Riches`
        # over the top of it is the one place archaic English survived
        # a full-tier book.
        ch = Chapter(i, modernize.modernize(heading, tier) or f'Part {i}')
        for p in paras:
            text, src = modernize.pair(p, tier, report)
            block = {'k': 'p', 't': text}
            if src:
                block['s'] = src          # the paragraph as it was printed
            ch.blocks.append(block)
        w.add(ch)

    if not w.chapters:
        return None
    return ('made', w.save(), report.as_dict())


def general(skip_ids):
    files = sorted(f for f in os.listdir(SRC) if f.endswith('.meta.json'))
    todo, stale = [], 0
    for fn in files:
        vid = fn[:-len('.meta.json')]
        # Downloads from before the catalog rewrite are still on disk, and
        # they are the ones that were picked by scraping search results:
        # French novels, `Moon of Israel: A Tale of the Exodus`, the
        # Rubaiyat parodies. Their metadata has no catalog classification,
        # which is exactly what marks them, and they are not read again.
        m = corpus.read_json(os.path.join(SRC, fn)) or {}
        if 'religion' not in m:
            stale += 1
            continue
        gid = int(vid.split('-')[1]) if '-' in vid and vid.split('-')[1].isdigit() else 0
        if (gid in skip_ids or gid in DR_SKIP or gid in DR_RANGE
                or gid in OWNED_ELSEWHERE):
            continue
        todo.append(vid)

    if stale:
        print(f'  passing over {stale} downloads from before the catalog')
    results = parallel.run(one_book, todo,
                           on_result=parallel.progress('gutenberg'))

    made = [r[1] for r in results if r[0] == 'made']
    reports = [r[2] for r in results if r[0] == 'made']
    fiction = [(r[1], r[2]) for r in results if r[0] == 'fiction']

    print(f'  general: {len(made)} books, '
          f'{sum(m["stats"]["words"] for m in made):,} words')
    if fiction:
        print(f'  refused as fiction ({len(fiction)}):')
        for t, why in fiction[:10]:
            print(f'    - {t}  [{why}]')
        if len(fiction) > 10:
            print(f'    … and {len(fiction) - 10} more')
    return made, reports


def main():
    report = modernize.Report()
    dr = douay(report)                       # 73 books, quick enough serially
    rest, reports = general(skip_ids=set())

    # The workers each kept their own tally; add them to the parent's.
    merged = parallel.merge_counters([report.as_dict()] + reports)
    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'gutenberg.json'),
                      merged)
    print(f'gutenberg: {len(dr) + len(rest)} works; modernizer changed '
          f'{merged["changed_occurrences"]:,} occurrences of '
          f'{merged["changed_forms"]} forms, '
          f'{merged["unresolved_forms"]} unresolved')


if __name__ == '__main__':
    main()
