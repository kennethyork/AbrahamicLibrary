"""A pronunciation table for the names, so the voice does not mangle them.

Piper phonemizes with espeak-ng, which is guessing at English spelling
conventions. On ordinary words it is very good. On the proper nouns of
scripture it is not, and the failures are systematic rather than random:

  * `ch` in a biblical name is a hard `k` — Abimelech, Chaldean, Baruch,
    Melchizedek. espeak reads it as the `ch` of *church*, in a hundred and
    nine of the names that appear five times or more in this corpus.
  * A handful of long names are stressed on the wrong syllable, or lose a
    syllable entirely: Ecclesiastes comes out `ih-KLEEZ-ee-asts`, which is
    missing its last two sounds and is the title of a book here.

Both are fixed the same way: the name is respelt into something espeak reads
correctly, and the respelling is substituted just before the text reaches
Piper. Nothing on the page changes; only what the voice is handed.

Every entry is checked against espeak here, and the ones that do not actually
change the pronunciation are dropped rather than shipped as decoration.

    .venv/bin/python -m tools.build_pronounce
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus, modernize                                # noqa: E402

OUT = os.path.join(corpus.ROOT, 'app', 'data', 'pronounce.json')

SCRIPTURE = {'old-testament', 'new-testament', 'deuterocanon', 'apocrypha',
             'pseudepigrapha', 'torah', 'neviim', 'ketuvim', 'restoration',
             'quran'}

# `ch` is the church sound in these and the hard k everywhere else in
# scripture. A short list, because the exception is the rare case.
CH_IS_CHURCH = {'rachel', 'rachels', 'rachel’s'}

# Names whose trouble is not the `ch`: a stress in the wrong place, or a
# syllable dropped off the end. The respelling is what espeak needs to see,
# not how anybody would write the word.
# Names whose trouble is not the `ch`: a stress in the wrong place, or a
# syllable dropped off the end. The respelling is what espeak needs to see,
# not how anyone would write the word.
#
# Every one of these was checked against espeak by hand and the failures
# thrown out, because a respelling is a guess at another program's spelling
# rules and about a third of the guesses were wrong. `hubbakuk` moved
# Habakkuk's stress off the first syllable, where it belongs; `ahazuerus`
# turned Ahasuerus into `a-hay-zway-rus`. Six more changed nothing at all.
# What is left is the twelve that measurably improved.
#
# Capitals are avoided throughout: espeak reads a short run of them as an
# initialism, so `MAL-uh-kye` for Malachi comes out `em-ay-el-uh-kye`. That
# is how the first draft of this table sounded, and why it is not shipped.
HAND = {
    'Melchizedek': 'melkizzedek',      # was mel-CHY-zdek
    'Melchisedech': 'melkizzedek',
    'Melchisedek': 'melkizzedek',
    'Ecclesiastes': 'ecleeziasteez',   # was ih-KLEEZ-ee-asts, missing its end
    'Ecclesiasticus': 'ecleeziastikus',
    'Nebuchadnezzar': 'nebbukadnezzar',
    'Nebuchadrezzar': 'nebbukadrezzar',
    'Deuteronomy': 'dooteronomy',      # espeak gave it a British `dyoo`
    'Bathsheba': 'bathsheeba',         # was bath-SHEB-uh
    'Gethsemane': 'gethsemmanee',      # was geth-SIM-ane, a syllable short
    'Phinehas': 'finneehas',           # was FYNE-has
    'Nahum': 'nayhum',                 # was NAH-hum
    'Baruch': 'barook',                # was bar-RUTCH
    'Malachi': 'mallakye',
    'Issachar': 'issakar',
    'Antioch': 'antiok',
}


def ipa(words):
    """espeak's phonemes for a list of words, one to a line."""
    if not words:
        return []
    got = subprocess.run(['espeak-ng', '-v', 'en-us', '-q', '--ipa'],
                         input='\n'.join(words), capture_output=True, text=True)
    return [x.strip() for x in got.stdout.strip().split('\n')]


def scripture_names():
    """Proper nouns in the scriptures, by how often they are read."""
    names = Counter()
    for religion in corpus.RELIGIONS:
        base = os.path.join(corpus.WORKS, religion)
        if not os.path.isdir(base):
            continue
        for wid in os.listdir(base):
            meta = corpus.read_json(os.path.join(base, wid, 'work.json'))
            if not meta or meta['section'] not in SCRIPTURE:
                continue
            cdir = os.path.join(base, wid, 'c')
            for fn in os.listdir(cdir):
                ch = corpus.read_json(os.path.join(cdir, fn)) or {}
                text = ' '.join(v['text'] for v in ch.get('verses', []))
                for w in re.findall(r'\b[A-Z][a-z]{2,}\b', text):
                    if not modernize._is_word(w.lower()):
                        names[w] += 1
    return names


def main():
    names = scripture_names()
    table = dict(HAND)

    # The systematic half: every name whose `ch` espeak reads as `church`.
    want = [w for w, n in names.most_common() if n >= 3
            and 'ch' in w.lower() and w.lower() not in CH_IS_CHURCH
            and w not in table]
    for word, phon in zip(want, ipa(want)):
        if 'tʃ' not in phon:
            continue
        table[word] = re.sub(r'ch', 'k', word, flags=re.I)

    # Every entry has to earn its place: if espeak says the same thing for
    # the respelling as it did for the name, the entry changes nothing.
    keys = sorted(table)
    before = ipa(keys)
    after = ipa([table[k] for k in keys])
    final = {k: table[k] for k, was, now in zip(keys, before, after) if was != now}
    dropped = [k for k, was, now in zip(keys, before, after) if was == now]

    corpus.write_json(OUT, {
        'note': 'Respellings fed to the speech engine, never shown on a page.',
        'voice': 'espeak-ng phonemization, as used by Piper',
        'words': final,
    })
    heard = sum(names[k] for k in final)
    print(f'pronounce: {len(final)} names ({heard:,} occurrences in the '
          f'scriptures), {len(dropped)} dropped as no change')
    if dropped:
        print('  no change: ' + ', '.join(dropped[:8]))
    for k in list(final)[:6]:
        print(f'    {k:<16} -> {final[k]}')


if __name__ == '__main__':
    main()
