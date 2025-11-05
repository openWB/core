<?php

namespace SimpleAPI;

/**
 * MQTT Client mit mosquitto_sub/mosquitto_pub
 * Einfach, robust und funktioniert sofort
 */
class MqttClient
{
    private $server;
    private $port;
    private $username;
    private $password;
    private $clientid;

    public function __construct($config)
    {
        $this->server = $config['mqtt']['server'] ?? 'localhost';
        $this->port = $config['mqtt']['port'] ?? 1883;
        $this->username = $config['mqtt']['username'] ?? '';
        $this->password = $config['mqtt']['password'] ?? '';
        $this->clientid = $config['mqtt']['clientid'] ?? 'SimpleAPI_' . uniqid();
    }

    /**
     * Verbindung testen
     */
    public function connect()
    {
        // Test-Verbindung mit mosquitto_sub
        $cmd = $this->buildMosquittoCommand('sub', 'test/connection', '', ['-C', '1', '-W', '1']);
        $result = shell_exec($cmd . ' 2>&1');
        
        // Wenn kein Fehler zurückkommt, ist die Verbindung OK
        return !preg_match('/error|failed|unable/i', $result ?? '');
    }

    /**
     * Wert aus MQTT Topic lesen
     */
    public function getValue($topic)
    {
        $cmd = $this->buildMosquittoCommand('sub', $topic, '', ['-C', '1', '-W', '3']);
        $output = shell_exec($cmd . ' 2>/dev/null');
        $value = trim($output ?? '');
        
        if ($value === '') {
            throw new \Exception("No data received for topic: $topic");
        }
        
        return $value;
    }

    /**
     * Wert in MQTT Topic schreiben
     */
    public function setValue($topic, $value)
    {
        $cmd = $this->buildMosquittoCommand('pub', $topic, $value);
        $result = shell_exec($cmd . ' 2>&1');
        
        // Prüfen ob Fehler aufgetreten sind
        if (preg_match('/error|failed|unable/i', $result ?? '')) {
            throw new \Exception("Failed to publish to topic: $topic - $result");
        }
        
        return true;
    }

    /**
     * Mosquitto-Kommando erstellen
     */
    private function buildMosquittoCommand($type, $topic, $message = '', $extraArgs = [])
    {
        $binary = $type === 'sub' ? 'mosquitto_sub' : 'mosquitto_pub';
        
        $cmd = sprintf(
            "%s -h %s -p %d",
            $binary,
            escapeshellarg($this->server),
            $this->port
        );
        
        // Username/Passwort hinzufügen falls konfiguriert
        if (!empty($this->username)) {
            $cmd .= sprintf(" -u %s", escapeshellarg($this->username));
        }
        if (!empty($this->password)) {
            $cmd .= sprintf(" -P %s", escapeshellarg($this->password));
        }
        
        // Topic hinzufügen
        $cmd .= sprintf(" -t %s", escapeshellarg($topic));
        
        // Message für publish
        if ($type === 'pub' && $message !== '') {
            $cmd .= sprintf(" -m %s", escapeshellarg($message));
        }
        
        // Extra-Argumente hinzufügen
        foreach ($extraArgs as $arg) {
            $cmd .= " " . $arg;
        }
        
        return $cmd;
    }

    /**
     * Alle verfügbaren IDs für einen bestimmten Typ finden
     */
    public function findAvailableIds($type)
    {
        $ids = [];
        $maxIds = $type === 'chargepoint' ? 8 : 10;
        
        for ($i = 0; $i <= $maxIds; $i++) {
            try {
                $testTopic = "openWB/{$type}/{$i}/get/power";
                $value = $this->getValue($testTopic);
                
                if ($value !== null && $value !== '') {
                    $ids[] = $i;
                }
            } catch (\Exception $e) {
                // ID nicht verfügbar, weiter
                continue;
            }
        }
        
        if (empty($ids)) {
            throw new \Exception("No {$type} devices found via MQTT");
        }
        
        return $ids;
    }

    /**
     * Niedrigste verfügbare ID für einen Typ finden
     */
    public function getLowestId($type)
    {
        $ids = $this->findAvailableIds($type);
        return min($ids);
    }

    /**
     * Verbindung schließen (dummy für Kompatibilität)
     */
    public function disconnect()
    {
        // Nicht nötig bei mosquitto_sub/pub
    }

    public function __destruct()
    {
        $this->disconnect();
    }
}