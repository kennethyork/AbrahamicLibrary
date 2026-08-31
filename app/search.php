<?php
/** Full-text search across the archive, through the FTS5 index. */
require __DIR__ . '/inc/boot.php';

$q        = trim((string) ($_GET['q'] ?? ''));
$religion = (string) ($_GET['religion'] ?? '');
$workId   = (string) ($_GET['work'] ?? '');
$page     = max(1, (int) ($_GET['p'] ?? 1));
$perPage  = 25;

/* The highlight is marked with control characters, not with tags. The
   snippet is escaped as ordinary text afterwards and only then are these
   turned into <mark>, so a `<` in a source text cannot become markup. */
const HI = "\x02";
const HO = "\x03";

$db      = search_db();
$hits    = [];
$total   = 0;
$error   = '';
$elapsed = 0.0;

if ($q !== '' && $db) {
    $match = fts_query($q);
    if ($match === '') {
        $error = 'Type a word or two to search for.';
    } else {
        $where  = ['passages MATCH :m'];
        $params = [':m' => $match];
        if ($religion !== '') {
            $where[]            = 'w.religion = :r';
            $params[':r']       = $religion;
        }
        if ($workId !== '') {
            $where[]            = 'p.work_id = :w';
            $params[':w']       = $workId;
        }
        $clause = implode(' AND ', $where);

        try {
            $started = microtime(true);

            $count = $db->prepare(
                "SELECT COUNT(*) FROM passages p
                 JOIN works w ON w.id = p.work_id
                 WHERE $clause"
            );
            $count->execute($params);
            $total = (int) $count->fetchColumn();

            $stmt = $db->prepare(
                "SELECT w.title, w.subtitle, w.religion, w.structure,
                        p.work_id, p.chapter, p.verse,
                        snippet(passages, 0, :hi, :ho, '…', 24) AS snip
                 FROM passages p
                 JOIN works w ON w.id = p.work_id
                 WHERE $clause
                 ORDER BY bm25(passages) LIMIT :lim OFFSET :off"
            );
            foreach ($params as $k => $v) {
                $stmt->bindValue($k, $v);
            }
            $stmt->bindValue(':hi', HI);
            $stmt->bindValue(':ho', HO);
            $stmt->bindValue(':lim', $perPage, PDO::PARAM_INT);
            $stmt->bindValue(':off', ($page - 1) * $perPage, PDO::PARAM_INT);
            $stmt->execute();
            $hits    = $stmt->fetchAll(PDO::FETCH_ASSOC);
            $elapsed = microtime(true) - $started;
        } catch (PDOException $ex) {
            $error = 'That search could not be run. Try plainer words.';
        }
    }
}

$pages        = (int) ceil($total / $perPage);
$pageTitle    = $q !== '' ? 'Search: ' . $q : 'Search';
$pageReligion = $religion;
require __DIR__ . '/inc/header.php';
?>

<div class="wrap">
  <div class="hero" style="padding-block:2rem 1rem">
    <h1>Search the archive</h1>
    <p class="lead">
      <?= num(catalog()['totals']['verses'] ?? 0) ?> verses and sections across
      all three traditions. Put a phrase in "quotes" to keep its words together.
    </p>
  </div>

  <form class="searchbar" method="get" action="search.php">
    <input type="search" name="q" value="<?= e($q) ?>" placeholder="covenant, &ldquo;the day of judgment&rdquo;, mercy&hellip;" autofocus>
    <select name="religion" aria-label="Limit to one religion">
      <option value="">All three religions</option>
      <?php foreach (['judaism', 'christianity', 'islam'] as $r): ?>
        <option value="<?= $r ?>" <?= $religion === $r ? 'selected' : '' ?>><?= e(religion_name($r)) ?></option>
      <?php endforeach; ?>
    </select>
    <?php if ($workId !== '' && ($wm = work($workId))): ?>
      <input type="hidden" name="work" value="<?= e($workId) ?>">
      <span class="tag" style="align-self:center">within <?= e($wm['title']) ?></span>
    <?php endif; ?>
    <button class="btn" type="submit">Search</button>
  </form>

  <?php if (!$db): ?>
    <div class="panel">
      <h2>The index has not been built</h2>
      <p class="muted">Run <code>python3 -m tools.build_search</code> to build it.</p>
    </div>

  <?php elseif ($error): ?>
    <p class="muted"><?= e($error) ?></p>

  <?php elseif ($q === ''): ?>
    <p class="muted">Reading is at the <a href="library.php">library</a>.</p>

  <?php elseif (!$total): ?>
    <div class="panel">
      <h2>Nothing found for &ldquo;<?= e($q) ?>&rdquo;</h2>
      <p class="muted">
        Every text here is modern English, so the old spellings are gone:
        try <em>you</em> rather than <em>thou</em>, <em>has</em> rather than
        <em>hath</em>.
      </p>
    </div>

  <?php else: ?>
    <p class="small muted">
      <?= num($total) ?> <?= $total === 1 ? 'passage' : 'passages' ?>
      in <?= number_format($elapsed * 1000, 0) ?> ms<?php
        if ($pages > 1) { echo ' &middot; page ' . num($page) . ' of ' . num($pages); } ?>
    </p>

    <?php foreach ($hits as $h):
        $vAnchor = preg_match('/^p/', (string) $h['verse'])
            ? '' : '#v' . preg_replace('/[^0-9a-z]/i', '', (string) $h['verse']); ?>
      <div class="hit">
        <a class="ref" href="<?= u('read.php', ['work' => $h['work_id'], 'c' => $h['chapter']]) . $vAnchor ?>">
          <?= e($h['title']) ?> <?= e($h['chapter']) ?><?= preg_match('/^p/', (string) $h['verse']) ? '' : ':' . e($h['verse']) ?>
        </a>
        <span class="where">
          <?= e(religion_name($h['religion'])) ?><?= $h['subtitle'] ? ' &middot; ' . e($h['subtitle']) : '' ?>
        </span>
        <p><?= str_replace([e(HI), e(HO)], ['<mark>', '</mark>'], e($h['snip'])) ?></p>
      </div>
    <?php endforeach; ?>

    <?php if ($pages > 1): ?>
      <nav class="pagination" aria-label="Result pages">
        <?php
        $base = ['q' => $q];
        if ($religion !== '') { $base['religion'] = $religion; }
        if ($workId !== '')   { $base['work'] = $workId; }
        $from = max(1, $page - 3);
        $to   = min($pages, $from + 6);
        if ($page > 1): ?>
          <a href="<?= u('search.php', $base + ['p' => $page - 1]) ?>">&larr; Back</a>
        <?php endif;
        for ($i = $from; $i <= $to; $i++):
            if ($i === $page): ?>
              <span aria-current="page"><?= $i ?></span>
            <?php else: ?>
              <a href="<?= u('search.php', $base + ['p' => $i]) ?>"><?= $i ?></a>
            <?php endif;
        endfor;
        if ($page < $pages): ?>
          <a href="<?= u('search.php', $base + ['p' => $page + 1]) ?>">Next &rarr;</a>
        <?php endif; ?>
      </nav>
    <?php endif; ?>
  <?php endif; ?>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
