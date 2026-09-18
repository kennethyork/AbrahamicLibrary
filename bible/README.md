# The Abrahamic Library — the print pipeline

This folder builds **Apocrypha Plus**, the printed companion volume to
[The Abrahamic Library](https://abrahamiclibrary.com/).

Both read the same modernization rules, so the printed book and the site
say the same thing in the same English.

## The relationship to the library

The library at [abrahamiclibrary.com](https://abrahamiclibrary.com/) holds
2,719 works of Judaism, Christianity and Islam in present-day American
English, drawn from the public domain. This pipeline typesets the
apocryphal and deuterocanonical books — the ones the library holds but a
reader may want in hand — into a single printed volume:

| | |
|---|---|
| **Edition** | `The Lampstand Apocrypha` (see `EDITION_NAME` in `build.py`) |
| **Source text** | The World English Bible, public domain |
| **Typefaces** | Gentium Plus and Gentium Book Plus, in `../fonts/` |
| **Output** | Print-ready PDF, and the cover files for KDP |

The book carries its own name rather than the library's: it is its own
edition of one part of the corpus, and it credits the World English Bible
as its source rather than claiming to be it.

## Building it

```sh
python3 -m bible.build              # the book, as a print-ready PDF
python3 -m bible.kdp                # the cover files
```

## What is here

| File | What it does |
|------|--------------|
| `build.py` | The book itself: front matter, running heads, page composition |
| `canon.py` | The fifteen books: their order, divisions and display names |
| `corrections.py` | Text corrections applied as the book is set |
| `design.py` | The visual scheme — margins, type sizes, ornaments |
| `enoch.py`, `eden.py`, `didache.py`, `fathers.py`, `jubilees_note.py` | The books that are not in the canon and their introductions |
| `intros.py`, `summaries.py` | Introductions and section summaries |
| `layout.py`, `typeset.py`, `render.py` | Line breaking, justification, page breaking |
| `usfm.py` | Reading USFM source files |
| `kdp.py`, `wake.py` | The cover files and the print checks |

## Terms

The **texts** this book sets are public domain, like everything in the
library: free to read, copy, print, sell and give away.

The **software** in this folder is free under the MIT License, which is in
the repository's [`LICENSE`](../LICENSE).
