"""Build the whole archive, from sources to a browsable site.

    .venv/bin/python -m tools.build_all            everything
    .venv/bin/python -m tools.build_all quran qa   only these stages

Every stage is safe to rerun. Fetching stages cache what they download, so a
second run costs nothing but the parsing.
"""
import importlib
import sys
import time

STAGES = [
    ('bible',     'tools.ingest_bible',     'World English Bible and the apocrypha'),
    ('quran',     'tools.ingest_quran',     'Qur’an in the public-domain translations'),
    ('jewish',    'tools.ingest_jewish',    'Tanakh and the curated Jewish works'),
    ('sefaria',   'tools.ingest_sefaria_library', 'the rest of the free Sefaria library'),
    ('gutenberg', 'tools.ingest_gutenberg', 'Douay-Rheims and the Gutenberg shelf'),
    ('ccel',      'tools.ingest_ccel',      'the Church Fathers'),
    ('mormon',    'tools.ingest_mormon',    'the Restoration scriptures'),
    ('archive',   'tools.ingest_archive',   'the Islamic texts from archive.org'),
    ('curated',   'tools.ingest_curated',   'the hand-picked texts no rule reaches'),
    ('prune',     'tools.prune',            'removing fiction, non-English and empty works'),
    ('catalog',   'tools.build_catalog',    'the browsable catalog'),
    ('plans',     'tools.build_plans',      'the reading plans and the daily verse'),
    ('links',     'tools.build_links',      'the citation index — who quotes what'),
    ('strongs',   'tools.ingest_strongs',   'Strong’s Hebrew and Greek dictionaries'),
    ('pronounce', 'tools.build_pronounce',  'the pronunciation table for the voice'),
    ('search',    'tools.build_search',     'the full-text index'),
    ('qa',        'tools.qa',               'checking what was built'),
]

ORDER = {name: i for i, (name, _, _) in enumerate(STAGES)}


def main(argv):
    want = [a for a in argv if not a.startswith('-')]
    stages = STAGES
    if want:
        unknown = [w for w in want if w not in ORDER]
        if unknown:
            sys.exit(f'unknown stage(s): {", ".join(unknown)}\n'
                     f'known: {", ".join(ORDER)}')
        stages = [s for s in STAGES if s[0] in want]

    failed = []
    for name, module, what in stages:
        print(f'\n=== {name}: {what}')
        started = time.time()
        try:
            mod = importlib.import_module(module)
            if name == 'prune':
                # In the pipeline the prune is meant to act, not just report.
                sys.argv = ['prune', '--apply']
            # qa exits non-zero when a work is broken; that is a report, not
            # a crash, so it is caught and carried to the end.
            try:
                mod.main()
            except SystemExit as e:
                if e.code:
                    failed.append(name)
        except Exception as e:                                # noqa: BLE001
            print(f'  ! {name} failed: {type(e).__name__}: {e}')
            failed.append(name)
        print(f'    ({time.time() - started:.1f}s)')

    if failed:
        print(f'\nstages needing attention: {", ".join(failed)}')
        return 1
    print('\nbuilt. Serve it with:  php -S 127.0.0.1:8080 -t app')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
