<?php

namespace SimpleAPI;

/**
 * Authentifizierung für die SimpleAPI
 */
class Authenticator
{
    private $config;

    public function __construct($config)
    {
        $this->config = $config;
    }

    /**
     * Authentifizierung prüfen
     */
    public function authenticate($params)
    {
        // Wenn keine Authentifizierung erforderlich ist
        if (!$this->isAuthRequired()) {
            return true;
        }

        // Bearer Token prüfen
        if ($this->checkBearerToken()) {
            return true;
        }

        // Username/Password prüfen
        if ($this->checkUsernamePassword($params)) {
            return true;
        }

        // Token aus Parameter prüfen
        if ($this->checkParameterToken($params)) {
            return true;
        }

        return false;
    }

    /**
     * Prüfen ob Authentifizierung erforderlich ist
     */
    private function isAuthRequired()
    {
        return $this->config['auth']['enabled'] ?? false;
    }

    /**
     * Bearer Token aus Authorization Header prüfen
     */
    private function checkBearerToken()
    {
        $headers = $this->getAuthorizationHeader();
        
        if (!$headers) {
            return false;
        }

        // Bearer Token extrahieren
        if (preg_match('/Bearer\s+(.*)$/i', $headers, $matches)) {
            $token = $matches[1];
            return $this->validateToken($token);
        }

        return false;
    }

    /**
     * Username/Password aus POST-Parametern prüfen
     */
    private function checkUsernamePassword($params)
    {
        if (!isset($params['username']) || !isset($params['password'])) {
            return false;
        }

        $username = $params['username'];
        $password = $params['password'];

        // Nur bei HTTPS erlaubt
        if (!$this->isHttps() && $this->config['auth']['require_https']) {
            return false;
        }

        return $this->validateCredentials($username, $password);
    }

    /**
     * Token aus Parameter prüfen
     */
    private function checkParameterToken($params)
    {
        if (!isset($params['token'])) {
            return false;
        }

        // Nur bei HTTPS erlaubt
        if (!$this->isHttps() && $this->config['auth']['require_https']) {
            return false;
        }

        return $this->validateToken($params['token']);
    }

    /**
     * Token validieren
     */
    private function validateToken($token)
    {
        $validTokens = $this->config['auth']['tokens'] ?? [];
        
        foreach ($validTokens as $validToken) {
            if (hash_equals($validToken, $token)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Benutzerdaten validieren
     */
    private function validateCredentials($username, $password)
    {
        $users = $this->config['auth']['users'] ?? [];
        
        if (!isset($users[$username])) {
            return false;
        }

        $storedPassword = $users[$username];

        // Passwort-Hash prüfen
        if (strpos($storedPassword, '$') === 0) {
            // Gehashtes Passwort
            return password_verify($password, $storedPassword);
        } else {
            // Klartext (nicht empfohlen)
            return hash_equals($storedPassword, $password);
        }
    }

    /**
     * Authorization Header abrufen
     */
    private function getAuthorizationHeader()
    {
        $headers = null;

        if (isset($_SERVER['Authorization'])) {
            $headers = trim($_SERVER['Authorization']);
        } elseif (isset($_SERVER['HTTP_AUTHORIZATION'])) {
            $headers = trim($_SERVER['HTTP_AUTHORIZATION']);
        } elseif (function_exists('apache_request_headers')) {
            $requestHeaders = apache_request_headers();
            $requestHeaders = array_combine(
                array_map('ucwords', array_keys($requestHeaders)), 
                array_values($requestHeaders)
            );
            
            if (isset($requestHeaders['Authorization'])) {
                $headers = trim($requestHeaders['Authorization']);
            }
        }

        return $headers;
    }

    /**
     * Prüfen ob HTTPS verwendet wird
     */
    private function isHttps()
    {
        return (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ||
               $_SERVER['SERVER_PORT'] == 443 ||
               (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https');
    }
}