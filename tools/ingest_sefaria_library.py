"""Ingest everything the Sefaria walk found under a free licence.

`tools.discover_sefaria` writes the manifest; this reads it, fetches each
text, and files it by the Sefaria category it sits under. Works already
brought in by `tools.ingest_jewish` — the Tanakh above all — are skipped, so
the two ingesters can both be run without one overwriting the other.

Everything taken here is a translation of the 19th or early 20th century, so
everything takes the full modernization tier.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize, sefaria                       # noqa: E402
from tools.corpus import Chapter, Work, rights                     # noqa: E402
from tools.ingest_jewish import LIBRARY, TANAKH, flatten, plain    # noqa: E402

MANIFEST = os.path.join(corpus.CORPUS, 'manifests', 'sefaria.json')

# Sefaria's top category -> the archive's section
SECTIONS = {
    'Tanakh':         'jewish-study',      # the commentaries on it
    'Mishnah':        'mishnah',
    'Tosefta':        'mishnah',
    'Talmud':         'talmud',
    'Midrash':        'midrash',
    'Halakhah':       'halakhah',
    'Responsa':       'halakhah',
    'Kabbalah':       'kabbalah',
    'Chasidut':       'kabbalah',
    'Jewish Thought': 'jewish-philosophy',
    'Musar':          'jewish-philosophy',
    'Liturgy':        'liturgy',
    'Second Temple':  'jewish-history',
    'Reference':      'jewish-study',
}

# Already ingested by tools.ingest_jewish, in better-chosen editions.
ALREADY = ({t for t, _, _ in TANAKH}
           | {t for t, _, _, _, _ in LIBRARY})

MAX_CHAPTERS = 2000     # a guard against a pathological nesting


def main():
    manifest = corpus.read_json(MANIFEST)
    if not manifest:
        sys.exit(f'no manifest at {MANIFEST} — run tools.discover_sefaria first')

    report = modernize.Report()
    made, skipped, failed = [], 0, 0

    for i, entry in enumerate(manifest):
        title = entry['title']
        if title in ALREADY:
            skipped += 1
            continue

        top = entry['path'][0] if entry.get('path') else ''
        section = SECTIONS.get(top)
        if not section:
            skipped += 1
            continue

        version = entry['versions'][0]['versionTitle']
        try:
            got = sefaria.text(title, version)
        except Exception:                                     # noqa: BLE001
            failed += 1
            continue
        if not got or not got.get('text'):
            failed += 1
            continue
        if str(got.get('license', '')).strip().lower() not in sefaria.FREE:
            skipped += 1
            continue

        chunks = flatten(got['text'])[:MAX_CHAPTERS]
        w = Work(id='sef-' + corpus.slugify(title), title=title,
                 subtitle=' › '.join(entry.get('path', [])[1:3]),
                 religion='judaism', section=section, sort=i,
                 structure='verse', canon='secondary',
                 translation=version, modernization='full',
                 rights=rights(f'Public domain. Supplied by Sefaria as '
                               f'“{version}”.',
                               entry['versions'][0].get('versionSource')
                               or 'https://www.sefaria.org/'),
                 provenance={'source': 'Sefaria', 'sefaria_title': title,
                             'version': version,
                             'category': ' › '.join(entry.get('path', []))})

        for ci, chunk in enumerate(chunks, 1):
            ch = Chapter(ci, f'Chapter {ci}')
            for vi, raw in enumerate(chunk, 1):
                text = plain(raw)
                if not text:
                    continue
                said, src = modernize.pair(text, 'full', report)
                ch.verses.append({
                    'n': str(vi), 'text': said, 'notes': [],
                    **({'src': src} if src else {}),
                })
            if ch.verses:
                w.add(ch)

        if not w.chapters:
            failed += 1
            continue
        made.append(w.save())

        if len(made) % 50 == 0:
            print(f'  {len(made)} ingested, {skipped} skipped, {failed} empty',
                  flush=True)

    corpus.write_json(os.path.join(corpus.CORPUS, 'reports', 'sefaria.json'),
                      report.as_dict())
    d = report.as_dict()
    print(f'sefaria library: {len(made)} works, '
          f'{sum(m["stats"]["chapters"] for m in made)} chapters, '
          f'{sum(m["stats"]["words"] for m in made):,} words '
          f'({skipped} skipped, {failed} with no usable text); '
          f'modernizer changed {d["changed_occurrences"]:,} occurrences, '
          f'{d["unresolved_forms"]} forms unresolved')


if __name__ == '__main__':
    main()
