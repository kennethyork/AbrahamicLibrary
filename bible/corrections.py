"""Explicit editorial corrections applied on top of the source text.

The source files are left untouched; every change this edition makes to the
text as received is listed here so it can be audited. Each entry records the
evidence for treating the reading as an error rather than a variant.

Because these corrections alter the text as published, this edition is not
called the World English Bible (per the publisher's request that a changed
text carry a different name).
"""
import re

# usfm id -> (as received, corrected, short was, short now, why)
BOOK_TITLES = {
    'EXO': ("The Second Book of Mosis, Commonly Called Exodus",
            "The Second Book of Moses, Commonly Called Exodus",
            "Mosis", "Moses",
            "misspelling; the book's own \\mt1 line reads 'Moses'"),
    'LEV': ("The Third Book of Mosis, Commonly Called Leviticus",
            "The Third Book of Moses, Commonly Called Leviticus",
            "Mosis", "Moses",
            "misspelling; the book's own \\mt1 line reads 'Moses'"),
    'ECC': ("Ecclesiates or, The Preacher",
            "Ecclesiastes, or The Preacher",
            "Ecclesiates or,", "Ecclesiastes, or",
            "misspelling; the book's own \\mt1 line reads 'Ecclesiastes', "
            "and the comma moves to the idiomatic position"),
}

DISPLAY = {'EXO': 'Exodus', 'LEV': 'Leviticus', 'ECC': 'Ecclesiastes'}


# --- spelling normalised to US English ---------------------------------
#
# Each of these appears in the source alongside the US form used elsewhere in
# the same translation, so they are internal inconsistencies rather than a
# British edition. Whole-word, case-preserving.
WORD_FIXES = {
    'sceptre': 'scepter', 'sceptres': 'scepters',
    'valour': 'valor',
    'sepulchres': 'sepulchers',
    'leapt': 'leaped',
    'travelled': 'traveled', 'traveller': 'traveler', 'travellers': 'travelers',
    'jeweller': 'jeweler',
    'axe': 'ax',
    'enamoured': 'enamored',        # Wisdom 8:2
    'recognising': 'recognizing',   # Wisdom 10:8
    'fulfilment': 'fulfillment',    # Sirach 21:11
    # the wider apocrypha, added later and less closely edited
    'harbour': 'harbor',            # 4 Maccabees 13:7   (harbor 8x elsewhere)
    'honouring': 'honoring',        # 4 Maccabees 8:4
    'cancelling': 'canceling',      # 4 Maccabees 2:8
    'counselling': 'counseling',    # 4 Maccabees 8:28   (counselor 23x elsewhere)
    'dishevelled': 'disheveled',    # 3 Maccabees 1:4    (shriveled, leveled elsewhere)
}

# --- proper names: the Latin digraph, Americanised -----------------------
#
# American Bibles simplify the ae/oe digraph in PLACE and PEOPLE names
# (-aea → -ea, -aean(s) → -ean(s)) but keep it in the -aeus PERSONAL ending.
# Hebrew names in -ael ("el", God: Ishmael, Michael, Raphael, Hazael) and
# genuine two-vowel sequences (Aroer, Doeg, Elioenai) are never touched.
NAME_FIXES = {
    'Arimathaea': 'Arimathea',
    'Idumaea': 'Idumea', 'Idumaeans': 'Idumeans',
    'Ituraea': 'Iturea',
    'Chaldaeans': 'Chaldeans',
    'Beroea': 'Berea',
    'Hasidaeans': 'Hasideans',
    'Elymaeans': 'Elymeans',
    'Nabathaeans': 'Nabateans',
    'Zabadaeans': 'Zabadeans',
    'Maccabaeus': 'Maccabeus',
    'Asmodaeus': 'Asmodeus',
    'Nanaea': 'Nanea',
    'Dotaea': 'Dotea',
    'Aphaerema': 'Apherema',
    'Lacedaemonians': 'Lacedemonians',
    # Obscure deuterocanonical names, simplified for consistency with the above.
    # Cendebeus is the form the NABRE uses; the rest follow the same rule.
    'Arkesaeus': 'Arkeseus',
    'Arsaeus': 'Arseus',
    'Cendebaeus': 'Cendebeus',
    'Gennaeus': 'Genneus',
    'Ruphaeus': 'Rupheus',
    'Sarsathaeus': 'Sarsatheus',
    'Zabuthaeus': 'Zabutheus',
    'Bugaean': 'Bugean',
    'Chaereas': 'Chereas',
    'Coelesyria': 'Celesyria',
    # the king's name: 150 'Manasseh' against 10 'Manasses' in the source
    'Manasses': 'Manasseh',
    'Coele': 'Cele',                # matches Celesyria above
}

# Kept as received, because these ARE the American forms — simplifying them
# would move away from American practice, not toward it:
#   Alphaeus Bartimaeus Thaddaeus Zacchaeus Lebbaeus Timaeus Hymenaeus
#   Caesar Caesarea Esdraelon Praetorium Phoebe Phoenicia Phoenix Chloe
#   Tryphaena Epaenetus
# Kept because the final -ae is a Latin ending, not the digraph, as in the
# names American Bibles print unchanged (Cenchreae, Colossae):
#   Cenchreae Colossae Konae
# Kept deliberately: Baean. The rule would give "Bean", which collides with
# the common noun — "the sons of Bean" reads as the vegetable.

# Deliberately NOT changed, though a naive spell-check flags them:
#   Tyre            the Phoenician city, not British for "tire"
#   spelt           a species of wheat (Exod 9:32, Isa 28:25, Ezek 4:9)
#   smelt           smelting ore (Job 28:2)
#   burnt offering  standard US biblical usage
#   axes            spelled identically in both
NOT_CHANGED = ['Tyre', 'spelt', 'smelt', 'burnt', 'axes']

