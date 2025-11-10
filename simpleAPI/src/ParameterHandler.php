<?php

namespace SimpleAPI;

/**
 * Handler für das Lesen und Schreiben von Parametern über MQTT
 */
class ParameterHandler
{
    private $mqttClient;

    public function __construct($mqttClient)
    {
        $this->mqttClient = $mqttClient;
    }

    /**
     * Parameter lesen
     */
    public function readParameter($param, $id)
    {
        switch ($param) {
            case 'get_chargepoint_all':
                return $this->getChargepointAll($id);

            case 'get_chargepoint_voltage_p1':
                return $this->getChargepointVoltage($id, 1);

            case 'get_chargepoint_voltage_p2':
                return $this->getChargepointVoltage($id, 2);

            case 'get_chargepoint_voltage_p3':
                return $this->getChargepointVoltage($id, 3);

            case 'get_chargepoint_voltages':
                return $this->getChargepointVoltages($id);

            case 'get_chargepoint_current_p1':
                return $this->getChargepointCurrent($id, 1);

            case 'get_chargepoint_current_p2':
                return $this->getChargepointCurrent($id, 2);

            case 'get_chargepoint_current_p3':
                return $this->getChargepointCurrent($id, 3);

            case 'get_chargepoint_currents':
                return $this->getChargepointCurrents($id);

            case 'get_chargepoint_power':
                return $this->getChargepointPower($id);

            case 'get_chargepoint_powers':
                return $this->getChargepointPowers($id);

            case 'battery':
                return $this->getBattery($id);

            case 'pv':
                return $this->getPv($id);

            case 'get_counter':
                return $this->getCounter($id);

                // Chargepoint - Einzelwerte
            case 'get_chargepoint_imported':
                return $this->getChargepointImported($id);
            case 'get_chargepoint_exported':
                return $this->getChargepointExported($id);
            case 'get_chargepoint_soc':
                return $this->getChargepointSoc($id);
            case 'get_chargepoint_state_str':
                return $this->getChargepointStateStr($id);
            case 'get_chargepoint_fault_str':
                return $this->getChargepointFaultStr($id);
            case 'get_chargepoint_fault_state':
                return $this->getChargepointFaultState($id);
            case 'get_chargepoint_phases_in_use':
                return $this->getChargepointPhasesInUse($id);
            case 'get_chargepoint_plug_state':
                return $this->getChargepointPlugState($id);
            case 'get_chargepoint_charge_state':
                return $this->getChargepointChargeState($id);
            case 'get_chargepoint_chargemode':
                return $this->getChargepointChargemode($id);

                // Counter - Einzelwerte
            case 'get_counter_voltage_p1':
                return $this->getCounterVoltageP1($id);
            case 'get_counter_voltage_p2':
                return $this->getCounterVoltageP2($id);
            case 'get_counter_voltage_p3':
                return $this->getCounterVoltageP3($id);
            case 'get_counter_voltages':
                return $this->getCounterVoltages($id);
            case 'get_counter_current_p1':
                return $this->getCounterCurrentP1($id);
            case 'get_counter_current_p2':
                return $this->getCounterCurrentP2($id);
            case 'get_counter_current_p3':
                return $this->getCounterCurrentP3($id);
            case 'get_counter_currents':
                return $this->getCounterCurrents($id);
            case 'get_counter_power':
                return $this->getCounterPower($id);
            case 'get_counter_powers':
                return $this->getCounterPowers($id);
            case 'get_counter_power_factors':
                return $this->getCounterPowerFactors($id);
            case 'get_counter_imported':
                return $this->getCounterImported($id);
            case 'get_counter_exported':
                return $this->getCounterExported($id);
            case 'get_counter_daily_imported':
                return $this->getCounterDailyImported($id);
            case 'get_counter_daily_exported':
                return $this->getCounterDailyExported($id);
            case 'get_counter_frequency':
                return $this->getCounterFrequency($id);
            case 'get_counter_fault_str':
                return $this->getCounterFaultStr($id);
            case 'get_counter_fault_state':
                return $this->getCounterFaultState($id);

                // Battery - Zusätzliche Einzelwerte
            case 'get_battery':
                return $this->getBattery($id);
            case 'get_battery_power':
                return $this->getBatteryPower($id);
            case 'get_battery_soc':
                return $this->getBatterySoc($id);
            case 'get_battery_currents':
                return $this->getBatteryCurrents($id);
            case 'get_battery_imported':
                return $this->getBatteryImported($id);
            case 'get_battery_exported':
                return $this->getBatteryExported($id);
            case 'get_battery_daily_imported':
                return $this->getBatteryDailyImported($id);
            case 'get_battery_daily_exported':
                return $this->getBatteryDailyExported($id);
            case 'get_battery_fault_str':
                return $this->getBatteryFaultStr($id);
            case 'get_battery_fault_state':
                return $this->getBatteryFaultState($id);
            case 'get_battery_power_limit_controllable':
                return $this->getBatteryPowerLimitControllable($id);

                // PV - Zusätzliche Einzelwerte
            case 'get_pv':
                return $this->getPv($id);
            case 'get_pv_power':
                return $this->getPvPower($id);
            case 'get_pv_currents':
                return $this->getPvCurrents($id);
            case 'get_pv_exported':
                return $this->getPvExported($id);
            case 'get_pv_daily_exported':
                return $this->getPvDailyExported($id);
            case 'get_pv_monthly_exported':
                return $this->getPvMonthlyExported($id);
            case 'get_pv_yearly_exported':
                return $this->getPvYearlyExported($id);
            case 'get_pv_fault_str':
                return $this->getPvFaultStr($id);
            case 'get_pv_fault_state':
                return $this->getPvFaultState($id);

            default:
                return null;
        }
    }

