"""Telling a religious text from a story about one.

A search for "arabian" or "persian poetry" returns the Arabian Nights, fairy
tales, adventure novels and — in quantity — the Edwardian fashion for
parodying the Rubáiyát: *Rubáiyát of a Motor Car*, *of Bridge*, *of a Huffy
Husband*. None of that belongs in a library of sources.

The test is Project Gutenberg's own subject headings, which are Library of
Congress headings and say plainly when a book is fiction. Where a book has no
headings, the title is asked instead.

The hard part is that the line is not "poetry vs prose". Rumi's Masnavi,
Attar's Conference of the Birds, Saadi's Gulistan and Hafiz's Divan are
poetry and are also the primary literature of Sufism; the Psalms are poetry.
So verse is never excluded for being verse. What is excluded is fiction,
parody, juvenile retelling and stage drama.
"""
import re

# Library of Congress subject headings that mean a made-up story.
FICTION_SUBJECTS = re.compile(
    r'--\s*Fiction|^Fiction|\bFiction\b|'
    r'Fairy tales|Folklore|Legends and stories|'
    r'Juvenile fiction|Juvenile literature|Children.s stories|'
    r'Short stories|Adventure stories|Love stories|War stories|'
    r'Detective and mystery|Science fiction|Historical fiction|'
    r'Parodies, imitations|Humorous poetry|Humorous stories|'
    r'Wit and humor|Satire|Limericks|Nonsense verses|'
    r'\bDrama\b|--\s*Drama|\bPlays\b|Comedies|Tragedies|'
    r'Romances|Allegories|Fables|Tales\b',
    re.I)

# Titles that give it away when there are no subject headings at all.
FICTION_TITLE = re.compile(
    r'\ba (?:tale|novel|romance|story|play|comedy|drama)\b|'
    r'\btales? (?:of|from)\b|\bstories (?:of|from|for)\b|'
    r'\bparod|\bimitation|\bburlesque|\brhymes?\b|\blimerick|'
    r'\bfor (?:children|boys|girls|young)\b|\bnursery\b|'
    r'\bfairy\b|\bmyths?\b|\badventures? of\b|'
    r'\bplay in (?:one|two|three|four|five)\b|'
    r'\bfrom broadway\b|\bmotor car\b|\bof bridge\b|\bhusband\b|'
    r'\bbachelor\b|\bhuffy\b|\bjr\.',
    re.I)

# Primary religious literature that the tests above would otherwise catch.
# Each is a source text of its tradition, whatever form it takes.
ALWAYS_KEEP = re.compile(
    r'masnavi|mesnevi|mathnawi|'
    r'conference of the birds|mantiq|'
    r'gulistan|bustan|rose garden|'
    r'divan|diwan|'
    r'koran|qur.?an|bible|talmud|mishnah|midrash|zohar|'
    r'hadith|hadees|mishcat|mishkat|sunna|'
    r'apocrypha|pseudepigrapha|gospel|epistle|psalm|'
    r'confessions|city of god|summa|imitation of christ|'
    r'pilgrim.s progress|'                    # allegory, but a primary work
    r'sacred books of the east',
    re.I)

# A parody names its target and then swerves. "Rubaiyat of Omar Khayyam" is
# the poem; "Rubaiyat of a Motor Car" is not. Keep the first, drop the rest.
RUBAIYAT_REAL = re.compile(
    r'rub[aá]iy[aá]t of omar khayy[aá]m\s*$|'
    r'rub[aá]iy[aá]t of omar khayy[aá]m[,:]|'
    r'^the rub[aá]iy[aá]t\s*$|'
    r'rub[aá]iy[aá]t.{0,40}(rendered|translat|persian|version)',
    re.I)
RUBAIYAT_ANY = re.compile(r'rub[aá]iy[aá]t|rubaiyat', re.I)


def verdict(title, subjects=()):
    """-> (keep: bool, why: str)"""
    title = (title or '').strip()
    subject_text = ' ; '.join(subjects or ())

    if ALWAYS_KEEP.search(title):
        return True, 'primary religious text'

    # The Rubáiyát fashion, judged on its own
    if RUBAIYAT_ANY.search(title):
        if RUBAIYAT_REAL.search(title):
            return True, 'a translation of the Rubáiyát'
        return False, 'a Rubáiyát parody or imitation'

    hit = FICTION_SUBJECTS.search(subject_text)
    if hit:
        return False, f'subject heading “{hit.group(0)}”'

    hit = FICTION_TITLE.search(title)
    if hit:
        return False, f'title says “{hit.group(0)}”'

    return True, ''


def is_fiction(title, subjects=()):
    keep, _ = verdict(title, subjects)
    return not keep
