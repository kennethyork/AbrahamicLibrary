<?php
/**
 * Everything a reader has made: highlights, notes, bookmarks, and where they
 * have been.
 *
 * The page is deliberately empty when it is served. There are no accounts
 * here and nothing about a reader ever reaches the server, so all of this is
 * read out of localStorage by `assets/me.js` once the page is up. The cost is
 * that it cannot be printed from the server; the benefit is that a library
 * anyone can host holds nothing about anyone.
 */
require __DIR__ . '/inc/boot.php';

$pageTitle = 'Your reading';
require __DIR__ . '/inc/header.php';
?>

<section class="wrap hero" style="padding-bottom:1rem">
  <p class="eyebrow">On this device only</p>
  <h1>Your reading</h1>
  <p class="lead">
    Every highlight, note and bookmark you have made. None of it has left this
    browser &mdash; there is no account behind it and nothing was sent
    anywhere. Take a copy whenever you like.
  </p>
  <div class="actions">
    <button class="btn" type="button" data-export>Download a copy</button>
    <label class="btn alt" style="cursor:pointer">
      Restore from a copy
      <input type="file" accept="application/json" hidden data-import>
    </label>
  </div>
  <p class="small muted" data-io-msg role="status"></p>
</section>

<section class="wrap" data-panel="continue" hidden>
  <div class="section-head"><h2>Pick up where you left off</h2></div>
  <div class="grid-works" data-list="continue"></div>
</section>

<section class="wrap" data-panel="notes" hidden>
  <div class="section-head">
    <h2>Your notes</h2>
    <span class="muted small" data-count="notes"></span>
  </div>
  <div data-list="notes"></div>
</section>

<section class="wrap" data-panel="highlights" hidden>
  <div class="section-head">
    <h2>Your highlights</h2>
    <span class="muted small" data-count="highlights"></span>
  </div>
  <div data-list="highlights"></div>
</section>

<section class="wrap" data-panel="bookmarks" hidden>
  <div class="section-head"><h2>Bookmarks</h2></div>
  <div data-bookmark-list></div>
</section>

<section class="wrap" data-panel="empty" hidden>
  <div class="hero" style="padding-block:2rem">
    <h2>Nothing saved yet</h2>
    <p class="lead">
      Open any chapter and tap a verse. You can colour it, write a note on it,
      copy it or set it beside another translation.
    </p>
    <div class="actions">
      <a class="btn" href="<?= e(u('read.php', ['work' => 'webu-gen', 'c' => '1'])) ?>">Start at Genesis 1</a>
      <a class="btn alt" href="plans.php">Or follow a reading plan</a>
    </div>
  </div>
</section>

<script src="assets/me.js" defer></script>
<?php require __DIR__ . '/inc/footer.php'; ?>