_ALL_FIXES = dict(WORD_FIXES)
_ALL_FIXES.update({k.lower(): v for k, v in NAME_FIXES.items()})
_WORD_RE = re.compile(r'\b(' + '|'.join(sorted(_ALL_FIXES, key=len, reverse=True))
                      + r')\b', re.IGNORECASE)


# --- wholesale British -> American, for the Enoch companion volume --------
#
# The World English Bible needed only the fixes above, because it varies from
# itself and the American form is already the one it mostly uses. Laurence's
# 1883 Enoch is uniformly British, so it needs a general conversion instead.
# Kept separate so the record shows which rule applied to which book.
BRITISH_TO_AMERICAN = {}
for _b, _a in [('colour', 'color'), ('honour', 'honor'), ('labour', 'labor'),
               ('neighbour', 'neighbor'), ('splendour', 'splendor'),
               ('vapour', 'vapor'), ('clamour', 'clamor'), ('odour', 'odor'),
               ('favour', 'favor'), ('valour', 'valor'), ('armour', 'armor'),
               ('rumour', 'rumor'), ('ardour', 'ardor'), ('fervour', 'fervor'),
               ('succour', 'succor'), ('vigour', 'vigor'), ('endeavour', 'endeavour')]:
    if _b == _a:
        continue
    for _sfx in ('', 's', 'ed', 'ing', 'able', 'ful', 'less'):
        BRITISH_TO_AMERICAN[_b + _sfx] = _a + _sfx
BRITISH_TO_AMERICAN.update({
    'endeavour': 'endeavor', 'endeavours': 'endeavors',
    'endeavoured': 'endeavored', 'endeavouring': 'endeavoring',
    'offence': 'offense', 'offences': 'offenses',
    'defence': 'defense', 'defences': 'defenses',
    'licence': 'license', 'licences': 'licenses',
    'unravelling': 'unraveling', 'unravelled': 'unraveled',
    'revelling': 'reveling', 'revelled': 'reveled',
    'pretence': 'pretense',
    'sulphur': 'sulfur', 'sulphurous': 'sulfurous',
    'fulfil': 'fulfill', 'fulfils': 'fulfills', 'fulfilment': 'fulfillment',
    'centre': 'center', 'centres': 'centers',
    'centred': 'centered', 'centring': 'centering',
    'metre': 'meter', 'metres': 'meters', 'litre': 'liter',
    'fibre': 'fiber', 'sombre': 'somber', 'lustre': 'luster',
    'spectre': 'specter', 'calibre': 'caliber', 'ochre': 'ocher',
    'sceptre': 'scepter', 'sceptres': 'scepters',
    'sepulchre': 'sepulcher', 'sepulchres': 'sepulchers',
    'grey': 'gray', 'plough': 'plow', 'ploughs': 'plows',
    'judgement': 'judgment', 'judgements': 'judgments',
    'travelled': 'traveled', 'travelling': 'traveling',
    'traveller': 'traveler', 'travellers': 'travelers',
    'marvellous': 'marvelous', 'counsellor': 'counselor',
    'counsellors': 'counselors', 'enrol': 'enroll', 'enrols': 'enrolls',
    'skilful': 'skillful', 'wilful': 'willful', 'gaol': 'jail',
    'mould': 'mold', 'moulded': 'molded', 'smoulder': 'smolder',
    'connexion': 'connection', 'storey': 'story', 'draught': 'draft',
    'amongst': 'among', 'whilst': 'while', 'betwixt': 'between',
    'saviour': 'savior', 'saviours': 'saviors',
    'behaviour': 'behavior', 'behaviours': 'behaviors',
    'practise': 'practice', 'practised': 'practiced',
    'practising': 'practicing', 'practises': 'practices',
    'recognise': 'recognize', 'recognised': 'recognized',
    'recognising': 'recognizing', 'recognises': 'recognizes',
    'theatre': 'theater', 'theatres': 'theaters', 'meagre': 'meager',
    'enquire': 'inquire', 'enquired': 'inquired', 'enquiry': 'inquiry',
    'levelled': 'leveled', 'levelling': 'leveling',
    'panelling': 'paneling', 'panelled': 'paneled',
    'amphitheatre': 'amphitheater', 'amphitheatres': 'amphitheaters',
    'councillor': 'councilor', 'councillors': 'councilors',
    'counselled': 'counseled', 'counselling': 'counseling',
    'dishonour': 'dishonor', 'dishonours': 'dishonors',
    'dishonoured': 'dishonored', 'dishonourable': 'dishonorable',
    'humour': 'humor', 'humours': 'humors',
    'marvelled': 'marveled', 'marvelling': 'marveling',
    'parlour': 'parlor', 'parlours': 'parlors',
    'quarrelling': 'quarreling', 'quarrelled': 'quarreled',
    'savour': 'savor', 'savours': 'savors', 'savoured': 'savored',
    'savoury': 'savory',
    'worshipper': 'worshiper', 'worshippers': 'worshipers',
    'spake': 'spoke', 'brake': 'broke', 'clave': 'clung',
    'stedfast': 'steadfast', 'stedfastness': 'steadfastness',
    'stedfastly': 'steadfastly', 'shew': 'show', 'shewed': 'showed',
    'shewing': 'showing', 'shews': 'shows', 'shewn': 'shown',
})

_BR_RE = re.compile(r'\b(' + '|'.join(sorted(BRITISH_TO_AMERICAN, key=len, reverse=True))
                    + r')\b', re.IGNORECASE)


