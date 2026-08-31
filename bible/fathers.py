"""Reader for the Apostolic Fathers, Roberts–Donaldson translation (1870).

Source: the Ante-Nicene Christian Library vol. I (Edinburgh, T. & T. Clark),
via Project Gutenberg. Public domain.

Three things about the source shape the reader:

* There is no verse numbering — chapters and paragraphs only — so these books
  set without verse numbers, and running heads carry the chapter alone.
* The Ignatian epistles print the Shorter and Longer recensions in alternating
  blocks. Only the Shorter is set here; the Longer is a later expansion, and
  interleaving both would be unreadable.
* Each work is preceded by the 1870 editors' Introductory Notice. Those are
  modern editorial matter rather than the ancient text, and are skipped.
"""
import re

from .usfm import Book, Block, Verse, Chapter, Text, Note
from .corrections import (fix_text, americanize, modernize, resyntax,
                          resentence)
from .enoch import _collect_notes, roman_to_int, ROMAN

CAPS = re.compile(r"^[A-ZÆŒ][A-ZÆŒ0-9 .,'’\-—:()]+$")


def _norm(s):
    # resyntax runs last as well as inside fix_text: modernize creates new
    # archaic constructions as it goes (didst bring -> did bring, hath
    # given -> has given), and those must be re-examined afterwards.
    return resentence(resyntax(modernize(americanize(fix_text(s)))))


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _clean_head(s):
    """Tidy a chapter title: drop the recension marker and any note caller."""
    s = re.sub(r'[—\-–]\s*(SHORTER|LONGER)\.?\s*$', '', _clean(s))
    s = re.sub(r'\[\d+\]', '', s)
    return s.strip('_ ').rstrip('.').strip()


def _note_parts(body):
    parts, i = [], 0
    for m in re.finditer(r'_([^_]+)_', body):
        if m.start() > i:
            parts.append(('ft', _norm(body[i:m.start()]).strip()))
        parts.append(('fqa', _norm(m.group(1)).strip()))
        i = m.end()
    if body[i:].strip():
        parts.append(('ft', _norm(body[i:]).strip()))
    return [(k, t) for k, t in parts if t]


def _runs(s, notes, ref=''):
    out = []
    for chunk in re.split(r'(\[\d+\])', s):
        m = re.fullmatch(r'\[(\d+)\]', chunk)
        if m:
            body = notes.get(m.group(1))
            if body:
                out.append(Note('f', ref, _note_parts(body)))
            continue
        i = 0
        for it in re.finditer(r'_([^_]+)_', chunk):
            if it.start() > i:
                out.append(Text(_norm(chunk[i:it.start()])))
            out.append(Text(_norm(it.group(1)), italic=True))
            i = it.end()
        if chunk[i:]:
            out.append(Text(_norm(chunk[i:])))
    return [r for r in out if not isinstance(r, Text) or r.s]


# (start marker, running-head name, printed title)
WORKS = [
    ('THE FIRST EPISTLE OF CLEMENT.', '1 Clement',
     'The First Epistle of Clement to the Corinthians'),
    ('THE SECOND EPISTLE OF CLEMENT.', '2 Clement',
     'The Second Epistle of Clement'),
    ('THE EPISTLE OF POLYCARP.', 'Polycarp',
     'The Epistle of Polycarp to the Philippians'),
    ('THE MARTYRDOM OF POLYCARP.', 'Martyrdom of Polycarp',
     'The Martyrdom of Polycarp'),
    ('THE EPISTLE OF BARNABAS.', 'Barnabas', 'The Epistle of Barnabas'),
    ('THE EPISTLE OF IGNATIUS TO THE EPHESIANS.', 'Ignatius to the Ephesians',
     'The Epistle of Ignatius to the Ephesians'),
    ('THE EPISTLE OF IGNATIUS TO THE MAGNESIANS.', 'Ignatius to the Magnesians',
     'The Epistle of Ignatius to the Magnesians'),
    ('THE EPISTLE OF IGNATIUS TO THE TRALLIANS.', 'Ignatius to the Trallians',
     'The Epistle of Ignatius to the Trallians'),
    ('THE EPISTLE OF IGNATIUS TO THE ROMANS.', 'Ignatius to the Romans',
     'The Epistle of Ignatius to the Romans'),
    ('THE EPISTLE OF IGNATIUS TO THE PHILADELPHIANS.',
     'Ignatius to the Philadelphians',
     'The Epistle of Ignatius to the Philadelphians'),
    ('THE EPISTLE OF IGNATIUS TO THE SMYRNÆANS.', 'Ignatius to the Smyrnaeans',
     'The Epistle of Ignatius to the Smyrnaeans'),
    ('THE EPISTLE OF IGNATIUS TO POLYCARP.', 'Ignatius to Polycarp',
     'The Epistle of Ignatius to Polycarp'),
    ('THE EPISTLES OF IGNATIUS AFTER THE SYRIAC VERSION.', 'Syriac Ignatius',
     'The Epistles of Ignatius after the Syriac Version'),
    ('THE MARTYRDOM OF IGNATIUS.', 'Martyrdom of Ignatius',
     'The Martyrdom of Ignatius'),
    ('THE EPISTLE TO DIOGNETUS.', 'Diognetus', 'The Epistle to Diognetus'),
    ('THE PASTOR OF HERMAS.', 'Hermas', 'The Pastor of Hermas'),
    ('FRAGMENTS OF PAPIAS.', 'Papias', 'Fragments of Papias'),
]

