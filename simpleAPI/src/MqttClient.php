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

    // Cache für bekannte IDs
    private static $knownIds = [];

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
        $cmd = $this->buildMosquittoCommand('sub', 'test/connection', '', 1);
        $result = shell_exec($cmd . ' 2>&1');

        // Wenn kein Fehler zurückkommt, ist die Verbindung OK
        return !preg_match('/error|failed|unable/i', $result ?? '');
    }

    /**
     * Wert aus MQTT Topic lesen
     */
    public function getValue($topic)
    {
        $cmd = $this->buildMosquittoCommand('sub', $topic, '', 1);
        $output = shell_exec($cmd . ' 2>/dev/null');
        $value = trim($output ?? '');

        if ($value === '') {
            throw new \Exception("No data received for topic: $topic");
        }

        // Bei mosquitto_sub mit -v wird das Format "topic value" ausgegeben
        // Wir müssen das Topic-Präfix entfernen
        if (strpos($value, $topic . ' ') === 0) {
            $value = substr($value, strlen($topic . ' '));
        }

        return $value;
    }

    /**
     * Mehrere Topics gleichzeitig abfragen (Performance-Optimierung)
     */
    public function getMultipleValues($topics)
    {
        $results = [];

        $cmd = $this->buildMosquittoCommand('sub', $topics, '', count($topics));
        $cmd .= ' 2>/dev/null';

        $output = shell_exec($cmd);
        $lines = explode("\n", trim($output ?? ''));

        foreach ($lines as $line) {
            if (strpos($line, ' ') !== false) {
                list($topic, $value) = explode(' ', $line, 2);
                $results[$topic] = $value;
            }
        }

        // Nur Topics zurückgeben, die erfolgreich abgerufen wurden
        return $results;
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
    private function buildMosquittoCommand($type, $topics, $message = '', $count = null, $timeout = 1, $extraArgs = [])
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

        // Topic(s) hinzufügen
        if (is_array($topics)) {
            foreach ($topics as $topic) {
                $cmd .= sprintf(" -t %s", escapeshellarg($topic));
            }
        } else {
            $cmd .= sprintf(" -t %s", escapeshellarg($topics));
        }

        // Count und Timeout für subscribe
        if ($type === 'sub') {
            // Ausgabe des Topics erzwingen
            $cmd .= " -v";
            if ($count !== null) {
                $cmd .= sprintf(" -C %d", intval($count));
            }
            if ($timeout !== null) {
                $cmd .= sprintf(" -W %d", intval($timeout));
            }
        }

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
     * Alle verfügbaren IDs für einen bestimmten Typ finden (MQTT Wildcard Scan)
     */
    public function findAvailableIds($type)
    {
        // MQTT Wildcard verwenden um alle Topics zu finden
        $pattern = "openWB/{$type}/+/get/imported";

        $cmd = $this->buildMosquittoCommand('sub', $pattern, '');
        $cmd .= ' 2>/dev/null';

        $output = shell_exec($cmd);
        $ids = [];

        if ($output) {
            $lines = explode("\n", trim($output));
            foreach ($lines as $line) {
                if (preg_match("/openWB\/{$type}\/(\d+)\/get\/imported\s+(.+)/", $line, $matches)) {
                    $id = intval($matches[1]);
                    $value = trim($matches[2]);

                    // Nur IDs mit gültigen Werten (nicht null oder leer)
                    if ($value !== '' && $value !== 'null' && is_numeric($value)) {
                        $ids[] = $id;
                    }
                }
            }
        }

        $ids = array_unique($ids);

        if (empty($ids)) {
            throw new \Exception("No {$type} devices found via MQTT wildcard scan");
        }

        return $ids;
    }

    /**
     * Niedrigste verfügbare ID für einen Typ finden (Dynamische Erkennung)
     */
    public function getLowestId($type)
    {
        // Cache prüfen
        if (isset(self::$knownIds[$type])) {
            return self::$knownIds[$type];
        }

        // Alle verfügbaren IDs für diesen Typ finden
        $availableIds = $this->findAvailableIds($type);

        if (!empty($availableIds)) {
            // Niedrigste ID zurückgeben
            sort($availableIds, SORT_NUMERIC);
            $lowestId = $availableIds[0];
            self::$knownIds[$type] = $lowestId;
            return $lowestId;
        }

        return null;
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
