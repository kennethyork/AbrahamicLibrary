<?php
/**
 * Reads a verse aloud.
 *
 * Piper is a neural text-to-speech engine that runs on the machine serving
 * the page — no account, no API key, nothing sent anywhere. It fits this
 * archive for the same reason the World English Bible does: the voice is
 * `ljspeech`, whose model card says `License: public domain`. Three of the
 * five best English voices Piper offers are CC BY-NC, and a library whose
 * whole point is that it can be sold cannot use a voice that cannot be.
 *
 * Audio is made once and kept. A verse is about three seconds of speech and
 * eleven kilobytes of Opus, so a chapter costs well under a megabyte and is
 * only paid for if somebody actually listens to it.
 *
 * The text spoken is read out of the corpus by work, chapter and verse. It is
 * never taken from the request, and it reaches Piper down a pipe rather than
 * through a shell, so there is no line here for anyone to inject into.
 */
require __DIR__ . '/inc/boot.php';

const PIPER_BIN   = '/home/kennethhy/.local/bin/piper';
const PIPER_VOICE = __DIR__ . '/../voices/en_US-ljspeech-high.onnx';
const AUDIO_DIR   = CORPUS_DIR . '/audio';
const FFMPEG      = '/usr/bin/ffmpeg';

function fail(int $code, string $why): never
{
    http_response_code($code);
    header('Content-Type: text/plain; charset=utf-8');
    echo $why;
    exit;
}

if (!is_file(PIPER_BIN) || !is_file(PIPER_VOICE)) {
    fail(503, 'No voice is installed on this server.');
}

$id = (string) ($_GET['work'] ?? '');
$n  = (string) ($_GET['c'] ?? '');
$v  = (string) ($_GET['v'] ?? '');

$meta = work($id);
$ch   = $meta ? chapter($id, $n) : null;
if (!$meta || !$ch) {
    fail(404, 'No such chapter.');
}

/* The text always comes from the corpus, never from the query. */
$text = null;
foreach ($ch['verses'] ?? [] as $verse) {
    if ((string) $verse['n'] === $v) {
        $text = $verse['text'];
        break;
    }
}
if ($text === null && preg_match('/^p(\d+)$/', $v, $m)) {
    $i = 0;
    foreach ($ch['blocks'] ?? [] as $b) {
        if (($b['k'] ?? 'p') === 'p' && ++$i === (int) $m[1]) {
            $text = $b['t'];
            break;
        }
    }
}
if ($text === null || trim($text) === '') {
    fail(404, 'No such verse.');
}

/**
 * Respell the names the phonemizer gets wrong, just before the voice sees
 * them. Nothing on the page changes — this is only what Piper is handed.
 *
 * The table is built by `tools.build_pronounce` from the names that actually
 * appear in these scriptures, and it exists because espeak-ng reads the `ch`
 * of a biblical name as the `ch` of *church*: Abimelech, Chaldean, Baruch,
 * Melchizedek. In this corpus that is a hundred and eighty-four names and
 * four thousand occurrences of them.
 */
function respell(string $text): string
{
    static $table = null;
    if ($table === null) {
        $raw = @file_get_contents(__DIR__ . '/data/pronounce.json');
        $d = $raw ? json_decode($raw, true) : null;
        $table = (is_array($d) && !empty($d['words'])) ? $d['words'] : [];
    }
    if (!$table) {
        return $text;
    }
    return preg_replace_callback(
        '/\b[A-Z][A-Za-z]{2,}\b/',
        fn($m) => $table[$m[0]] ?? $m[0],
        $text);
}

/* Long paragraphs are refused rather than left to run for minutes. */
if (mb_strlen($text) > 3000) {
    $text = mb_substr($text, 0, 3000);
}

$safe  = preg_replace('/[^A-Za-z0-9._-]/', '', $id);
$cn    = preg_replace('/[^A-Za-z0-9._-]/', '', $n);
$vn    = preg_replace('/[^A-Za-z0-9._-]/', '', $v);
$dir   = AUDIO_DIR . "/$safe/$cn";
$out   = "$dir/$vn.opus";

if (!is_file($out)) {
    if (!is_dir($dir) && !@mkdir($dir, 0775, true) && !is_dir($dir)) {
        fail(500, 'Cannot write the audio cache.');
    }
    $wav = tempnam(sys_get_temp_dir(), 'aa-tts') . '.wav';

    /* An array command: no shell, so nothing in the text can be a shell
       character. The text goes down stdin. */
    $p = proc_open(
        [PIPER_BIN, '-m', PIPER_VOICE, '-f', $wav],
        [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']],
        $pipes);
    if (!is_resource($p)) {
        @unlink($wav);
        fail(500, 'Could not start the voice.');
    }
    fwrite($pipes[0], respell($text) . "\n");
    fclose($pipes[0]);
    stream_get_contents($pipes[1]);
    stream_get_contents($pipes[2]);
    foreach ([1, 2] as $k) {
        fclose($pipes[$k]);
    }
    proc_close($p);

    if (!is_file($wav) || filesize($wav) < 1000) {
        @unlink($wav);
        fail(500, 'The voice produced nothing.');
    }

    /* Opus at 24k: about eleven kilobytes for a verse, against a hundred and
       fifty for the WAV Piper hands back. */
    if (is_file(FFMPEG)) {
        $q = proc_open(
            [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y',
             '-i', $wav, '-c:a', 'libopus', '-b:a', '24k', $out],
            [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $qp);
        if (is_resource($q)) {
            stream_get_contents($qp[1]);
            stream_get_contents($qp[2]);
            fclose($qp[1]);
            fclose($qp[2]);
            proc_close($q);
        }
    }
    if (!is_file($out)) {          /* no ffmpeg — serve the WAV instead */
        $out = "$dir/$vn.wav";
        @rename($wav, $out);
    } else {
        @unlink($wav);
    }
}

$type = str_ends_with($out, '.opus') ? 'audio/ogg' : 'audio/wav';
header('Content-Type: ' . $type);
header('Content-Length: ' . filesize($out));
header('Cache-Control: public, max-age=31536000, immutable');
header('X-Voice: ljspeech (public domain) via Piper');
readfile($out);
