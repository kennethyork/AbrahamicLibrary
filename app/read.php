<?php
require __DIR__ . '/inc/boot.php';

$id   = (string) ($_GET['work'] ?? '');
$n    = (string) ($_GET['c'] ?? '1');
$meta = work($id);
$ch   = $meta ? chapter($id, $n) : null;

if (!$meta || !$ch) {
    http_response_code(404);
    $pageTitle = 'Not found';
    require __DIR__ . '/inc/header.php';
    echo '<div class="wrap hero"><h1>No such chapter</h1>'
       . '<p class="lead">The library lists everything the archive holds.</p>'
       . '<a class="btn" href="library.php">Open the library</a></div>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

[$prev, $next] = neighbours($meta, $n);
$others  = editions_of($meta);
$title   = $ch['title'] ?: ('Chapter ' . $n);
$refBase = $meta['title'] . ' ' . $n;

$pageTitle    = $meta['title'] . ' ' . $n;
$pageReligion = $meta['religion'];
require __DIR__ . '/inc/header.php';
?>

<div class="wrap">
  <p class="crumbs">
    <a href="library.php">Library</a> &rsaquo;
    <a href="<?= u('library.php', ['religion' => $meta['religion']]) ?>"><?= e(religion_name($meta['religion'])) ?></a> &rsaquo;
    <a href="<?= u('work.php', ['work' => $id]) ?>"><?= e($meta['title']) ?></a>
  </p>
</div>

<article class="wrap reader" data-reader
         data-work="<?= e($id) ?>" data-c="<?= e($n) ?>"
         data-title="<?= e($meta['title']) ?>"
         data-religion="<?= e($meta['religion']) ?>"
         data-verses="1">
  <div class="reader-tools">
    <button type="button" data-size="-1" aria-label="Smaller text">A&minus;</button>
    <button type="button" data-size="1" aria-label="Larger text">A+</button>
    <button type="button" data-flowing aria-pressed="false">Flowing</button>
    <button type="button" data-bookmark="<?= e($meta['title'] . ' ' . $n) ?>">Bookmark</button>
    <?php if ($others): ?>
      <a class="btn alt" style="padding:.3rem .7rem;font-size:.8rem"
         href="<?= u('compare.php', ['work' => $id, 'c' => $n]) ?>">Compare</a>
    <?php endif; ?>
  </div>

  <header class="reader-head">
    <h1><?= e($meta['title']) ?></h1>
    <p class="sub">
      <?= e($title) ?>
      <?php if (!empty($meta['edition']['translator'])): ?>
        &middot; <?= e($meta['edition']['translator']) ?>
      <?php endif; ?>
    </p>
  </header>

  <?php foreach ($ch['blocks'] ?? [] as $b): ?>
    <?php if (($b['k'] ?? '') === 'meta'): ?>
      <p class="chapter-meta"><?= e($b['t']) ?></p>
    <?php endif; ?>
  <?php endforeach; ?>

  <div class="reader-body" data-body>
  <div class="scripture">
    <?php
    $notes = [];

    /* Section headings carry the verse they open, so they can be put back
       in their place as the verses are written out. */
    $headings = [];
    foreach ($ch['blocks'] ?? [] as $b) {
        if (($b['k'] ?? '') === 'h' && isset($b['at'])) {
            $headings[(string) $b['at']][] = $b['t'];
        }
    }

    if (!empty($ch['verses'])):
        foreach ($ch['verses'] as $v):
            $vid = 'v' . preg_replace('/[^0-9a-z]/i', '', (string) $v['n']);
            foreach ($v['notes'] ?? [] as $note) {
                $notes[] = $note + ['anchor' => $vid];
            }
            foreach ($headings[(string) $v['n']] ?? [] as $h): ?>
              <h3 class="head"><?= e($h) ?></h3>
            <?php endforeach; ?>
        <span class="v" id="<?= e($vid) ?>"
              data-work="<?= e($id) ?>" data-c="<?= e($n) ?>" data-v="<?= e($v['n']) ?>"
              data-ref="<?= e($refBase . ':' . $v['n']) ?>">
          <a class="vn" href="#<?= e($vid) ?>" data-ref="<?= e($refBase . ':' . $v['n']) ?>"><?= e($v['n']) ?></a><?= e($v['text']) ?>
        </span>
      <?php endforeach;
    else:
        $pn = 1;
        foreach ($ch['blocks'] ?? [] as $b):
            $kind = $b['k'] ?? 'p';
            if ($kind === 'h'): ?>
              <h3 class="head"><?= e($b['t']) ?></h3>
            <?php elseif ($kind !== 'meta'): ?>
              <?php /* A prose work has no verses to key a highlight to, so the
                       paragraph is the unit instead. Its number is its position
                       in the chapter, which is stable as long as the chapter is
                       — the same promise the verse numbers make. */ ?>
              <p class="pb" id="p<?= $pn ?>"
                 data-work="<?= e($id) ?>" data-c="<?= e($n) ?>" data-v="p<?= $pn ?>"
                 data-ref="<?= e($refBase) ?> &para;<?= $pn ?>"><?= e($b['t']) ?></p>
              <?php $pn++;
            endif;
        endforeach;
    endif;
    ?>
  </div>

  <?php /* The two margins. A study Bible puts the editor's notes on one side
           and leaves the other for the reader's pencil, and that is what these
           are: the translator's notes to the left of the column, your own to
           the right. Each one is pinned level with the verse it belongs to by
           assets/study.js; where the window is too narrow for margins they
           fall back under the text, in order, and nothing is lost. */ ?>
  <aside class="margin margin-a" data-margin="source"
         aria-label="Notes on the text"<?= $notes ? '' : ' hidden' ?>>
    <h3 class="margin-h">Notes on the text</h3>
    <?php foreach ($notes as $i => $note): ?>
      <div class="mnote" data-for="<?= e($note['anchor']) ?>">
        <b><?= e($note['ref'] ?? '') ?></b>
        <span><?= e($note['text']) ?></span>
      </div>
    <?php endforeach; ?>
  </aside>

  <aside class="margin margin-b" data-margin="mine" aria-label="Your notes" hidden>
    <h3 class="margin-h">Your notes</h3>
  </aside>
  </div>

  <nav class="pager">
    <?php if ($prev !== null): ?>
      <a rel="prev" href="<?= u('read.php', ['work' => $id, 'c' => $prev]) ?>">&larr; <?= e($prev) ?></a>
    <?php else: ?><span></span><?php endif; ?>

    <a href="<?= u('work.php', ['work' => $id]) ?>">All chapters</a>

    <?php if ($next !== null): ?>
      <a rel="next" href="<?= u('read.php', ['work' => $id, 'c' => $next]) ?>"><?= e($next) ?> &rarr;</a>
    <?php else: ?><span></span><?php endif; ?>
  </nav>

  <p class="small muted center" style="margin-top:2rem">
    <?= e($meta['edition']['translation'] ?: 'Public domain text') ?>.
    <?= e(tier_label($meta['edition']['modernization'] ?? null)) ?> &mdash;
    <a href="about.php">what that means</a>.
  </p>
</article>

<!-- The verse action bar. Hidden until a verse is chosen; the whole thing
     is driven by assets/study.js and stores nothing off this device. -->
<div class="vbar" data-vbar hidden role="toolbar" aria-label="Chosen verses">
  <div class="wrap vbar-in">
    <span class="vbar-ref" data-vbar-ref></span>
    <span class="hl-swatches">
      <?php foreach (HIGHLIGHTS as $key => $label): ?>
        <button type="button" class="sw sw-<?= e($key) ?>" data-hl="<?= e($key) ?>"
                title="<?= e($label) ?>"><span class="sr"><?= e($label) ?></span></button>
      <?php endforeach; ?>
      <button type="button" class="sw sw-none" data-hl="" title="Clear highlight">
        <span class="sr">Clear highlight</span>
      </button>
    </span>
    <button type="button" data-act="note">Note</button>
    <button type="button" data-act="copy">Copy</button>
    <button type="button" data-act="share">Link</button>
    <?php if ($others): ?>
      <button type="button" data-act="compare"
              data-href="<?= e(u('compare.php', ['work' => $id, 'c' => $n])) ?>">Compare</button>
    <?php endif; ?>
    <button type="button" data-act="close" aria-label="Done">&times;</button>
  </div>
  <form class="vbar-note" data-note-form hidden>
    <label class="sr" for="note-text">Your note</label>
    <textarea id="note-text" rows="3" placeholder="What do you want to remember about this?"></textarea>
    <div class="vbar-note-actions">
      <button type="submit" class="btn">Save note</button>
      <button type="button" class="btn alt" data-note-delete>Delete</button>
      <button type="button" class="btn alt" data-note-cancel>Cancel</button>
    </div>
  </form>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
