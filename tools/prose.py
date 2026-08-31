"""Turning plain-text books into chapters of paragraphs.

Project Gutenberg and the Christian Classics Ethereal Library both publish
plain text, and neither marks its structure in any formal way. What follows
are the heuristics that recover it: strip the boilerplate, find the headings,
gather the paragraphs. They are heuristics and they are described as such —
where one cannot find a structure, the work is still readable as a single
run of prose rather than being dropped.
"""
import re

# --- boilerplate ----------------------------------------------------------

RE_PG_START = re.compile(
    r'^\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*\s*$',
    re.M | re.I)
RE_PG_END = re.compile(
    r'^\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*\s*$',
    re.M | re.I)

RE_CCEL_RULE = re.compile(r'^\s*_{15,}\s*$', re.M)


def strip_gutenberg(text):
    """The book itself, without the licence wrapped around it."""
    m = RE_PG_START.search(text)
    if m:
        text = text[m.end():]
    m = RE_PG_END.search(text)
    if m:
        text = text[:m.start()]
    # the transcriber's note and the producer credit, when they lead
    text = re.sub(r'\A\s*(Produced by|E-text prepared by|Transcribed).*?\n\n',
                  '', text, count=1, flags=re.S | re.I)
    return text.strip()


def ccel_sections(text):
    """CCEL rules its sections off with a line of underscores."""
    return [s for s in RE_CCEL_RULE.split(text) if s.strip()]


# --- headings -------------------------------------------------------------

# A footnote block, which CCEL sets between sections exactly as it sets a
# section: the leading marker is what tells them apart.
RE_FOOTNOTE = re.compile(r'^\s*\[\d+\]')

# Roman or arabic chapter openings, in the many forms these books use.
RE_HEADING = re.compile(
    r'^\s*(?:'
    r'(?:CHAPTER|CHAP\.|BOOK|PART|SECTION|LETTER|EPISTLE|HOMILY|ORATION|'
    r'DISCOURSE|SERMON|TRACTATE|CANON|ARTICLE|PSALM|SURA|ACT)\s+'
    r'[IVXLCDM0-9]+|'
    r'[IVXLCDM]{1,7}\.\s+\S|'
    r'\d{1,3}\.\s+[A-Z]'
    r')', re.I)


def looks_like_heading(line):
    s = line.strip()
    if not s or len(s) > 120:
        return False
    if RE_FOOTNOTE.match(s):
        return False
    if RE_HEADING.match(s):
        return True
    # a short line in capitals, which is how most of these books set a title
    letters = [c for c in s if c.isalpha()]
    if len(letters) >= 3 and all(c.isupper() for c in letters) and len(s) < 90:
        return True
    return False


# --- paragraphs -----------------------------------------------------------

def paragraphs(chunk):
    """Blank-line-separated paragraphs, rewrapped onto one line each."""
    out = []
    for block in re.split(r'\n\s*\n', chunk):
        text = ' '.join(block.split())
        if text:
            out.append(text)
    return out


def is_front_matter(heading):
    """Contents pages, indexes and licence blocks are not chapters."""
    h = heading.strip().lower().rstrip('.:')
    return h in {
        'contents', 'table of contents', 'index', 'indexes', 'index.',
        'footnotes', 'transcriber\'s note', 'transcriber\'s notes',
        'illustrations', 'list of illustrations', 'advertisement',
        'errata', 'colophon', 'bibliography', 'the end',
    }


def chunk_to_chapter(chunk, min_chars=400):
    """-> (heading, [paragraph, ...]) or None if it is not a chapter."""
    paras = paragraphs(chunk)
    if not paras:
        return None
    heading = ''
    if looks_like_heading(paras[0]) or len(paras[0]) < 90:
        heading = paras[0]
        body = paras[1:]
    else:
        body = paras
    if RE_FOOTNOTE.match(heading or (body[0] if body else '')):
        return None
    if is_front_matter(heading):
        return None
    if sum(len(p) for p in body) < min_chars:
        return None
    return heading, body


def split_by_headings(text, min_chars=1200):
    """Break a run of prose at its headings.

    Used for books with no other structure. A heading only opens a new
    chapter once the one before it has enough text to be worth being one,
    so a run of headings in a contents list does not shatter the book.
    """
    chapters, heading, body = [], '', []

    def flush():
        if body and sum(len(p) for p in body) >= 200:
            chapters.append((heading, list(body)))

    for para in paragraphs(text):
        if looks_like_heading(para) and sum(len(p) for p in body) >= min_chars:
            flush()
            heading, body = para, []
        elif looks_like_heading(para) and not body:
            heading = para
        else:
            body.append(para)
    flush()
    return chapters
