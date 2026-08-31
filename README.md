# The Abrahamic Archive

A study library of the Jewish, Christian and Islamic source texts, in the
public domain, brought to one standard of present-day American English.

Two things live in this repository:

* **`app/`** — the study site. Plain PHP, CSS, JavaScript and HTML. No
  framework, no build step, no package manager. Drop it on any host that
  runs PHP.
* **`bible/` and `make_*.py`** — the print pipeline that typesets
  *Apocrypha Plus*, the 786-page volume. Untouched, and still builds.

Both read the same modernization rules, so the book and the site say the same
thing in the same English.

```sh
.venv/bin/python -m tools.build_all      # sources  ->  corpus
php -S 127.0.0.1:8080 -t app             # read it
```

## The site

| Page | What it does |
|---|---|
| `index.php` | The three religions, and where to start in each |
| `library.php` | Browse by religion, then by section; sections page |
| `work.php` | One work: its chapters, its edition, its rights |
| `read.php` | The reader — verse numbers, footnotes, size and layout |
| `compare.php` | The same chapter in two or more translations, side by side |
| `search.php` | Full-text search across everything |
| `about.php` | What was done to the texts, and where they came from |

`compare.php` is the reason the archive is arranged the way it is. Genesis 1
can be read in the World English Bible, the 1917 Jewish Publication Society
translation and the Douay-Rheims at once; the Qur'an's opening in Yusuf Ali,
Pickthall, Shakir and Sale.

Reading preferences and bookmarks are kept in the reader's own browser and
are never sent anywhere.

## What is in it

| Religion | Works | Words |
|---|---:|---:|
| **Judaism** | 1,070 | 17,791,024 |
| **Christianity** | 2,742 | 218,714,013 |
| **Islam** | 405 | 41,818,545 |
| **Total** | **4,217** | **278,323,582** |

| Religion | What the archive holds |
|---|---|
| **Judaism** | The Tanakh (JPS 1917), and everything Sefaria holds under a free licence — Talmud, Mishnah, Tosefta, Halakhah, Midrash, Kabbalah, liturgy — plus Maimonides, the Kuzari and Pirkei Avot |
| **Christianity** | The World English Bible with the deuterocanon and wider apocrypha, the complete Douay-Rheims, the King James Version, the Ante-Nicene and Nicene Fathers in 38 volumes, the creeds and confessions, and the Gutenberg religious shelf |
| **Islam** | The Qur'an in four English translations — Yusuf Ali, Pickthall, Shakir and Sale — with hadith (Mishcat-ul-Masabih 1809, Bukhari selections 1906), the life of the Prophet, and the Sufi literature |

The Hebrew scriptures are carried twice on purpose: once under Christianity
in Christian order and a Christian translation, once under Judaism in the
Tanakh's own order and division and a Jewish translation. Neither stands in
for the other, and `compare.php` sets them side by side.

Islam is the smallest shelf, and that is a fact about the sources rather than
about the collecting. There is no Sefaria or CCEL for Islam; the standard
modern hadith translations are still in copyright; and Project Gutenberg's
whole English Islamic holding is 141 titles. The rest came from archive.org,
one publication date at a time.

## Everything here is free to reprint

The archive takes nothing that is not public domain. Where a library offers a
better-edited modern translation under a licence forbidding commercial use —
CC-BY-NC, which most of Sefaria's best English is under — that translation is
passed over rather than included. `tools/sefaria.py` enforces this: nothing is
fetched unless its licence is Public Domain or CC0.

