"""Ingest the Church Fathers from the Christian Classics Ethereal Library.

Thirty-eight volumes: the ten of the Ante-Nicene Fathers and the two
fourteen-volume series of the Nicene and Post-Nicene Fathers. All are the
Edinburgh translations of 1867–1900, so all take the full modernization tier.

CCEL rules each of its sections off with a line of underscores, and sets the
footnotes between the sections in the same way. A section whose first line is
a footnote marker, or that is too short to be a chapter, is not made one; its
text is still reachable through search.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize, parallel, prose               # noqa: E402
from tools.corpus import Chapter, Work, rights                     # noqa: E402

SRC = os.path.join(corpus.ROOT, 'sources', 'collector', 'ccel')

CCEL_RIGHTS = rights(
    'Public domain. The Edinburgh translations of the Fathers, published '
    '1867–1900, supplied by the Christian Classics Ethereal Library.',
    'https://www.ccel.org/')

SERIES = {
    'anf':    ('The Ante-Nicene Fathers', 0),
    'npnf1':  ('Nicene and Post-Nicene Fathers, First Series', 100),
    'npnf2':  ('Nicene and Post-Nicene Fathers, Second Series', 200),
}

RE_TITLE = re.compile(r'^\s*Title:\s*(.+)$', re.M)
RE_HEADER_END = re.compile(r'^\s*_{15,}\s*$', re.M)


def volume_meta(vid, text):
    """-> (series key, number, title)"""
    m = RE_TITLE.search(text[:4000])
    title = m.group(1).strip() if m else vid.upper()
    # 'ANF01. The Apostolic Fathers with Justin Martyr and Irenaeus'
    # 'ANF01. ...', 'NPNF2-06. ...', 'NPNF-211. ...'
    title = re.sub(r'^(?:ANF|NPNF)[-\d]*\.?\s*', '', title).strip()

    if vid.startswith('anf'):
        return 'anf', int(vid[3:]), title
    if vid.startswith('npnf1'):
        return 'npnf1', int(vid[5:]), title
    if vid.startswith('npnf2'):
        return 'npnf2', int(vid[5:]), title
    return 'anf', 99, title


def one_volume(fn):
    """Parse, modernize and save one Fathers volume, in its own process."""
    vid = fn[:-4]
    path = os.path.join(SRC, fn)
    with open(path, encoding='utf-8', errors='replace') as fh:
        text = fh.read()

    series, number, title = volume_meta(vid, text)
    series_name, base_sort = SERIES[series]

    # drop the CCEL catalogue header that opens every file
    parts = RE_HEADER_END.split(text, maxsplit=2)
    body = parts[2] if len(parts) > 2 else text

    report = modernize.Report()
    w = Work(id=f'ccel-{vid}', title=title,
             subtitle=f'{series_name}, volume {number}',
             religion='christianity', section='fathers',
             sort=base_sort + number, structure='prose',
             canon='secondary',
             translation=series_name,
             translator='Roberts, Donaldson, Schaff and others',
             year=1885, modernization='full', rights=CCEL_RIGHTS,
             provenance={'source': 'Christian Classics Ethereal Library',
                         'source_file': os.path.relpath(path, corpus.ROOT),
                         'note': 'Sections are those CCEL rules off in the '
                                 'source; footnote blocks are not made '
                                 'chapters.'})

    n = 0
    for chunk in prose.ccel_sections(body):
        got = prose.chunk_to_chapter(chunk)
        if not got:
            continue
        heading, paras = got
        n += 1
        # The heading gets the same tier as the text under it. Modernizing
        # the body and leaving `Of the Vanity of Him that Hath Riches`
        # over the top of it is the one place archaic English survived
        # a full-tier book.
        ch = Chapter(n, modernize.modernize(heading, 'full'))
        for p in paras:
            text, src = modernize.pair(p, 'full', report)
            block = {'k': 'p', 't': text}
            if src:
                block['s'] = src          # the paragraph as it was printed
            ch.blocks.append(block)
        w.add(ch)

    if not w.chapters:
        return None
    return w.save(), report.as_dict(), title


def main():
    files = sorted(f for f in os.listdir(SRC) if f.endswith('.txt'))
    if not files:
        sys.exit(f'no CCEL volumes in {SRC}')

    results = parallel.run(one_volume, files,
                           on_result=parallel.progress('ccel'))
    made = [r[0] for r in results]
    merged = parallel.merge_counters([r[1] for r in results])

    for meta, _rep, title in sorted(results, key=lambda r: r[0]['sort']):
        print(f'  {meta["id"]}: {meta["stats"]["chapters"]:4d} chapters, '
              f'{meta["stats"]["words"]:>9,} words  {title[:52]}')

    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'ccel.json'),
                      merged)
    print(f'ccel: {len(made)} volumes, '
          f'{sum(m["stats"]["chapters"] for m in made)} chapters, '
          f'{sum(m["stats"]["words"] for m in made):,} words; '
          f'modernizer changed {merged["changed_occurrences"]:,} occurrences, '
          f'{merged["unresolved_forms"]} forms unresolved')


if __name__ == '__main__':
    main()
