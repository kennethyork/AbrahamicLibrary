"""Preflight for Kindle Direct Publishing.

KDP rejects a book block for reasons that are invisible on screen: a page
whose text crosses into the binding, a page count outside the band its trim
allows, an odd count, a font the file names but does not carry. Each of those
is cheap to test on the finished PDF and expensive to discover after upload,
so the build tests them.

The gutter rule is the one worth stating plainly. KDP's minimum inside margin
rises with thickness, because a thick book does not open flat and the inner
column disappears into the spine. At this book's size that is 0.875 in, and a
page laid out as a recto while it prints as a verso has its gutter on the
outer edge instead — the text block sits over the binding. Nothing about the
page looks wrong; only its parity is.
"""
import os
import re
import subprocess

IN = 72.0

# KDP paperback, black ink. The page-count band sets the minimum inside
# margin; the outside minimum is flat.
GUTTER_MIN = [(150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75),
              (828, 0.875)]
OUTER_MIN = 0.25
PAGES_MIN, PAGES_MAX = 24, 828

# Trims KDP offers with no bleed, in inches.
TRIMS = {
    (5.0, 8.0), (5.06, 7.81), (5.25, 8.0), (5.5, 8.5), (6.0, 9.0),
    (6.14, 9.21), (6.69, 9.61), (7.0, 10.0), (7.44, 9.69), (7.5, 9.25),
    (8.0, 10.0), (8.5, 11.0), (8.27, 11.69),
}

_PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>',
                   re.S)
_WORD = re.compile(r'xMin="([-\d.]+)" yMin="([-\d.]+)"'
                   r' xMax="([-\d.]+)" yMax="([-\d.]+)"')


def gutter_required(pages):
    """KDP's minimum inside margin, in inches, for a block this thick."""
    for limit, need in GUTTER_MIN:
        if pages <= limit:
            return need
    return GUTTER_MIN[-1][1]


def _pages(path):
    """Every page as (width, height, [(x0, y0, x1, y1) ...]) in points.

    Boxes come from pdftotext, which measures y downward from the top edge.
    """
    xml = subprocess.run(['pdftotext', '-bbox', path, '-'],
                         capture_output=True, text=True).stdout
    out = []
    for w, h, body in _PAGE.findall(xml):
        boxes = [tuple(map(float, m.groups())) for m in _WORD.finditer(body)]
        out.append((float(w), float(h), boxes))
    return out


def _fonts(path):
    """(name, embedded) for every font the file names."""
    lines = subprocess.run(['pdffonts', path], capture_output=True,
                           text=True).stdout.splitlines()[2:]
    out = []
    for ln in lines:
        f = ln.split()
        if len(f) >= 5:
            out.append((f[0], f[-4] == 'yes'))
    return out


def check_block(path, verbose=True):
    """Preflight a book block. Returns a list of problems; empty means clean.

    Page 1 is taken to be a recto, as it is in a bound book, so odd pages
    carry the gutter on the left and even pages on the right.
    """
    problems, notes = [], []
    pages = _pages(path)
    n = len(pages)

    if n % 2:
        problems.append(f'page count {n} is odd; a sheet has two sides, so '
                        f'the printer would add the leaf and the spine width '
                        f'computed from this count would be wrong')
    if not PAGES_MIN <= n <= PAGES_MAX:
        problems.append(f'page count {n} is outside KDP\'s range for black '
                        f'ink, {PAGES_MIN}-{PAGES_MAX}')

    sizes = {(round(w / IN, 3), round(h / IN, 3)) for w, h, _ in pages}
    if len(sizes) > 1:
        problems.append(f'pages are not all one size: {sorted(sizes)}')
    trim = sorted(sizes)[0]
    if trim not in TRIMS:
        problems.append(f'{trim[0]} x {trim[1]} in is not a KDP trim size')
    notes.append(f'trim {trim[0]} x {trim[1]} in, {n} pages')

    need = gutter_required(n)
    worst = {'gutter': (9e9, 0), 'outer': (9e9, 0),
             'top': (9e9, 0), 'bottom': (9e9, 0)}
    for i, (w, h, boxes) in enumerate(pages, 1):
        if not boxes:
            continue                              # a blank leaf has no margins
        left = min(b[0] for b in boxes)
        right = w - max(b[2] for b in boxes)
        recto = i % 2 == 1
        for k, v in (('gutter', left if recto else right),
                     ('outer', right if recto else left),
                     ('top', min(b[1] for b in boxes)),
                     ('bottom', h - max(b[3] for b in boxes))):
            if v < worst[k][0]:
                worst[k] = (v, i)

    for k, floor in (('gutter', need), ('outer', OUTER_MIN),
                     ('top', OUTER_MIN), ('bottom', OUTER_MIN)):
        got, page = worst[k]
        if got > 8e8:
            continue
        side = 'recto' if page % 2 else 'verso'
        if got / IN < floor - 1e-6:
            problems.append(
                f'{k} margin is {got / IN:.3f} in on page {page} (a {side}); '
                f'KDP requires {floor:.3f} in at {n} pages')
        notes.append(f'least {k:<7} {got / IN:.3f} in (page {page}, {side}) '
                     f'— {floor:.3f} in required')

    missing = [f for f, emb in _fonts(path) if not emb]
    if missing:
        problems.append('fonts named but not embedded: ' + ', '.join(missing))
    notes.append(f'{len(_fonts(path))} fonts, all embedded'
                 if not missing else '')

    if verbose:
        print('KDP preflight — ' + os.path.basename(path))
        for ln in notes:
            if ln:
                print('  ' + ln)
        for p in problems:
            print('  FAIL: ' + p)
        if not problems:
            print('  pass')
    return problems


