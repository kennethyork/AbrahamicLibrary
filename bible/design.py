"""The visual scheme for Apocrypha Plus.

The theme is the book's own title. *Apokryphos* means hidden away — these are
writings kept off the lampstand but never quite put out. So: a night ground,
one small light, and the light used sparingly enough that it reads as kept
rather than displayed.

Everything is drawn as vectors rather than placed as images, so it holds at
any trim size and adds nothing to the file but a few hundred bytes.
"""
from reportlab.lib.colors import Color

def _c(h):
    h = h.lstrip('#')
    return Color(*(int(h[i:i+2], 16) / 255 for i in (0, 2, 4)))


# --- palette --------------------------------------------------------------
# Five colours, no more. The first two carry the book; the rest are accents
# that appear on perhaps a dozen pages out of five hundred.
VELLUM = _c('#F2EDE3')   # paper ground — warm, not white
INK    = _c('#1B1714')   # body text — warm near-black, to suit Gentium
NIGHT  = _c('#1B2A41')   # cover and part titles — deep, unsaturated indigo
LAMP   = _c('#C8963E')   # the one light — amber, for rules and the device
OXIDE  = _c('#8A3B2A')   # muted rust — rare, for division numerals only

GREY   = _c('#6E6A64')   # for footnote rules and other quiet furniture


def lamp(c, cx, cy, h, color=LAMP, ink=None):
    """The device: a small oil lamp with a flame, drawn to height `h`."""
    w = h * 1.9
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(max(0.5, h * 0.045))
    c.setLineCap(1)

    # the flame — two arcs meeting at a point
    p = c.beginPath()
    p.moveTo(cx, cy + h * 0.98)
    p.curveTo(cx - h * 0.20, cy + h * 0.62, cx - h * 0.17, cy + h * 0.44,
              cx, cy + h * 0.36)
    p.curveTo(cx + h * 0.17, cy + h * 0.44, cx + h * 0.20, cy + h * 0.62,
              cx, cy + h * 0.98)
    c.drawPath(p, stroke=0, fill=1)

    # the vessel — a shallow bowl with a spout to the left
    b = c.beginPath()
    b.moveTo(cx - w * 0.50, cy + h * 0.10)
    b.curveTo(cx - w * 0.30, cy - h * 0.34, cx + w * 0.30, cy - h * 0.34,
              cx + w * 0.46, cy + h * 0.10)
    b.curveTo(cx + w * 0.20, cy + h * 0.22, cx - w * 0.24, cy + h * 0.22,
              cx - w * 0.50, cy + h * 0.10)
    c.drawPath(b, stroke=1, fill=0)
    c.restoreState()


def lozenge(c, cx, cy, r, color=LAMP, filled=True):
    """A small diamond, used to break a rule."""
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    p = c.beginPath()
    p.moveTo(cx, cy + r); p.lineTo(cx + r * 0.62, cy)
    p.lineTo(cx, cy - r); p.lineTo(cx - r * 0.62, cy)
    p.close()
    c.drawPath(p, stroke=0 if filled else 1, fill=1 if filled else 0)
    c.restoreState()


def broken_rule(c, x1, x2, y, color=LAMP, gap=7.0, weight=0.6):
    """A rule interrupted at its centre by a lozenge.

    The break is the point: the line is continuous everywhere but the middle,
    where something is set aside.
    """
    mid = (x1 + x2) / 2
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(weight)
    c.line(x1, y, mid - gap, y)
    c.line(mid + gap, y, x2, y)
    c.restoreState()
    lozenge(c, mid, y, gap * 0.42, color)


def double_rule(c, x1, x2, y, color=LAMP, sep=2.2):
    """A thick-then-thin pair, the old printer's way of closing a section."""
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(1.1); c.line(x1, y, x2, y)
    c.setLineWidth(0.4); c.line(x1, y - sep, x2, y - sep)
    c.restoreState()