def americanize(s: str) -> str:
    """Convert a uniformly British text to American spelling."""
    if not s:
        return s
    return _BR_RE.sub(lambda m: _match_case(m.group(0),
                                            BRITISH_TO_AMERICAN[m.group(0).lower()]), s)


# --- Early Modern English -> present-day English, for the Enoch volume ----
#
# Laurence wrote in 1883 in the older manner. Changing this is not spelling
# normalisation but modernisation: the result is Laurence's translation
# altered, and the title page says so. Only pronouns and verb inflections are
# touched, each form checked in context first — `art` is verbal throughout
# ("thou art"), never the noun; `thine` occurs once, possessive. Constructions
# that would need the sentence rebuilt (whence, thence, hither) are left, as
# rewriting syntax would be composing a new translation rather than
# modernising this one.
MODERNIZE = {
    # pronouns
    'thou': 'you', 'thee': 'you', 'thy': 'your', 'thine': 'your', 'ye': 'you',
    # verbs taking the second person singular
    'art': 'are', 'hast': 'have', 'shalt': 'shall', 'wilt': 'will',
    'dost': 'do', 'didst': 'did', 'canst': 'can', 'wast': 'were',
    'wert': 'were', 'mayest': 'may', 'mightest': 'might', 'shouldst': 'should',
    'wouldst': 'would', 'couldst': 'could', 'hadst': 'had',
    'knowest': 'know', 'hearest': 'hear', 'beholdest': 'behold',
    'perceivest': 'perceive', 'possessest': 'possess', 'reignest': 'reign',
    'seest': 'see', 'sayest': 'say', 'givest': 'give', 'comest': 'come',
    'doest': 'do', 'goest': 'go', 'livest': 'live', 'speakest': 'speak',
    # third person singular
    'hath': 'has', 'doth': 'does', 'saith': 'says',
    # preposition
    'unto': 'to',
}

# Third-person -eth and second-person -est forms. Written out rather than
# derived: a stemming rule turns "abideth" into "abids" and "cometh" into
# "coms". Superlatives and nouns that merely end in -est (greatest, forest,
# harvest, honest, priest, tempest) are absent from these tables by design,
# as are the names and ordinals that end in -eth (Nazareth, Japheth,
# twentieth).
MODERNIZE.update({
    'abideth': 'abides', 'asketh': 'asks', 'beareth': 'bears',
    'becometh': 'becomes', 'believeth': 'believes', 'bringeth': 'brings',
    'burneth': 'burns', 'calleth': 'calls', 'causeth': 'causes',
    'chasteneth': 'chastens', 'chooseth': 'chooses', 'cometh': 'comes',
    'confesseth': 'confesses', 'continueth': 'continues',
    'delighteth': 'delights', 'desireth': 'desires', 'doubteth': 'doubts',
    'dwelleth': 'dwells', 'edifieth': 'edifies', 'endeth': 'ends',
    'endureth': 'endures', 'entangleth': 'entangles', 'followeth': 'follows',
    'giveth': 'gives', 'glorieth': 'glories', 'glorifieth': 'glorifies',
    'goeth': 'goes', 'doeth': 'does', 'hateth': 'hates', 'healeth': 'heals',
    'heareth': 'hears', 'honoureth': 'honors', 'implieth': 'implies',
    'keepeth': 'keeps', 'killeth': 'kills', 'knoweth': 'knows',
    'leadeth': 'leads', 'lighteth': 'lights', 'liveth': 'lives',
    'loveth': 'loves', 'maketh': 'makes', 'meaneth': 'means',
    'ministereth': 'ministers', 'nourisheth': 'nourishes', 'openeth': 'opens',
    'possesseth': 'possesses', 'presideth': 'presides',
    'proceedeth': 'proceeds', 'profaneth': 'profanes', 'puffeth': 'puffs',
    'raiseth': 'raises', 'receiveth': 'receives', 'redeemeth': 'redeems',
    'rejoiceth': 'rejoices', 'reproveth': 'reproves', 'resisteth': 'resists',
    'ruleth': 'rules', 'saluteth': 'salutes', 'scourgeth': 'scourges',
    'seemeth': 'seems', 'showeth': 'shows', 'sinneth': 'sins',
    'sleepeth': 'sleeps', 'speaketh': 'speaks', 'taketh': 'takes',
    'teacheth': 'teaches', 'testifieth': 'testifies', 'trembleth': 'trembles',
    'uttereth': 'utters', 'warreth': 'wars', 'willeth': 'wills',
    'worketh': 'works', 'woundeth': 'wounds',
    'eateth': 'eats', 'increaseth': 'increases', 'lodgeth': 'lodges',
    'ordereth': 'orders', 'drinketh': 'drinks', 'standeth': 'stands',
    'walketh': 'walks', 'wisheth': 'wishes', 'judgeth': 'judges',

    'barest': 'bore', 'bearest': 'bear', 'bringest': 'bring',
    'broughtest': 'brought', 'callest': 'call', 'castest': 'cast',
    'changest': 'change', 'contractest': 'contract', 'darest': 'dare',
    'desirest': 'desire', 'despisest': 'despise', 'endeavourest': 'endeavor',
    'enterest': 'enter', 'gavest': 'gave', 'hatest': 'hate',
    'heardest': 'heard', 'judgest': 'judge', 'knewest': 'knew',
    'layest': 'lay', 'lettest': 'let', 'lovest': 'love', 'makest': 'make',
    'ministerest': 'minister', 'obeyest': 'obey', 'offerest': 'offer',
    'oughtest': 'ought', 'persuadest': 'persuade', 'pretendest': 'pretend',
    'reprovest': 'reprove', 'revilest': 'revile', 'sawest': 'saw',
    'searchest': 'search', 'seemest': 'seem', 'sendest': 'send',
    'sentest': 'sent', 'settest': 'set', 'shouldest': 'should',
    'sittest': 'sit', 'slanderest': 'slander', 'tarriest': 'tarry',
    'thoughtest': 'thought', 'threatenest': 'threaten',
    'travailest': 'travail', 'wentest': 'went', 'wouldest': 'would',
    'madest': 'made', 'openest': 'open', 'didst': 'did',
    'wroughtest': 'wrought', 'spakest': 'spoke',
})

