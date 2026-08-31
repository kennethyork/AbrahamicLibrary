"""Build the catalog the web app browses.

One file, `corpus/catalog.json`, holding every work's metadata arranged by
religion and section — small enough for the app to read on every request, so
the app needs no database to show a library page.
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus                                          # noqa: E402
from tools.corpus import RELIGIONS, SECTION_INDEX                 # noqa: E402


def main():
    works = corpus.all_work_meta()
    by_religion = defaultdict(lambda: defaultdict(list))
    cross = defaultdict(lambda: defaultdict(list))

    for m in works:
        by_religion[m['religion']][m['section']].append(m)
        for other in m.get('also_in', []):
            if other['religion'] != m['religion']:
                cross[other['religion']][other['section']].append(
                    dict(m, sort=other['sort'], borrowed_from=m['religion']))

    catalog = {'name': 'The Abrahamic Archive', 'religions': [],
               'built_at': corpus.now()}
    totals = {'works': 0, 'chapters': 0, 'verses': 0, 'words': 0}

    for rid, meta in RELIGIONS.items():
        sections = []
        r_tot = {'works': 0, 'chapters': 0, 'verses': 0, 'words': 0}
        for sid, name, blurb in meta['sections']:
            items = list(by_religion[rid].get(sid, []))
            items += cross[rid].get(sid, [])
            items.sort(key=lambda m: (m.get('sort', 0), m['title']))
            if not items:
                continue
            entries = []
            for m in items:
                entries.append({
                    'id': m['id'], 'title': m['title'],
                    'subtitle': m.get('subtitle', ''),
                    'religion': m['religion'],
                    'canon': m.get('canon', 'secondary'),
                    'structure': m.get('structure', 'prose'),
                    'edition': m.get('edition', {}),
                    'rights': m.get('rights', {}),
                    'stats': m.get('stats', {}),
                    'borrowed_from': m.get('borrowed_from'),
                })
                if not m.get('borrowed_from'):
                    for k in ('chapters', 'verses', 'words'):
                        r_tot[k] += m['stats'].get(k, 0)
                    r_tot['works'] += 1
            sections.append({'id': sid, 'name': name, 'blurb': blurb,
                             'works': entries})
        catalog['religions'].append({
            'id': rid, 'name': meta['name'], 'blurb': meta['blurb'],
            'sections': sections, 'totals': r_tot,
        })
        for k in totals:
            totals[k] += r_tot[k]

    catalog['totals'] = totals
    corpus.write_json(os.path.join(corpus.CORPUS, 'catalog.json'), catalog)

    print(f'catalog: {totals["works"]} works, {totals["chapters"]} chapters, '
          f'{totals["verses"]} verses, {totals["words"]:,} words')
    for r in catalog['religions']:
        print(f'  {r["name"]:14s} {r["totals"]["works"]:5d} works  '
              f'{len(r["sections"])} sections')


if __name__ == '__main__':
    main()
