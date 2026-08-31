"""Walk Sefaria's table of contents and find everything free to reprint.

Writes a manifest of every English text Sefaria holds under a Public Domain
or CC0 licence, with the category path it sits under, so the ingester can
file it in the archive. Cached per title, so it can be stopped and restarted.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, sefaria                                  # noqa: E402

MANIFEST = os.path.join(corpus.CORPUS, 'manifests', 'sefaria.json')

# Sefaria's top-level categories worth walking. 'Reference' is grammars and
# dictionaries; 'Second Temple' is Josephus, Philo and the apocrypha, which
# Christianity already carries from better sources.
CATEGORIES = {
    'Tanakh', 'Mishnah', 'Talmud', 'Midrash', 'Halakhah', 'Kabbalah',
    'Jewish Thought', 'Liturgy', 'Tosefta', 'Chasidut', 'Musar',
    'Responsa', 'Second Temple', 'Reference',
}


def leaves(node, path=()):
    """Every text title in the tree, with the categories above it."""
    if isinstance(node, list):
        for item in node:
            yield from leaves(item, path)
        return
    if not isinstance(node, dict):
        return
    if 'contents' in node:
        name = node.get('category') or node.get('title') or ''
        yield from leaves(node['contents'], path + (name,) if name else path)
        return
    title = node.get('title')
    if title:
        yield title, path


def main():
    toc = sefaria.toc()
    if not toc:
        sys.exit('could not fetch Sefaria table of contents')

    found = list(leaves(toc))
    wanted = [(t, p) for t, p in found if p and p[0] in CATEGORIES]
    print(f'{len(found)} titles in the table of contents, '
          f'{len(wanted)} in the categories worth walking')

    manifest, checked = [], 0
    for title, path in wanted:
        checked += 1
        try:
            vers = sefaria.pd_versions(title)
        except Exception as e:                                # noqa: BLE001
            print(f'  ! {title}: {e}')
            continue
        if vers:
            manifest.append({'title': title, 'path': list(path),
                             'versions': vers})
        if checked % 100 == 0:
            print(f'  {checked}/{len(wanted)} checked, {len(manifest)} free',
                  flush=True)
            corpus.write_json(MANIFEST, manifest)

    corpus.write_json(MANIFEST, manifest)
    print(f'done: {len(manifest)} titles with a public-domain English text')
    cats = {}
    for m in manifest:
        cats[m['path'][0]] = cats.get(m['path'][0], 0) + 1
    for c, n in sorted(cats.items(), key=lambda kv: -kv[1]):
        print(f'  {n:5d}  {c}')


if __name__ == '__main__':
    main()