_MOD_RE = re.compile(r'\b(' + '|'.join(sorted(MODERNIZE, key=len, reverse=True))
                     + r')\b', re.IGNORECASE)


# Phrases, applied before the word-by-word pass. Order matters: "from whence"
# must be caught before bare "whence", or it becomes "from from where".
#
# Not attempted here, deliberately:
#   lest    — every one of its uses needs the clause rebuilt around an
#             inserted negation ("lest he fall" -> "so that he does not
#             fall"). No substitution can do that.
#   behold  — only about a quarter of its uses are the interjection; the rest
#             are the plain verb ("to behold the glory"), which "look" ruins.
#             Changing part of them would leave the book inconsistent with
#             itself, which is worse than leaving it alone.
PHRASES = [
    (r'\binsomuch that\b', 'so that'),
    (r'\bforasmuch as\b', 'since'),
    (r'\bforthwith\b', 'at once'),
    (r'\bfrom whence\b', 'from where'),
    (r'\bfrom thence\b', 'from there'),
    (r'\bwhence\b', 'from where'),
    (r'\bthence\b', 'from there'),
]
_PHRASES = [(re.compile(p, re.IGNORECASE), r) for p, r in PHRASES]


# --- relative "that" -> "who" ---------------------------------------------
#
# "he that knows all things" is a relative clause and wants "he who"; "told
# him that he knew" is a conjunction and must not be touched. What tells them
# apart is the next word: a relative "that" is followed by its own verb, a
# conjunction by the subject of a new clause.
#
# This began as a plain "him that" -> "him who" rule, which printed eleven
# broken sentences ("besought him who he would come down to my house"). The
# verb is now required explicitly, and a following subject blocks the match.
# Told apart by what follows "that". A relative clause continues with its
# verb; a conjunction opens a new clause with a subject. Listing the verbs
# was the first attempt and it does not close — English has too many — so the
# test is inverted: convert unless a subject follows. The pattern is
# case-sensitive on purpose, because a capital after "that" is a proper noun
# and therefore a subject ("told him that Nicanor was disloyal").
_NOT_REL = (r'he|she|it|they|we|you|i|the|this|these|those|there|a|an|his|'
            r'her|their|my|your|our|its|what|which|who|whom|whose|how|'
            r'if|when|where|whether|since|because|neither|either|both|'
            # still in their old forms at this point: resyntax runs once
            # before modernize turns ye into you
            r'ye|thou|thee|thy|thine')
_REL_RE = re.compile(
    r'\b([Hh]e|[Hh]im|[Ss]he|[Hh]er|[Tt]hey|[Tt]hem|[Tt]hose) that\b'
    r'(?=\s+(?!(?:' + _NOT_REL + r')\b)[a-z])')
_REL_TO = {'he': 'he who', 'him': 'him who', 'she': 'she who',
           'her': 'her who', 'they': 'those who', 'them': 'those who',
           'those': 'those who'}


