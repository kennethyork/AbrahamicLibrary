"""The apocrypha: order, divisions and display names for the fifteen books.

Arranged as printed apocrypha have been since the Geneva and King James
editions and as the NRSV gives them: the books received as canonical by the
Catholic and Orthodox churches first, then the wider set preserved alongside
them.
"""

# Books that KJV-tradition apocrypha print under their own titles, each a
# slice of a source book. `select` is [(chapter, first verse, last verse)],
# None..None meaning the whole chapter. Verse numbers are kept as the source
# gives them, so a reference still points where it always did.
DERIVED = {
    'ESA': dict(src='ESG', name='The Rest of Esther',
                title='The Rest of the Chapters of the Book of Esther',
                select=[('4', 18, 47), ('10', 4, 14)]),
    'BA5': dict(src='BAR', name='Baruch', title='Baruch',
                select=[(str(n), None, None) for n in range(1, 6)]),
    'EJE': dict(src='BAR', name='Epistle of Jeremiah',
                title='The Epistle of Jeremiah',
                select=[('6', None, None)]),
    'S3H': dict(src='DAG', name='Song of the Three',
                title='The Song of the Three Holy Children',
                select=[('3', 24, 90)]),
    'SUS': dict(src='DAG', name='Susanna',
                title='The History of Susanna',
                select=[('13', None, None)]),
    'BEL': dict(src='DAG', name='Bel and the Dragon',
                title='Bel and the Dragon',
                select=[('14', None, None)]),
}

# Received as canonical by the Catholic and Orthodox churches — the
# deuterocanon. Esther and Daniel stand in their Greek forms, which carry the
# additions the shorter Hebrew text lacks.
DEUTEROCANONICAL = [
    ("TOB", "Tobit"),
    ("JDT", "Judith"),
    ("ESA", "The Rest of Esther"),
    ("WIS", "Wisdom"),
    ("SIR", "Sirach"),
    ("BA5", "Baruch"),
    ("EJE", "Epistle of Jeremiah"),
    ("S3H", "Song of the Three"),
    ("SUS", "Susanna"),
    ("BEL", "Bel and the Dragon"),
    ("1MA", "1 Maccabees"),
    ("2MA", "2 Maccabees"),
]

# Outside that canon: read in some Orthodox traditions, or preserved in the
# Septuagint and Vulgate appendices.
WIDER = [
    ("1ES", "1 Esdras"),
    ("MAN", "Prayer of Manasseh"),
    ("PS2", "Psalm 151"),
    ("3MA", "3 Maccabees"),
    ("2ES", "2 Esdras"),
    ("4MA", "4 Maccabees"),
]

# Each division opens on a part-title page.
DIVISIONS = [
    ("ap", "The Apocrypha", "The Deuterocanonical Books", DEUTEROCANONICAL),
    ("ap", None, "The Wider Apocrypha", WIDER),
]

ORDER = [bid for _, _, _, books in DIVISIONS for bid, _ in books]
NAMES = {bid: name for _, _, _, books in DIVISIONS for bid, name in books}
assert len(ORDER) == 18, len(ORDER)

DEUTEROCANON = {bid for bid, _ in DEUTEROCANONICAL}
WIDER_APOCRYPHA = {bid for bid, _ in WIDER}

# Books present in the source but not printed here: the sixty-six
# protocanonical books, and the shorter Hebrew Esther and Daniel, whose text
# the Greek forms above already carry.
NOT_PRINTED = {"EST", "DAN"}

# Books set as poetry throughout.
POETIC = {"PS2", "SIR", "WIS", "S3H"}