# The 1870 edition closes with an appendix of letters it prints as spurious.
# They are set here in their own division, labelled as the editors labelled
# them, so the collection is complete without passing them off as genuine.
SPURIOUS = [
    ('THE EPISTLE OF IGNATIUS TO THE TARSIANS.', 'To the Tarsians',
     'The Epistle of Ignatius to the Tarsians'),
    ('THE EPISTLE OF IGNATIUS TO THE ANTIOCHIANS.', 'To the Antiochians',
     'The Epistle of Ignatius to the Antiochians'),
    ('THE EPISTLE OF IGNATIUS TO HERO, A DEACON OF ANTIOCH.', 'To Hero',
     'The Epistle of Ignatius to Hero, a Deacon of Antioch'),
    ('THE EPISTLE OF IGNATIUS TO THE PHILIPPIANS.', 'To the Philippians',
     'The Epistle of Ignatius to the Philippians'),
    ('THE EPISTLE OF MARIA THE PROSELYTE TO IGNATIUS.', 'Maria to Ignatius',
     'The Epistle of Maria the Proselyte to Ignatius'),
    ('THE EPISTLE OF IGNATIUS TO MARY AT NEAPOLIS, NEAR ZARBUS.',
     'To Mary at Neapolis', 'The Epistle of Ignatius to Mary at Neapolis'),
    ('THE EPISTLE OF IGNATIUS TO ST JOHN THE APOSTLE.', 'To St John',
     'The Epistle of Ignatius to St John the Apostle'),
    ('A SECOND EPISTLE OF IGNATIUS TO ST JOHN.', 'To St John II',
     'A Second Epistle of Ignatius to St John'),
    ('THE EPISTLE OF IGNATIUS TO THE VIRGIN MARY.', 'To the Virgin Mary',
     'The Epistle of Ignatius to the Virgin Mary'),
    ('REPLY OF THE BLESSED VIRGIN TO THIS LETTER.', 'The Reply',
     'Reply of the Blessed Virgin to this Letter'),
]

# Hermas's three-level structure; these head sections rather than chapters.
SECTION = re.compile(r'^(BOOK [A-Z]+\.|VISION [A-Z]+\.|COMMANDMENT [A-Z]+\.'
                     r'|SIMILITUDE [A-Z]+\.)')


def _find_works(lines, table=None, stop_at='INDEX OF SUBJECTS.'):
    """Locate each work's span. Returns [(name, title, start, end)]."""
    marks = []
    for key, name, title in (table or WORKS):
        idx = [i for i, l in enumerate(lines) if l.strip() == key]
        # a work's title is printed in the contents and again above the text;
        # the last occurrence before the indexes is the text itself
        idx = [i for i in idx if i > 150]
        if idx:
            marks.append((idx[-1] if name == 'Hermas' else idx[0], name, title))
    marks.sort()
    stop = next((i for i, l in enumerate(lines)
                 if l.strip() == stop_at and i > 150), len(lines))
    out = []
    for k, (start, name, title) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else stop
        out.append((name, title, start, end))
    return out