# --- archaic constructions, safe for every source -------------------------
#
# Rewrites that need more than one word swapped. Each was read in place
# first; the counts in the comments are the occurrences found in this
# volume. Replacements may use backreferences, so these are applied with
# _sub_case rather than the plain word tables.
SYNTAX = [
    # narrative filler, 50 uses; modern translations drop or plain it
    (r'\bit came to pass,? that\b', 'it happened that'),
    (r'\bit came to pass\b', 'it happened'),
    # emphatic "did" + bare verb, 21 uses; negatives and questions are
    # already modern ("did not eat", "did he eat") and do not match
    # the compound must precede the singles, or "did eat and drink"
    # loses the second verb and comes out "ate and drink"
    (r'\bdid eat and drink\b', 'ate and drank'),
    (r'\bdid eat\b', 'ate'), (r'\bdid drink\b', 'drank'),
    (r'\bdid bring\b', 'brought'), (r'\bdid bear\b', 'bore'),
    (r'\bdid call\b', 'called'), (r'\bdid show\b', 'showed'),
    (r'\bdid stand\b', 'stood'), (r'\bdid run\b', 'ran'),
    (r'\bdid give\b', 'gave'), (r'\bdid take\b', 'took'),
    (r'\bdid make\b', 'made'), (r'\bdid say\b', 'said'),
    (r'\bdid see\b', 'saw'), (r'\bdid know\b', 'knew'),
    (r'\bdid come\b', 'came'), (r'\bdid go\b', 'went'),
    (r'\bdid hear\b', 'heard'), (r'\bdid keep\b', 'kept'),
    (r'\bdid find\b', 'found'), (r'\bdid send\b', 'sent'),
    (r'\bdid speak\b', 'spoke'), (r'\bdid write\b', 'wrote'),
    (r'\bdid choose\b', 'chose'), (r'\bdid fall\b', 'fell'),
    # a second-person -st that outlived the hand-written table; no English
    # word ends in -edst except these, so the rule is safe as a pattern
    (r'\b([a-z]+ed)st\b', r'\1'),
    # British -our survives on inflected forms the word table missed
    # (favourer, labourers, neighbourhood). The stems are listed whole, so
    # "four", "hour", "pour", "devour" and "your" cannot match.
    # a prefix may sit in front of the stem, as in dishonourably
    (r'\b([a-z]*?)(col|hon|fav|flav|neighb|lab|savi|behavi|arm|vap|od|rum|val|'
     r'harb|hum|splend|endeav)our(ers|er|ed|ing|able|ably|hood|ites|ite|s|)\b',
     r'\1\2or\3'),
    (r'\bpretence(s|)\b', r'pretense\1'),
    (r'\bplough(shares|share|men|man|ed|ing|s|)\b', r'plow\1'),
    # Scanning errors in the 1926 transcription, each read in context first.
    # "greives" is the armor, not the verb: the man is struck on the shins.
    # Two scanning errors that produced real words, so no spell check
    # would ever flag them. Both are fixed by the phrase around them:
    # a global rule on fan or m would do damage elsewhere.
    (r'\bnever fan\b', 'never fall'),
    (r'\bwere m grievous\b', 'were in grievous'),
    # the 1926 transcription runs three words together in Ode 3
    (r'\bIputon\b', 'I put on'),
    (r'\bwnen\b', 'when'), (r'\bwno\b', 'who'),
    (r'\bgreives\b', 'greaves'), (r'\bswared\b', 'swore'),
    (r'\blayed\b', 'laid'), (r'\bcraftly\b', 'craftily'),
    # older forms and British spellings that survived because each occurs
    # only once or twice in five hundred thousand words
    (r'\brancour\b', 'rancor'), (r'\bleant\b', 'leaned'),
    (r'\bmayst\b', 'may'), (r'\bowest\b', 'owe'),
    (r'\buseth\b', 'uses'), (r'\bliest\b', 'lie'),
    (r'\bdigged\b', 'dug'), (r'\btrode\b', 'trod'),
    (r'\bafore\b', 'before'), (r'\bhaply\b', 'perhaps'),
    (r'\bcontemn\b', 'despise'), (r'\breft of\b', 'deprived of'),
    # withal carries two senses here. After a noun it is a postponed
    # with — something to cover the body withal. Before a verb, or
    # after an adjective, it means besides, and those two are taken
    # first so the general rule cannot reach them.
    (r'\band withal\b', 'and yet'),
    (r'\b(benignant|good|kind|wise|just) withal\b', r'\1 besides'),
    (r'\bwithal\b', 'with'),
    # "suffer" in its old sense of allow, 6 uses; "suffering no injury"
    # is the modern sense and is left alone
    (r'\bsuffers (me|him|her|them|us|it) not to\b', r'does not allow \1 to'),
    (r'\bsuffer (me|him|her|them|us|it) not to\b', r'do not allow \1 to'),
    (r'\bsuffer (me|him|her|them|us|it) to\b', r'allow \1 to'),
    (r'\bsuffered (me|him|her|them|us|it) to\b', r'allowed \1 to'),
    # "wax" in its old sense of become, 3 uses
    (r'\bwax old\b', 'grow old'), (r'\bwaxed old\b', 'grew old'),
    (r'\bwax strong\b', 'grow strong'),
    (r'\bwaxed strong\b', 'grew strong'),
    # set phrases
    (r'\bof a truth\b', 'in truth'),
    (r'\bin no wise\b', 'in no way'),
    (r'\bin any wise\b', 'in any way'),
    (r'\bfor to (be|do|have|make|take|give|see|go|come|think|know|say|work|eat|drink|build|serve|learn|receive|prepare|destroy|kill)\b',
     r'to \1'),
    # the World English Bible's own wording in 2 Esdras; "who" is the
    # object of "to" here, so it wants the fronted "to whom"
    (r'\bthose who the world belongs to\b', 'those to whom the world belongs'),
    # an adverb can sit between the two words, and moving it keeps the
    # result idiomatic: "it therefore behoves us" -> "it is therefore
    # fitting for us", not "it therefore is fitting for us"
    (r'\bit (therefore|then|thus|also|now) behoves\b',
     r'it is \1 fitting for'),
    (r'\bit (therefore|then|thus|also|now) behoved\b',
     r'it was \1 fitting for'),
    (r'\bit behoves\b', 'it is fitting for'),
    (r'\bit behoved\b', 'it was fitting for'),
    # there-/here-/where- compounds
    (r'\bwherewith shall\b', 'with what shall'),
    (r'\bwherewith\b', 'with which'),
    (r'\bthereupon\b', 'then'),
    (r'\bhereupon\b', 'at this'),
    # the last -eth verbs; the regex is spelled out because "seeth" is
    # "se"+"eth", which a stem-plus-eth pattern misses
    (r'\bseeth\b', 'sees'), (r'\blieth\b', 'lies'),
    # older spellings
    (r'\bWo is\b', 'Woe is'), (r'\bwo is\b', 'woe is'),
    # "burnt offering" and "burnt sacrifice" are standard American biblical
    # usage and stay; every other "burnt" is the plain past tense
    (r'\bburnt (?!offering|sacrifice)', 'burned '),
]
_SYNTAX = [(re.compile(p, re.IGNORECASE), r) for p, r in SYNTAX]


def _sub_case(m, repl):
    """Expand a replacement template, keeping the match's opening capital."""
    out = m.expand(repl)
    if m.group(0)[:1].isupper():
        out = out[:1].upper() + out[1:]
    return out


def resyntax(s: str) -> str:
    """Rewrite archaic constructions. Safe for every source in the book."""
    if not s:
        return s
    for rx, repl in _SYNTAX:
        s = rx.sub(lambda m, r=repl: _sub_case(m, r), s)
    return _REL_RE.sub(
        lambda m: _match_case(m.group(0), _REL_TO[m.group(1).lower()]), s)

