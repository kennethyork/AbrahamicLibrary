"""Talking to Sefaria, and only ever taking what is free to reprint.

Sefaria carries many translations under licences this archive cannot use —
CC-BY-NC above all, which forbids the selling the rest of the project is
built to allow. `pd_versions()` is the gate: nothing is fetched unless its
licence is Public Domain or CC0.
"""
import json
import re
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from tools import corpus

CACHE = os.path.join(corpus.ROOT, 'sources', 'collector', 'sefaria')
API = 'https://www.sefaria.org/api'
UA = 'AbrahamicArchive/1.0 (public-domain text collection)'

FREE = {'public domain', 'cc0'}

# Copyright in the United States runs ninety-five years from publication, so
# in 2026 everything published through 1930 is free.
PD_CUTOFF = 1930
RE_YEAR = re.compile(r'\b(1[5-9]\d\d|20[0-2]\d)\b')


def dated_after_cutoff(version_title):
    """Does the version name its own publication, and is it too recent?

    Sefaria's editions name themselves — `Loeb Classical Library, Harvard
    University Press, 1941`, `The Mishneh Torah by Maimonides. trans. by
    Moses Hyamson, 1937-1949`. Where they do, the date is evidence and it
    can contradict the licence field beside it.
    """
    years = [int(y) for y in RE_YEAR.findall(version_title or '')]
    return bool(years) and max(years) > PD_CUTOFF

_last = [0.0]


def _get(url, tries=3):
    """One GET, politely paced."""
    for attempt in range(tries):
        wait = 0.34 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.loads(fh.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            # 400 is Sefaria's answer to a version title it does not hold,
            # and 404 to a ref it does not hold: both mean "nothing here".
            if e.code in (400, 404):
                return None
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == tries - 1:
                return None
            time.sleep(2 * (attempt + 1))
    return None


def _cache_path(kind, key):
    return os.path.join(CACHE, kind, corpus.slugify(key) + '.json')


def cached(kind, key, fetch):
    path = _cache_path(kind, key)
    hit = corpus.read_json(path)
    if hit is not None:
        return hit
    got = fetch()
    if got is not None:
        corpus.write_json(path, got)
    return got


def versions(title):
    """Every version Sefaria holds for a title."""
    def fetch():
        url = f'{API}/texts/versions/{urllib.parse.quote(title)}'
        got = _get(url)
        if isinstance(got, dict):
            got = got.get('versions', [])
        return got if isinstance(got, list) else []
    return cached('versions', title, fetch) or []


# Sefaria files a German or French translation under language 'en' when it is
# a translation *of* the Hebrew held alongside the English; the version title
# is what actually says which language it is.
RE_LANG_TAG = re.compile(r'\[(\w{2})\]\s*$')


def pd_versions(title):
    """English versions that are public domain or CC0, best first."""
    out = []
    for v in versions(title):
        lic = str(v.get('license', '')).strip().lower()
        actual = v.get('actualLanguage')
        lang = actual or v.get('language')
        tag = RE_LANG_TAG.search(v.get('versionTitle') or '')
        if tag and tag.group(1).lower() != 'en':
            continue
        # `Public Domain` on a 1941 Harvard University Press book is a
        # claim that the copyright expired, and the date on the cover says
        # it has not. `CC0` is different in kind: a dedication the rights
        # holder made, which no date can contradict. So past the cutoff
        # only CC0 counts — and where a text has both, as most of these do,
        # refusing the dated one falls back to Sefaria's own free
        # translation rather than losing the book.
        if lic == 'public domain' and dated_after_cutoff(v.get('versionTitle')):
            continue
        if lang == 'en' and lic in FREE:
            out.append({
                'versionTitle': v.get('versionTitle'),
                'license': v.get('license'),
                'versionSource': v.get('versionSource') or v.get('versionUrl') or '',
                'priority': v.get('priority') or 0,
                'status': v.get('status') or '',
            })
    # a locked, higher-priority version is the better edition
    out.sort(key=lambda v: (-float(v['priority'] or 0),
                            v['license'].lower() != 'public domain'))
    return out


def text(title, version_title):
    """The whole book, as Sefaria's nested lists."""
    def fetch():
        v = urllib.parse.quote(f'english|{version_title}', safe='')
        url = f'{API}/v3/texts/{urllib.parse.quote(title)}?version={v}'
        got = _get(url)
        if not got:
            return None
        vers = (got.get('versions') or [{}])[0]
        return {
            'title': got.get('title') or title,
            'book': got.get('book') or title,
            'versionTitle': vers.get('versionTitle'),
            'license': vers.get('license'),
            'versionSource': vers.get('versionSource', ''),
            'text': vers.get('text'),
        }
    return cached('text', f'{title}--{version_title}', fetch)


def index(title):
    return cached('index', title, lambda: _get(f'{API}/index/{urllib.parse.quote(title)}'))


def toc():
    """Sefaria's whole table of contents."""
    return cached('toc', 'toc', lambda: _get(f'{API}/index/'))