def _drop_editorial_notice(blocks):
    """Remove the 1870 editors' own preface from the front of a work.

    Two works — the Shepherd of Hermas and the Epistle to Diognetus — are
    introduced in the source volume by an Introductory Notice written by
    Roberts and Donaldson themselves: who they think wrote it, which
    manuscripts survive, and what the abbreviations in their footnotes stand
    for. Nearly a thousand words of it in the case of Hermas. Set as plain
    paragraphs it read as the opening of the ancient work, which it is not.

    This edition prints the ancient text without a modern editor in front of
    it, the same rule that governs the 1926 material elsewhere. The notice
    runs from the first paragraph to the heading that opens the work proper,
    so everything before that heading goes.
    """
    if not blocks:
        return blocks
    first = ' '.join(i.s for i in blocks[0].items if isinstance(i, Text))
    if not first.strip().lower().startswith('introductory notice'):
        return blocks
    for n, b in enumerate(blocks):
        if b.style == 's1':
            return blocks[n:]
    return blocks


def parse(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    body = raw.split('*** START', 1)[-1].split('*** END', 1)[0]
    lines = [l.rstrip() for l in body.split('\n')]
    notes, consumed = _collect_notes(lines)

    spans = _find_works(lines, WORKS, stop_at='APPENDIX.')
    spans += _find_works(lines, SPURIOUS, stop_at='INDEX OF SUBJECTS.')
    books = []
    for name, title, start, end in spans:
        bk = Book(id=name[:3].upper(), h=name, toc1=title, toc2=name)
        chapter = 0
        cur, pending = None, []
        skipping = False        # inside an Introductory Notice
        longer = False          # inside a Longer-recension block
        head_buf = None

        def flush():
            nonlocal cur, pending
            if pending:
                txt = _clean(' '.join(pending))
                if txt:
                    if cur is None:
                        cur = Block('p')
                        bk.blocks.append(cur)
                    cur.items.extend(_runs(txt, notes, str(chapter)))
            pending = []

        for i in range(start + 1, end):
            if i in consumed:
                continue
            s = lines[i].strip()
            if not s:
                # a blank line ends a heading as well as a paragraph; without
                # this an unbalanced italic marker swallows the text below it
                if head_buf is not None:
                    txt = _clean_head(' '.join(head_buf))
                    if txt:
                        b = Block('s1'); b.items = [Text(_norm(txt))]
                        bk.blocks.append(b)
                    head_buf = None
                flush()
                cur = None
                continue

            if s == 'INTRODUCTORY NOTICE.':
                flush(); cur = None
                skipping = True
                continue
            if skipping:
                # the notice runs until the work's own heading or first chapter
                if CAPS.match(s) or s.startswith('CHAP.'):
                    skipping = False
                else:
                    continue

            if s == 'SHORTER.':
                flush(); cur = None
                longer = False          # a recension switch, not a chapter
                continue
            if s == 'LONGER.':
                flush(); cur = None
                longer = True
                continue

            m = re.match(rf'^CHAP\.\s+({ROMAN})\.?\s*[—\-–]?\s*(.*)$', s)
            if m:
                flush(); cur = None
                longer = False          # a new chapter closes the Longer block
                chapter = roman_to_int(m.group(1))
                bk.blocks.append(Block('c', [Chapter(str(chapter))]))
                head_buf = [m.group(2)] if m.group(2) else []
                continue
            if longer:
                continue
            if head_buf is not None:
                head_buf.append(s)
                joined = ' '.join(head_buf)
                if joined.count('_') % 2 == 0:      # the italic title closed
                    txt = _clean_head(joined)
                    if txt:
                        b = Block('s1'); b.items = [Text(_norm(txt))]
                        bk.blocks.append(b)
                    head_buf = None
                continue

            if SECTION.match(s) or (CAPS.match(s) and len(s) > 8):
                flush(); cur = None
                b = Block('s1'); b.items = [Text(_norm(_clean(s).rstrip('.')))]
                bk.blocks.append(b)
                continue

            pending.append(s)
        flush()
        bk.blocks = [b for b in bk.blocks if b.style == 'c' or b.items]
        bk.blocks = _drop_editorial_notice(bk.blocks)
        books.append(bk)
    return books
