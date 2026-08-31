<?php
/** The page shell. Every page requires boot.php then this. */
$pageTitle   = $pageTitle   ?? '';
$pageReligion = $pageReligion ?? '';
$bodyClass   = $bodyClass   ?? '';
?>
<!doctype html>
<html lang="en"<?= $pageReligion ? ' data-religion="' . e($pageReligion) . '"' : '' ?>>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= $pageTitle ? e($pageTitle) . ' — ' . APP_NAME : APP_NAME ?></title>
<meta name="description" content="<?= e(APP_TAGLINE) ?>">
<link rel="stylesheet" href="assets/style.css">
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#faf8f4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14140f" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Archive">
<link rel="apple-touch-icon" href="assets/icons/apple-touch-180.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#128214;</text></svg>">
</head>
<body class="<?= e($bodyClass) ?>">
<a class="skip" href="#main">Skip to content</a>

<header class="site">
  <div class="wrap bar">
    <a class="brand" href="index.php">
      <span class="mark" aria-hidden="true"></span>
      <span class="brand-text">
        <strong>The Abrahamic Archive</strong>
        <small><?= e(APP_TAGLINE) ?></small>
      </span>
    </a>

    <nav class="nav" aria-label="Main">
      <a href="<?= u('library.php', ['religion' => 'judaism']) ?>" class="r-judaism">Judaism</a>
      <a href="<?= u('library.php', ['religion' => 'christianity']) ?>" class="r-christianity">Christianity</a>
      <a href="<?= u('library.php', ['religion' => 'islam']) ?>" class="r-islam">Islam</a>
      <a href="library.php">Library</a>
      <a href="plans.php">Plans</a>
      <a href="me.php">Mine</a>
      <a href="about.php">About</a>
    </nav>

    <form class="find" action="search.php" method="get" role="search">
      <label class="sr" for="q">Search the archive</label>
      <input type="search" id="q" name="q" placeholder="Search all texts&hellip;"
             value="<?= e($_GET['q'] ?? '') ?>" autocomplete="off">
      <button type="submit" aria-label="Search">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16.5 16.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
    </form>

    <button class="theme" type="button" data-theme-toggle aria-label="Switch between light and dark">
      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z" fill="currentColor"/></svg>
    </button>
  </div>
</header>

<main id="main">
