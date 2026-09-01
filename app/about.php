<?php
/** What was done to the texts, and where they came from. */
require __DIR__ . '/inc/boot.php';

$cat     = catalog();
$reports = [];
foreach (glob(CORPUS_DIR . '/reports/*.json') ?: [] as $path) {
    $reports[basename($path, '.json')] = json_file($path) ?? [];
}

/* Every distinct rights statement in the archive, with what it covers. */
$sources = [];
foreach ($cat['religions'] as $r) {
    foreach ($r['sections'] as $s) {
        foreach ($s['works'] as $w) {
            if (!empty($w['borrowed_from'])) {
                continue;
            }
            $key = $w['rights']['statement'] ?? 'Public domain.';
            if (!isset($sources[$key])) {
                $sources[$key] = [
                    'statement' => $key,
                    'religions' => [],
                    'works'     => 0,
                    'examples'  => [],
                ];
            }
            $sources[$key]['works']++;
            $sources[$key]['religions'][$r['name']] = true;
            if (count($sources[$key]['examples']) < 3
                    && !empty($w['edition']['translation'])) {
                $sources[$key]['examples'][] = $w['edition']['translation'];
            }
        }
    }
}
uasort($sources, fn($a, $b) => $b['works'] <=> $a['works']);
/* Sefaria names the edition inside its rights line, so there are hundreds of
   near-identical rows. The big ones are the ones worth showing. */
$sourcesShown = array_slice($sources, 0, 25, true);
$sourcesRest  = array_slice($sources, 25, null, true);

$changed = $unresolved = 0;
foreach ($reports as $rep) {
    $changed    += (int) ($rep['changed_occurrences'] ?? 0);
    $unresolved += (int) ($rep['unresolved_occurrences'] ?? 0);
}

$pageTitle = 'About the archive';
require __DIR__ . '/inc/header.php';
?>

