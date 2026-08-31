<?php
require __DIR__ . '/inc/boot.php';

$cat    = catalog();
$totals = $cat['totals'] ?? [];
$pageTitle = '';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero">
  <p class="eyebrow">Judaism &middot; Christianity &middot; Islam</p>
  <h1>Read the sources, in plain modern English.</h1>
  <p class="lead">
    The scriptures of the three Abrahamic religions, with the literature that
    grew around them &mdash; every one of them in the public domain, and every
    one brought to present-day American English by the same rules, so you can
    read across a tradition without stumbling over four centuries of shifting
    grammar.
  </p>

  <div class="actions">
    <a class="btn" href="library.php">Open the library</a>
    <a class="btn alt" href="about.php">How the texts were prepared</a>
  </div>

  <div class="figures">
    <div class="figure"><strong><?= num($totals['works'] ?? 0) ?></strong><span>works</span></div>
    <div class="figure"><strong><?= num($totals['chapters'] ?? 0) ?></strong><span>chapters</span></div>
    <div class="figure"><strong><?= num($totals['verses'] ?? 0) ?></strong><span>verses and sections</span></div>
    <div class="figure"><strong><?= num($totals['words'] ?? 0) ?></strong><span>words</span></div>
  </div>
</section>

<?php $vod = verse_of_the_day(); if ($vod): ?>
<section class="wrap">
  <article class="daily" data-r="<?= e($vod['religion']) ?>">
    <p class="eyebrow">Today</p>
    <blockquote><?= e($vod['text']) ?></blockquote>
    <p class="daily-ref">
      <a href="<?= e(u('read.php', ['work' => $vod['work'], 'c' => $vod['c']])) ?>#v<?= e(preg_replace('/[^0-9a-z]/i', '', $vod['v'])) ?>"><?= e($vod['ref']) ?></a>
      <?php if ($vod['edition']): ?><span class="muted"> &middot; <?= e($vod['edition']) ?></span><?php endif; ?>
    </p>
  </article>
</section>
<?php endif; ?>

<section class="wrap" data-continue hidden>
  <div class="section-head">
    <h2>Pick up where you left off</h2>
    <a class="more" href="me.php">Everything you have saved &rarr;</a>
  </div>
  <div class="grid-works" data-continue-list></div>
</section>

<section class="wrap">
  <div class="section-head">
    <h2>Reading plans</h2>
    <a class="more" href="plans.php">All plans &rarr;</a>
  </div>
  <div class="grid-works">
    <?php foreach (array_slice(plans(), 0, 3) as $p): ?>
      <a class="work-card plan-card" href="<?= e(u('plan.php', ['id' => $p['id']])) ?>"
         <?= $p['religion'] ? 'data-r="' . e($p['religion']) . '"' : '' ?>
         data-plan-card="<?= e($p['id']) ?>" data-days="<?= count($p['days']) ?>">
        <b><?= e($p['name']) ?></b>
        <span class="plan-blurb"><?= e($p['blurb']) ?></span>
        <small><?= count($p['days']) ?> days</small>
        <span class="plan-progress" data-plan-progress hidden>
          <span class="bar"><span></span></span><em></em>
        </span>
      </a>
    <?php endforeach; ?>
  </div>
</section>

<section class="wrap">
  <div class="three">
    <?php foreach ($cat['religions'] as $r): ?>
      <a class="faith" data-r="<?= e($r['id']) ?>" href="<?= u('library.php', ['religion' => $r['id']]) ?>">
        <h2><?= e($r['name']) ?></h2>
        <p><?= e($r['blurb']) ?></p>
        <span class="count">
          <?= num($r['totals']['works']) ?> works &middot;
          <?= num($r['totals']['words']) ?> words
        </span>
      </a>
    <?php endforeach; ?>
  </div>
</section>

<section class="wrap">
  <div class="section-head">
    <h2>Where to start</h2>
    <p>The texts each tradition opens with.</p>
  </div>
  <div class="grid-works">
    <?php
    $starts = [
        ['jps-genesis', 'The Torah opens', '1'],
        ['webu-jhn', 'The fourth gospel', '1'],
        ['quran-yusufali', 'The Opening', '1'],
        ['webu-gen', 'In the beginning', '1'],
        ['sef-pirkei-avot', 'The Fathers', '1'],
        ['webu-psa', 'The Psalms', '23'],
    ];
    foreach ($starts as [$wid, $why, $ch]):
        $m = work($wid);
        if (!$m) continue; ?>
      <a class="work-card" href="<?= u('read.php', ['work' => $wid, 'c' => $ch]) ?>">
        <b><?= e($m['title']) ?><?= $ch !== '1' ? ' ' . e($ch) : '' ?></b>
        <small><?= e($why) ?> &middot; <?= e($m['edition']['translator'] ?: religion_name($m['religion'])) ?></small>
      </a>
    <?php endforeach; ?>
  </div>
</section>

<section class="wrap">
  <div class="section-head">
    <h2>Your bookmarks</h2>
    <p>Kept in this browser only &mdash; never sent anywhere.</p>
  </div>
  <div data-bookmark-list></div>
</section>

<script src="assets/plan.js" defer></script>
<?php require __DIR__ . '/inc/footer.php'; ?>
