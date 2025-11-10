<?php


require_once __DIR__ . '/src/MqttClient.php';
require_once __DIR__ . '/src/ParameterHandler.php';
require_once __DIR__ . '/src/Authenticator.php';


use SimpleAPI\MqttClient;
use SimpleAPI\ParameterHandler;
use SimpleAPI\Authenticator;

/**
 * SimpleAPI - HTTP zu MQTT Bridge für OpenWB
 */
class SimpleAPI
{
    private $config;
    private $mqttClient;
    private $parameterHandler;
    private $authenticator;

    public function __construct()
    {
        // Konfiguration laden
        $this->config = require __DIR__ . '/config/config.php';

        // MQTT Client initialisieren
        $this->mqttClient = new MqttClient($this->config);

        // Parameter Handler initialisieren
        $this->parameterHandler = new ParameterHandler($this->mqttClient);

        // Authenticator initialisieren
        $this->authenticator = new Authenticator($this->config);
    }

    /**
     * HTTP Request verarbeiten
     */
    public function handleRequest()
    {
        try {
            // Content-Type setzen
            header('Content-Type: application/json');

            // CORS Headers wenn konfiguriert
            if ($this->config['api']['cors_enabled'] ?? false) {
                header('Access-Control-Allow-Origin: *');
                header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
                header('Access-Control-Allow-Headers: Content-Type, Authorization');
            }

            // OPTIONS Request für CORS
            if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
                http_response_code(200);
                return;
            }

            // Parameter sammeln (GET und POST)
            $params = array_merge($_GET, $_POST);

            // Debug-Modus
            if (isset($params['debug']) && $params['debug'] === 'true') {
                $this->config['debug'] = true;
            }

            // Authentifizierung prüfen wenn erforderlich
            if (!$this->authenticator->authenticate($params)) {
                http_response_code(401);
                echo json_encode([
                    'success' => false,
                    'message' => 'Authentication failed'
                ]);
                return;
            }

            // Schreibvorgänge prüfen
            $writeParams = $this->getWriteParameters($params);
            if (!empty($writeParams)) {
                $result = $this->handleWriteRequest($writeParams, $params);

                // Raw-Output für Schreibvorgänge
                if (isset($params['raw']) && $params['raw'] === 'true') {
                    if ($result['success']) {
                        echo "OK"; // Erfolgreiche Schreibvorgänge -> "OK"
                    } else {
                        echo "ERROR: " . ($result['message'] ?? 'Unknown error');
                    }
                } else {
                    echo json_encode($result);
                }
                return;
            }

            // Lesevorgänge verarbeiten
            $readParams = $this->getReadParameters($params);
            if (!empty($readParams)) {
                $result = $this->handleReadRequest($readParams, $params);

                // Raw-Ausgabe Validierung
                if (isset($params['raw']) && $params['raw'] === 'true') {
                    if (count($readParams) > 1) {
                        // Fehler: Raw-Output nur bei einzelnen Parametern erlaubt
                        http_response_code(400);
                        echo json_encode([
                            'success' => false,
                            'message' => 'Raw output (raw=true) is only allowed for single parameter requests',
                            'error' => 'Multiple parameters detected: ' . implode(', ', array_keys($readParams))
                        ]);
                        return;
                    }

                    // Prüfe ob der Parameter für Raw-Output geeignet ist
                    $paramName = array_keys($readParams)[0];
                    if ($this->isComplexParameter($paramName)) {
                        http_response_code(400);
                        echo json_encode([
                            'success' => false,
                            'message' => 'Raw output (raw=true) is not supported for complex parameters',
                            'error' => "Parameter '{$paramName}' returns multiple values. Use specific single-value parameters instead.",
                            'suggestion' => 'Try parameters like get_counter_power, get_counter_voltage_p1, etc.'
                        ]);
                        return;
                    }

                    // Einzelner Parameter: Raw-Output verwenden
                    echo $this->formatRawOutput($result);
                } else {
                    echo json_encode($result);
                }
                return;
            }

            // Keine gültigen Parameter
            http_response_code(400);
            echo json_encode([
                'success' => false,
                'message' => 'No valid parameters provided'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode([
                'success' => false,
                'message' => 'Internal server error',
                'error' => $this->config['debug'] ? $e->getMessage() : 'An error occurred'
            ]);
        }
    }

    /**
     * Schreibbare Parameter aus Request extrahieren
     */
    private function getWriteParameters($params)
    {
        $writeParams = [];
        $writeableKeys = [
            'set_chargemode',
            'chargecurrent',
            'minimal_pv_soc',
            'minimal_permanent_current',
            'max_price_eco',
            'chargepoint_lock',
            'bat_mode'
        ];

        foreach ($writeableKeys as $key) {
            if (isset($params[$key])) {
                $writeParams[$key] = $params[$key];
            }
        }

        return $writeParams;
    }

    /**
     * Lesbare Parameter aus Request extrahieren
     */
    private function getReadParameters($params)
    {
        $readParams = [];
        $readableKeys = [
            // Chargepoint - Alle Daten
            'get_chargepoint_all',
            // Chargepoint - Spannungen
            'get_chargepoint_voltage_p1',
            'get_chargepoint_voltage_p2',
            'get_chargepoint_voltage_p3',
            'get_chargepoint_voltages',
            // Chargepoint - Ströme  
            'get_chargepoint_current_p1',
            'get_chargepoint_current_p2',
            'get_chargepoint_current_p3',
            'get_chargepoint_currents',
            // Chargepoint - Leistungen
            'get_chargepoint_power',
            'get_chargepoint_powers',
            // Chargepoint - Status & Energie
            'get_chargepoint_imported',
            'get_chargepoint_exported',
            'get_chargepoint_soc',
            'get_chargepoint_state_str',
            'get_chargepoint_fault_str',
            'get_chargepoint_fault_state',
            'get_chargepoint_phases_in_use',
            'get_chargepoint_plug_state',
            'get_chargepoint_charge_state',
            'get_chargepoint_chargemode',
            // Counter - Alle Daten  
            'get_counter',
            // Counter - Spannungen
            'get_counter_voltage_p1',
            'get_counter_voltage_p2',
            'get_counter_voltage_p3',
            'get_counter_voltages',
            // Counter - Ströme
            'get_counter_current_p1',
            'get_counter_current_p2',
            'get_counter_current_p3',
            'get_counter_currents',
            // Counter - Leistungen
            'get_counter_power',
            'get_counter_powers',
            'get_counter_power_factors',
            // Counter - Energie & Status
            'get_counter_imported',
            'get_counter_exported',
            'get_counter_daily_imported',
            'get_counter_daily_exported',
            'get_counter_frequency',
            'get_counter_fault_str',
            'get_counter_fault_state',
            // Battery - Alle Daten
            'battery',
            'get_battery',
            // Battery - Einzelwerte
            'get_battery_power',
            'get_battery_soc',
            'get_battery_currents',
            'get_battery_imported',
            'get_battery_exported',
            'get_battery_daily_imported',
            'get_battery_daily_exported',
            'get_battery_fault_str',
            'get_battery_fault_state',
            'get_battery_power_limit_controllable',
            // PV - Alle Daten
            'pv',
            'get_pv',
            // PV - Einzelwerte
            'get_pv_power',
            'get_pv_currents',
            'get_pv_exported',
            'get_pv_daily_exported',
            'get_pv_monthly_exported',
            'get_pv_yearly_exported',
            'get_pv_fault_str',
            'get_pv_fault_state'
        ];

        foreach ($readableKeys as $key) {
            if (isset($params[$key])) {
                $readParams[$key] = $params[$key];
            }
        }

        return $readParams;
    }

    /**
     * Schreibanfrage verarbeiten
     */
    private function handleWriteRequest($writeParams, $allParams)
    {
        foreach ($writeParams as $param => $value) {
            $chargepointId = $allParams['chargepoint_nr'] ?? null;

            // Auto-ID Feature: Niedrigste ID finden wenn keine angegeben
            if ($chargepointId === null && $this->isChargepointParameter($param)) {
                try {
                    $chargepointId = $this->mqttClient->getLowestId('chargepoint');
                    if ($chargepointId === null) {
                        return [
                            'success' => false,
                            'message' => 'No chargepoints available for auto-ID'
                        ];
                    }
                } catch (Exception $e) {
                    return [
                        'success' => false,
                        'message' => 'Auto-ID failed: ' . $e->getMessage()
                    ];
                }
            }

            $result = $this->parameterHandler->writeParameter($param, $value, $chargepointId);

            if (!$result['success']) {
                return $result;
            }
        }

        // Erfolgreiche Antwort für ersten Parameter (OpenWB Kompatibilität)
        $firstParam = array_keys($writeParams)[0];
        $firstValue = $writeParams[$firstParam];

        return [
            'success' => true,
            'message' => $this->getSuccessMessage($firstParam, $firstValue, $chargepointId ?? null),
            'data' => [
                'chargepoint_nr' => $chargepointId,
                $firstParam => $firstValue
            ]
        ];
    }

    /**
     * Leseanfrage verarbeiten
     */
    private function handleReadRequest($readParams, $allParams)
    {
        $result = [];

        foreach ($readParams as $param => $id) {
            try {
                // Auto-ID Feature: Niedrigste ID finden wenn "auto" oder leer
                if ($id === 'auto' || $id === '') {
                    $type = $this->getTypeFromParameter($param);
                    $id = $this->mqttClient->getLowestId($type);

                    if ($id === null) {
                        continue; // Skip wenn keine ID gefunden
                    }
                }

                $data = $this->parameterHandler->readParameter($param, $id);
                if ($data !== null) {
                    $result = array_merge($result, $data);
                }
            } catch (Exception $e) {
                // Wenn Auto-ID fehlschlägt, versuche ID 0 als Fallback
                if (($id === 'auto' || $id === '') && $this->config['debug']) {
                    $result['debug_info'][] = "Auto-ID failed for $param: " . $e->getMessage();
                }

                // Fallback auf ID 0 für Chargepoints
                if (strpos($param, 'chargepoint') !== false) {
                    try {
                        $data = $this->parameterHandler->readParameter($param, 0);
                        if ($data !== null) {
                            $result = array_merge($result, $data);
                        }
                    } catch (Exception $fallbackError) {
                        if ($this->config['debug']) {
                            $result['debug_info'][] = "Fallback to ID 0 failed for $param: " . $fallbackError->getMessage();
                        }
                    }
                }
            }
        }

        return $result;
    }

    /**
     * Typ aus Parameter ermitteln
     */
    private function getTypeFromParameter($param)
    {
        if (strpos($param, 'chargepoint') !== false || strpos($param, 'get_chargepoint') !== false) {
            return 'chargepoint';
        } elseif (strpos($param, 'battery') !== false) {
            return 'bat';  // MQTT Topic verwendet 'bat' nicht 'battery'
        } elseif (strpos($param, 'pv') !== false) {
            return 'pv';
        } elseif (strpos($param, 'counter') !== false) {
            return 'counter';
        }

        return 'chargepoint'; // Fallback
    }

    /**
     * Prüfen ob Parameter komplex ist (mehrere Werte zurückgibt)
     */
    private function isComplexParameter($param)
    {
        $complexParameters = [
            'get_chargepoint_all',
            'get_counter',
            'battery',
            'get_battery',
            'pv',
            'get_pv',
            'get_chargepoint_voltages',
            'get_chargepoint_currents',
            'get_chargepoint_powers',
            'get_counter_voltages',
            'get_counter_currents',
            'get_counter_powers',
            'get_counter_power_factors',
            'get_battery_currents',
            'get_pv_currents'
        ];

        return in_array($param, $complexParameters);
    }

    /**
     * Prüfen ob Parameter zu Chargepoint gehört
     */
    private function isChargepointParameter($param)
    {
        $chargepointParameters = [
            'set_chargemode',
            'chargecurrent',
            'minimal_pv_soc',
            'minimal_permanent_current',
            'max_price_eco',
            'chargepoint_lock',
            'bat_mode'
        ];

        return in_array($param, $chargepointParameters) || strpos($param, 'chargepoint') !== false;
    }

    /**
     * Erfolgs-Nachricht generieren
     */
    private function getSuccessMessage($param, $value, $chargepointId)
    {
        switch ($param) {
            case 'set_chargemode':
                return "Chargemode for chargepoint {$chargepointId} set to {$value}.";
            case 'chargecurrent':
                return "Chargecurrent for chargepoint {$chargepointId} set to {$value}A";
            default:
                return "Parameter {$param} set to {$value}.";
        }
    }

    /**
     * Raw-Ausgabe formatieren
     */
    private function formatRawOutput($data)
    {
        if (is_array($data)) {
            $firstKey = array_keys($data)[0];
            $firstValue = $data[$firstKey];

            if (is_array($firstValue) && count($firstValue) === 1) {
                return array_values($firstValue)[0];
            }
        }

        return $data;
    }
}

// API instanziieren und Request verarbeiten
$api = new SimpleAPI();
$api->handleRequest();
