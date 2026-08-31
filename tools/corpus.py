"""The canonical corpus: taxonomy, work schema, and the store on disk.

Every ingester, whatever it reads, writes through `Work.save()`, so the web
app only ever meets one shape. A work is stored as a small metadata file plus
one file per chapter:

    corpus/works/<religion>/<work-id>/work.json      metadata + chapter list
    corpus/works/<religion>/<work-id>/c/<n>.json     one chapter

split that way because a Church Fathers volume runs to five megabytes and the
reader should never have to parse five megabytes to show one chapter.
"""
import json
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, 'corpus')
WORKS = os.path.join(CORPUS, 'works')

# --- the taxonomy ---------------------------------------------------------
#
# Three religions, each with its own sections in its own traditional order.
# A work belongs to exactly one religion; works the traditions share (the
# Hebrew Bible above all) are filed under each, pointing at the same text.
RELIGIONS = {
    'judaism': {
        'name': 'Judaism',
        'blurb': 'The Tanakh, the rabbinic literature that reads it, and the '
                 'philosophy, mysticism and history that grew from both.',
        'sections': [
            ('torah', 'The Torah', 'The five books of Moses.'),
            ('neviim', "The Prophets", 'Nevi’im — the former and latter prophets.'),
            ('ketuvim', 'The Writings', 'Ketuvim — poetry, wisdom and the later histories.'),
            ('mishnah', 'The Mishnah', 'The first written rabbinic law, c. 200 CE.'),
            ('talmud', 'The Talmud', 'The Gemara’s argument over the Mishnah.'),
            ('midrash', 'Midrash', 'Rabbinic exposition and narrative expansion.'),
            ('halakhah', 'Law', 'Halakhah — the codes, and the responsa that apply them.'),
            ('jewish-philosophy', 'Philosophy & Ethics', 'Reasoned accounts of the tradition.'),
            ('kabbalah', 'Mysticism', 'The mystical and esoteric literature.'),
            ('jewish-history', 'History', 'Josephus and the historians after him.'),
            ('liturgy', 'Liturgy & Prayer', 'The prayer book and the festival cycle.'),
            ('jewish-study', 'Study & Reference', 'Grammars, lexicons, introductions and commentary.'),
        ],
    },
    'christianity': {
        'name': 'Christianity',
        'blurb': 'The Bible, the books outside its canon that the early church '
                 'still read, and the Fathers who argued over both.',
        'sections': [
            ('old-testament', 'The Old Testament', 'The Hebrew scriptures in Christian order.'),
            ('new-testament', 'The New Testament', 'The gospels, the letters and the Revelation.'),
            ('deuterocanon', 'The Deuterocanonical Books', 'Received as scripture by most of the church.'),
            ('apocrypha', 'The Wider Apocrypha', 'Read widely, canonised narrowly.'),
            ('pseudepigrapha', 'The Pseudepigrapha', 'Enoch, Jubilees, and the books written under old names.'),
            ('nt-apocrypha', 'The New Testament Apocrypha', 'The gospels and acts left outside the canon.'),
            ('restoration', 'The Restoration Scriptures', 'The Book of Mormon, the Doctrine and Covenants and the Pearl of Great Price.'),
            ('fathers', 'The Church Fathers', 'The Ante-Nicene and Nicene writers.'),
            ('creeds', 'Creeds & Councils', 'What the church settled, and how.'),
            ('christian-history', 'History', 'The church’s account of itself.'),
            ('christian-study', 'Study & Reference', 'Commentary, introductions, atlases and lexicons.'),
        ],
    },
    'islam': {
        'name': 'Islam',
        'blurb': 'The Qur’an in the English translations that are free to '
                 'reprint, with the hadith, the life, and the devotional '
                 'literature around them.',
        'sections': [
            ('quran', 'The Qur’an', 'The scripture, in several public-domain translations.'),
            ('hadith', 'Hadith', 'The recorded sayings and practice of the Prophet.'),
            ('sira', 'The Life of the Prophet', 'Biography and the early campaigns.'),
            ('sufism', 'Sufism & Devotion', 'The mystical and poetic tradition.'),
            ('islamic-law', 'Law & Theology', 'Jurisprudence, creed and doctrine.'),
            ('islamic-history', 'History', 'The caliphates and the wider Muslim world.'),
            ('islamic-study', 'Study & Reference', 'Introductions, commentary and reference works.'),
        ],
    },
}

SECTION_INDEX = {
    sid: (rel, name, blurb, order)
    for rel, meta in RELIGIONS.items()
    for order, (sid, name, blurb) in enumerate(meta['sections'])
}

CANON = ('canonical', 'deuterocanonical', 'noncanonical', 'secondary')


