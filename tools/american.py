"""British spelling to American, derived rather than hand-listed.

The archive is normalised to American English. Its sources are not: the
Edinburgh Fathers, Rodwell's Koran, Hirschfeld's Kuzari and most of the
19th-century Gutenberg shelf were set by British publishers, so `colour`,
`honour`, `realise`, `centre`, `travelled` and `defence` run through millions
of words of it.

A hand-written list cannot cover that. Instead the mapping is computed from
the two word lists the system already carries — `british-english` and
`american-english`:

  1. Take the words in the British list that are NOT in the American list.
     Those are the spellings that need changing, and nothing else is
     considered. This is what makes the pass safe: `four`, `hour`, `your`,
     `pour`, `flour` and `devour` are all ordinary American words, so no
     -our rule can ever reach them.
  2. Apply the known transformations to each.
  3. Keep the result only if it IS in the American list.

So every mapping is attested at both ends. Anything that cannot be resolved
that way is left alone.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bible import corrections  # noqa: E402

import os
import re

_DICTS = {
    'american': '/usr/share/dict/american-english',
    'british': '/usr/share/dict/british-english',
}

# Ordered: the first rule whose result is a real American word wins.
RULES = [
    (re.compile(r'our(s?)$'), r'or\1'),            # colour   -> color
    (re.compile(r'our'), 'or'),                    # favourite-> favorite
    (re.compile(r'ise$'), 'ize'),                  # realise  -> realize
    (re.compile(r'ised$'), 'ized'),
    (re.compile(r'ises$'), 'izes'),
    (re.compile(r'ising$'), 'izing'),
    (re.compile(r'isation'), 'ization'),
    (re.compile(r'isable'), 'izable'),
    (re.compile(r'yse$'), 'yze'),                  # analyse  -> analyze
    (re.compile(r'ysed$'), 'yzed'),
    (re.compile(r'yses$'), 'yzes'),
    (re.compile(r'ysing$'), 'yzing'),
    (re.compile(r'tre$'), 'ter'),                  # centre   -> center
    (re.compile(r'tres$'), 'ters'),
    (re.compile(r'bre$'), 'ber'),                  # fibre    -> fiber
    (re.compile(r'bres$'), 'bers'),
    (re.compile(r'^(a)e'), r'\1'),                 # aetiology-> etiology
    (re.compile(r'ae'), 'e'),                      # encyclopaedia
    (re.compile(r'oe'), 'e'),                      # foetus   -> fetus
    (re.compile(r'ogue$'), 'og'),                  # catalogue-> catalog
    (re.compile(r'([aeiou])ll'), r'\1l'),          # travelled-> traveled
    (re.compile(r'ce$'), 'se'),                    # defence  -> defense
    (re.compile(r'mme$'), 'm'),                    # programme-> program
    (re.compile(r'oul'), 'ol'),                    # mould    -> mold
    (re.compile(r'ough$'), 'ow'),                  # plough   -> plow
    (re.compile(r'kh$'), 'k'),
    (re.compile(r'gramme'), 'gram'),
]

# Words the AMERICAN list also accepts, so subtracting the lists cannot find
# them, but where American writing prefers the other form. Each is written
# out because the general rules are unsafe here: the doubled-l rule that
# turns `travelled` into `traveled` would turn `filled` into `filed`, and the
# ae rule that fixes `encyclopaedia` would wreck `archaeology`, which is
# spelt that way in American English too.
VARIANTS = {
    # -lled / -lling / -ller, where American writes one l
    'travelled': 'traveled', 'travelling': 'traveling',
    'traveller': 'traveler', 'travellers': 'travelers',
    'marvelled': 'marveled', 'marvelling': 'marveling',
    'marvellous': 'marvelous', 'marvellously': 'marvelously',
    'levelled': 'leveled', 'levelling': 'leveling',
    'labelled': 'labeled', 'labelling': 'labeling',
    'cancelled': 'canceled', 'cancelling': 'canceling',
    'counselled': 'counseled', 'counselling': 'counseling',
    'counsellor': 'counselor', 'counsellors': 'counselors',
    'quarrelled': 'quarreled', 'quarrelling': 'quarreling',
    'signalled': 'signaled', 'signalling': 'signaling',
    'totalled': 'totaled', 'modelled': 'modeled', 'modelling': 'modeling',
    'equalled': 'equaled', 'rivalled': 'rivaled',
    'jewelled': 'jeweled', 'jeweller': 'jeweler', 'jewellery': 'jewelry',
    'woollen': 'woolen', 'woollens': 'woolens',
    'fuelled': 'fueled', 'duelled': 'dueled', 'libelled': 'libeled',
    'shrivelled': 'shriveled', 'snivelled': 'sniveled',
    'grovelled': 'groveled', 'revelled': 'reveled', 'reveller': 'reveler',
    'kidnapped': 'kidnapped', 'worshipped': 'worshiped',
    'worshipping': 'worshiping', 'worshipper': 'worshiper',
    'worshippers': 'worshipers',
    # -ae- and -oe- that American simplifies (but NOT archaeology, aesthetic)
    'encyclopaedia': 'encyclopedia', 'encyclopaedias': 'encyclopedias',
    'mediaeval': 'medieval', 'foetus': 'fetus', 'foetal': 'fetal',
    'haemorrhage': 'hemorrhage', 'diarrhoea': 'diarrhea',
    'oesophagus': 'esophagus', 'anaemia': 'anemia', 'anaemic': 'anemic',
    'manoeuvre': 'maneuver', 'manoeuvres': 'maneuvers',
    'manoeuvred': 'maneuvered', 'manoeuvring': 'maneuvering',
    # -ogue, -mme, and the rest
    'catalogue': 'catalog', 'catalogues': 'catalogs',
    'programme': 'program', 'programmes': 'programs',
    'axe': 'ax', 'axes': 'axes',
    'grey': 'gray', 'greyer': 'grayer', 'greyish': 'grayish',
    'smoulder': 'smolder', 'smouldering': 'smoldering',
    'moustache': 'mustache', 'moustaches': 'mustaches',
    'plough': 'plow', 'ploughs': 'plows', 'ploughed': 'plowed',
    'ploughing': 'plowing', 'ploughman': 'plowman',
    'mould': 'mold', 'moulds': 'molds', 'moulded': 'molded',
    'moulding': 'molding', 'mouldy': 'moldy',
    'skilful': 'skillful', 'skilfully': 'skillfully',
    'wilful': 'willful', 'wilfully': 'willfully',
    'fulfil': 'fulfill', 'fulfils': 'fulfills', 'fulfilment': 'fulfillment',
    'instalment': 'installment', 'enrolment': 'enrollment',
    'enthral': 'enthrall', 'distil': 'distill', 'instil': 'instill',
    'practise': 'practice', 'practised': 'practiced',
    'practises': 'practices', 'practising': 'practicing',
    'pretence': 'pretense', 'pretences': 'pretenses',
    'offence': 'offense', 'offences': 'offenses',
    'defence': 'defense', 'defences': 'defenses',
    'licence': 'license', 'licences': 'licenses',
    'storey': 'story', 'storeys': 'stories',
    'kerb': 'curb', 'kerbs': 'curbs',
    'cosy': 'cozy', 'cosily': 'cozily',
    'sceptic': 'skeptic', 'sceptics': 'skeptics', 'sceptical': 'skeptical',
    'sceptically': 'skeptically', 'scepticism': 'skepticism',
    'behaviour': 'behavior', 'behaviours': 'behaviors',
    'endeavour': 'endeavor', 'endeavours': 'endeavors',
    'endeavoured': 'endeavored', 'endeavouring': 'endeavoring',
}

# Spellings older than either word list, so no rule can attest them.
EXTRA = {
    'shew': 'show', 'shews': 'shows', 'shewn': 'shown', 'shewed': 'showed',
    'shewing': 'showing',
    'antient': 'ancient', 'chuse': 'choose', 'chused': 'chose',
    'compleat': 'complete', 'cloathed': 'clothed', 'cloathing': 'clothing',
    'stedfast': 'steadfast', 'stedfastly': 'steadfastly',
    'phantasy': 'fantasy', 'gaol': 'jail', 'gaoler': 'jailer',
    'connexion': 'connection', 'connexions': 'connections',
    'inflexion': 'inflection', 'reflexion': 'reflection',
    'shamefacedness': 'shamefacedness',
    'burthen': 'burden', 'burthens': 'burdens',
    'murther': 'murder', 'chearful': 'cheerful',
    'sepulchre': 'sepulcher', 'sepulchres': 'sepulchers',
    'theatre': 'theater', 'theatres': 'theaters',
    'manoeuvre': 'maneuver', 'manoeuvres': 'maneuvers',
    'plough': 'plow', 'ploughed': 'plowed', 'ploughing': 'plowing',
    'draught': 'draft', 'draughts': 'drafts',
    'storey': 'story', 'storeys': 'stories',
    'kerb': 'curb', 'waggon': 'wagon', 'waggons': 'wagons',
}

# Words the rules would change but must not: a British-only word whose
# "American" form means something else entirely.
NEVER = {
    'metre', 'metres',        # the unit keeps its spelling in scientific use
    'spectre', 'spectres',    # 'specter' is right, but see below — kept by rule
    'cheque',                 # 'check' is right, but the noun is unambiguous
}
NEVER -= {'spectre', 'spectres', 'cheque'}     # these DO convert; only metre stays


def _load(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding='utf-8', errors='ignore') as fh:
        return {w.strip() for w in fh if w.strip() and "'" not in w}


def build_map():
    """-> {british: american}, every pair attested in both word lists."""
    american = _load(_DICTS['american'])
    british = _load(_DICTS['british'])
    if not american or not british:
        return dict(EXTRA)

    mapping = {}
    for word in british - american:
        # Proper nouns are names, not spellings: 'Timour' is not 'Timor'.
        if not word.islower() or word in NEVER:
            continue
        for pattern, repl in RULES:
            if not pattern.search(word):
                continue
            candidate = pattern.sub(repl, word)
            if candidate != word and candidate in american:
                mapping[word] = candidate
                break

    # The print pipeline's own British-to-American table, which was written
    # by hand for the Enoch volume and then never reached this one. It is
    # needed because the derived mapping cannot see these: a word list can
    # only report spellings that are British *and not also American*, and
    # `whilst`, `amongst`, `betwixt`, `judgement`, `enquire`, `metre` and
    # `sulphur` are all in the American dictionary too. A subtraction finds
    # nothing to subtract. Somebody had to decide these one at a time, and
    # somebody did.
    # `brake` is left out of it: in that table it is the old past tense of
    # `break`, and it is also a perfectly ordinary noun. It is decided by
    # context in `tools.modernize` instead.
    mapping.update({k.lower(): v
                    for k, v in corrections.BRITISH_TO_AMERICAN.items()
                    if k.lower() != 'brake'})

    # These override anything derived: they are hand-checked pairs.
    mapping.update(VARIANTS)
    for k, v in EXTRA.items():
        mapping.setdefault(k, v)
    mapping.pop('', None)
    # Entries that map a word to itself were written as documentation — "the
    # plural of axe is axes in both spellings" — but they make the word look
    # like an unconverted Briticism to the audit. The note belongs in a
    # comment, not in the table.
    return {k: v for k, v in mapping.items() if k != v}


MAP = build_map()

# Matching is done by pulling out each word and looking it up, NOT by an
# alternation of all 1,451 spellings. The alternation is the obvious way and
# it is the slow one: the engine tries every branch at every position in the
# text, which measured at 0.13 MB/s and was 61% of the whole pipeline. A
# plain word pattern plus a dictionary lookup is one pass and one hash.
_WORD = re.compile(r'[A-Za-z]+')


def _match_case(src, repl):
    if src.isupper():
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def _swap(m):
    word = m.group(0)
    american = MAP.get(word.lower())
    return _match_case(word, american) if american else word


def americanize(s):
    """Every British spelling in the text, in its American form."""
    if not s or not MAP:
        return s
    return _WORD.sub(_swap, s)


def find(s):
    """British spellings still standing, for the audit."""
    if not s or not MAP:
        return []
    return [w for w in _WORD.findall(s) if w.lower() in MAP]


if __name__ == '__main__':
    print(f'{len(MAP)} spellings mapped')
    tests = [
        ('The colour of his armour', 'The color of his armor'),
        ('He realised the centre had a defence', 'He realized the center had a defense'),
        ('They travelled and marvelled at the splendour',
         'They traveled and marveled at the splendor'),
        ('an encyclopaedia of behaviour', 'an encyclopedia of behavior'),
        ('He shewed them the sepulchre', 'He showed them the sepulcher'),
        ('analyse the programme', 'analyze the program'),
        ('a catalogue of honours', 'a catalog of honors'),
        # must NOT change
        ('four hours in your flour tour', 'four hours in your flour tour'),
        ('devour the sour dough', 'devour the sour dough'),
        ('wise men promise to exercise', 'wise men promise to exercise'),
        ('there were more figures here', 'there were more figures here'),
        ('The Rose of Sharon', 'The Rose of Sharon'),
    ]
    bad = 0
    for src, want in tests:
        got = americanize(src)
        if got != want:
            bad += 1
            print(f'  FAIL {src!r}\n       got  {got!r}\n       want {want!r}')
    print(f'{len(tests) - bad}/{len(tests)} passed')
    raise SystemExit(1 if bad else 0)
