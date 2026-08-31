<?php
/** The reading plans on offer. */
require __DIR__ . '/inc/boot.php';

$plans = plans();
$pageTitle = 'Reading plans';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero" style="padding-bottom:1rem">
  <p class="eyebrow">A day at a time</p>
  <h1>Reading plans</h1>
  <p class="lead">
    A plan is a sequence of days and a few chapters in each. Nothing signs you
    up and nothing expires &mdash; the ticks are kept in this browser, so you
    can start one, leave it for a month and pick it up where you were.
  </p>
</section>

<section class="wrap">
  <div class="grid-works">
    <?php foreach ($plans as $p): ?>
      <a class="work-card plan-card" href="<?= e(u('plan.php', ['id' => $p['id']])) ?>"
         <?= $p['religion'] ? 'data-r="' . e($p['religion']) . '"' : '' ?>
         data-plan-card="<?= e($p['id']) ?>" data-days="<?= count($p['days']) ?>">
        <b><?= e($p['name']) ?></b>
        <span class="plan-blurb"><?= e($p['blurb']) ?></span>
        <small><?= count($p['days']) ?> days &middot;
          <?= array_sum(array_map(fn($d) => count($d['readings']), $p['days'])) ?> readings</small>
        <span class="plan-progress" data-plan-progress hidden>
          <span class="bar"><span></span></span>
          <em></em>
        </span>
      </a>
    <?php endforeach; ?>
  </div>
</section>

<script src="assets/plan.js" defer></script>
<?php require __DIR__ . '/inc/footer.php'; ?>
