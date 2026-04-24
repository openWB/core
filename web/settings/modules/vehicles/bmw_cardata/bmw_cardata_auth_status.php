<?php
header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);
if (!is_array($input)) {
    http_response_code(400);
    echo json_encode(['connected' => false, 'message' => '', 'error' => 'Ungültige Anfrage.']);
    exit;
}

$client_id = trim((string)($input['client_id'] ?? ''));
$device_code = trim((string)($input['device_code'] ?? ''));
$code_verifier = trim((string)($input['code_verifier'] ?? ''));
$expires_at = (int)($input['expires_at'] ?? 0);

if ($client_id === '' || $device_code === '' || $code_verifier === '') {
    echo json_encode([
        'connected' => false,
        'message'   => 'Noch keine BMW Auth gestartet.',
        'error'     => '',
    ]);
    exit;
}

if ($expires_at > 0 && time() > $expires_at) {
    echo json_encode([
        'connected' => false,
        'message'   => '',
        'error'     => 'BMW Auth ist abgelaufen. Bitte erneut starten.',
    ]);
    exit;
}

$post_data = http_build_query([
    'client_id'     => $client_id,
    'device_code'   => $device_code,
    'grant_type'    => 'urn:ietf:params:oauth:grant-type:device_code',
    'code_verifier' => $code_verifier,
]);

$ch = curl_init('https://customer.bmwgroup.com/gcdm/oauth/token');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/x-www-form-urlencoded',
    'Accept: application/json',
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($curl_error) {
    echo json_encode([
        'connected' => false,
        'message'   => '',
        'error'     => 'Verbindungsfehler: ' . $curl_error,
    ]);
    exit;
}

$data = json_decode($response, true);
if (!is_array($data)) {
    $data = [];
}

$error = (string)($data['error'] ?? '');

if ($http_code === 200 && !empty($data['access_token'])) {
    echo json_encode([
        'connected'     => true,
        'access_token'  => $data['access_token'],
        'refresh_token' => $data['refresh_token'] ?? '',
        'expires_at'    => time() + (($data['expires_in'] ?? 3600) - 60),
        'message'       => 'BMW verbunden.',
        'error'         => '',
    ]);
    exit;
}

if ($error === 'authorization_pending') {
    echo json_encode([
        'connected' => false,
        'message'   => 'Warte auf BMW-Bestätigung...',
        'error'     => '',
    ]);
    exit;
}

if ($error === 'slow_down') {
    echo json_encode([
        'connected' => false,
        'message'   => 'Warte auf BMW-Bestätigung...',
        'error'     => '',
        'interval'  => 10,
    ]);
    exit;
}

if ($error === 'authorization_declined') {
    echo json_encode([
        'connected' => false,
        'message'   => '',
        'error'     => 'BMW Auth wurde abgelehnt.',
    ]);
    exit;
}

if ($error === 'expired_token') {
    echo json_encode([
        'connected' => false,
        'message'   => '',
        'error'     => 'BMW Auth ist abgelaufen. Bitte erneut starten.',
    ]);
    exit;
}

$details = $error !== '' ? $error : ('HTTP ' . $http_code);
error_log('BMW auth_status error: ' . $response);

echo json_encode([
    'connected' => false,
    'message'   => '',
    'error'     => 'Fehler beim BMW-Token-Abruf: ' . $details,
]);
