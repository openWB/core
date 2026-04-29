<?php

return [
    // MQTT Broker Konfiguration
    'mqtt' => [
        'server' => 'localhost',
        'port' => 8883,
        'validate_cert' => false,
        'username' => '',
        'password' => '',
        'clientid' => 'SimpleAPI_' . uniqid()
    ],

    // API Konfiguration
    'api' => [
        'cors_enabled' => true,
        'max_request_size' => '10M'
    ],

    // Authentifizierung
    'auth' => [
        'enabled' => true,
        'require_https' => false,

        // Gültige Tokens
        'tokens' => [
            // 'your-secret-token-here'
        ],

        // Benutzer (Username => Passwort/Hash)
        'users' => [
            // 'admin' => password_hash('admin123', PASSWORD_DEFAULT),
            // 'user' => 'plaintext_password'
        ]
    ],

    // Debug-Modus
    'debug' => false
];