def check_cover(path, trim_w, trim_h, spine, bleed, safe, fold, verbose=True):
    """Preflight a cover wrap. Returns a list of problems; empty means clean.

    The wrap is one sheet carrying back cover, spine and front cover, and the
    two folds are the thing to get right: type that strays across one wraps
    around the corner of the finished book.
    """
    problems, notes = [], []
    pages = _pages(path)
    if len(pages) != 1:
        problems.append(f'a cover is one page; this file has {len(pages)}')
    w, h, boxes = pages[0]

    want_w, want_h = trim_w * 2 + spine + bleed * 2, trim_h + bleed * 2
    if abs(w - want_w) > 0.5 or abs(h - want_h) > 0.5:
        problems.append(f'wrap is {w / IN:.3f} x {h / IN:.3f} in; '
                        f'{want_w / IN:.3f} x {want_h / IN:.3f} in expected '
                        f'for a {spine / IN:.4f} in spine')
    notes.append(f'wrap {w / IN:.3f} x {h / IN:.3f} in, spine '
                 f'{spine / IN:.4f} in, bleed {bleed / IN:.3f} in')

    fold_l, fold_r = bleed + trim_w, bleed + trim_w + spine
    for x0, y0, x1, y1 in boxes:
        on_spine = x0 >= fold_l - 1 and x1 <= fold_r + 1
        if on_spine:
            lo, hi = fold_l + fold, fold_r - fold
            if x0 < lo or x1 > hi:
                problems.append(f'spine type reaches the fold at x={x0:.1f}'
                                f'-{x1:.1f}pt; keep it {fold / IN:.4f} in '
                                f'inside both folds')
        else:
            edge = bleed if x1 < fold_l else w - bleed      # the outer trim
            near = min(abs(x0 - edge), abs(x1 - edge))
            side = 'back' if x1 < fold_l else 'front'
            if near < safe:
                problems.append(f'{side}-cover type is {near / IN:.3f} in '
                                f'from the trim edge; {safe / IN:.2f} in '
                                f'is the safe margin')
            cross = fold_l if x1 < fold_l else fold_r
            if (x1 > cross - fold) if side == 'back' else (x0 < cross + fold):
                problems.append(f'{side}-cover type crosses the spine fold')
        if y0 < bleed + safe or y1 > h - bleed - safe:
            problems.append(f'cover type is inside {safe / IN:.2f} in of the '
                            f'top or bottom trim edge at y={y0:.1f}pt')

    missing = [f for f, emb in _fonts(path) if not emb]
    if missing:
        problems.append('fonts named but not embedded: ' + ', '.join(missing))

    if verbose:
        print('KDP preflight — ' + os.path.basename(path))
        for ln in notes:
            print('  ' + ln)
        for p in dict.fromkeys(problems):        # one line per distinct fault
            print('  FAIL: ' + p)
        if not problems:
            print('  pass')
    return problems


if __name__ == '__main__':
    import sys
    raise SystemExit(1 if check_block(sys.argv[1]) else 0)
