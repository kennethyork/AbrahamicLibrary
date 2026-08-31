"""Reading plans, written as data and checked against the corpus.

A plan is a named sequence of days, and each day is a few chapters to read.
They are generated rather than typed because a plan that points at a chapter
which is not there is worse than no plan at all: every reference below is
resolved against the works on disk, and the build fails loudly if one of them
has moved.

    .venv/bin/python -m tools.build_plans
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus                                          # noqa: E402

OUT = os.path.join(corpus.ROOT, 'app', 'data', 'plans.json')
DAILY_OUT = os.path.join(corpus.ROOT, 'app', 'data', 'daily.json')

# A verse a day. Chosen to run across all three traditions rather than to
# comfort — a reader who opens this page every morning should meet the Qur'an
# and the Talmud as often as the Psalms. The text is written out here with
# the reference so the home page needs no lookup at all.
DAILY = [
    ('webu-gen', '1', '1'), ('webu-gen', '1', '27'),
    ('jps-genesis', '12', '2'), ('jps-exodus', '3', '14'),
    ('jps-leviticus', '19', '18'), ('jps-deuteronomy', '6', '4'),
    ('jps-isaiah', '1', '17'), ('jps-isaiah', '40', '31'),
    ('jps-micah', '6', '8'), ('jps-psalms', '23', '1'),
    ('jps-psalms', '90', '12'), ('jps-proverbs', '3', '5'),
    ('jps-ecclesiastes', '3', '1'), ('jps-jonah', '4', '11'),
    ('webu-mat', '5', '9'), ('webu-mat', '6', '34'),
    ('webu-mat', '22', '39'), ('webu-luk', '6', '31'),
    ('webu-jhn', '1', '5'), ('webu-jhn', '8', '32'),
    ('webu-rom', '12', '21'), ('webu-1co', '13', '4'),
    ('webu-php', '4', '8'), ('webu-jas', '1', '19'),
    ('webu-sir', '6', '14'), ('webu-wis', '3', '1'),
    ('quran-pickthall', '1', '1'), ('quran-pickthall', '2', '286'),
    ('quran-pickthall', '13', '11'), ('quran-pickthall', '17', '23'),
    ('quran-pickthall', '49', '13'), ('quran-pickthall', '94', '5'),
    ('quran-pickthall', '103', '1'), ('quran-pickthall', '112', '1'),
    ('lds-bom-moroni', '7', '45'), ('lds-bom-2-nephi', '2', '25'),
]


def build_daily():
    out, missing = [], 0
    for wid, c, v in DAILY:
        m = load_work(wid)
        if not m:
            missing += 1
            continue
        ch = corpus.read_json(os.path.join(
            corpus.WORKS, m['religion'], wid, 'c', f'{c}.json'))
        verse = next((x for x in (ch or {}).get('verses', [])
                      if str(x['n']) == str(v)), None)
        if not verse:
            missing += 1
            continue
        out.append({'work': wid, 'c': c, 'v': v, 'religion': m['religion'],
                    'ref': f'{m["title"]} {c}:{v}', 'text': verse['text'],
                    'edition': m['edition'].get('translator') or ''})
    corpus.write_json(DAILY_OUT, {'verses': out})
    print(f'  daily          {len(out):3d} verses'
          + (f', {missing} could not be found' if missing else ''))
    return missing


def run(work, first=1, last=None, per_day=1):
    """Chapters `first`…`last` of one work, `per_day` at a time."""
    return {'work': work, 'first': first, 'last': last, 'per_day': per_day}


PLANS = [
    {
        'id': 'gospels',
        'name': 'The four Gospels',
        'religion': 'christianity',
        'blurb': 'Matthew, Mark, Luke and John, a chapter a day. Eighty-nine '
                 'chapters, and the whole of what the church says happened.',
        'runs': [run('webu-mat'), run('webu-mrk'), run('webu-luk'),
                 run('webu-jhn')],
    },
    {
        'id': 'torah',
        'name': 'The Torah',
        'religion': 'judaism',
        'blurb': 'The five books of Moses in the Jewish Publication Society '
                 'translation of 1917, a chapter a day.',
        'runs': [run('jps-genesis'), run('jps-exodus'), run('jps-leviticus'),
                 run('jps-numbers'), run('jps-deuteronomy')],
    },
    {
        'id': 'quran',
        'name': 'The Qur’an in a month',
        'religion': 'islam',
        'blurb': 'All hundred and fourteen suras in thirty days, in '
                 'Pickthall’s translation of 1930 — roughly the pace of a '
                 'juz a night in Ramadan.',
        'runs': [run('quran-pickthall', per_day=4)],
    },
    {
        'id': 'psalms',
        'name': 'The Psalms in a month',
        'religion': 'judaism',
        'blurb': 'Five psalms a day for thirty days, the way the Book of '
                 'Common Prayer and the siddur have both divided them.',
        'runs': [run('webu-psa', per_day=5)],
    },
    {
        'id': 'wisdom',
        'name': 'The wisdom books',
        'religion': 'christianity',
        'blurb': 'Proverbs, Ecclesiastes, the Wisdom of Solomon and Sirach — '
                 'the part of the canon that argues rather than narrates.',
        'runs': [run('webu-pro'), run('webu-ecc'), run('webu-wis'),
                 run('webu-sir', per_day=2)],
    },
    {
        'id': 'beginnings',
        'name': 'Beginnings, three ways',
        'religion': '',
        'blurb': 'Fourteen days on the same handful of stories — the '
                 'creation, the flood, Abraham, Joseph, Moses — read in the '
                 'Hebrew, Christian and Muslim scriptures one after another, '
                 'so the differences are in front of you rather than in '
                 'memory.',
        'days': [
            ('The creation', [('jps-genesis', '1'), ('quran-pickthall', '41')]),
            ('The garden', [('jps-genesis', '2'), ('jps-genesis', '3'),
                            ('quran-pickthall', '7')]),
            ('Cain and Abel', [('jps-genesis', '4'), ('quran-pickthall', '5')]),
            ('The flood', [('jps-genesis', '6'), ('jps-genesis', '7'),
                           ('quran-pickthall', '71')]),
            ('After the flood', [('jps-genesis', '8'), ('jps-genesis', '9'),
                                 ('quran-pickthall', '11')]),
            ('Babel', [('jps-genesis', '11'), ('quran-pickthall', '28')]),
            ('The call of Abraham', [('jps-genesis', '12'),
                                     ('quran-pickthall', '14')]),
            ('Abraham and the covenant', [('jps-genesis', '15'),
                                          ('jps-genesis', '17'),
                                          ('quran-pickthall', '2')]),
            ('The binding', [('jps-genesis', '22'), ('quran-pickthall', '37')]),
            ('Jacob', [('jps-genesis', '28'), ('jps-genesis', '32')]),
            ('Joseph', [('jps-genesis', '37'), ('quran-pickthall', '12')]),
            ('Joseph and his brothers', [('jps-genesis', '42'),
                                         ('jps-genesis', '45')]),
            ('Moses in Egypt', [('jps-exodus', '2'), ('jps-exodus', '3'),
                                ('quran-pickthall', '20')]),
            ('The sea', [('jps-exodus', '14'), ('quran-pickthall', '26')]),
        ],
    },
    {
        'id': 'fathers',
        'name': 'The early church, in its own words',
        'religion': 'christianity',
        'blurb': 'A first month with the Apostolic Fathers and the '
                 'apologists — the generation immediately after the New '
                 'Testament, arguing with Rome and with itself.',
        # Cut to a month on purpose. The Ante-Nicene volume runs to eight
        # hundred and forty-one sections; a plan that quietly turns into a
        # five-month commitment is not a first month with the Fathers.
        'runs': [run('cur-thedidache00alleuoft', last=20, per_day=2),
                 run('ccel-anf01', last=120, per_day=6)],
    },
    {
        'id': 'restoration',
        'name': 'The Book of Mormon',
        'religion': 'christianity',
        'blurb': 'All fifteen books, two hundred and thirty-nine chapters, '
                 'at four a day.',
        'runs': [run('lds-bom-1-nephi', per_day=4), run('lds-bom-2-nephi', per_day=4),
                 run('lds-bom-jacob', per_day=4), run('lds-bom-enos', per_day=4),
                 run('lds-bom-jarom', per_day=4), run('lds-bom-omni', per_day=4),
                 run('lds-bom-words-of-mormon', per_day=4),
                 run('lds-bom-mosiah', per_day=4), run('lds-bom-alma', per_day=4),
                 run('lds-bom-helaman', per_day=4), run('lds-bom-3-nephi', per_day=4),
                 run('lds-bom-4-nephi', per_day=4), run('lds-bom-mormon', per_day=4),
                 run('lds-bom-ether', per_day=4), run('lds-bom-moroni', per_day=4)],
    },
]


def load_work(wid):
    for religion in corpus.RELIGIONS:
        m = corpus.read_json(os.path.join(corpus.WORKS, religion, wid, 'work.json'))
        if m:
            return m
    return None


def expand(plan, problems):
    """-> [{'title': str, 'readings': [{work,title,c}]}]"""
    if plan.get('days'):
        days = []
        for title, refs in plan['days']:
            readings = []
            for wid, c in refs:
                m = load_work(wid)
                if not m:
                    problems.append(f'{plan["id"]}: no work {wid}')
                    continue
                if not any(str(ch['n']) == str(c) for ch in m['chapters']):
                    problems.append(f'{plan["id"]}: {wid} has no chapter {c}')
                    continue
                readings.append({'work': wid, 'title': m['title'], 'c': str(c)})
            if readings:
                days.append({'title': title, 'readings': readings})
        return days

    # A run of chapters, sliced `per_day` at a time and carried across the
    # boundary between one book and the next so no day is a stub.
    chapters = []
    for r in plan['runs']:
        m = load_work(r['work'])
        if not m:
            problems.append(f'{plan["id"]}: no work {r["work"]}')
            continue
        nums = [str(c['n']) for c in m['chapters']]
        start = r['first'] - 1
        end = r['last'] if r['last'] else len(nums)
        for n in nums[start:end]:
            chapters.append(({'work': r['work'], 'title': m['title'], 'c': n},
                             r['per_day']))
    days, i = [], 0
    while i < len(chapters):
        per = chapters[i][1]
        block = [c for c, _p in chapters[i:i + per]]
        first, last = block[0], block[-1]
        title = (f'{first["title"]} {first["c"]}' if len(block) == 1
                 else f'{first["title"]} {first["c"]}–{last["title"]} {last["c"]}'
                 if first['title'] != last['title']
                 else f'{first["title"]} {first["c"]}–{last["c"]}')
        days.append({'title': title, 'readings': block})
        i += per
    return days


def main():
    problems, out = [], []
    for plan in PLANS:
        days = expand(plan, problems)
        if not days:
            problems.append(f'{plan["id"]}: no days')
            continue
        out.append({
            'id': plan['id'], 'name': plan['name'],
            'religion': plan['religion'], 'blurb': plan['blurb'],
            'days': days,
        })
        print(f'  {plan["id"]:14} {len(days):3d} days, '
              f'{sum(len(d["readings"]) for d in days):4d} readings')
    corpus.write_json(OUT, {'plans': out})
    if build_daily():
        problems.append('some daily verses could not be found')
    for p in problems:
        print(f'  ! {p}')
    print(f'plans: {len(out)} written to {os.path.relpath(OUT, corpus.ROOT)}'
          + (f'; {len(problems)} problems' if problems else ''))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
