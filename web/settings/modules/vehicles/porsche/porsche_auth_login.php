<?php
// Porsche Connect Login-Endpoint fuer die openWB-Einstellungen.
// Durchlaeuft den Auth0-Login (Identifier-First: E-Mail -> Passwort -> Resume -> Token)
// und liefert access_token/refresh_token an die UI zurueck (die UI speichert sie in der
// Fahrzeug-Config). Analog zu bmw_cardata, aber E-Mail/Passwort statt Device-Code.
// Bei Captcha wird das Bild an die UI zurueckgegeben; der Folge-Aufruf schickt die Loesung + sid.

header('Content-Type: application/json');

const AUTH = 'identity.porsche.com';
const CLIENT_ID = 'XhygisuebbrqQ80byOuU5VncxLIm8E6H';
const REDIRECT = 'my-porsche-app://auth0/callback';
const AUDIENCE = 'https://api.porsche.com';
const SCOPE = 'openid profile email offline_access mbb ssodb badge vin dealers cars '
    . 'charging manageCharging plugAndCharge climatisation manageClimatisation '
    . 'pid:user_profile.porscheid:read pid:user_profile.name:read '
    . 'pid:user_profile.vehicles:read pid:user_profile.emails:read '
    . 'pid:user_profile.locale:read';

function out($arr)
{
    echo json_encode($arr);
    exit;
}
function fail($msg)
{
    out(['status' => 'error', 'message' => $msg]);
}

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) {
    http_response_code(400);
    fail('Ungueltige Anfrage.');
}
$email = trim((string)($in['email'] ?? ''));
$password = (string)($in['password'] ?? '');
$captcha = trim((string)($in['captcha'] ?? ''));
$sid = preg_replace('/[^a-f0-9]/', '', (string)($in['sid'] ?? ''));

if ($email === '' || $password === '') {
    fail('E-Mail und Passwort noetig.');
}

$jarDir = sys_get_temp_dir() . '/porsche_auth';
if (!is_dir($jarDir)) {
    @mkdir($jarDir, 0700, true);
}
// alte Sessions (>10 min) aufraeumen
foreach ((array)glob("$jarDir/*") as $f) {
    if (is_file($f) && (time() - filemtime($f)) > 600) {
        @unlink($f);
    }
}
if ($sid === '') {
    $sid = bin2hex(random_bytes(16));
}
$jar = "$jarDir/$sid.cookies";
$statefile = "$jarDir/$sid.state";

function mk($url, $jar)
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_COOKIEJAR => $jar,
        CURLOPT_COOKIEFILE => $jar,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36',
    ]);
    return $ch;
}

// Wenn eine Captcha-Loesung mit bekannter sid kommt: gespeicherten state wiederverwenden.
$state = '';
if ($captcha !== '' && is_file($statefile)) {
    $state = trim((string)file_get_contents($statefile));
}

// 1) /authorize -> Loginseite, state einsammeln (nur wenn noch kein state)
if ($state === '') {
    $q = http_build_query([
        'response_type' => 'code', 'client_id' => CLIENT_ID, 'redirect_uri' => REDIRECT,
        'audience' => AUDIENCE, 'scope' => SCOPE, 'state' => 'openwb',
    ]);
    $ch = mk('https://' . AUTH . '/authorize?' . $q, $jar);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    $body = curl_exec($ch);
    if ($body === false) {
        fail('Verbindungsfehler zu Porsche: ' . curl_error($ch));
    }
    $eff = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
    curl_close($ch);
    parse_str((string)parse_url($eff, PHP_URL_QUERY), $qp);
    $state = $qp['state'] ?? '';
    if ($state === '') {
        fail('Auth0-Flow konnte nicht gestartet werden (kein state).');
    }
}

// 2) Identifier (E-Mail) - ggf. mit Captcha-Loesung
$data = [
    'state' => $state, 'username' => $email, 'js-available' => 'true',
    'webauthn-available' => 'false', 'is-brave' => 'false',
    'webauthn-platform-available' => 'false', 'action' => 'default',
];
if ($captcha !== '') {
    $data['captcha'] = $captcha;
}
$ch = mk('https://' . AUTH . '/u/login/identifier?state=' . rawurlencode($state), $jar);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_exec($ch);
$hc = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($hc == 401) {
    fail('E-Mail wurde abgelehnt.');
}
if ($hc == 400) {
    // Captcha noetig -> Loginseite laden und Bild extrahieren
    $ch = mk('https://' . AUTH . '/u/login/identifier?state=' . rawurlencode($state), $jar);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    $page = (string)curl_exec($ch);
    curl_close($ch);
    if (preg_match('#data:image/[a-z]+;base64,[A-Za-z0-9+/=]{20,}#', $page, $m)
        || preg_match('#"image"\s*:\s*"(data:image[^"]+)"#', $page, $m)) {
        file_put_contents($statefile, $state);
        out(['status' => 'captcha', 'sid' => $sid, 'image' => end($m)]);
    }
    fail('Porsche verlangt aktuell ein Captcha, das nicht automatisch ausgelesen werden konnte. '
        . 'Bitte einmal in der My-Porsche-App vom selben Netz anmelden und erneut versuchen.');
}
@unlink($statefile);

// 3) Passwort
$ch = mk('https://' . AUTH . '/u/login/password?state=' . rawurlencode($state), $jar);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query([
    'state' => $state, 'username' => $email, 'password' => $password, 'action' => 'default',
]));
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_setopt($ch, CURLOPT_HEADER, true);
$resp = (string)curl_exec($ch);
$hc = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$hsize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$headers = substr($resp, 0, $hsize);
curl_close($ch);
if ($hc == 400) {
    fail('Passwort wurde abgelehnt.');
}
if (!preg_match('#^location:\s*(.+)$#mi', $headers, $lm)) {
    fail('Unerwartete Antwort im Passwort-Schritt (HTTP ' . $hc . ').');
}
$resume = trim($lm[1]);
sleep(2); // Auth0 braucht kurz, bis der Resume-Pfad gueltig ist

// 4) Resume -> Authorization-Code
$resumeUrl = (strpos($resume, 'http') === 0) ? $resume : ('https://' . AUTH . $resume);
$ch = mk($resumeUrl, $jar);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_setopt($ch, CURLOPT_HEADER, true);
$resp = (string)curl_exec($ch);
$hsize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$headers = substr($resp, 0, $hsize);
curl_close($ch);
if (!preg_match('#^location:\s*(.+)$#mi', $headers, $lm2)) {
    fail('Kein Authorization-Code erhalten.');
}
parse_str((string)parse_url(trim($lm2[1]), PHP_URL_QUERY), $cp);
$code = $cp['code'] ?? '';
if ($code === '') {
    fail('Kein Authorization-Code in der Antwort.');
}

// 5) Token-Austausch
$ch = mk('https://' . AUTH . '/oauth/token', $jar);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query([
    'client_id' => CLIENT_ID, 'grant_type' => 'authorization_code',
    'code' => $code, 'redirect_uri' => REDIRECT,
]));
$resp = (string)curl_exec($ch);
$hc = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);
@unlink($jar);
@unlink($statefile);

$tok = json_decode($resp, true);
if ($hc != 200 || !is_array($tok) || empty($tok['refresh_token'])) {
    fail('Token-Austausch fehlgeschlagen (HTTP ' . $hc . ').');
}

out([
    'status' => 'ok',
    'access_token' => $tok['access_token'] ?? '',
    'refresh_token' => $tok['refresh_token'],
    'expires_at' => time() + (int)($tok['expires_in'] ?? 0),
    'message' => 'Porsche verbunden.',
]);
