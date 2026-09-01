<?php
/**
 * Strong's Hebrew and Greek dictionaries, 1894.
 *
 * Three ways in, because a reader arrives from three directions: with a
 * number they saw somewhere, with a transliterated word, or — most often —
 * with an English word and the question of what stands behind it.
 *
 * That last one works because Strong ended every entry with the English words
 * the King James translators used for it. Indexed backwards, `mercy` returns
 * the six different Hebrew and Greek words that English flattens into one.
 */
require __DIR__ . '/inc/boot.php';

$term = trim((string) ($_GET['q'] ?? ''));
$entries = [];
$mode = '';

if ($term !== '' && ($db = strongs_db())) {
    if (preg_match('/^([HGhg])\s*(\d{1,4})$/', $term, $m)) {
        $mode = 'number';
        $entries = strongs_entry(strtoupper($m[1]) . $m[2]);
    } else {
        $word = strtolower(preg_replace('/[^A-Za-z\'-]/', '', $term));
        if ($word !== '') {
            $entries = strongs_by_english($word);
            $mode = $entries ? 'english' : '';
            if (!$entries) {
                $entries = strongs_by_word($word);
                $mode = $entries ? 'word' : 'none';
            }
        }
    }
}

$pageTitle = $term !== '' ? 'Strong’s: ' . $term : 'Strong’s dictionaries';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero" style="padding-bottom:1rem">
  <p class="eyebrow">Hebrew and Greek</p>
  <h1>Strong’s dictionaries</h1>
  <form class="searchbar" action="strongs.php" method="get" role="search">
    <label class="sr" for="q">A word or a number</label>
    <input type="search" id="q" name="q" value="<?= e($term) ?>"
           placeholder="mercy, covenant, agape, H430, G26&hellip;" autocomplete="off">
    <button class="btn" type="submit">Look it up</button>
  </form>
  <?php if ($term === ''): ?>
    <p class="lead">
      Give it an English word and it will show you what stands behind it &mdash;
      <a href="?q=mercy">mercy</a> is six different words in Hebrew and Greek,
      and they do not mean the same thing. Or give it a transliteration
      (<a href="?q=agape">agape</a>, <a href="?q=shalowm">shalowm</a>) or a
      number (<a href="?q=H430">H430</a>, <a href="?q=G26">G26</a>).
    </p>
  <?php elseif ($mode === 'english'): ?>
    <p class="lead">
      <?= count($entries) ?> Hebrew and Greek words that the King James
      translators rendered <strong><?= e($term) ?></strong>.
    </p>
  <?php elseif ($mode === 'none'): ?>
    <p class="lead">Nothing in either dictionary answers to that.</p>
  <?php endif; ?>
</section>

<?php if ($entries): ?>
  <section class="wrap">
    <?php foreach ($entries as $x): ?>
      <article class="lex" data-r="<?= $x['lang'] === 'hebrew' ? 'judaism' : 'christianity' ?>">
        <p class="lex-head">
          <a class="lex-id" href="<?= e(u('strongs.php', ['q' => $x['id']])) ?>"><?= e($x['id']) ?></a>
          <b class="lex-word"><?= e($x['word']) ?></b>
          <?php if ($x['pron']): ?><span class="lex-pron">[<?= e($x['pron']) ?>]</span><?php endif; ?>
          <span class="muted small"><?= $x['lang'] === 'hebrew' ? 'Hebrew' : 'Greek' ?></span>
        </p>
        <p class="lex-sense"><?= e($x['sense']) ?></p>
        <?php if ($x['kjv']): ?>
          <p class="lex-kjv"><span>Rendered</span> <?= e($x['kjv']) ?></p>
        <?php endif; ?>
        <p class="lex-links">
          <a href="<?= e(u('concordance.php', ['w' => preg_replace('/[^A-Za-z].*$/', '', $x['word'])])) ?>">Count this word in the archive</a>
        </p>
      </article>
    <?php endforeach; ?>
  </section>
<?php endif; ?>

<section class="wrap">
  <p class="small muted">
    James Strong, <em>The Exhaustive Concordance of the Bible</em>, 1894 —
    public domain, scanned by archive.org. The Hebrew and Greek scripts
    themselves did not survive the scanner, so what is shown is Strong’s own
    transliteration, which is what an English reader wants in any case.
    11,762 of the 14,298 entries were recovered; where one is missing, the
    scan of that page defeated it.
  </p>
</section>

<?php require __DIR__ . '/inc/footer.php'; ?>