def slugify(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = s.encode('ascii', 'ignore').decode('ascii').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return re.sub(r'-{2,}', '-', s)[:80] or 'untitled'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Chapter:
    """One chapter. Verse works carry `verses`; prose works carry `blocks`."""

    def __init__(self, n, title='', verses=None, blocks=None):
        self.n = str(n)
        self.title = title
        self.verses = verses or []          # [{'n': '1', 'text': '...'}]
        self.blocks = blocks or []          # [{'k': 'p'|'h'|'q', 't': '...'}]

    def text(self):
        if self.verses:
            return '\n'.join(v['text'] for v in self.verses)
        return '\n'.join(b['t'] for b in self.blocks)

    def as_dict(self):
        d = {'n': self.n, 'title': self.title}
        if self.verses:
            d['verses'] = self.verses
        if self.blocks:
            # a verse chapter may still carry a note of its own — where a
            # sura was revealed, what a psalm's superscription says
            d['blocks'] = self.blocks
        return d


class Work:
    def __init__(self, id, title, religion, section, *, subtitle='',
                 structure='prose', canon='secondary', sort=0,
                 translation='', translator='', year=None,
                 modernization='safe', rights=None, provenance=None,
                 also_in=None):
        if religion not in RELIGIONS:
            raise ValueError(f'unknown religion {religion!r}')
        if section not in SECTION_INDEX:
            raise ValueError(f'unknown section {section!r}')
        self.id = id
        self.title = title
        self.subtitle = subtitle
        self.religion = religion
        self.section = section
        self.sort = sort
        self.canon = canon
        self.structure = structure
        self.translation = translation
        self.translator = translator
        self.year = year
        self.modernization = modernization
        self.rights = rights or {}
        self.provenance = provenance or {}
        self.also_in = also_in or []        # [(religion, section, sort)]
        self.chapters = []

    def add(self, chapter):
        self.chapters.append(chapter)

    # --- statistics -------------------------------------------------------
    def stats(self):
        verses = sum(len(c.verses) for c in self.chapters)
        text = '\n'.join(c.text() for c in self.chapters)
        return {
            'chapters': len(self.chapters),
            'verses': verses,
            'words': len(text.split()),
            'characters': len(text),
        }

    def full_text(self):
        return '\n'.join(c.text() for c in self.chapters)

    def dir(self):
        return os.path.join(WORKS, self.religion, self.id)

    def meta(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'religion': self.religion,
            'section': self.section,
            'section_name': SECTION_INDEX[self.section][1],
            'sort': self.sort,
            'canon': self.canon,
            'structure': self.structure,
            'language': 'en-US',
            'edition': {
                'translation': self.translation,
                'translator': self.translator,
                'year': self.year,
                'modernization': self.modernization,
            },
            'rights': self.rights,
            'provenance': dict(self.provenance, ingested_at=now()),
            'also_in': [{'religion': r, 'section': s, 'sort': o}
                        for r, s, o in self.also_in],
            'stats': self.stats(),
            'chapters': [{'n': c.n, 'title': c.title,
                          'verses': len(c.verses)} for c in self.chapters],
        }

    def save(self):
        # A work can change religion between builds — the Gutenberg catalog's
        # Library of Congress class reclassified sixteen of them — and writing
        # the new copy does not remove the old one, which would leave the same
        # id filed under two religions and break the search index's primary
        # key. Any older copy elsewhere goes first.
        for other in RELIGIONS:
            if other == self.religion:
                continue
            stale = os.path.join(WORKS, other, self.id)
            if os.path.isdir(stale):
                shutil.rmtree(stale)

        d = self.dir()
        cdir = os.path.join(d, 'c')
        os.makedirs(cdir, exist_ok=True)
        for stale in os.listdir(cdir):
            os.remove(os.path.join(cdir, stale))
        for c in self.chapters:
            write_json(os.path.join(cdir, f'{c.n}.json'), c.as_dict())
        m = self.meta()
        write_json(os.path.join(d, 'work.json'), m)
        return m


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def all_work_meta():
    """Every work.json on disk, in catalog order."""
    out = []
    for religion in RELIGIONS:
        base = os.path.join(WORKS, religion)
        if not os.path.isdir(base):
            continue
        for wid in sorted(os.listdir(base)):
            m = read_json(os.path.join(base, wid, 'work.json'))
            if m:
                out.append(m)
    out.sort(key=lambda m: (m['religion'],
                            SECTION_INDEX.get(m['section'], ('', '', '', 99))[3],
                            m.get('sort', 0), m['title']))
    return out


PD = {
    'status': 'public-domain',
    'statement': 'Public domain in the United States.',
}


def rights(statement, url='', status='public-domain'):
    return {'status': status, 'statement': statement, 'source_url': url}
