<?php
/**
 * RapidWombat → SifuFinds webhook receiver.
 *
 * URL: https://sifufinds.com/webhooks/rapidwombat.php
 *
 * RapidWombat POSTs {id, title, content (markdown), cover_image} with
 * "Authorization: Bearer <secret token>" the moment an article publishes
 * (docs.rapidwombat.com/integrations/webhooks). This endpoint does NOT write
 * to the site itself — the site is static HTML generated from
 * blog/posts.json, and a deploy overwrites anything written on the server.
 * Instead it verifies the token and forwards the article to GitHub as a
 * repository_dispatch event; .github/workflows/rapidwombat_import.yml then
 * imports it into posts.json, regenerates the page, runs every deploy gate
 * and commits. Same pattern as the Sanity sync: an authoring source, never a
 * separate rendering path.
 *
 * Secrets live in rapidwombat-secrets.php, which is NOT in git (public repo).
 * deploy_hostinger.yml writes it into the deploy copy from the
 * RAPIDWOMBAT_WEBHOOK_TOKEN / RAPIDWOMBAT_DISPATCH_TOKEN repo secrets.
 */

declare(strict_types=1);

const GITHUB_REPO = 'sifufinds/Sifufinds_Bets';
const EVENT_TYPE = 'rapidwombat_article';
const MAX_BODY_BYTES = 2 * 1024 * 1024;
const MIN_CONTENT_CHARS = 200;
const MAX_TITLE_CHARS = 300;

header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: no-store');

function respond(int $status, array $body): void
{
    http_response_code($status);
    echo json_encode($body);
    exit;
}

function load_config(): ?array
{
    $path = __DIR__ . '/rapidwombat-secrets.php';
    if (!is_file($path)) {
        return null;
    }
    $config = require $path;
    if (!is_array($config) || empty($config['webhook_token']) || empty($config['dispatch_token'])) {
        return null;
    }
    return $config;
}

function bearer_token(): string
{
    // LiteSpeed/Apache can strip Authorization before PHP sees it; .htaccess
    // copies it into HTTP_AUTHORIZATION, and getallheaders() is a fallback.
    $header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    if ($header === '' && function_exists('getallheaders')) {
        foreach (getallheaders() as $name => $value) {
            if (strcasecmp($name, 'Authorization') === 0) {
                $header = $value;
                break;
            }
        }
    }
    if (preg_match('/^Bearer\s+(.+)$/i', trim($header), $m)) {
        return trim($m[1]);
    }
    return '';
}

function validate_article(array $data): array
{
    $id = $data['id'] ?? null;
    if (!(is_string($id) || is_int($id)) || !preg_match('/^[A-Za-z0-9_-]{1,100}$/', (string) $id)) {
        respond(422, ['ok' => false, 'error' => 'id must be 1-100 chars of letters, digits, _ or -']);
    }
    $title = trim((string) ($data['title'] ?? ''));
    if ($title === '' || mb_strlen($title) > MAX_TITLE_CHARS) {
        respond(422, ['ok' => false, 'error' => 'title is required (max ' . MAX_TITLE_CHARS . ' chars)']);
    }
    $content = (string) ($data['content'] ?? '');
    if (mb_strlen(trim($content)) < MIN_CONTENT_CHARS) {
        respond(422, ['ok' => false, 'error' => 'content is missing or too short']);
    }
    $cover = trim((string) ($data['cover_image'] ?? ''));
    if ($cover !== '' && !preg_match('#^https?://#i', $cover)) {
        $cover = '';
    }
    return ['id' => (string) $id, 'title' => $title, 'content' => $content, 'cover_image' => $cover];
}

function dispatch_to_github(array $article, string $token): array
{
    // Gzip + base64 the body so long articles stay well inside GitHub's
    // repository_dispatch payload limits.
    $payload = json_encode([
        'event_type' => EVENT_TYPE,
        'client_payload' => [
            'id' => $article['id'],
            'title' => $article['title'],
            'content_gzip_b64' => base64_encode(gzencode($article['content'], 9)),
            'cover_image' => $article['cover_image'],
            'attempt' => 1,
        ],
    ]);

    $ch = curl_init('https://api.github.com/repos/' . GITHUB_REPO . '/dispatches');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 20,
        CURLOPT_HTTPHEADER => [
            'Accept: application/vnd.github+json',
            'Authorization: Bearer ' . $token,
            'X-GitHub-Api-Version: 2022-11-28',
            'User-Agent: sifufinds-rapidwombat-webhook',
            'Content-Type: application/json',
        ],
    ]);
    $response = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    return ['status' => $status, 'error' => $error, 'response' => is_string($response) ? $response : ''];
}

$config = load_config();
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($method === 'GET') {
    respond(200, ['ok' => true, 'service' => 'rapidwombat-webhook', 'configured' => $config !== null]);
}
if ($method !== 'POST') {
    header('Allow: GET, POST');
    respond(405, ['ok' => false, 'error' => 'method not allowed']);
}
if ($config === null) {
    error_log('rapidwombat webhook: config missing — check RAPIDWOMBAT_* repo secrets and redeploy');
    respond(503, ['ok' => false, 'error' => 'webhook not configured']);
}
if (!hash_equals((string) $config['webhook_token'], bearer_token())) {
    respond(401, ['ok' => false, 'error' => 'invalid or missing bearer token']);
}

$raw = file_get_contents('php://input', false, null, 0, MAX_BODY_BYTES + 1);
if ($raw === false || strlen($raw) > MAX_BODY_BYTES) {
    respond(413, ['ok' => false, 'error' => 'payload too large']);
}
$data = json_decode($raw, true);
if (!is_array($data)) {
    respond(400, ['ok' => false, 'error' => 'body must be JSON']);
}

$article = validate_article($data);
$result = dispatch_to_github($article, (string) $config['dispatch_token']);

if ($result['status'] !== 204) {
    error_log(sprintf(
        'rapidwombat webhook: GitHub dispatch failed for article %s — HTTP %d %s %s',
        $article['id'],
        $result['status'],
        $result['error'],
        substr($result['response'], 0, 300)
    ));
    // 502 tells RapidWombat the delivery failed so it can be retried.
    respond(502, ['ok' => false, 'error' => 'could not queue article for publishing']);
}

respond(202, ['ok' => true, 'queued' => $article['id']]);