MODERNIZE.update({
    'hither': 'here', 'thither': 'there', 'whither': 'where',
    'verily': 'truly', 'nay': 'no', 'yea': 'yes',
    'divers': 'various', 'sundry': 'various', 'nigh': 'near',
    'aught': 'anything', 'naught': 'nothing', 'durst': 'dared',
    'fain': 'gladly', 'straightway': 'immediately', 'raiment': 'clothing',
    'beseech': 'beg', 'beseeching': 'begging', 'thrice': 'three times',
    'thereof': 'of it', 'therein': 'in it', 'thereto': 'to it',
    'thereon': 'on it', 'whereof': 'of which', 'wherein': 'in which',
})
# the table grew after _MOD_RE was first built, so rebuild it
_MOD_RE = re.compile(r'\b(' + '|'.join(sorted(MODERNIZE, key=len, reverse=True))
                     + r')\b', re.IGNORECASE)

# The pseudepigrapha brought in a far larger stock of -eth and -est verbs than
# the earlier sources needed, too many to write out by hand as those were.
# They are derived instead, and then checked: for each word the infinitive is
# recovered and looked up in the system's American word list, and the inflected
# result must be a real word too, or the word is set aside for a decision. That
# catches the failure that made hand-writing necessary the first time — a bare
# stem that is itself a word, so "spareth" resolves to "spar" and comes out
# "spars". Thirteen such cases were found and settled one at a time; the ones
# the rule got wrong are corrected below the generated tables.
MODERNIZE.update({
    'abominateth': 'abominates', 'abstaineth': 'abstains', 'accepteth': 'accepts',
    'accuseth': 'accuses', 'addeth': 'adds', 'addresseth': 'addresses',
    'aideth': 'aids', 'appeareth': 'appears', 'ariseth': 'arises',
    'attacketh': 'attacks', 'awaiteth': 'awaits', 'befalleth': 'befalls',
    'beginneth': 'begins', 'behaveth': 'behaves', 'beholdeth': 'beholds',
    'belongeth': 'belongs', 'bestoweth': 'bestows', 'betrayeth': 'betrays',
    'blesseth': 'blesses', 'blindeth': 'blinds', 'blotteth': 'blots',
    'breaketh': 'breaks', 'buddeth': 'buds', 'busieth': 'busies',
    'casteth': 'casts', 'ceaseth': 'ceases', 'changeth': 'changes',
    'cleanseth': 'cleanses', 'cleaveth': 'cleaves', 'committeth': 'commits',
    'concealeth': 'conceals', 'conceiveth': 'conceives', 'correcteth': 'corrects',
    'counteth': 'counts', 'coveteth': 'covets', 'crusheth': 'crushes',
    'curseth': 'curses', 'darkeneth': 'darkens', 'deceiveth': 'deceives',
    'defileth': 'defiles', 'defraudeth': 'defrauds', 'delivereth': 'delivers',
    'denieth': 'denies', 'departeth': 'departs', 'despiseth': 'despises',
    'destroyeth': 'destroys', 'deviseth': 'devises', 'disappeareth': 'disappears',
    'disobeyeth': 'disobeys', 'dispraiseth': 'disparages', 'disturbeth': 'disturbs',
    'divideth': 'divides', 'drieth': 'dries', 'driveth': 'drives',
    'encompasseth': 'encompasses', 'enlighteneth': 'enlightens', 'entereth': 'enters',
    'entreateth': 'entreats', 'envieth': 'envies', 'erreth': 'errs',
    'exalteth': 'exalts', 'fadeth': 'fades', 'falleth': 'falls',
    'fasteth': 'fasts', 'feareth': 'fears', 'filleth': 'fills',
    'findeth': 'finds', 'flameth': 'flames', 'fleeth': 'flees',
    'flourisheth': 'flourishes', 'forbiddeth': 'forbids', 'forceth': 'forces',
    'forgiveth': 'forgives', 'gathereth': 'gathers', 'gazeth': 'gazes',
    'getteth': 'gets', 'gnaweth': 'gnaws', 'grieveth': 'grieves',
    'guideth': 'guides', 'hearkeneth': 'hearkens', 'heateth': 'heats',
    'hindereth': 'hinders', 'holdeth': 'holds', 'intercedeth': 'intercedes',
    'justifieth': 'justifies', 'kindleth': 'kindles', 'lacketh': 'lacks',
    'languisheth': 'languishes', 'laudeth': 'lauds', 'layeth': 'lays',
    'licketh': 'licks', 'listeneth': 'listens', 'longeth': 'longs',
    'looketh': 'looks', 'manifesteth': 'manifests', 'mateth': 'mates',
    'meeteth': 'meets', 'mocketh': 'mocks', 'mourneth': 'mourns',
    'needeth': 'needs', 'numbereth': 'numbers', 'offereth': 'offers',
    'overcometh': 'overcomes', 'overreacheth': 'overreaches', 'overthroweth': 'overthrows',
    'overwhelmeth': 'overwhelms', 'perisheth': 'perishes', 'persuadeth': 'persuades',
    'perverteth': 'perverts', 'pitieth': 'pities', 'pleaseth': 'pleases',
    'plundereth': 'plunders', 'praiseth': 'praises', 'prayeth': 'prays',
    'preserveth': 'preserves', 'prospereth': 'prospers', 'provoketh': 'provokes',
    'refresheth': 'refreshes', 'regardeth': 'regards', 'remembereth': 'remembers',
    'reneweth': 'renews', 'repenteth': 'repents', 'requiteth': 'requites',
    'resenteth': 'resents', 'resteth': 'rests', 'restraineth': 'restrains',
    'revealeth': 'reveals', 'reverenceth': 'reverences', 'riseth': 'rises',
    'runneth': 'runs', 'sateth': 'sates', 'saveth': 'saves',
    'searcheth': 'searches', 'seeketh': 'seeks', 'seizeth': 'seizes',
    'serveth': 'serves', 'setteth': 'sets', 'shareth': 'shares',
    'singeth': 'sings', 'smiteth': 'smites', 'spareth': 'spares',
    'stealeth': 'steals', 'stirreth': 'stirs', 'strengtheneth': 'strengthens',
    'stumbleth': 'stumbles', 'succeedeth': 'succeeds', 'suffereth': 'suffers',
    'suggesteth': 'suggests', 'swalloweth': 'swallows', 'sweareth': 'swears',
    'sympathiseth': 'sympathizes', 'talketh': 'talks', 'tendeth': 'tends',
    'thinketh': 'thinks', 'toucheth': 'touches', 'transgresseth': 'transgresses',
    'troubleth': 'troubles', 'trusteth': 'trusts', 'turneth': 'turns',
    'uprooteth': 'uproots', 'visiteth': 'visits', 'waiteth': 'waits',
    'waketh': 'wakes', 'weareth': 'wears', 'welcometh': 'welcomes',
})
MODERNIZE.update({
    'abidest': 'abide', 'askest': 'ask', 'begettest': 'beget',
    'blessest': 'bless', 'camest': 'came', 'chastenest': 'chasten',
    'committest': 'commit', 'dreadest': 'dread', 'dwellest': 'dwell',
    'eatest': 'eat', 'findest': 'find', 'finishest': 'finish',
    'hearkenest': 'hearken', 'helpest': 'help', 'holdest': 'hold',
    'laughest': 'laugh', 'listest': 'wish', 'rearest': 'rear',
    'receivest': 'receive', 'seekest': 'seek', 'sellest': 'sell',
    'sleepest': 'sleep', 'spreadest': 'spread', 'stealest': 'steal',
    'strengthenest': 'strengthen', 'sufferest': 'suffer', 'tellest': 'tell',
    'thinkest': 'think', 'visitest': 'visit', 'willest': 'will',
    'winnest': 'win', 'wishest': 'wish',
})
_MOD_RE = re.compile(r'\b(' + '|'.join(sorted(MODERNIZE, key=len, reverse=True))
                     + r')\b', re.IGNORECASE)



