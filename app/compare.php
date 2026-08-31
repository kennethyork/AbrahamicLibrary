<?php
/**
 * Two or more translations of the same chapter, side by side.
 *
 * This is what the archive is for: the Qur'an in four English hands, or the
 * Hebrew scriptures in a Jewish and a Christian translation, with the verse
 * numbers lined up so a difference is visible rather than remembered.
 */
require __DIR__ . '/inc/boot.php';

$id   = (string) ($_GET['work'] ?? '');
$n    = (string) ($_GET['c'] ?? '1');
$meta = work($id);

if (!$meta) {
    http_response_code(404);
    $pageTitle = 'Not found';
    require __DIR__ . '/inc/header.php';
    echo '<div class="wrap hero"><h1>No such work</h1>'
       . '<a class="btn" href="library.php">Open the library</a></div>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

/* Which editions to show: this one, plus any the reader ticked, else all. */
$available = editions_of($meta);
$chosen    = $_GET['with'] ?? null;
$chosenIds = is_array($chosen) ? $chosen : ($chosen !== null ? [$chosen] : null);

$columns = [$meta];
foreach ($available as $o) {
    if ($chosenIds === null || in_array($o['id'], $chosenIds, true)) {
        $m = work($o['id']);
        if ($m) {
            $columns[] = $m;
        }
    }
}

[$prev, $next] = neighbours($meta, $n);

$pageTitle    = $meta['title'] . ' ' . $n . ' compared';
$pageReligion = $meta['religion'];
require __DIR__ . '/inc/header.php';
?>

<div class="wrap">
  <p class="crumbs">
    <a href="library.php">Library</a> &rsaquo;
    <a href="<?= u('work.php', ['work' => $id]) ?>"><?= e($meta['title']) ?></a> &rsaquo;
    Comparing
  </p>

  <div class="hero" style="padding-block:1.5rem .5rem">
    <h1><?= e($meta['title']) ?> <?= e($n) ?></h1>
    <p class="lead"><?= count($columns) ?> translations, verse by verse.</p>
  </div>

  <?php if (count($available) > 0): ?>
    <form method="get" class="searchbar" style="margin-bottom:1.5rem">
      <input type="hidden" name="work" value="<?= e($id) ?>">
      <input type="hidden" name="c" value="<?= e($n) ?>">
      <?php foreach ($available as $o): ?>
        <label class="tag" style="padding:.4rem .7rem;text-transform:none;font-size:.82rem">
          <input type="checkbox" name="with[]" value="<?= e($o['id']) ?>"
                 <?= ($chosenIds === null || in_array($o['id'], $chosenIds, true)) ? 'checked' : '' ?>>
          <?= e($o['edition']['translator'] ?: $o['title']) ?>
        </label>
      <?php endforeach; ?>
      <button class="btn alt" type="submit" style="padding:.4rem .9rem">Show these</button>
    </form>
  <?php endif; ?>

  <div class="compare-grid">
    <?php foreach ($columns as $col):
        $cch = chapter($col['id'], $n); ?>
      <section class="compare-col">
        <h3>
          <?= e($col['edition']['translator'] ?: $col['title']) ?>
          <?php if (!empty($col['edition']['year'])): ?>
            <span class="muted small">&middot; <?= e((string) $col['edition']['year']) ?></span>
          <?php endif; ?>
        </h3>

        <?php if (!$cch): ?>
          <p class="muted small">This edition has no chapter <?= e($n) ?>.</p>
        <?php else: ?>
          <div class="scripture">
            <?php if (!empty($cch['verses'])): ?>
              <?php foreach ($cch['verses'] as $v): ?>
                <span class="v" id="<?= e($col['id'] . '-v' . preg_replace('/[^0-9a-z]/i', '', (string) $v['n'])) ?>">
                  <a class="vn" href="#<?= e($col['id'] . '-v' . preg_replace('/[^0-9a-z]/i', '', (string) $v['n'])) ?>"
                     data-ref="<?= e($col['title'] . ' ' . $n . ':' . $v['n']) ?>"><?= e($v['n']) ?></a><?= e($v['text']) ?>
                </span>
              <?php endforeach; ?>
            <?php else: ?>
              <?php foreach ($cch['blocks'] ?? [] as $b): ?>
                <?php if (($b['k'] ?? '') !== 'meta'): ?><p><?= e($b['t']) ?></p><?php endif; ?>
              <?php endforeach; ?>
            <?php endif; ?>
          </div>
        <?php endif; ?>
      </section>
    <?php endforeach; ?>
  </div>

  <nav class="pager">
    <?php if ($prev !== null): ?>
      <a rel="prev" href="<?= u('compare.php', ['work' => $id, 'c' => $prev]) ?>">&larr; <?= e($prev) ?></a>
    <?php else: ?><span></span><?php endif; ?>
    <a href="<?= u('read.php', ['work' => $id, 'c' => $n]) ?>">Read this one alone</a>
    <?php if ($next !== null): ?>
      <a rel="next" href="<?= u('compare.php', ['work' => $id, 'c' => $next]) ?>"><?= e($next) ?> &rarr;</a>
    <?php else: ?><span></span><?php endif; ?>
  </nav>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
