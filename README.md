# The Abrahamic Library

The scriptures of Judaism, Christianity and Islam, with the literature that
grew around them — every one of them in the public domain, and every one
brought to present-day American English by the same rules, so you can read
across a tradition without stumbling over four centuries of shifting
grammar.

**2,719 works · 232,545 chapters · 273,072 verses and sections · 223,907,542 words.**

**Read it at [abrahamiclibrary.com](https://abrahamiclibrary.com/)** — or at
[kennethyork.github.io/AbrahamicLibrary](https://kennethyork.github.io/AbrahamicLibrary/)
until the domain's DNS is pointed here.

## What this repository is

The repository is the **built library**, published by GitHub Pages from the
`docs/` folder. There is no PHP, no database, no server, and no build step
on the reader's side: every page is drawn in the browser from compressed
data files that a plain file host can serve.

The whole library is **38 files** in `docs/`.

### What is where

| Path | What it is |
|------|------------|
| `docs/index.html` | The home page: the figures, a verse for the day, three ways in |
| `docs/library.html` | Every view of the library — all three religions, one, or one section. The address says which: `library.html?religion=judaism` |
| `docs/work.html` | One work's page — `work.html?work=kjv-bible` |
| `docs/read.html` | The reader — `read.html?work=jps-genesis&c=1` |
| `docs/compare.html` | One chapter in every translation — `compare.html?work=quran-pickthall&c=1` |
| `docs/search.html` | A reference, a word, or a title — `search.html?q=mercy` |
| `docs/strongs.html` | The word study — `strongs.html?q=H430` |
| `docs/cited.html` | Who quotes a verse — `cited.html?ref=isaiah\|7\|14` |
| `docs/plans.html`, `docs/plan.html` | 115 reading plans — `plan.html?id=torah` |
| `docs/about.html`, `docs/me.html` | What was done to the texts; your own highlights and notes |
| `docs/corpus/index.json` | Every work id, with where its metadata sits in `meta.bin` |
| `docs/corpus/meta.bin` | One gzip member per work: its metadata, its tally of modernized verses, and each chapter's place in a bundle |
| `docs/corpus/<religion>/b*.bin` | The chapter text itself, gzipped members read by byte range |
| `docs/data/bundle*.bin` | The catalog, the plans, the Strong's dictionaries, the interlinear, the citation index and the search index |
| `docs/data/bundle.json.gz` | Where each part of the data bundles lives |
| `docs/assets/site.js` | Every script the library has, in one file |
| `docs/assets/style.css` | The stylesheet |
| `docs/sw.js`, `docs/manifest.json`, `docs/offline.html` | The service worker, the web-app manifest, the offline page |
| `docs/CNAME` | The custom domain GitHub Pages answers for |

Also here, and not used by the published library:

- **`LICENSE`** — MIT, covering all the software in this repository.
- **`bible/`** — the print pipeline that typesets *Apocrypha Plus*, the
  printed companion volume. Its own README is in the folder.
- **`fonts/`** — Gentium Plus and Gentium Book Plus, the typefaces the book
  is set in, under the SIL Open Font License. Their README says so.
- **`app/`** — the original PHP application the site was ported from,
  kept for reference. The published library does not run PHP.

Nothing on the site talks to a server beyond asking for files. Highlights,
notes, bookmarks, reading positions and plan progress live in the browser's
own storage and are never sent anywhere; **Mine** hands them back as a file
on request.

## Reading it

- **Home** — the library's figures, a verse for the day, the reading plans,
  and three ways in (Judaism, Christianity, Islam).
- **The library** — every work, arranged as each tradition arranges it. The
  complete Bibles and complete Qur'ans stand at the top of the whole-library
  view; the sections follow.
- **Reader** — a chapter with the translator's notes in one margin and
  yours in the other, a *Flowing* toggle, *As printed* for the verses the
  modernizer changed (a work's page offers it too, opening the book in that
  mode and keeping the choice as you read on), highlighters, notes, copying
  and linking.
- **Compare** — the same chapter in every translation the library holds,
  verse by verse.
- **Word study** — an English word and the Hebrew and Greek standing behind
  it, or an interlinear of the original for a chapter that has one.
- **Search** — a reference (`John 3:16`), a word, or a book title. Every
  word of every work is indexed: *mercy* finds 46,666 places.
- **Cited by** — every work in the library that quotes a given verse, which
  is where a library becomes a study.
- **Plans** — 115 reading plans; the ticks are kept in your browser.

## How the data is packed

Two ideas make a two-gigabyte library fit a static host in 38 files.

**Chapters are read by byte range.** GitHub Pages answers a `Range` request
with a 206 and exactly those bytes, so the corpus becomes eleven files:
an index and a metadata bundle are fetched whole, and a chapter comes out
of its religion's bundle with one request of about 2 KB. Bundles roll over
before 90 MB, so no file approaches the host's 100 MB limit.

**The search index matches SQLite FTS5 exactly.** The library used to
search with FTS5 on a PHP host; the shipped index tokenizes and stems as
FTS5's `porter unicode61` did — apostrophes separate words, accents are
folded, then Porter — and was checked term by term against the original
until the two agreed for a dozen words (`mercy`, `god`, `israel`,
`covenant`, …). The postings are varint unit ids and counts, sharded by
term, so a query fetches one shard.

## Rebuilding

The build tools live in the source project that produced `docs/`; this
repository carries the built result. For reference, the pipeline is:

    python3 -m tools.build_all            # everything, in order
    python3 -m tools.pack_corpus          # corpus/ -> docs/corpus/**   (chapter bundles)
    python3 -m tools.build_search_index   #         -> docs/data/search/**
    python3 -m tools.build_bundles        # data/** -> docs/data/bundle*.bin
    python3 -m tools.build_assets         # assets/** -> docs/assets/site.js
    python3 -m tools.build_pages          #         -> docs/*.html

`build_all` skips the two slow steps when their output is already newer
than the corpus, so changing a page costs seconds rather than an hour.

## Rights

- The **texts** are public domain, and so are these modernized editions of
  them: free to read, copy, print, sell and give away, no permission or
  attribution needed. Each work's page names its source and its rights;
  `about.html` lists every rights statement in the library.
- The **Strong's dictionaries** are James Strong, *The Exhaustive
  Concordance of the Bible* (1894), public domain, scanned by archive.org
  and transcribed by Open Scriptures (CC BY-SA).
- The **Hebrew interlinear** is the Open Scriptures Morphological Hebrew
  Bible (the Westminster Leningrad Codex with morphology), CC BY 4.0.
- The **Greek interlinear** is the Statistical Restoration Greek New
  Testament, provided by `scrollmapper/bible_databases`, CC BY 4.0.
- The **software** is free under the [MIT License](LICENSE): use it, change
  it, publish it, sell it, keep the notice with it.