    /**
     * Parameter schreiben
     */
    public function writeParameter($param, $value, $chargepointId = null)
    {
        try {
            switch ($param) {
                case 'set_chargemode':
                    return $this->setChargemode($chargepointId, $value);
                case 'chargecurrent':
                    return $this->setChargecurrent($chargepointId, $value);
                case 'minimal_permanent_current':
                    return $this->setMinimalPermanentCurrent($chargepointId, $value);
                case 'minimal_pv_soc':
                    return $this->setMinimalPvSoc($chargepointId, $value);
                case 'max_price_eco':
                    return $this->setMaxPriceEco($chargepointId, $value);
                case 'chargepoint_lock':
                    return $this->setChargepointLock($chargepointId, $value);
                case 'bat_mode':
                    return $this->setBatMode($value);
                default:
                    return ['success' => false, 'message' => 'Unknown write parameter'];
            }
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }

    /**
     * Alle Daten eines Ladepunkts (Performance-optimiert)
     */
    private function getChargepointAll($id)
    {
        $prefix = "openWB/chargepoint/{$id}/get/";

        // Alle benötigten Topics in einem Aufruf abfragen
        $topics = [
            $prefix . 'power',
            $prefix . 'voltages',
            $prefix . 'currents',
            $prefix . 'powers',
            $prefix . 'state_str',
            $prefix . 'fault_str',
            $prefix . 'fault_state',
            $prefix . 'imported',
            $prefix . 'exported',
            $prefix . 'phases_in_use',
            $prefix . 'plug_state',
            $prefix . 'charge_state',
            $prefix . 'soc',
            $prefix . 'soc_timestamp',
            $prefix . 'vehicle_id',
            $prefix . 'evse_current',
            "openWB/chargepoint/{$id}/set/charge_template"
        ];

        $values = $this->mqttClient->getMultipleValues($topics);

        // Arrays parsen
        try {
            $voltages = json_decode($values[$prefix . 'voltages'] ?? '[]', true) ?: [0, 0, 0];
            $currents = json_decode($values[$prefix . 'currents'] ?? '[]', true) ?: [0, 0, 0];
            $powers = json_decode($values[$prefix . 'powers'] ?? '[]', true) ?: [0, 0, 0];
        } catch (Exception $e) {
            $voltages = [0, 0, 0];
            $currents = [0, 0, 0];
            $powers = [0, 0, 0];
        }

        // Chargemode aus Template extrahieren
        $chargemode = 'stop';
        try {
            $template = json_decode($values["openWB/chargepoint/{$id}/set/charge_template"] ?? '{}', true);
            $chargemode = $template['chargemode']['selected'] ?? 'stop';
        } catch (Exception $e) {
            // Fallback
        }

        $data = [
            "chargepoint_{$id}" => [
                'power' => floatval($values[$prefix . 'power'] ?? 0),
                'voltages' => [
                    floatval($voltages[0] ?? 0),
                    floatval($voltages[1] ?? 0),
                    floatval($voltages[2] ?? 0)
                ],
                'currents' => [
                    floatval($currents[0] ?? 0),
                    floatval($currents[1] ?? 0),
                    floatval($currents[2] ?? 0)
                ],
                'powers' => [
                    floatval($powers[0] ?? 0),
                    floatval($powers[1] ?? 0),
                    floatval($powers[2] ?? 0)
                ],
                'state_str' => $values[$prefix . 'state_str'] ?? 'Unbekannt',
                'fault_str' => $values[$prefix . 'fault_str'] ?? 'Kein Fehler',
                'fault_state' => intval($values[$prefix . 'fault_state'] ?? 0),
                'imported' => floatval($values[$prefix . 'imported'] ?? 0),
                'exported' => floatval($values[$prefix . 'exported'] ?? 0),
                'phases_in_use' => intval($values[$prefix . 'phases_in_use'] ?? 1),
                'plug_state' => $this->parseBooleanValue($values[$prefix . 'plug_state'] ?? 'false'),
                'charge_state' => $this->parseBooleanValue($values[$prefix . 'charge_state'] ?? 'false'),
                'soc' => floatval($values[$prefix . 'soc'] ?? 0),
                'soc_timestamp' => $values[$prefix . 'soc_timestamp'] ?? null,
                'vehicle_id' => $values[$prefix . 'vehicle_id'] ?? null,
                'evse_current' => floatval($values[$prefix . 'evse_current'] ?? 0),
                'chargemode' => $chargemode
            ]
        ];

        // manual_lock Status auslesen
        $manualLockTopic = "openWB/chargepoint/{$id}/set/manual_lock";
        $manualLock = $this->mqttClient->getValue($manualLockTopic);
        $data["chargepoint_{$id}"]['manual_lock'] = $this->parseBooleanValue($manualLock ?? 'false');

        return $data;
    }

    /**
     * Boolean-Wert parsen
     */
    private function parseBooleanValue($value)
    {
        if (is_bool($value)) {
            return $value;
        }

        $value = strtolower(trim($value, '"'));
        return in_array($value, ['true', '1', 'yes', 'on']);
    }

    /**
     * Spannung einer Phase
     */
    private function getChargepointVoltage($id, $phase)
    {
        // OpenWB gibt Spannungen als Array zurück: [237.79, 0, 0]
        $topic = "openWB/chargepoint/{$id}/get/voltages";
        $voltagesJson = $this->mqttClient->getValue($topic);

        try {
            $voltages = json_decode($voltagesJson, true);
            $voltage = $voltages[$phase - 1] ?? 0; // Array ist 0-basiert, Phase 1-basiert

            return [
                "chargepoint_{$id}" => [
                    "voltage_p{$phase}" => floatval($voltage)
                ]
            ];
        } catch (Exception $e) {
            return [
                "chargepoint_{$id}" => [
                    "voltage_p{$phase}" => 0
                ]
            ];
        }
    }

    /**
     * Alle Spannungen
     */
    private function getChargepointVoltages($id)
    {
        $topic = "openWB/chargepoint/{$id}/get/voltages";
        $voltagesJson = $this->mqttClient->getValue($topic);

        try {
            $voltages = json_decode($voltagesJson, true);

            return [
                "chargepoint_{$id}" => [
                    'voltages' => [
                        floatval($voltages[0] ?? 0),
                        floatval($voltages[1] ?? 0),
                        floatval($voltages[2] ?? 0)
                    ]
                ]
            ];
        } catch (Exception $e) {
            return [
                "chargepoint_{$id}" => [
                    'voltages' => [0, 0, 0]
                ]
            ];
        }
    }

    /**
     * Strom einer Phase
     */
    private function getChargepointCurrent($id, $phase)
    {
        // OpenWB gibt Ströme als Array zurück: [0, 0, 0]
        $topic = "openWB/chargepoint/{$id}/get/currents";
        $currentsJson = $this->mqttClient->getValue($topic);

        try {
            $currents = json_decode($currentsJson, true);
            $current = $currents[$phase - 1] ?? 0; // Array ist 0-basiert, Phase 1-basiert

            return [
                "chargepoint_{$id}" => [
                    "current_p{$phase}" => floatval($current)
                ]
            ];
        } catch (Exception $e) {
            return [
                "chargepoint_{$id}" => [
                    "current_p{$phase}" => 0
                ]
            ];
        }
    }

    /**
     * Alle Ströme
     */
    private function getChargepointCurrents($id)
    {
        $topic = "openWB/chargepoint/{$id}/get/currents";
        $currentsJson = $this->mqttClient->getValue($topic);

        try {
            $currents = json_decode($currentsJson, true);

            return [
                "chargepoint_{$id}" => [
                    'currents' => [
                        floatval($currents[0] ?? 0),
                        floatval($currents[1] ?? 0),
                        floatval($currents[2] ?? 0)
                    ]
                ]
            ];
        } catch (Exception $e) {
            return [
                "chargepoint_{$id}" => [
                    'currents' => [0, 0, 0]
                ]
            ];
        }
    }

    /**
     * Gesamtleistung
     */
    private function getChargepointPower($id)
    {
        $topic = "openWB/chargepoint/{$id}/get/power";
        $power = $this->getNumericValue($topic);

        return [
            "chargepoint_{$id}" => [
                'power' => $power
            ]
        ];
    }

    /**
     * Leistung aller Phasen
     */
    private function getChargepointPowers($id)
    {
        $topic = "openWB/chargepoint/{$id}/get/powers";
        $powersJson = $this->mqttClient->getValue($topic);

        try {
            $powers = json_decode($powersJson, true);

            return [
                "chargepoint_{$id}" => [
                    'powers' => [
                        floatval($powers[0] ?? 0),
                        floatval($powers[1] ?? 0),
                        floatval($powers[2] ?? 0)
                    ]
                ]
            ];
        } catch (Exception $e) {
            return [
                "chargepoint_{$id}" => [
                    'powers' => [0, 0, 0]
                ]
            ];
        }
    }

    /**
     * Batterie-Daten (Performance-optimiert)
     */
    private function getBattery($id)
    {
        $prefix = "openWB/bat/{$id}/get/";

        // Alle benötigten Topics in einem Aufruf abfragen
        $topics = [
            $prefix . 'power',
            $prefix . 'soc',
            $prefix . 'currents',
            $prefix . 'imported',
            $prefix . 'exported',
            $prefix . 'daily_imported',
            $prefix . 'daily_exported',
            $prefix . 'fault_str',
            $prefix . 'fault_state',
            $prefix . 'power_limit_controllable'
        ];

        $values = $this->mqttClient->getMultipleValues($topics);

        // Currents Array parsen
        try {
            $currents = json_decode($values[$prefix . 'currents'] ?? '[]', true) ?: [0, 0, 0];
        } catch (Exception $e) {
            $currents = [0, 0, 0];
        }

        return [
            "battery_{$id}" => [
                'power' => floatval($values[$prefix . 'power'] ?? 0),
                'soc' => intval($values[$prefix . 'soc'] ?? 0),
                'currents' => [
                    floatval($currents[0] ?? 0),
                    floatval($currents[1] ?? 0),
                    floatval($currents[2] ?? 0)
                ],
                'imported' => floatval($values[$prefix . 'imported'] ?? 0),
                'exported' => floatval($values[$prefix . 'exported'] ?? 0),
                'daily_imported' => floatval($values[$prefix . 'daily_imported'] ?? 0),
                'daily_exported' => floatval($values[$prefix . 'daily_exported'] ?? 0),
                'fault_str' => $values[$prefix . 'fault_str'] ?? 'Kein Fehler',
                'fault_state' => intval($values[$prefix . 'fault_state'] ?? 0),
                'power_limit_controllable' => $this->parseBooleanValue($values[$prefix . 'power_limit_controllable'] ?? 'false')
            ]
        ];
    }

    /**
     * PV-Daten (Performance-optimiert)
     */
    private function getPv($id)
    {
        $prefix = "openWB/pv/{$id}/get/";

        // Alle benötigten Topics in einem Aufruf abfragen
        $topics = [
            $prefix . 'power',
            $prefix . 'currents',
            $prefix . 'exported',
            $prefix . 'daily_exported',
            $prefix . 'monthly_exported',
            $prefix . 'yearly_exported',
            $prefix . 'fault_str',
            $prefix . 'fault_state'
        ];

        $values = $this->mqttClient->getMultipleValues($topics);

        // Currents Array parsen
        try {
            $currents = json_decode($values[$prefix . 'currents'] ?? '[]', true) ?: [0, 0, 0];
        } catch (Exception $e) {
            $currents = [0, 0, 0];
        }

        return [
            "pv_{$id}" => [
                'power' => floatval($values[$prefix . 'power'] ?? 0),
                'currents' => [
                    floatval($currents[0] ?? 0),
                    floatval($currents[1] ?? 0),
                    floatval($currents[2] ?? 0)
                ],
                'exported' => floatval($values[$prefix . 'exported'] ?? 0),
                'daily_exported' => floatval($values[$prefix . 'daily_exported'] ?? 0),
                'monthly_exported' => floatval($values[$prefix . 'monthly_exported'] ?? 0),
                'yearly_exported' => floatval($values[$prefix . 'yearly_exported'] ?? 0),
                'fault_str' => $values[$prefix . 'fault_str'] ?? 'Kein Fehler',
                'fault_state' => intval($values[$prefix . 'fault_state'] ?? 0)
            ]
        ];
    }

    /**
     * Zähler-Daten (Counter) - Performance-optimiert
     */
    private function getCounter($id)
    {
        $prefix = "openWB/counter/{$id}/get/";

        // Alle benötigten Topics in einem Aufruf abfragen
        $topics = [
            $prefix . 'power',
            $prefix . 'voltages',
            $prefix . 'currents',
            $prefix . 'powers',
            $prefix . 'power_factors',
            $prefix . 'frequency',
            $prefix . 'exported',
            $prefix . 'daily_exported',
            $prefix . 'imported',
            $prefix . 'daily_imported',
            $prefix . 'fault_str',
            $prefix . 'fault_state'
        ];

        $values = $this->mqttClient->getMultipleValues($topics);

        // Arrays parsen
        try {
            $voltages = json_decode($values[$prefix . 'voltages'] ?? '[]', true) ?: [0, 0, 0];
            $currents = json_decode($values[$prefix . 'currents'] ?? '[]', true) ?: [0, 0, 0];
            $powers = json_decode($values[$prefix . 'powers'] ?? '[]', true) ?: [0, 0, 0];
            $power_factors = json_decode($values[$prefix . 'power_factors'] ?? '[]', true) ?: [0, 0, 0];
        } catch (Exception $e) {
            $voltages = [0, 0, 0];
            $currents = [0, 0, 0];
            $powers = [0, 0, 0];
            $power_factors = [0, 0, 0];
        }

        return [
            "counter_{$id}" => [
                'power' => floatval($values[$prefix . 'power'] ?? 0),
                'voltages' => [
                    floatval($voltages[0] ?? 0),
                    floatval($voltages[1] ?? 0),
                    floatval($voltages[2] ?? 0)
                ],
                'currents' => [
                    floatval($currents[0] ?? 0),
                    floatval($currents[1] ?? 0),
                    floatval($currents[2] ?? 0)
                ],
                'powers' => [
                    floatval($powers[0] ?? 0),
                    floatval($powers[1] ?? 0),
                    floatval($powers[2] ?? 0)
                ],
                'power_factors' => [
                    floatval($power_factors[0] ?? 0),
                    floatval($power_factors[1] ?? 0),
                    floatval($power_factors[2] ?? 0)
                ],
                'frequency' => floatval($values[$prefix . 'frequency'] ?? 50.0),
                'exported' => floatval($values[$prefix . 'exported'] ?? 0),
                'daily_exported' => floatval($values[$prefix . 'daily_exported'] ?? 0),
                'imported' => floatval($values[$prefix . 'imported'] ?? 0),
                'daily_imported' => floatval($values[$prefix . 'daily_imported'] ?? 0),
                'fault_str' => $values[$prefix . 'fault_str'] ?? 'Kein Fehler',
                'fault_state' => intval($values[$prefix . 'fault_state'] ?? 0)
            ]
        ];
    }

    /**
     * Lademodus setzen (OpenWB Template-System)
     */
    private function setChargemode($chargepointId, $mode)
    {
        // Gültige Modi mapping
        $validModes = [
            'instant' => 'instant_charging',
            'pv' => 'pv_charging',
            'eco' => 'eco_charging',
            'stop' => 'stop',
            'target' => 'scheduled_charging'
        ];

        if (!isset($validModes[$mode])) {
            return ['success' => false, 'message' => 'Invalid chargemode. Valid modes: ' . implode(', ', array_keys($validModes))];
        }

        $selectedMode = $validModes[$mode];

        try {
            // 1. Aktuelles Template von /set/charge_template auslesen 
            $templateTopic = "openWB/chargepoint/{$chargepointId}/set/charge_template";
            $templateJson = $this->mqttClient->getValue($templateTopic);

            if (!$templateJson) {
                return ['success' => false, 'message' => 'Could not read current charge template from set topic'];
            }

            $template = json_decode($templateJson, true);
            if (!$template) {
                return ['success' => false, 'message' => 'Invalid charge template format'];
            }

            // 2. Chargemode im Template ändern
            if (!isset($template['chargemode'])) {
                $template['chargemode'] = [];
            }

            $template['chargemode']['selected'] = $selectedMode;

            // 3. Geändertes Template an /set/charge_template zurückschreiben
            $setTopic = "openWB/set/chargepoint/{$chargepointId}/set/charge_template";
            $newTemplateJson = json_encode($template);

            if ($this->mqttClient->setValue($setTopic, $newTemplateJson)) {
                return ['success' => true, 'message' => "Chargemode set to {$mode} ({$selectedMode})"];
            }

            return ['success' => false, 'message' => 'Failed to update charge template'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Error setting chargemode: ' . $e->getMessage()];
        }
    }

    /**
     * Ladestrom setzen (instant_charging.current im Template)
     */
    private function setChargecurrent($chargepointId, $current)
    {
        try {
            $templateTopic = "openWB/chargepoint/{$chargepointId}/set/charge_template";
            $templateJson = $this->mqttClient->getValue($templateTopic);
            if (!$templateJson) {
                return ['success' => false, 'message' => 'Could not read current charge template from set topic'];
            }
            $template = json_decode($templateJson, true);
            if (!$template || !isset($template['chargemode']['instant_charging'])) {
                return ['success' => false, 'message' => 'Invalid charge template format or missing instant_charging'];
            }
            $template['chargemode']['instant_charging']['current'] = floatval($current);
            $setTopic = "openWB/set/chargepoint/{$chargepointId}/set/charge_template";
            $newTemplateJson = json_encode($template);
            if ($this->mqttClient->setValue($setTopic, $newTemplateJson)) {
                return ['success' => true, 'message' => "Chargecurrent set to {$current}A for chargepoint {$chargepointId}"];
            }
            return ['success' => false, 'message' => 'Failed to update charge template'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Error setting chargecurrent: ' . $e->getMessage()];
        }
    }

    /**
     * Minimalen permanenten Strom setzen (pv_charging.min_current im Template)
     */
    private function setMinimalPermanentCurrent($chargepointId, $value)
    {
        try {
            $templateTopic = "openWB/chargepoint/{$chargepointId}/set/charge_template";
            $templateJson = $this->mqttClient->getValue($templateTopic);
            if (!$templateJson) {
                return ['success' => false, 'message' => 'Could not read current charge template from set topic'];
            }
            $template = json_decode($templateJson, true);
            if (!$template || !isset($template['chargemode']['pv_charging'])) {
                return ['success' => false, 'message' => 'Invalid charge template format or missing pv_charging'];
            }
            $template['chargemode']['pv_charging']['min_current'] = floatval($value);
            $setTopic = "openWB/set/chargepoint/{$chargepointId}/set/charge_template";
            $newTemplateJson = json_encode($template);
            if ($this->mqttClient->setValue($setTopic, $newTemplateJson)) {
                return ['success' => true, 'message' => "Minimal permanent current set to {$value}A for chargepoint {$chargepointId}"];
            }
            return ['success' => false, 'message' => 'Failed to update charge template'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Error setting minimal permanent current: ' . $e->getMessage()];
        }
    }

    /**
     * Minimalen PV SoC setzen (pv_charging.min_soc im Template)
     */
    private function setMinimalPvSoc($chargepointId, $value)
    {
        try {
            $templateTopic = "openWB/chargepoint/{$chargepointId}/set/charge_template";
            $templateJson = $this->mqttClient->getValue($templateTopic);
            if (!$templateJson) {
                return ['success' => false, 'message' => 'Could not read current charge template from set topic'];
            }
            $template = json_decode($templateJson, true);
            if (!$template || !isset($template['chargemode']['pv_charging'])) {
                return ['success' => false, 'message' => 'Invalid charge template format or missing pv_charging'];
            }
            $template['chargemode']['pv_charging']['min_soc'] = intval($value);
            $setTopic = "openWB/set/chargepoint/{$chargepointId}/set/charge_template";
            $newTemplateJson = json_encode($template);
            if ($this->mqttClient->setValue($setTopic, $newTemplateJson)) {
                return ['success' => true, 'message' => "Minimal PV SoC set to {$value}% for chargepoint {$chargepointId}"];
            }
            return ['success' => false, 'message' => 'Failed to update charge template'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Error setting minimal PV SoC: ' . $e->getMessage()];
        }
    }

    /**
     * Maximalen ECO-Preis setzen (eco_charging.max_price im Template)
     */
    private function setMaxPriceEco($chargepointId, $value)
    {
        try {
            $templateTopic = "openWB/chargepoint/{$chargepointId}/set/charge_template";
            $templateJson = $this->mqttClient->getValue($templateTopic);
            if (!$templateJson) {
                return ['success' => false, 'message' => 'Could not read current charge template from set topic'];
            }
            $template = json_decode($templateJson, true);
            if (!$template || !isset($template['chargemode']['eco_charging'])) {
                return ['success' => false, 'message' => 'Invalid charge template format or missing eco_charging'];
            }
            $template['chargemode']['eco_charging']['max_price'] = floatval($value);
            $setTopic = "openWB/set/chargepoint/{$chargepointId}/set/charge_template";
            $newTemplateJson = json_encode($template);
            if ($this->mqttClient->setValue($setTopic, $newTemplateJson)) {
                return ['success' => true, 'message' => "Max price eco set to {$value} for chargepoint {$chargepointId}"];
            }
            return ['success' => false, 'message' => 'Failed to update charge template'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Error setting max price eco: ' . $e->getMessage()];
        }
    }

    /**
     * Chargepoint Lock setzen
     */
    private function setChargepointLock($chargepointId, $value)
    {
        $topic = "openWB/set/chargepoint/{$chargepointId}/set/manual_lock";
        $lockValue = $value ? 'true' : 'false';
        if ($this->mqttClient->setValue($topic, $lockValue)) {
            return ['success' => true, 'message' => "Chargepoint lock set to {$lockValue} for chargepoint {$chargepointId}"];
        }
        return ['success' => false, 'message' => 'Failed to set chargepoint lock'];
    }

    /**
     * Batterie-Modus setzen
     */
    private function setBatMode($value)
    {
        // Gültige Modi
        $validModes = ['min_soc_bat_mode', 'ev_mode', 'bat_mode'];

        if (!in_array($value, $validModes)) {
            return ['success' => false, 'message' => 'Invalid bat_mode. Valid modes: ' . implode(', ', $validModes)];
        }

        try {
            $topic = "openWB/set/general/chargemode_config/pv_charging/bat_mode";

            if ($this->mqttClient->setValue($topic, $value)) {
                return ['success' => true, 'message' => "Bat mode set to {$value}"];
            }

            return ['success' => false, 'message' => 'Failed to set bat mode'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Error setting bat mode: ' . $e->getMessage()];
        }
    }
}