Sources: [eBible.org](https://ebible.org/engwebu/) (World English Bible,
dedicated to the public domain), [Sefaria](https://www.sefaria.org/),
[Project Gutenberg](https://www.gutenberg.org/), and the
[Christian Classics Ethereal Library](https://www.ccel.org/).

## The modernization

The rules are `bible/corrections.py`, written and checked by hand for the
print volume. `tools/modernize.py` wraps them so they can be applied to
sources that module never saw, in three tiers:

* **none** — left exactly as received.
* **safe** — spelling made American, formal vocabulary made plain
  (*thereof* → *of it*), archaic constructions rebuilt. Pronouns and verb
  endings untouched. This is the tier for a translation that is already
  modern, such as the World English Bible, where there is nothing archaic
  left to resolve.
* **full** — the above, plus Early Modern pronouns and verb inflection.
  *thou, thee, thy, ye* → *you, your*; *hath, doth, saith* → *has, does,
  says*; the whole *-eth* and *-est* classes.

### The one word that decides a tier

`art` is both the verb in *thou art* and the noun in *a work of art*, and a
flat rule turning it into *are* wrecks the second. That single word is why the
`safe` tier exists at all. It is now settled by context instead — `art` is the
verb only where *thou* stands beside it, before or after, as it does in
*whither art thou going* — so a modern history that quotes the King James
Bible can take the full tier: the quotation is modernized and the author's own
sentence about art is not.

### Why the verb endings are not simply stripped

Stripping `-eth` turns *abideth* into "abids" and *cometh* into "coms". The
print volume avoided this by writing out each of ~135 verbs by hand, which was
enough for one book of four translators. An archive of several hundred books
meets thousands of distinct forms, so the pass is generative — and every
candidate is checked against the system dictionary before it is accepted:

* A word that is **itself ordinary English is never touched**. That one rule
  protects *forest, harvest, priest, tempest, honest, interest, greatest,
  twentieth, death, breath* and *beneath* without naming any of them.
* A stem is used only if it is a real word, which is how *cometh* reaches
  *come* and not *com* (a dictionary word), and *sitteth* reaches *sit* and
  not *sitt*.
* A British stem the American dictionary cannot see is tried in its American
  form: *favoureth* → *favors*, *mouldeth* → *molds*, *recogniseth* →
  *recognizes*.
* **Anything unresolved is left exactly as it was** and written to
  `corpus/reports/*.json` for a person to rule on. The archive would rather
  keep an archaic word than invent one.

The hand-written table still runs first and still wins; the generative pass
only sees the long tail. A handful of forms resolve to a real but wrong word
by the general rule — *putteth* would become "putts", because *putt* is the
golf stroke — and those are listed outright in `OVERRIDE`.

Run the rules against their own tests:

```sh
python3 tools/modernize.py     # 39 cases, including everything that must NOT change
```

### Two things deliberately left

**`lest`** — removing it means rebuilding the clause around an inserted
negation, *lest he fall* → *so that he does not fall*. No substitution can do
that.

**`behold`** — only about a quarter of its uses are the exclamation; the rest
are the plain verb, which *look* destroys (*to behold the glory*).

## How it is laid out

```
app/            the site: plain PHP, CSS, JS, HTML
corpus/         what the site reads — generated, safe to delete and rebuild
  catalog.json    every work's metadata, arranged by religion and section
  works/<religion>/<work-id>/
      work.json       metadata and the chapter list
      c/<n>.json      one chapter
  search.sqlite   the FTS5 index
  reports/        what the modernizer changed, and what QA found
sources/        the raw downloads, cached; never edited
src/            the print volume's sources (USFM, the older translations)
bible/          the print pipeline, and corrections.py — the rules
tools/          the build pipeline
```

Chapters are stored one per file because a Church Fathers volume runs to five
megabytes, and the reader should never parse five megabytes to show one
chapter. `corpus/` and `sources/` sit outside `app/`, so nothing in them can
be fetched except through a page.

## The pipeline

`tools.build_all` runs the lot; any stage can be run alone.

| Stage | Does |
|---|---|
| `tools.ingest_bible` | USFM → the WEB with its deuterocanon and apocrypha |
| `tools.ingest_quran` | Four English Qur'ans, verse-aligned |
| `tools.ingest_jewish` | The Tanakh and the curated Jewish works |
| `tools.ingest_sefaria_library` | Everything else Sefaria holds free |
| `tools.ingest_gutenberg` | The Douay-Rheims, and the Gutenberg shelf |
| `tools.ingest_ccel` | 38 volumes of the Fathers |
| `tools.build_catalog` | `corpus/catalog.json` |
| `tools.build_search` | `corpus/search.sqlite` |
| `tools.qa` | Checks it, and says what is wrong |

Collecting, which only needs running when you want more:

| Tool | Does |
|---|---|
| `tools.discover_sefaria` | Walks Sefaria's whole table of contents and writes a manifest of every English text under a free licence |
| `tools.fetch_gutenberg` | Searches Gutenberg by subject and downloads what it finds |
| `tools.prune` | Lists works that are not English or have no text; `--apply` removes them |

### Four guards

Collecting at this scale sweeps in things that do not belong, so each is
refused by a rule rather than by hand.

| Guard | Refuses |
|---|---|
| `tools/sefaria.py` | Anything whose licence is not Public Domain or CC0 — which is why Sefaria's better-edited CC-BY-NC translations were passed over |
| `tools/fetch_archive.py` | Anything on archive.org without a publication date of 1929 or earlier, and any modern reprint uploaded under an old date |
| `tools/english.py` | Anything not actually English, asked of the text rather than the catalogue |
| `tools/nonfiction.py` | Fiction, drama, parody and juvenile retelling |

**Language.** Gutenberg's search returns every language and its language field
is often missing. A Spanish history of a Zaragoza castle scores 0.18 on the
English dictionary where a real English book scores 0.85 or better, so the
text is asked, not the label.

**Fiction.** A search for "arabian" or "persian poetry" returns the Arabian
Nights, Beatrix Potter, *Dubliners*, and — in quantity — the Edwardian fashion
for parodying the Rubáiyát: *of a Motor Car*, *of Bridge*, *of a Huffy
Husband*. The test is Project Gutenberg's Library of Congress subject
headings, which say plainly when a book is a story. The line is **not** verse
against prose: Rumi's *Masnavi*, Attar's *Conference of the Birds*, Saadi's
*Gulistan* and Hafiz's *Divan* are poetry and are also the primary literature
of Sufism, so they are named in an always-keep list. What goes is fiction,
parody and drama. 419 works were removed this way.

## American English throughout

Most of these sources were set by British publishers — the Edinburgh Fathers,
Rodwell's Koran, Hirschfeld's Kuzari, most of the 19th-century Gutenberg
shelf — so *colour*, *honour*, *realise*, *centre*, *travelled* and *defence*
run through millions of words.

`tools/american.py` normalises them, and the mapping is **derived, not
hand-written**. The system carries both a `british-english` and an
`american-english` word list, so:

1. Take the words in the British list that are **not** in the American list.
2. Apply the known transformations to each.
3. Keep the result only if it **is** in the American list.

Every pair is attested at both ends, and 1,451 spellings are mapped. Step 1 is
what makes it safe: *four*, *hour*, *your*, *pour*, *flour* and *devour* are
ordinary American words, so no `-our` rule can ever reach them.

Two classes need a hand-written list even so, and get one. Words the American
list *also* accepts, where American writing still prefers the other form
(*travelled* → *traveled*); and spellings older than either list
(*shew* → *show*, *connexion* → *connection*, *burthen* → *burden*). The
general rules are unsafe for these: the doubled-l rule that fixes *travelled*
would turn *filled* into *filed*, and the `ae` rule that fixes
*encyclopaedia* would wreck *archaeology*, which is spelt that way in
American English too.

```sh
python3 tools/american.py      # 12 cases, including everything that must NOT change
```

The texts stay as JSON because that is what the reader serves. SQLite is only
the search index: scanning a million verses of JSON on every search would not
answer in a useful time. `pdo_sqlite` ships with PHP, so nothing is installed
to use it.

## The print volume

Unchanged, and still the same commands:

```sh
.venv/bin/python make_apocrypha_plus.py     # block, then preflight
.venv/bin/python make_cover.py              # cover, sized from the block
.venv/bin/python -m bible.kdp build/Apocrypha-Plus.pdf
```

*Apocrypha Plus* — 786 pages, 77 works, 5.5 × 8.5 in. One volume gathering the
books outside the Protestant sixty-six that the early church read, copied and
argued over: the deuterocanon, the wider apocrypha, Enoch, the New Testament
apocrypha and the Apostolic Fathers. Text fidelity was verified by
re-assembling all 8,999 paragraphs from the typeset lines: 0 differences
across 1,842,267 characters.
