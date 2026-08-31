"""Check the corpus, and say plainly what is wrong with it.

Run after a build. Nothing here fixes anything; it reports, and exits
non-zero if a work is broken rather than merely imperfect.

  broken     a work the reader cannot open: a missing chapter file, an empty
             chapter, a work with no text at all.
  imperfect  a work that reads, but whose preparation is incomplete: archaic
             forms still standing in a text marked as fully modernized, or a
             missing rights statement.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize                                # noqa: E402

REPORT = os.path.join(corpus.CORPUS, 'reports', 'qa.json')


def check(meta):
    """-> (broken[], warnings[], archaic Counter)"""
    broken, warn = [], []
    wid = meta['id']
    cdir = os.path.join(corpus.WORKS, meta['religion'], wid, 'c')
    archaic = Counter()

    if not meta.get('chapters'):
        broken.append('no chapters')
        return broken, warn, archaic

    if not (meta.get('rights') or {}).get('statement'):
        warn.append('no rights statement')

    empty = 0
    for ch in meta['chapters']:
        path = os.path.join(cdir, f'{ch["n"]}.json')
        data = corpus.read_json(path)
        if data is None:
            broken.append(f'chapter {ch["n"]} missing on disk')
            continue
        text = ' '.join(
            [v.get('text', '') for v in data.get('verses', [])]
            + [b.get('t', '') for b in data.get('blocks', [])])
        if not text.strip():
            empty += 1
        if meta.get('edition', {}).get('modernization') == 'full':
            archaic.update(modernize.audit(text))

    if empty:
        (broken if empty == len(meta['chapters']) else warn).append(
            f'{empty} of {len(meta["chapters"])} chapters have no text')

    if meta['stats'].get('words', 0) < 20:
        broken.append('almost no text')

    return broken, warn, archaic


def main():
    works = corpus.all_work_meta()
    if not works:
        sys.exit('no works in the corpus — run the ingesters first')

    broken_works, warned_works = {}, {}
    archaic_all = Counter()
    per_religion = Counter()

    for meta in works:
        per_religion[meta['religion']] += 1
        broken, warn, archaic = check(meta)
        archaic_all.update(archaic)
        if broken:
            broken_works[meta['id']] = broken
        if warn:
            warned_works[meta['id']] = warn

    report = {
        'checked_at': corpus.now(),
        'works': len(works),
        'by_religion': dict(per_religion),
        'broken': broken_works,
        'warnings': warned_works,
        'archaic_forms_remaining': dict(archaic_all.most_common(300)),
        'archaic_total': sum(archaic_all.values()),
    }
    corpus.write_json(REPORT, report)

    print(f'qa: {len(works)} works checked')
    for r, n in sorted(per_religion.items()):
        print(f'  {r:14s} {n:5d}')
    print(f'  broken:   {len(broken_works)}')
    print(f'  warnings: {len(warned_works)}')
    print(f'  archaic forms still standing: {sum(archaic_all.values()):,} '
          f'in {len(archaic_all)} distinct forms')
    if archaic_all:
        top = ', '.join(f'{w} ({n})' for w, n in archaic_all.most_common(12))
        print(f'    most common: {top}')
    for wid, why in list(broken_works.items())[:15]:
        print(f'  ! {wid}: {"; ".join(why)}')

    print(f'\nwritten to {os.path.relpath(REPORT, corpus.ROOT)}')
    sys.exit(1 if broken_works else 0)


if __name__ == '__main__':
    main()