<div class="wrap">
  <div class="hero" style="padding-block:2.5rem 1rem">
    <h1>What was done to these texts</h1>
    <p class="lead">
      Nothing here is a new translation. The words are the translators&rsquo; own.
      What changed is the grammar of another century &mdash; the pronouns, the
      verb endings, and the spelling &mdash; brought to one present-day American
      standard so that four hundred years of translators can be read side by side.
    </p>
  </div>

  <div class="section-head"><h2>The three tiers</h2>
    <p>Not every text needs the same treatment.</p></div>

  <div class="three">
    <div class="panel">
      <h3>As received</h3>
      <p class="muted small">The text exactly as the translator left it. Used
        where a text is already plain, or where changing it would lose the sense.</p>
    </div>
    <div class="panel">
      <h3>Lightly modernized</h3>
      <p class="muted small">
        Spelling made American, a few formal words made plain
        (<em>thereof</em> &rarr; <em>of it</em>), and archaic constructions
        rebuilt. Pronouns and verb endings are left alone &mdash; the tier for
        a translation that is already modern, such as the World English Bible,
        where there is nothing archaic to resolve.
      </p>
    </div>
    <div class="panel">
      <h3>Modernized in full</h3>
      <p class="muted small">
        Everything above, plus the Early Modern pronouns and verb inflections:
        <em>thou, thee, thy, ye</em> &rarr; <em>you, your</em>;
        <em>hath, doth, saith</em> &rarr; <em>has, does, says</em>;
        the whole <em>-eth</em> and <em>-est</em> classes. <em>art</em> is
        settled by context rather than by tier, so a modern history that
        quotes the King James Bible can take this tier: the quotation is
        modernized and the author&rsquo;s own &ldquo;work of art&rdquo; is not.
      </p>
    </div>
  </div>

  <div class="section-head"><h2>How a verb ending is resolved</h2>
    <p>Why <em>abideth</em> becomes <em>abides</em> and <em>harvest</em> stays put.</p></div>

  <div class="panel">
    <p>
      A rule that simply strips <em>-eth</em> turns <em>abideth</em> into
      &ldquo;abids&rdquo; and <em>cometh</em> into &ldquo;coms&rdquo;. So no
      ending is stripped on faith. Every candidate stem is checked against an
      English dictionary before it is accepted, and three things follow from that:
    </p>
    <ul class="muted">
      <li>A word that is <em>itself</em> ordinary English is never touched.
          That is what protects <em>forest, harvest, priest, tempest, honest,
          interest, greatest, twentieth, death</em> and <em>beneath</em>.</li>
      <li>A stem is only used if it is a real word, which is how
          <em>cometh</em> reaches <em>come</em> rather than <em>com</em>, and
          <em>sitteth</em> reaches <em>sit</em> rather than <em>sitt</em>.</li>
      <li>Anything that cannot be resolved with confidence is
          <strong>left exactly as it was</strong> and written to a report for a
          person to rule on. The archive would rather keep an archaic word than
          invent one.</li>
    </ul>
    <?php if ($changed): ?>
      <p class="small muted">
        Across the archive the generative pass changed
        <strong><?= num($changed) ?></strong> occurrences and left
        <strong><?= num($unresolved) ?></strong> unresolved for review.
      </p>
    <?php endif; ?>
  </div>

  <div class="section-head"><h2>Two things deliberately left</h2></div>
  <div class="panel">
    <p class="muted">
      <strong>lest.</strong> Removing it means rebuilding the clause around an
      inserted negation &mdash; <em>lest he fall</em> becomes <em>so that he
      does not fall</em>. No word-for-word substitution can do that, and doing
      it by hand would be composing new translations.
    </p>
    <p class="muted">
      <strong>behold.</strong> Only about a quarter of its uses are the
      exclamation; the rest are the plain verb, which <em>look</em> destroys
      &mdash; <em>to behold the glory</em>. Changing the quarter would leave a
      book inconsistent with itself, which is worse than leaving it whole.
    </p>
  </div>

  <div class="section-head" id="rights"><h2>Sources and rights</h2>
    <p>Every text here is free to read, copy, print, sell and give away.
       That applies to the texts and to these modernized editions of them.
       It does not apply to the software that serves them, which is the
       author&rsquo;s and is not open source.</p></div>

  <div class="panel">
    <p class="muted small">
      The archive takes nothing that is not in the public domain. Where a
      library offers a better-edited modern translation under a licence that
      forbids commercial use, that translation is passed over rather than
      included &mdash; the point of the project is a library that anyone can
      reprint without asking.
    </p>
    <table style="width:100%;border-collapse:collapse;font-size:.88rem;margin-top:1rem">
      <thead>
        <tr style="text-align:left;border-bottom:1px solid var(--line)">
          <th style="padding:.5rem .5rem .5rem 0">Where it is used</th>
          <th style="padding:.5rem">Works</th>
          <th style="padding:.5rem">Rights</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($sourcesShown as $s): ?>
          <tr style="border-bottom:1px solid var(--line-soft);vertical-align:top">
            <td style="padding:.6rem .5rem .6rem 0">
              <strong><?= e(implode(', ', array_keys($s['religions']))) ?></strong>
              <?php if ($s['examples']): ?>
                <br><span class="muted small">
                  e.g. <?= e(implode('; ', array_slice($s['examples'], 0, 2))) ?>
                </span>
              <?php endif; ?>
            </td>
            <td style="padding:.6rem .5rem"><?= num($s['works']) ?></td>
            <td style="padding:.6rem .5rem" class="muted">
              <?= e($s['statement']) ?>
            </td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
    <?php if ($sourcesRest): ?>
      <p class="small muted" style="margin-top:1rem">
        &hellip; and <?= num(count($sourcesRest)) ?> further rights statements
        covering <?= num(array_sum(array_column($sourcesRest, 'works'))) ?>
        works, each named on that work&rsquo;s own page. Every one is public
        domain or CC0.
      </p>
    <?php endif; ?>
  </div>

  <div class="section-head"><h2>How it is built</h2></div>
  <div class="panel">
    <p class="muted small">
      The reading texts are flat JSON files, one per chapter, outside the
      document root. Search runs on a SQLite FTS5 index built from them. The
      site itself is plain PHP, CSS, JavaScript and HTML &mdash; no framework,
      no build step, no package manager. Your bookmarks and reading settings
      live in your own browser and are never sent anywhere.
    </p>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
