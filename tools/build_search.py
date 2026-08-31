"""Build the full-text search index.

The texts themselves stay as JSON — that is what the reader serves. This is
only the index, in SQLite's FTS5, because scanning a million verses of JSON
on every search would not answer in a useful time. PHP reads it through
pdo_sqlite, which ships with PHP; nothing is installed to use it.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus                                          # noqa: E402

DB = os.path.join(corpus.CORPUS, 'search.sqlite')

SCHEMA = """
PRAGMA journal_mode = OFF;
PRAGMA synchronous = OFF;

DROP TABLE IF EXISTS passages;
CREATE VIRTUAL TABLE passages USING fts5(
    body,
    work_id UNINDEXED,
    chapter UNINDEXED,
    verse   UNINDEXED,
    tokenize = "unicode61 remove_diacritics 2"
);

DROP TABLE IF EXISTS works;
CREATE TABLE works (
    id        TEXT PRIMARY KEY,
    title     TEXT,
    subtitle  TEXT,
    religion  TEXT,
    section   TEXT,
    translator TEXT,
    structure TEXT
);
CREATE INDEX works_religion ON works(religion);
"""


def rows(meta):
    """Every searchable passage of one work."""
    wid = meta['id']
    cdir = os.path.join(corpus.WORKS, meta['religion'], wid, 'c')
    for ch in meta.get('chapters', []):
        data = corpus.read_json(os.path.join(cdir, f'{ch["n"]}.json'))
        if not data:
            continue
        for v in data.get('verses', []):
            if v.get('text'):
                yield v['text'], wid, ch['n'], v['n']
        for i, b in enumerate(data.get('blocks', []), 1):
            if b.get('k') in ('p', 'q', 'h') and b.get('t'):
                yield b['t'], wid, ch['n'], f'p{i}'


def main():
    if os.path.exists(DB):
        os.remove(DB)
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)

    works = corpus.all_work_meta()
    total = 0
    for meta in works:
        db.execute(
            'INSERT INTO works VALUES (?,?,?,?,?,?,?)',
            (meta['id'], meta['title'], meta.get('subtitle', ''),
             meta['religion'], meta['section'],
             meta.get('edition', {}).get('translator', ''),
             meta.get('structure', 'prose')))
        batch = list(rows(meta))
        db.executemany(
            'INSERT INTO passages (body, work_id, chapter, verse) '
            'VALUES (?,?,?,?)', batch)
        total += len(batch)
        db.commit()

    db.execute("INSERT INTO passages(passages) VALUES('optimize')")
    db.commit()
    db.execute('VACUUM')
    db.close()
    size = os.path.getsize(DB) / 1e6
    print(f'search: {total:,} passages from {len(works)} works, '
          f'{size:.1f} MB')


if __name__ == '__main__':
    main()
