"""Run the ingesters across every core.

The work is embarrassingly parallel: each book is parsed, modernized and
written on its own, into its own directory, touching nothing another book
touches. The only shared thing is the modernizer's report, and that is a pair
of counters, so each worker returns its own and the parent adds them up.

The modernization is the expensive part — a hundred million words through
several thousand regular expressions — and it is pure CPU, so processes are
what is wanted rather than threads: Python's global lock would serialise
threads back down to one core.
"""
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed


def workers(reserve=1):
    """How many processes to run: every core but one, so the machine stays usable."""
    n = os.cpu_count() or 1
    override = os.environ.get('ARCHIVE_WORKERS')
    if override and override.isdigit():
        return max(1, int(override))
    return max(1, n - reserve)


def run(fn, items, on_result=None, reserve=1, chunk_label='items'):
    """Map `fn` over `items` in parallel, in completion order.

    `fn` must be a module-level function taking one item and returning
    whatever the caller wants; it runs in another process, so it must not
    depend on anything the parent set up after import.

    -> list of results, with None dropped.
    """
    items = list(items)
    if not items:
        return []

    n = workers(reserve)
    if n == 1 or len(items) == 1:
        out = []
        for i, item in enumerate(items, 1):
            got = fn(item)
            if got is not None:
                out.append(got)
            if on_result:
                on_result(i, len(items), got)
        return out

    out = []
    done = 0
    with ProcessPoolExecutor(max_workers=n) as pool:
        futures = {pool.submit(fn, item): item for item in items}
        for future in as_completed(futures):
            done += 1
            try:
                got = future.result()
            except Exception as e:                            # noqa: BLE001
                print(f'  ! {futures[future]}: {type(e).__name__}: {e}',
                      flush=True)
                got = None
            if got is not None:
                out.append(got)
            if on_result:
                on_result(done, len(items), got)
    return out


def merge_counters(dicts):
    """Add up the {'changed': {...}, 'unresolved': {...}} a worker returns."""
    changed, unresolved, skipped = Counter(), Counter(), Counter()
    for d in dicts:
        if not d:
            continue
        changed.update(d.get('changed', {}))
        unresolved.update(d.get('unresolved', {}))
        skipped.update(d.get('skipped_as_real_words', {}))
    return {
        'changed_forms': len(changed),
        'changed_occurrences': sum(changed.values()),
        'unresolved_forms': len(unresolved),
        'unresolved_occurrences': sum(unresolved.values()),
        'changed': dict(changed.most_common()),
        'unresolved': dict(unresolved.most_common()),
        'skipped_as_real_words': dict(skipped.most_common(200)),
    }


def progress(label):
    """A callback that prints one line every 25 finished items."""
    def report(done, total, _got):
        if done % 25 == 0 or done == total:
            print(f'  {label}: {done}/{total}', flush=True)
    return report
