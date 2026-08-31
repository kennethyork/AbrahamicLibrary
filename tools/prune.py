"""Remove works that should not be in the corpus.

Two kinds:

  fiction       The Arabian Nights, fairy tales, adventure novels and the
                Edwardian fashion for parodying the Rubaiyat. Judged on
                Library of Congress subject headings, which say plainly when
                a book is a story.
  not English   Gutenberg's search returns every language and its language
                field is often missing, so books in Spanish, French, German
                and Latin get collected. The text itself is asked, not the
                label.
  too thin      A work whose text did not survive parsing — a few words, or
                none. Better absent than present and empty.

    .venv/bin/python -m tools.prune            report only, changes nothing
    .venv/bin/python -m tools.prune --apply    delete what it lists
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, english, nonfiction                      # noqa: E402

MIN_WORDS = 120


def body_of(meta, limit=60000):
    """Enough of a work's text to judge it by."""
    cdir = os.path.join(corpus.WORKS, meta['religion'], meta['id'], 'c')
    out = []
    size = 0
    for ch in meta.get('chapters', [])[:12]:
        data = corpus.read_json(os.path.join(cdir, f'{ch["n"]}.json'))
        if not data:
            continue
        for v in data.get('verses', []):
            out.append(v.get('text', ''))
        for b in data.get('blocks', []):
            out.append(b.get('t', ''))
        size = sum(len(s) for s in out)
        if size > limit:
            break
    return ' '.join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    apply = '--apply' in argv
    works = corpus.all_work_meta()
    doomed = []

    for meta in works:
        # The scriptures are never pruned: they are the point of the archive,
        # and a short book of the Bible is short on purpose.
        if meta.get('canon') in ('canonical', 'deuterocanonical'):
            continue
        # Fiction, drama and parody: a library of sources, not of stories.
        keep, why = nonfiction.verdict(
            meta.get('title', ''),
            meta.get('provenance', {}).get('subjects', []) or [])
        if not keep:
            doomed.append((meta, f'fiction — {why}'))
            continue
        words = meta.get('stats', {}).get('words', 0)
        if words < MIN_WORDS:
            doomed.append((meta, f'only {words} words'))
            continue
        text = body_of(meta)
        if not english.is_english(text):
            known, marks = english.score(text)
            doomed.append((meta, f'not English (known {known:.2f}, '
                                 f'markers {marks:.2f})'))

    for meta, why in doomed:
        print(f'  {meta["religion"]:13} {meta["id"]:16} {why:38} '
              f'{meta["title"][:44]}')

    print(f'\n{len(doomed)} of {len(works)} works would be removed')

    if not apply:
        print('nothing changed — rerun with --apply to remove them')
        return 0

    for meta, _ in doomed:
        d = os.path.join(corpus.WORKS, meta['religion'], meta['id'])
        if os.path.isdir(d):
            shutil.rmtree(d)
    print(f'removed {len(doomed)} works; rebuild the catalog and index next')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
