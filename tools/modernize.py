"""The shared modernization engine for the whole archive.

Every text in the archive passes through here, whatever religion it belongs
to. The rules themselves come from `bible/corrections.py`, which was written
and hand-checked for the Apocrypha Plus volume; this module wraps them so
they can be applied to sources that module never saw — a 1734 Qur'an, a 1917
Tanakh, a 19th-century Talmud — and adds a generative pass for the long tail
of archaic verb forms that a hand-written table cannot cover at this scale.

Three tiers:

  none   the text is left exactly as received.
  safe   spelling, formal vocabulary and archaic constructions only.
         Pronouns and verb endings are left alone. This is the tier for a
         translation that is already modern, such as the World English
         Bible, where there is nothing archaic to resolve.
  full   `safe`, plus Early Modern pronouns and verb inflection —
         thou/thee/thy/ye, hath/doth/saith, the -eth and -est classes.
         `art` is resolved by context rather than by tier, so this is safe
         even for a modern book that quotes the King James Bible: the
         quotation is modernized and the author's own "work of art" is not.

The generative pass exists because the hand table holds ~135 verbs, which was
enough for one volume of four translators. A corpus of several hundred books
meets thousands of distinct forms. Rather than stem blindly — the failure the
hand table was written to avoid, where `abideth` becomes "abids" — every
candidate stem is checked against the system dictionary, and a form that
cannot be resolved with confidence is LEFT ALONE and written to the
unresolved report for a human to rule on.
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bible import corrections  # noqa: E402
from tools import american    # noqa: E402

TIERS = ('none', 'safe', 'full')

# --- the dictionary -------------------------------------------------------
#
# American English, because the archive is normalised to American spelling.
_DICT_PATHS = ('/usr/share/dict/american-english', '/usr/share/dict/words')


def _load_dict():
    for p in _DICT_PATHS:
        if os.path.exists(p):
            with open(p, encoding='utf-8', errors='ignore') as fh:
                words = {w.strip().lower() for w in fh if w.strip()}
            # possessives and contractions in the list are noise here
            return {w for w in words if "'" not in w}
    return set()


WORDS = _load_dict()

# The hand table is authoritative: it ran first and was checked in context.
_HAND = {k.lower() for k in corrections.MODERNIZE}

# --- forms the generative pass must not touch -----------------------------
#
# Anything that is itself a dictionary word is skipped automatically, which
# covers the whole class the hand table had to exclude by name — greatest,
# forest, harvest, priest, tempest, twentieth, death, breath, beneath. These
# are the ones a dictionary cannot rule on.
NEVER = {
    # ordinals and names that are not in the word list
    'japheth', 'nazareth', 'ashtoreth', 'shibboleth', 'jehoshaphat',
    'anathoth', 'gennesareth', 'naioth', 'aroth', 'meroth',
    'hundredth', 'thousandth',
    # Hebrew and Arabic transliterations that end in -eth / -est by accident
    'sukkoth', 'shavuoth', 'sheloshet', 'bereshith', 'kohelet', 'chesed',
}

# --- generative collisions, ruled on by hand ------------------------------
#
# Each of these resolves to a real but WRONG word by the general rule, so the
# answer is given explicitly. They were found by running the pass over the
# whole corpus and reading every form it changed.
OVERRIDE = {
    # 'putt' is a dictionary word (the golf stroke), so the doubled-consonant
    # rule cannot fire and 'putteth' would come out as "putts".
    'putteth': 'puts', 'puttest': 'put',
    # -nge: 'singe', 'ringe', 'stinge' are or look like words, and the -ng
    # rule below catches most, but these read better stated outright.
    'singeth': 'sings', 'singest': 'sing',
    'ringeth': 'rings', 'ringest': 'ring',
    'wringeth': 'wrings', 'wringest': 'wring',
    'springeth': 'springs', 'springest': 'spring',
    'clingeth': 'clings', 'flingeth': 'flings', 'stingeth': 'stings',
    'swingeth': 'swings', 'hangeth': 'hangs', 'hangest': 'hang',
    # 'doe' is a dictionary word (the deer), which misroutes the -est form.
    'doest': 'do', 'doeth': 'does',
    # 'hat', 'com', 'cal', 'writ', 'se', 'bear' are all dictionary words;
    # these are the forms where that matters and the general rule is unsafe.
    'wilt': 'will', 'shouldest': 'should', 'wouldest': 'would',
    'couldest': 'could', 'durst': 'dared',
}


def _is_word(w):
    return w in WORDS


def _third_person(stem):
    """Present third-person singular of a bare verb stem."""
    if re.search(r'(s|x|z|ch|sh|o)$', stem):
        return stem + 'es'
    if re.search(r'[^aeiou]y$', stem):
        return stem[:-1] + 'ies'
    return stem + 's'


def _stem(base):
    """Resolve the bare verb behind an -eth/-est form, or None.

    `base` is the word with its ending already stripped: cometh -> 'com'.
    Every candidate is checked against the dictionary; nothing is guessed.
    """
    # -ng verbs first: 'singe' and 'ringe' exist, so base+'e' is a trap.
    # 'chang' is not a word, so 'change' is still reached by the fallthrough.
    if base.endswith('ng') and _is_word(base):
        return base
    # a doubled final consonant that is not itself a word: sitt -> sit,
    # runn -> run, beginn -> begin. 'call' and 'dwell' are words, so they
    # never reach this and keep their second l.
    if (not _is_word(base) and len(base) > 2
            and base[-1] == base[-2] and base[-1].isalpha()
            and base[-1] not in 'aeiou' and _is_word(base[:-1])):
        return base[:-1]
    # the silent e, which stripping removed: com -> come, giv -> give.
    # Preferred over the bare stem because 'com' and 'hat' are themselves
    # dictionary words and would give "coms" and "hats".
    if _is_word(base + 'e'):
        return base + 'e'
    if _is_word(base):
        return base
    # crieth -> cri -> cry
    if base.endswith('i') and _is_word(base[:-1] + 'y'):
        return base[:-1] + 'y'
    # A British stem the American dictionary cannot see: favoureth -> favor,
    # mouldeth -> mold, recogniseth -> recognize. The archive is normalised to
    # American spelling anyway, so the American form is the one wanted.
    for variant in _british_variants(base):
        if _is_word(variant):
            return variant
        if _is_word(variant + 'e'):
            return variant + 'e'
    # trafficketh -> traffic: the k English adds before a suffix
    if base.endswith('ck') and _is_word(base[:-1]):
        return base[:-1]
    # spellings that fell out of use entirely, so no dictionary holds them
    if base in ARCHAIC_STEMS:
        return ARCHAIC_STEMS[base]
    # A prefixed verb the word list does not carry on its own:
    # befooleth -> befool, forsweareth -> forswear, misleadeth -> mislead.
    # The prefix must be one that makes verbs, and what follows it must be a
    # verb in its own right, so this cannot invent a word.
    for pre in ('be', 'un', 're', 'mis', 'out', 'over', 'under', 'fore',
                'with', 'dis', 'en', 'for'):
        if base.startswith(pre) and len(base) > len(pre) + 2:
            rest = base[len(pre):]
            if _is_word(rest):
                return base
            if _is_word(rest + 'e'):
                return base + 'e'
    return None


# Archaic spellings with a modern equivalent, where the old form is not in
# any word list: 'sheweth' -> 'shows', 'spake' is left alone as a real past.
# Keys are the stem left after the ending is stripped, so 'sheweth' arrives
# here as 'shew' and 'chuseth' as 'chus'.
ARCHAIC_STEMS = {
    'shew': 'show', 'chus': 'choose', 'cloath': 'clothe',
    'prophecy': 'prophesy', 'sacrific': 'sacrifice',
    'stablish': 'establish', 'astonish': 'astonish', 'ravish': 'ravish',
}

_BRITISH = (('our', 'or'), ('ise', 'ize'), ('isa', 'iza'), ('yse', 'yze'),
            ('oul', 'ol'), ('aeo', 'eo'), ('oeu', 'eu'))

# the stem left when -eth is stripped from an -ise verb ends in -is, not -ise
_BRITISH_SUFFIX = (('is', 'iz'), ('ys', 'yz'))


def _british_variants(base):
    """American spellings of a British stem, most likely first."""
    seen = []
    for brit, amer in _BRITISH:
        if brit in base:
            v = base.replace(brit, amer)
            if v not in seen:
                seen.append(v)
    for brit, amer in _BRITISH_SUFFIX:
        if base.endswith(brit) and len(base) > len(brit) + 2:
            v = base[:-len(brit)] + amer
            if v not in seen:
                seen.append(v)
    # travelleth -> travel, counselleth -> counsel
    if len(base) > 3 and base.endswith('ll'):
        seen.append(base[:-1])
    return seen


_RE_ETH = re.compile(r'\b([A-Za-z]{2,})eth\b')
_RE_EST = re.compile(r'\b([A-Za-z]{2,})est\b')
_RE_DST = re.compile(r'\b([A-Za-z]{2,}d)st\b')


class Report:
    """What the generative pass did, so it can be audited."""

    def __init__(self):
        self.changed = Counter()
        self.unresolved = Counter()
        self.skipped_real_word = Counter()

    def merge(self, other):
        self.changed.update(other.changed)
        self.unresolved.update(other.unresolved)
        self.skipped_real_word.update(other.skipped_real_word)

    def as_dict(self):
        return {
            'changed_forms': len(self.changed),
            'changed_occurrences': sum(self.changed.values()),
            'unresolved_forms': len(self.unresolved),
            'unresolved_occurrences': sum(self.unresolved.values()),
            'changed': dict(self.changed.most_common()),
            'unresolved': dict(self.unresolved.most_common()),
            'skipped_as_real_words': dict(self.skipped_real_word.most_common(200)),
        }


def _apply(rx, s, resolve, report):
    def repl(m):
        whole = m.group(0)
        low = whole.lower()
        if low in _HAND or low in NEVER:
            return whole
        if low in OVERRIDE:
            out = OVERRIDE[low]
            report.changed[low] += 1
            return corrections._match_case(whole, out)
        # A form that is itself an ordinary English word is not an archaic
        # verb: forest, harvest, priest, tempest, greatest, twentieth.
        if _is_word(low):
            report.skipped_real_word[low] += 1
            return whole
        # A capitalised word inside a sentence is a name, not a verb.
        if whole[:1].isupper() and m.start() > 0 and s[m.start() - 1] not in '.!?"“\n':
            return whole
        out = resolve(m.group(1).lower())
        if out is None:
            report.unresolved[low] += 1
            return whole
        report.changed[low] += 1
        return corrections._match_case(whole, out)

    return rx.sub(repl, s)


def generative(s, report=None):
    """Modernize the -eth / -est / -dst forms the hand table does not list."""
    report = report if report is not None else Report()
    if not s:
        return s
    # cometh -> comes
    s = _apply(_RE_ETH, s, lambda b: (lambda st: _third_person(st) if st else None)(_stem(b)), report)
    # lovest -> love
    s = _apply(_RE_EST, s, _stem, report)
    # calledst -> called
    s = _apply(_RE_DST, s, lambda b: b if _is_word(b) else None, report)
    return s


# --- protecting the noun 'art' -------------------------------------------
#
# The hand table turns `art` into `are`, which is right for "thou art" and
# ruinous for "he used his art to force". The word is only the verb when
# `thou` stands before it, so the noun is put beyond the table's reach for
# the length of the pass and put back afterwards. This is what lets a book of
# history that quotes the King James Bible be modernized on the full tier:
# the quotation is fixed and the author's own prose about art survives.
_ART_KEEP = '\x1e'
_RE_ART = re.compile(r'\bart\b', re.IGNORECASE)

# `thou` immediately before the verb — "thou art", "thou not art" — allowing
# one adverb between.
_ART_BEFORE = re.compile(r'\bthou\W+(?:\w+\W+)?$', re.IGNORECASE)
# `thou` immediately after it, which is how a question inverts:
# "art thou the king", "whither art thou going", "art not thou".
# The lookahead settles "his art, thou art": when another `art` follows the
# `thou`, that later one is the verb and this one is the noun.
_ART_AFTER = re.compile(r'^\W+(?:not\W+)?thou\b(?!\W+art\b)', re.IGNORECASE)


def _protect_art(s):
    """Hide every `art` that is the noun, so the table cannot reach it."""
    if 'art' not in s.lower():
        return s, []
    kept = []

    def hide(m):
        before = s[max(0, m.start() - 20):m.start()]
        after = s[m.end():m.end() + 16]
        if _ART_BEFORE.search(before) or _ART_AFTER.match(after):
            return m.group(0)          # the verb: leave it for the table
        kept.append(m.group(0))
        return _ART_KEEP

    return _RE_ART.sub(hide, s), kept


# --- deciding the word `brake` -------------------------------------------
#
# `brake` is the old past tense of `break` — "and he brake the bread" — and
# it is also an ordinary noun: the brake on a wheel, a cane-brake, a thicket.
# In these sources the verb runs eight hundred and fifteen to thirty-one,
# which is a good reason to convert it and no reason at all to convert it
# blindly. A determiner in front of it makes it the noun.
_RE_BRAKE = re.compile(r'\bbrake\b', re.IGNORECASE)
_BRAKE_NOUN = re.compile(
    r'\b(?:the|a|an|his|her|its|their|our|your|my|this|that|these|those|'
    r'hand|air|foot|cane|sugar|steam|vacuum)\W+$', re.IGNORECASE)


def _fix_brake(s):
    if 'brake' not in s.lower():
        return s

    def go(m):
        before = s[max(0, m.start() - 16):m.start()]
        if _BRAKE_NOUN.search(before):
            return m.group(0)
        return corrections._match_case(m.group(0), 'broke')

    return _RE_BRAKE.sub(go, s)


def _restore_art(s, kept):
    if not kept:
        return s
    out = iter(kept)
    return re.sub(re.escape(_ART_KEEP), lambda _: next(out), s)


# --- the same rules, applied faster ---------------------------------------
#
# `corrections` matches its word tables with one big alternation each, which
# makes the engine try every branch at every position. The tables themselves
# are exactly right and are not touched; they are just applied by pulling out
# each word and looking it up, which is one pass and one hash. The multi-word
# rules — the phrases, and the SYNTAX rewrites in `resyntax` — still go
# through their own regexes, because a word lookup cannot see across a space.
_WORD_TOKEN = re.compile(r"[A-Za-z]+")


# Words that join two things said to be different. A replacement that lands
# on the far side of one of these, echoing what is already there, has turned
# a pair into a repetition.
_PAIRED = frozenset(('and', 'or', 'nor'))


def _table_pass(s, table):
    """Replace whole words from `table`, keeping their case.

    A one-for-one table cannot see its own output. `supplication` -> `prayer`
    is right on its own and wrong in "prayer and supplication", where it
    yields "prayer and prayer": the phrase named two things and the swap
    leaves it naming one thing twice. Four hundred and sixty files in this
    corpus had that. So a replacement is refused when it would only echo the
    word across an `and`, `or` or `nor` — the older word stays. A reader who
    meets one unfamiliar word is better served than one handed a sentence
    that has quietly lost half of what it said.
    """
    toks = _WORD_TOKEN.findall(s)
    if not toks:
        return s
    # The effective value of every word, so a refusal also sees the case
    # where both sides of the `and` are being swapped to the same thing.
    eff = [table.get(w.lower(), w).lower() for w in toks]
    i = [-1]

    def swap(m):
        i[0] += 1
        n = i[0]
        word = m.group(0)
        repl = table.get(word.lower())
        if not repl:
            return word
        low = repl.lower()
        if ((n >= 2 and toks[n - 1].lower() in _PAIRED and eff[n - 2] == low)
                or (n + 2 < len(toks) and toks[n + 1].lower() in _PAIRED
                    and eff[n + 2] == low)):
            eff[n] = word.lower()       # it stays, so neighbours see the old word
            return word
        return corrections._match_case(word, repl)

    return _WORD_TOKEN.sub(swap, s)


def _fix_text(s):
    """corrections.fix_text, tokenized. Same tables, same order."""
    s = corrections.resyntax(s)                     # multi-word rewrites
    s = _table_pass(s, corrections.VOCABULARY)
    return _table_pass(s, corrections._ALL_FIXES)


def _modernize_table(s):
    """corrections.modernize, tokenized. Phrases first, as it does."""
    for rx, repl in corrections._PHRASES:
        s = rx.sub(lambda m, r=repl: corrections._match_case(m.group(0), r), s)
    return _table_pass(s, corrections.MODERNIZE)


def modernize(s, tier='safe', report=None):
    """Bring a run of source text to present-day American English."""
    if not s or tier == 'none':
        return s
    s = untype(s)                          # `haſt` is `hast` before anything
    if tier not in TIERS:
        raise ValueError(f'unknown tier {tier!r}; expected one of {TIERS}')
    s = _fix_text(s)                       # vocabulary and constructions
    # Spelling is not a matter of tier: the archive is American English
    # throughout, so this runs on everything that is modernized at all.
    s = american.americanize(s)
    s = _fix_brake(s)
    if tier == 'full':
        s, kept = _protect_art(s)
        s = _modernize_table(s)            # the hand-checked table, first
        s = generative(s, report)          # then the long tail
        s = _restore_art(s, kept)
    return s


# --- the long s, and the ligatures around it ------------------------------
#
# Eighteenth-century printing sets a non-final `s` as `ſ`, and nothing in
# these tables can see it: `haſt` is not `hast`, so it is not `have`, and
# `ſaith` is not `saith`, so it is not `says`. The 1717 Sentences of Ali and
# the 1810 Mishcat-ul-Masabih came in with twelve thousand of them between
# them and went straight through the modernizer untouched.
#
# The substitution is unambiguous — a long s is an s, always, and the
# ligatures are the letters they join — so it is done before any rule runs
# rather than being added to the tables word by word.
OLD_TYPE = {
    'ſ': 's', 'ﬀ': 'ff', 'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬃ': 'ffi', 'ﬄ': 'ffl',
    'ﬅ': 'st', 'ﬆ': 'st', 'Ꞅ': 'S',
}
_OLD_TYPE_RE = re.compile('[' + ''.join(OLD_TYPE) + ']')


def untype(s):
    """Modern letters for the ones the old presses used."""
    if not s:
        return s
    return _OLD_TYPE_RE.sub(lambda m: OLD_TYPE[m.group(0)], s)


def pair(s, tier='safe', report=None):
    """-> (modernized, as printed) — the second only where they differ.

    The archive's most questionable claim is that it has not changed what a
    text says, only how it says it. A reader has no way to check that unless
    the words that were there are still there, so the ingesters keep both.

    `None` is returned for the source where nothing changed, which is most of
    the World English Bible and none of Sale's Koran. That keeps the corpus
    from doubling for the sake of sentences that were already modern.
    """
    out = modernize(s, tier, report)
    return out, (None if out == s else s)


def audit(s):
    """Archaic forms still standing in a finished text."""
    found = Counter()
    for rx in (_RE_ETH, _RE_EST):
        for m in rx.finditer(s):
            low = m.group(0).lower()
            if not _is_word(low) and low not in NEVER:
                found[low] += 1
    for w in re.findall(r'\b(thou|thee|thy|thine|ye|hath|doth|saith|unto|'
                        r'hast|shalt|wilt|dost|didst|canst|wast|wert)\b',
                        s, re.IGNORECASE):
        found[w.lower()] += 1
    # `art` counts only where it is the verb — "thou art" — never where it is
    # the noun, which the modernizer is right to have left alone.
    for w in american.find(s):
        found[w.lower()] += 1
    for m in _RE_ART.finditer(s):
        before = s[max(0, m.start() - 20):m.start()]
        after = s[m.end():m.end() + 16]
        if _ART_BEFORE.search(before) or _ART_AFTER.match(after):
            found['art'] += 1
    return found


if __name__ == '__main__':
    tests = [
        ('cometh', 'comes'), ('abideth', 'abides'), ('teacheth', 'teaches'),
        ('crieth', 'cries'), ('sitteth', 'sits'), ('putteth', 'puts'),
        ('calleth', 'calls'), ('dwelleth', 'dwells'), ('runneth', 'runs'),
        ('giveth', 'gives'), ('writeth', 'writes'), ('hateth', 'hates'),
        ('singeth', 'sings'), ('changeth', 'changes'), ('beginneth', 'begins'),
        ('goeth', 'goes'), ('seeth', 'sees'), ('fleeth', 'flees'),
        ('lovest', 'love'), ('gavest', 'gave'), ('wentest', 'went'),
        ('knowest', 'know'), ('hatest', 'hate'), ('calledst', 'called'),
        # must be left exactly as they are
        ('forest', 'forest'), ('harvest', 'harvest'), ('priest', 'priest'),
        ('tempest', 'tempest'), ('greatest', 'greatest'), ('honest', 'honest'),
        ('twentieth', 'twentieth'), ('death', 'death'), ('beneath', 'beneath'),
        ('Nazareth', 'Nazareth'), ('Japheth', 'Japheth'), ('breath', 'breath'),
        ('interest', 'interest'), ('conquest', 'conquest'), ('earnest', 'earnest'),
    ]
    rep = Report()
    bad = 0
    for src, want in tests:
        got = generative(corrections.modernize(src), rep)
        if got != want:
            bad += 1
            print(f'  FAIL {src!r}: got {got!r}, want {want!r}')
    print(f'{len(tests) - bad}/{len(tests)} passed')
    if rep.unresolved:
        print('unresolved:', dict(rep.unresolved))
    sys.exit(1 if bad else 0)
