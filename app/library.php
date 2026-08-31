<?php
/**
 * Browsing: all three religions, one religion, or one section of one.
 *
 * A section can hold hundreds of works, so a religion page shows only the
 * opening of each section and links through to the section itself, which
 * pages. Nothing here ever renders the whole archive at once.
 */
require __DIR__ . '/inc/boot.php';

const PREVIEW  = 12;   // works shown per section on a religion page
const PER_PAGE = 60;   // works per page on a section page

$wantR = (string) ($_GET['religion'] ?? '');
$wantS = (string) ($_GET['section'] ?? '');
$page  = max(1, (int) ($_GET['p'] ?? 1));

$one = $wantR ? religion($wantR) : null;

/* find the section, when one was asked for */
$section = null;
if ($one && $wantS) {
    foreach ($one['sections'] as $s) {
        if ($s['id'] === $wantS) {
            $section = $s;
            break;
        }
    }
}

$pageTitle    = $section ? $section['name'] : ($one ? $one['name'] : 'The library');
$pageReligion = $one['id'] ?? '';
require __DIR__ . '/inc/header.php';

/** One work's card. */
function work_card(array $w): void
{ ?>
  <a class="work-card" href="<?= u('work.php', ['work' => $w['id']]) ?>">
    <b><?= e($w['title']) ?></b>
    <?php if (!empty($w['subtitle'])): ?>
      <small><?= e($w['subtitle']) ?></small>
    <?php endif; ?>
    <small>
      <?php if (!empty($w['borrowed_from'])): ?>
        <span class="tag borrowed">also in <?= e(religion_name($w['borrowed_from'])) ?></span>
      <?php endif; ?>
      <?= num($w['stats']['chapters'] ?? 0) ?> chapters<?php
      if (!empty($w['edition']['translator'])): ?> &middot; <?= e($w['edition']['translator']) ?><?php
      endif; ?>
    </small>
  </a>
<?php }
?>

<div class="wrap">

<?php if ($wantR && !$one): ?>
  <div class="hero">
    <h1>Nothing under that name</h1>
    <p class="lead">The library holds Judaism, Christianity and Islam.</p>
    <a class="btn" href="library.php">See all three</a>
  </div>

<?php elseif ($section): ?>
  <?php
  $works = $section['works'];
  $total = count($works);
  $pages = max(1, (int) ceil($total / PER_PAGE));
  $page  = min($page, $pages);
  $slice = array_slice($works, ($page - 1) * PER_PAGE, PER_PAGE);
  ?>
  <p class="crumbs">
    <a href="library.php">Library</a> &rsaquo;
    <a href="<?= u('library.php', ['religion' => $one['id']]) ?>"><?= e($one['name']) ?></a> &rsaquo;
    <?= e($section['name']) ?>
  </p>

  <div class="hero" style="padding-block:2rem 1rem">
    <h1><?= e($section['name']) ?></h1>
    <p class="lead"><?= e($section['blurb']) ?></p>
    <p class="small muted"><?= num($total) ?> works<?= $pages > 1 ? ' &middot; page ' . num($page) . ' of ' . num($pages) : '' ?></p>
  </div>

  <div class="grid-works">
    <?php foreach ($slice as $w) { work_card($w); } ?>
  </div>

  <?php if ($pages > 1): ?>
    <nav class="pagination" aria-label="Pages">
      <?php
      $base = ['religion' => $one['id'], 'section' => $section['id']];
      $from = max(1, $page - 3);
      $to   = min($pages, $from + 6);
      if ($page > 1): ?>
        <a href="<?= u('library.php', $base + ['p' => $page - 1]) ?>">&larr; Back</a>
      <?php endif;
      for ($i = $from; $i <= $to; $i++):
          if ($i === $page): ?><span aria-current="page"><?= $i ?></span>
          <?php else: ?><a href="<?= u('library.php', $base + ['p' => $i]) ?>"><?= $i ?></a><?php endif;
      endfor;
      if ($page < $pages): ?>
        <a href="<?= u('library.php', $base + ['p' => $page + 1]) ?>">Next &rarr;</a>
      <?php endif; ?>
    </nav>
  <?php endif; ?>

<?php else: ?>
  <?php $list = $one ? [$one] : catalog()['religions']; ?>

  <?php if ($one): ?>
    <p class="crumbs"><a href="library.php">Library</a> &rsaquo; <?= e($one['name']) ?></p>
  <?php endif; ?>

  <div class="hero" style="padding-block:2rem 1rem">
    <h1><?= $one ? e($one['name']) : 'The whole library' ?></h1>
    <p class="lead">
      <?= $one ? e($one['blurb'])
               : 'Everything in the archive, arranged as each tradition arranges it.' ?>
    </p>
    <p class="small muted">
      <?php $t = $one ? $one['totals'] : catalog()['totals']; ?>
      <?= num($t['works'] ?? 0) ?> works &middot;
      <?= num($t['chapters'] ?? 0) ?> chapters &middot;
      <?= num($t['words'] ?? 0) ?> words
    </p>
  </div>

  <?php foreach ($list as $r): ?>
    <?php if (!$one): ?>
      <div class="section-head">
        <h2><a href="<?= u('library.php', ['religion' => $r['id']]) ?>"><?= e($r['name']) ?></a></h2>
        <p><?= num($r['totals']['works']) ?> works</p>
      </div>
    <?php endif; ?>

    <?php foreach ($r['sections'] as $s):
        $count = count($s['works']); ?>
      <div class="section-head">
        <h2>
          <a href="<?= u('library.php', ['religion' => $r['id'], 'section' => $s['id']]) ?>">
            <?= e($s['name']) ?>
          </a>
        </h2>
        <p><?= e($s['blurb']) ?></p>
      </div>
      <div class="grid-works">
        <?php foreach (array_slice($s['works'], 0, PREVIEW) as $w) { work_card($w); } ?>
      </div>
      <?php if ($count > PREVIEW): ?>
        <p style="margin:.7rem 0 0">
          <a href="<?= u('library.php', ['religion' => $r['id'], 'section' => $s['id']]) ?>">
            All <?= num($count) ?> in <?= e($s['name']) ?> &rarr;
          </a>
        </p>
      <?php endif; ?>
    <?php endforeach; ?>
  <?php endforeach; ?>

<?php endif; ?>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
