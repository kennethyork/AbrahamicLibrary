<?php
/** One reading plan, day by day. Progress is the reader's own and is kept
 *  in their browser; the server has no idea who is on which day. */
require __DIR__ . '/inc/boot.php';

$id   = (string) ($_GET['id'] ?? '');
$plan = plan($id);

if (!$plan) {
    http_response_code(404);
    $pageTitle = 'Not found';
    require __DIR__ . '/inc/header.php';
    echo '<div class="wrap hero"><h1>No such plan</h1>'
       . '<a class="btn" href="plans.php">See the plans</a></div>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

$pageTitle    = $plan['name'];
$pageReligion = $plan['religion'] ?? '';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero" style="padding-bottom:1rem">
  <p class="crumbs"><a href="plans.php">Reading plans</a></p>
  <h1><?= e($plan['name']) ?></h1>
  <p class="lead"><?= e($plan['blurb']) ?></p>
  <div class="actions">
    <a class="btn" href="#" data-plan-jump>Go to today’s reading</a>
    <button class="btn alt" type="button" data-plan-reset>Start over</button>
    <button class="btn alt" type="button" data-plan-save hidden>Save for offline</button>
  </div>
  <p class="plan-progress big" data-plan-progress>
    <span class="bar"><span></span></span>
    <em></em>
  </p>
</section>

<section class="wrap" data-plan="<?= e($plan['id']) ?>">
  <ol class="plan-days">
    <?php foreach ($plan['days'] as $i => $d): ?>
      <li class="plan-day" data-day="<?= $i ?>" id="day<?= $i + 1 ?>">
        <label class="plan-tick">
          <input type="checkbox" data-plan-done="<?= $i ?>">
          <span class="sr">Mark day <?= $i + 1 ?> as read</span>
        </label>
        <div class="plan-body">
          <p class="plan-n">Day <?= $i + 1 ?></p>
          <h2><?= e($d['title']) ?></h2>
          <p class="plan-links">
            <?php foreach ($d['readings'] as $r): ?>
              <a href="<?= e(u('read.php', ['work' => $r['work'], 'c' => $r['c']])) ?>">
                <?= e($r['title'] . ' ' . $r['c']) ?></a>
            <?php endforeach; ?>
          </p>
        </div>
      </li>
    <?php endforeach; ?>
  </ol>
</section>

<script src="assets/plan.js" defer></script>
<?php require __DIR__ . '/inc/footer.php'; ?>