def modernize(s: str) -> str:
    """Bring Early Modern pronouns and verb inflections to present-day forms."""
    if not s:
        return s
    for rx, repl in _PHRASES:
        s = rx.sub(lambda m, r=repl: _match_case(m.group(0), r), s)
    return _MOD_RE.sub(lambda m: _match_case(m.group(0),
                                             MODERNIZE[m.group(0).lower()]), s)


def _match_case(src: str, repl: str) -> str:
    if src.isupper():
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def fix_text(s: str) -> str:
    """Apply the US-English spelling and syntax corrections to a run of text."""
    if not s:
        return s
    s = resyntax(s)
    s = _VOCAB_RE.sub(lambda m: _match_case(m.group(0),
                                            VOCABULARY[m.group(0).lower()]), s)
    return _WORD_RE.sub(lambda m: _match_case(m.group(0),
                                              _ALL_FIXES[m.group(0).lower()]), s)


# --- formal vocabulary, safe everywhere -----------------------------------
#
# Applied to every source, the World English Bible included. Only words with
# no modern homograph appear here: the full modernizer cannot be run over the
# World English Bible, because its rule art -> are would turn Wisdom's "used
# his art to force" into "used his are to force".
VOCABULARY = {
    'thereof': 'of it', 'therein': 'in it', 'thereto': 'to it',
    'thereon': 'on it', 'whereof': 'of which', 'wherein': 'in which',
    'thrice': 'three times', 'sundry': 'various', 'divers': 'various',
    'nigh': 'near', 'aught': 'anything', 'naught': 'nothing',
    'durst': 'dared', 'fain': 'gladly', 'straightway': 'immediately',
    'raiment': 'clothing', 'verily': 'truly',
    # Formal words with a plain equivalent that means the same thing. Only
    # words where the swap is exact are here. The heavy vocabulary of the
    # Greek histories — sanctuary, sacrifice, cavalry, infantry, treasury,
    # ancestors — is left alone, because those words carry the sense and any
    # substitute would be vaguer rather than simpler.
    'implored': 'begged', 'implore': 'beg', 'imploring': 'begging',
    'exhorted': 'urged', 'exhort': 'urge', 'exhorting': 'urging',
    'perpetrated': 'committed', 'exceedingly': 'very',
    'supplication': 'prayer', 'supplications': 'prayers',
    'conspirator': 'plotter', 'conspirators': 'plotters',
    'necessary': 'needed', 'endeavored': 'tried', 'endeavor': 'try',
    'entreated': 'begged', 'entreat': 'beg', 'entreating': 'begging',
    'sepulcher': 'tomb', 'sepulchers': 'tombs',
    # added after a construction scan of the finished volume found them
    # still standing; none has a modern homograph
    'besought': 'begged', 'privily': 'secretly', 'heretofore': 'until now',
    'vesture': 'clothing', 'visage': 'face', 'quickened': 'made alive',
    'smote': 'struck', 'slew': 'killed', 'begat': 'fathered',
    # British forms that survived because they are rare enough to have been
    # missed by the spelling pass
    'learnt': 'learned', 'catalogue': 'catalog', 'draughts': 'drinks',
}

_VOCAB_RE = re.compile(r'\b(' + '|'.join(sorted(VOCABULARY, key=len, reverse=True))
                       + r')\b', re.IGNORECASE)


