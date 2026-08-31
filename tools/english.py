"""Is this text actually English?

Gutenberg's own language field is not always there, and its search returns
books in every language. Rather than trusting a label, this asks the text:
what share of its words are in an English dictionary?

Spanish, French, German and Latin all score far below English on this,
because their function words — de, la, und, der, et, in — are mostly not
English words, and function words are most of any text. English scores well
above, because its own function words are.
"""
import re

from tools.modernize import WORDS

RE_WORD = re.compile(r"[A-Za-z][A-Za-z']+")

# Words common in other languages that are also English words, so they cannot
# be counted as evidence of English: 'no', 'a', 'me', 'con', 'son', 'die'.
AMBIGUOUS = {
    'a', 'no', 'me', 'con', 'son', 'die', 'der', 'in', 'is', 'la', 'le',
    'as', 'at', 'do', 'so', 'us', 'an', 'am', 'on', 'or', 'to', 'ye',
    'et', 'ex', 'per', 'pro', 'sic', 'ad', 'de', 'da', 'se', 'si', 'ma',
}

# A strong signal: the English function words no other language shares.
ENGLISH_MARKERS = {
    'the', 'and', 'that', 'with', 'which', 'their', 'have', 'from', 'were',
    'been', 'they', 'this', 'would', 'there', 'them', 'said', 'when', 'who',
    'shall', 'what', 'these', 'about', 'other', 'into', 'than', 'could',
}


def score(text, sample=40000):
    """-> (share of words that are English, share that are English markers)"""
    words = [w.lower() for w in RE_WORD.findall(text[:sample])]
    words = [w for w in words if len(w) > 1]
    if len(words) < 50:
        return 0.0, 0.0
    known = sum(1 for w in words if w in WORDS and w not in AMBIGUOUS)
    marks = sum(1 for w in words if w in ENGLISH_MARKERS)
    return known / len(words), marks / len(words)


def is_english(text, min_known=0.55, min_markers=0.04):
    """True when the text reads as English rather than another language.

    The two tests together: a high dictionary share alone can be reached by
    Latin (many English words are Latin), and the marker share alone can be
    fooled by a short quotation. Both must hold.
    """
    known, marks = score(text)
    return known >= min_known and marks >= min_markers
