<?php
/**
 * A concordance over the whole archive.
 *
 * Search answers "where does this phrase appear"; a concordance answers a
 * different question — "how does this tradition use this word, and how much
 * more than that one does". So the shape here is counts first and passages
 * second: how often a word is used, by which religion, in which works, and
 * only then a sample of the lines themselves.
 *
 * It runs on the same full-text index the search does, which already knows
 * every word in two hundred and forty-nine million.
 */
require __DIR__ . '/inc/boot.php';

$word = trim((string) ($_GET['w'] ?? ''));
/* One word, letters only. A concordance of a phrase is a search, and there
   is a page for that. */
$word = preg_replace('/[^A-Za-z\'’-]/u', '', $word);

$total = 0;
$byReligion = [];
$byWork = [];
$lines = [];
$db = $word !== '' ? search_db() : null;

if ($db) {
    $q = fts_query($word);
    try {
        $st = $db->prepare(
            "SELECT w.religion, w.title, p.work_id, p.chapter, p.verse,
                    snippet(passages, 0, :hi, :ho, '…', 18) AS snip
               FROM passages p JOIN works w ON w.id = p.work_id
              WHERE passages MATCH :q
              LIMIT 4000");
        $st->execute([':q' => $q, ':hi' => HI, ':ho' => HO]);
        foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) {
            $total++;
            $byReligion[$r['religion']] = ($byReligion[$r['religion']] ?? 0) + 1;
            $k = $r['work_id'];
            if (!isset($byWork[$k])) {
                $byWork[$k] = ['title' => $r['title'], 'religion' => $r['religion'], 'n' => 0];
            }
            $byWork[$k]['n']++;
            if (count($lines) < 60) {
                $lines[] = $r;
            }
        }
    } catch (Throwable $e) {
        $total = 0;
    }
}
uasort($byWork, fn($a, $b) => $b['n'] <=> $a['n']);
$capped = $total >= 4000;

$pageTitle = $word !== '' ? 'Concordance: ' . $word : 'Concordance';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero" style="padding-bottom:1rem">
  <p class="eyebrow">Word study</p>
  <h1>Concordance</h1>
  <form class="searchbar" action="concordance.php" method="get" role="search">
    <label class="sr" for="w">A word to count</label>
    <input type="search" id="w" name="w" value="<?= e($word) ?>"
           placeholder="mercy, covenant, mercy, jihad, sabbath&hellip;" autocomplete="off">
    <button class="btn" type="submit">Count it</button>
  </form>
  <?php if ($word === ''): ?>
    <p class="lead">
      One word at a time. You will get how often it is used, how that use is
      divided between the three traditions, which works lean on it hardest,
      and a sample of the lines themselves.
    </p>
    <p class="small muted">
      Looking for a phrase rather than a word? <a href="search.php">Search</a>
      takes those.
    </p>
  <?php endif; ?>
</section>

<?php if ($word !== ''): ?>
  <section class="wrap">
    <div class="figures">
      <div class="figure">
        <strong><?= num($total) ?><?= $capped ? '+' : '' ?></strong>
        <span>passages</span>
      </div>
      <?php foreach (['judaism', 'christianity', 'islam'] as $r): ?>
        <div class="figure" data-r="<?= e($r) ?>">
          <strong><?= num($byReligion[$r] ?? 0) ?></strong>
          <span><?= e(religion_name($r)) ?></span>
        </div>
      <?php endforeach; ?>
      <div class="figure"><strong><?= num(count($byWork)) ?></strong><span>works</span></div>
    </div>
    <?php if ($capped): ?>
      <p class="small muted">
        Counting stops at four thousand passages &mdash; enough to show the
        shape of a common word without reading the whole index for it.
      </p>
    <?php endif; ?>
  </section>

  <?php if ($total): ?>
    <section class="wrap">
      <div class="section-head"><h2>Where it is used most</h2></div>
      <?php
      $max = max(array_map(fn($w) => $w['n'], $byWork));
      $top = array_slice($byWork, 0, 25, true);
      ?>
      <div class="conc-bars">
        <?php foreach ($top as $id => $w): ?>
          <a class="conc-bar" href="<?= e(u('search.php', ['q' => $word, 'work' => $id])) ?>"
             data-r="<?= e($w['religion']) ?>">
            <span class="conc-t"><?= e($w['title']) ?></span>
            <span class="conc-track">
              <span style="width:<?= (int) round(100 * $w['n'] / $max) ?>%"></span>
            </span>
            <span class="conc-n"><?= num($w['n']) ?></span>
          </a>
        <?php endforeach; ?>
      </div>
    </section>

    <section class="wrap">
      <div class="section-head"><h2>In its places</h2></div>
      <?php foreach ($lines as $l): ?>
        <article class="hit">
          <p class="hit-ref">
            <a href="<?= e(u('read.php', ['work' => $l['work_id'], 'c' => $l['chapter']])) ?>#v<?= e(preg_replace('/[^0-9a-z]/i', '', (string) $l['verse'])) ?>">
              <?= e($l['title'] . ' ' . $l['chapter'] . ($l['verse'] !== '' ? ':' . $l['verse'] : '')) ?>
            </a>
          </p>
          <p><?= str_replace([e(HI), e(HO)], ['<mark>', '</mark>'], e($l['snip'])) ?></p>
        </article>
      <?php endforeach; ?>
    </section>
  <?php else: ?>
    <section class="wrap"><p class="muted">No passage in the archive uses that word.</p></section>
  <?php endif; ?>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
