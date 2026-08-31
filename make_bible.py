#!/usr/bin/env python3
"""Build the printable Apocrypha PDF from the USFM sources.

    python make_bible.py                       # the book
    python make_bible.py --body 8.5 --leading 10.2   # a looser setting
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bible import build                                          # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--body', type=float, default=8.0, help='body type size (pt)')
    ap.add_argument('--leading', type=float, default=9.6, help='leading (pt)')
    ap.add_argument('--trim', default='5.5x8.5', choices=['5.5x8.5', '6x9'],
                    help='page trim size')
    ap.add_argument('-o', '--out', default='The-Lampstand-Apocrypha.pdf')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, a.out)
    n, t = build.render_pdf(path, body=a.body, leading=a.leading, trim=a.trim)
    print(f"\n{a.out}: {t} pages")


if __name__ == '__main__':
    main()