def book_title(bid: str, received: str) -> str:
    """Return the corrected display title for a book, if it has one."""
    entry = BOOK_TITLES.get(bid)
    if entry and received.strip() == entry[0]:
        return entry[1]
    return received


def manifest():
    """Short lines naming each correction, for the edition notice."""
    order = ['EXO', 'LEV', 'ECC']
    return [(DISPLAY[b], BOOK_TITLES[b][2], BOOK_TITLES[b][3]) for b in order]


def full_manifest():
    """Long form, with the evidence, for the record."""
    return [f"{DISPLAY[b]}: “{w}” → “{n}” ({why})"
            for b, (_, _, w, n, why) in sorted(BOOK_TITLES.items())]


# --- long sentences broken into shorter ones -----------------------------
#
# The translators of 1870 and 1883 wrote the long periodic sentence of their
# day: clause piled on clause, one sentence running past sixty words. The
# words are theirs and stay theirs. All that changes here is a mark of
# punctuation and the capital after it, so no word is added, removed or
# moved, and the sentence still says exactly what it said.
#
# A break is only taken where an independent clause plainly begins — after a
# semicolon or a comma-and, and only when a subject pronoun follows. That
# test is deliberately narrow. "He came and saw" has no subject after the
# and and is left alone, as is any list of the form "A, B, and C".
# After a comma the test stays strict, because a comma-and joins noun
# phrases at least as often as clauses: an explicit subject pronoun must
# follow. After a semicolon it can be looser — a semicolon already marks a
# clause boundary — except where the next word opens a subordinate clause,
# which would leave a fragment standing as a sentence.
_SUBJ_AFTER = r'(?:He|She|It|They|We|You|I|There|This|These|Those)'
_SUBORD = (r'that|which|who|whom|whose|because|since|although|though|while|'
           r'when|whenever|where|wherever|if|unless|until|till|lest|as|than|'
           r'whereby|wherein|whereof|whereupon|to|in')
_SPLIT_COMMA = re.compile(
    r'(?P<lead>,)\s+(?P<conj>and |but |for |so |therefore |yet )'
    r'(?P<subj>' + _SUBJ_AFTER + r')\b')
# "and" coordinates noun phrases as often as clauses, so it keeps the strict
# test above. But, therefore, so and yet almost never join two nouns, so
# after those a split is safe without an explicit pronoun — provided the
# next word does not open a subordinate clause.
_SPLIT_ADVERSATIVE = re.compile(
    r'(?P<lead>,)\s+(?P<conj>but |therefore |so |yet |nevertheless )'
    r'(?P<subj>(?!(?:' + _SUBORD + r')\b)[a-z])')
# A comma-and followed by a noun phrase is the commonest join in the Greek
# histories, and it is the one that keeps their sentences at thirty words.
# It is also the dangerous one, because "the law, and the prophets" is a list
# and not two clauses. The test is therefore a subject followed by a finite
# verb: a determiner or possessive, one or two words of noun phrase, and then
# a verb from a closed list of common finite forms. A list has no verb after
# it, so it cannot match.
_FINITE_V = (r'was|were|is|are|has|had|have|would|will|shall|should|could|'
             r'came|went|took|gave|made|said|sent|began|became|stood|fell|'
             r'died|rose|left|found|brought|called|ordered|commanded|'
             r'gathered|returned|entered|answered|received|appointed|'
             r'[a-z]{3,}ed')
_SPLIT_NP = re.compile(
    r'(?P<lead>,)\s+(?P<conj>and |but |so |therefore |yet )'
    r'(?P<subj>(?:the|his|her|their|our|your|its|a|an|all|many|some|'
    r'both|these|those|two|three)\s+'
    r'(?:[a-z]+\s+){0,2}(?:' + _FINITE_V + r')\b)')

_SPLIT_SEMI = re.compile(
    r'(?P<lead>;)\s+(?P<conj>and |but |for |so |nor |yet |therefore |)'
    r'(?P<subj>(?!(?:' + _SUBORD + r')\b)[A-Za-z])')

SENTENCE_MAX = 32          # words; above this a break is looked for
SENTENCE_MIN = 7           # never leave a piece shorter than this


def _split_once(sent):
    """Break one sentence at the safest point nearest its middle."""
    words = sent.split()
    if len(words) <= SENTENCE_MAX:
        return None
    mid = len(sent) / 2
    best = None
    cands = (list(_SPLIT_COMMA.finditer(sent))
             + list(_SPLIT_ADVERSATIVE.finditer(sent))
             + list(_SPLIT_NP.finditer(sent))
             + list(_SPLIT_SEMI.finditer(sent)))
    for m in cands:
        left, right = sent[:m.start()], sent[m.end('lead'):].lstrip()
        if len(left.split()) < SENTENCE_MIN or len(right.split()) < SENTENCE_MIN:
            continue
        d = abs(m.start() - mid)
        if best is None or d < best[0]:
            best = (d, m)
    if best is None:
        return None
    m = best[1]
    left = sent[:m.start()].rstrip()
    if not left.endswith(('.', '!', '?')):
        left += '.'
    rest = m.group('conj') + m.group('subj') + sent[m.end():]
    rest = rest[:1].upper() + rest[1:]
    return left, rest


def resentence(s: str) -> str:
    """Break over-long sentences. Punctuation only; every word is kept."""
    if not s or len(s.split()) <= SENTENCE_MAX:
        return s
    out = []
    for sent in re.split(r'(?<=[.!?])\s+', s):
        stack, guard = [sent], 0
        while stack and guard < 40:
            guard += 1
            cur = stack.pop(0)
            piece = _split_once(cur)
            if piece is None:
                out.append(cur)
            else:
                stack = [piece[0], piece[1]] + stack
        out.extend(stack)
    return ' '.join(out)
