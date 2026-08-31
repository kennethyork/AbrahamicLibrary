<?php
require __DIR__ . '/inc/boot.php';

$id   = (string) ($_GET['work'] ?? '');
$meta = work($id);

if (!$meta) {
    http_response_code(404);
    $pageTitle = 'Not found';
    require __DIR__ . '/inc/header.php';
    echo '<div class="wrap hero"><h1>No such work</h1>'
       . '<p class="lead">It may have been renamed. The library lists everything.</p>'
       . '<a class="btn" href="library.php">Open the library</a></div>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

$others    = editions_of($meta);
$named     = false;
foreach ($meta['chapters'] as $c) {
    if ($c['title'] !== '' && !preg_match('/^Chapter /', $c['title'])) {
        $named = true;
        break;
    }
}

$pageTitle    = $meta['title'];
$pageReligion = $meta['religion'];
require __DIR__ . '/inc/header.php';
?>

<div class="wrap">
  <p class="crumbs">
    <a href="library.php">Library</a> &rsaquo;
    <a href="<?= u('library.php', ['religion' => $meta['religion']]) ?>"><?= e(religion_name($meta['religion'])) ?></a> &rsaquo;
    <?= e($meta['section_name'] ?? '') ?>
  </p>

  <div class="work-head">
    <div>
      <h1><?= e($meta['title']) ?></h1>
      <?php if (!empty($meta['subtitle'])): ?>
        <p class="lead" style="margin-bottom:1rem"><?= e($meta['subtitle']) ?></p>
      <?php endif; ?>

      <div class="actions">
        <a class="btn" href="<?= u('read.php', ['work' => $id, 'c' => $meta['chapters'][0]['n'] ?? '1']) ?>">
          Start reading
        </a>
        <?php if ($others): ?>
          <a class="btn alt" href="<?= u('compare.php', ['work' => $id, 'c' => $meta['chapters'][0]['n'] ?? '1']) ?>">
            Compare translations
          </a>
        <?php endif; ?>
        <a class="btn alt" href="<?= u('search.php', ['q' => '', 'work' => $id]) ?>">Search inside</a>
      </div>

      <?php
      /* A Fathers volume can run to a thousand named sections, so the
         contents page pages rather than printing all of them at once. */
      $all     = $meta['chapters'];
      $total   = count($all);
      $perPage = $named ? 60 : 400;
      $pages   = max(1, (int) ceil($total / $perPage));
      $page    = min(max(1, (int) ($_GET['p'] ?? 1)), $pages);
      $slice   = array_slice($all, ($page - 1) * $perPage, $perPage);
      ?>
      <div class="section-head">
        <h2><?= $named ? 'Contents' : 'Chapters' ?></h2>
        <p>
          <?= num($total) ?> in all<?= $pages > 1 ? ' &middot; page ' . num($page) . ' of ' . num($pages) : '' ?>
        </p>
      </div>

      <?php if ($named): ?>
        <div class="grid-works">
          <?php foreach ($slice as $c): ?>
            <a class="work-card" href="<?= u('read.php', ['work' => $id, 'c' => $c['n']]) ?>">
              <b><?= e($c['title'] ?: $c['n']) ?></b>
              <small><?= $c['verses'] ? num($c['verses']) . ' verses' : 'Section ' . e($c['n']) ?></small>
            </a>
          <?php endforeach; ?>
        </div>
      <?php else: ?>
        <div class="chapters">
          <?php foreach ($slice as $c): ?>
            <a href="<?= u('read.php', ['work' => $id, 'c' => $c['n']]) ?>"><?= e($c['n']) ?></a>
          <?php endforeach; ?>
        </div>
      <?php endif; ?>

      <?php if ($pages > 1): ?>
        <nav class="pagination" aria-label="Contents pages">
          <?php
          $from = max(1, $page - 3);
          $to   = min($pages, $from + 6);
          if ($page > 1): ?>
            <a href="<?= u('work.php', ['work' => $id, 'p' => $page - 1]) ?>">&larr; Back</a>
          <?php endif;
          for ($i = $from; $i <= $to; $i++):
              if ($i === $page): ?><span aria-current="page"><?= $i ?></span>
              <?php else: ?><a href="<?= u('work.php', ['work' => $id, 'p' => $i]) ?>"><?= $i ?></a><?php endif;
          endfor;
          if ($page < $pages): ?>
            <a href="<?= u('work.php', ['work' => $id, 'p' => $page + 1]) ?>">Next &rarr;</a>
          <?php endif; ?>
        </nav>
      <?php endif; ?>
    </div>

    <aside class="panel factbox">
      <h3>This edition</h3>
      <dl>
        <?php if (!empty($meta['edition']['translation'])): ?>
          <dt>Translation</dt><dd><?= e($meta['edition']['translation']) ?></dd>
        <?php endif; ?>
        <?php if (!empty($meta['edition']['translator'])): ?>
          <dt>Translator</dt><dd><?= e($meta['edition']['translator']) ?></dd>
        <?php endif; ?>
        <?php if (!empty($meta['edition']['year'])): ?>
          <dt>Published</dt><dd><?= e((string) $meta['edition']['year']) ?></dd>
        <?php endif; ?>
        <dt>English</dt><dd><?= e(tier_label($meta['edition']['modernization'] ?? null)) ?></dd>
        <dt>Length</dt>
        <dd><?= num($meta['stats']['chapters']) ?> chapters,
            <?= num($meta['stats']['words']) ?> words</dd>
        <dt>Rights</dt>
        <dd>
          <?= e($meta['rights']['statement'] ?? 'Public domain.') ?>
          <?php if (!empty($meta['rights']['source_url'])): ?>
            <br><a href="<?= e($meta['rights']['source_url']) ?>" rel="noopener nofollow">Source</a>
          <?php endif; ?>
        </dd>
      </dl>

      <?php if ($others): ?>
        <h3 style="margin-top:1.2rem">Also translated by</h3>
        <div class="chapters named">
          <?php foreach ($others as $o): ?>
            <a href="<?= u('work.php', ['work' => $o['id']]) ?>">
              <?= e($o['edition']['translator'] ?: $o['id']) ?>
            </a>
          <?php endforeach; ?>
        </div>
      <?php endif; ?>

      <p class="small muted" style="margin-top:1rem">
        <?= e(tier_label($meta['edition']['modernization'] ?? null)) ?>.
        <a href="about.php">What that changed</a>.
      </p>
    </aside>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
