<?php
/**
 * Every work in the archive that cites one verse.
 *
 * This is the page that makes the difference between a library and a study
 * app. Isaiah 7:14 is not only a verse; it is an argument that has been had
 * for two thousand years, and the works that had it are all here.
 */
require __DIR__ . '/inc/boot.php';

$ref  = (string) ($_GET['ref'] ?? '');
$bits = explode('|', $ref);

if (count($bits) !== 3 || !preg_match('/^[a-z0-9-]+$/', $bits[0])
        || !ctype_digit($bits[1]) || !ctype_digit($bits[2])) {
    http_response_code(400);
    $pageTitle = 'Not a reference';
    require __DIR__ . '/inc/header.php';
    echo '<div class="wrap hero"><h1>Not a reference</h1>'
       . '<a class="btn" href="library.php">Open the library</a></div>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

[$book, $chapter, $verse] = $bits;
$rows  = cited_by($ref);
$label = ucwords(str_replace('-', ' ', $book));

/* The verse itself, in whichever edition of the book the archive holds. */
$text = '';
$link = '';
$db   = links_db();
if ($db) {
    $q = $db->prepare('SELECT work, label FROM book WHERE key = ?');
    if ($q && $q->execute([$book])) {
        foreach ($q->fetchAll(PDO::FETCH_ASSOC) as $b) {
            $ch = chapter($b['work'], $chapter);
            foreach ($ch['verses'] ?? [] as $v) {
                if ((string) $v['n'] === $verse) {
                    $text  = $v['text'];
                    $label = $b['label'];
                    $link  = u('read.php', ['work' => $b['work'], 'c' => $chapter]);
                    break;
                }
            }
            if ($text !== '') {
                break;
            }
        }
    }
}

$byReligion = [];
foreach ($rows as $r) {
    $byReligion[$r['religion']][] = $r;
}

$pageTitle = $label . ' ' . $chapter . ':' . $verse . ' — cited by';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero" style="padding-bottom:1rem">
  <p class="eyebrow">Cited by <?= count($rows) ?> work<?= count($rows) === 1 ? '' : 's' ?></p>
  <h1><?= e($label . ' ' . $chapter . ':' . $verse) ?></h1>
  <?php if ($text): ?>
    <blockquote class="cited-text"><?= e($text) ?></blockquote>
    <p><a class="btn alt" href="<?= e($link) ?>#v<?= e($verse) ?>">Read it in place</a></p>
  <?php endif; ?>
  <p class="lead">
    Every work here quotes this verse in its own text. The count is how many
    times &mdash; a book that returns to a verse eleven times is arguing with
    it, not mentioning it.
  </p>
</section>

<?php if (!$rows): ?>
  <section class="wrap">
    <p class="muted">Nothing in the archive cites this verse.</p>
  </section>
<?php endif; ?>

<?php foreach ($byReligion as $religion => $works): ?>
  <section class="wrap" data-religion="<?= e($religion) ?>">
    <div class="section-head">
      <h2><?= e(religion_name($religion)) ?></h2>
      <span class="muted small"><?= count($works) ?> works</span>
    </div>
    <div class="cite-list">
      <?php foreach ($works as $w): ?>
        <a class="cite-row" href="<?= e(u('work.php', ['work' => $w['work']])) ?>">
          <span class="cite-n"><?= (int) $w['n'] ?></span>
          <span class="cite-t"><?= e($w['title']) ?></span>
        </a>
      <?php endforeach; ?>
    </div>
  </section>
<?php endforeach; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
