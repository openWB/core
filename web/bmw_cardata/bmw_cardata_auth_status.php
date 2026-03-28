<?php
header('Content-Type: application/json');

$status_file = '/var/www/html/openWB/data/bmw_cardata_auth_status.json';

if (!file_exists($status_file)) {
    echo json_encode([
        'connected' => false,
        'message'   => 'Noch keine BMW Auth gestartet.',
        'error'     => '',
    ]);
    exit;
}

$status = json_decode(file_get_contents($status_file), true);
if (!$status) {
    echo json_encode(['connected' => false, 'error' => 'Status-Datei konnte nicht gelesen werden.']);
    exit;
}

// Bereits verbunden?
if (!empty($status['connected'])) {
    echo json_encode([
        'connected' => true,
        'message'   => 'BMW verbunden.',
        'error'     => '',
    ]);
    exit;
}

// Abgelaufen?
if (time() > ($status['expires_at'] ?? 0)) {
    echo json_encode([
        'connected' => false,
        'message'   => '',
        'error'     => 'BMW Auth ist abgelaufen. Bitte erneut starten.',
    ]);
    exit;
}

// Token pollen
$post_data = http_build_query([
    'client_id'     => $status['client_id'],
    'device_code'   => $status['device_code'],
    'grant_type'    => 'urn:ietf:params:oauth:grant-type:device_code',
    'code_verifier' => $status['code_verifier'],
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

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($curl_error) {
    echo json_encode([
        'connected' => false,
        'message'   => 'Warte auf BMW-Bestätigung...',
        'user_code' => $status['user_code'],
        'verification_uri' => $status['verification_uri'],
        'error'     => '',
    ]);
    exit;
}

$data = json_decode($response, true);
$error = $data['error'] ?? '';

// Noch nicht bestätigt oder zu schnelles Polling – kein Fehler!
if (in_array($error, ['authorization_pending', 'slow_down']) || $http_code === 400) {
    echo json_encode([
        'connected'        => false,
        'user_code'        => $status['user_code'],
        'verification_uri' => $status['verification_uri'],
        'message'          => 'Warte auf BMW-Bestätigung...',
        'error'            => '',
    ]);
    exit;
}

// Erfolgreich
if ($http_code === 200 && !empty($data['access_token'])) {
    $expires_at = time() + ($data['expires_in'] ?? 3600) - 60;

    // Status-Datei aktualisieren
    $status['connected'] = true;
    $status['message'] = 'BMW Auth erfolgreich abgeschlossen.';
    $status['error'] = '';
    file_put_contents($status_file, json_encode($status, JSON_PRETTY_PRINT));

    // Tokens zurückgeben – UI speichert sie in der openWB-Konfiguration
    echo json_encode([
        'connected'     => true,
        'access_token'  => $data['access_token'],
        'refresh_token' => $data['refresh_token'] ?? '',
        'expires_at'    => $expires_at,
        'message'       => 'BMW verbunden.',
        'error'         => '',
    ]);
    exit;
}

// Sonstiger Fehler
echo json_encode([
    'connected' => false,
    'message'   => '',
    'error'     => 'Fehler: ' . ($response ?: 'HTTP ' . $http_code),
]);
