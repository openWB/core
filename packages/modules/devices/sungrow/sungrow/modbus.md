# Modbus Adressen für Sungrow SH* und SG* Wechselrichter

## Datengrundlage:
* TI_20230918_Communication Protocol of Residential and Commerical PV Grid-connected Inverter_V1.1.58_EN.pdf
* TI_20231019_Communication Protocol of Residential Hybrid Inverter_V1.1.2_EN.pdf
* modbus_finder.py an SH10RT-V112 (LAN) Firmware SAPPHIRE-H_B001.V000.P005-20231027
* modbus_finder.py an SH10RT-V112 (WiNet-S) Firmware WINET-SV200.001.00.P023
* modbus_finder.py an SG10RT (WiNet-S) Firmware BERYL-S_B000.V000.P039-20230626 / WINET-SV200.001.00.P023

## Werte
| Wert                                | SH_LAN | SH_WiNet | SG_WiNet      | Einheit | Typ            | Bemerkung                                                        |
|-------------------------------------|--------|----------|---------------|---------|----------------|------------------------------------------------------------------|
| WR: Zähler inkl. Batterieentladung  | 5003   | 5003     | --            | 0.1 kWh | UINT_32 mixed  | Delta zu 'WR: Zähler Gesamtertrag' ist entladene **Netz**energie |
| WR: Zähler Gesamtertrag             | 5660   | --       | 5143          | 0.1 kWh | UINT_32 mixed  | Wirkleistungszähler, abweichend zu Gesamt-PV-Stromerzeugung      |
| WR: AC Ausgangsspannung Phase A     | 5018   | 5018     | 5018          | 0.1 V   | UINT_16 little | Unterscheidet sich pro WR (nicht vom Meter gemessen)             |
| WR: AC Ausgangsspannung Phase B     | 5019   | 5019     | 5019          | 0.1 V   | UINT_16 little | Unterscheidet sich pro WR (nicht vom Meter gemessen)             |
| WR: AC Ausgangsspannung Phase C     | 5020   | 5020     | 5020          | 0.1 V   | UINT_16 little | Unterscheidet sich pro WR (nicht vom Meter gemessen)             |
| WR: Akt. DC Bruttoleistung          | 5016   | 5016     | 5016          | 1 W     | INT_32 mixed   |                                                                  |
| WR: Akt. AC Wirkleistung            | 13033  | 13033    | --            | 1 W     | INT_32 mixed   | ggf. Speicherladung addieren für effektive PV-Leistung           |
| WR: Akt. AC Wirkleistung            | 5030   | --       | 5030          | 1 W     | INT_32 mixed   | 5030 "altes" Register, 13033 bevorzugt für SH Versionen          |
| WR: Akt. Leistungsfluss             | 13000  | 13000    | --            | ja/nein | 8-bit bitmask  | (v.r.) Bit0: PV-Erzeugung, Bit1: Batt. lädt, Bit2: Batt. entlädt |
| BAT: Akt. Leistung (ein-/ausgehend) | 13021  | 13021    | --            | 1 W     | UINT16 little  | Immer positiv, bei Be- und Entladung. WR Leistungsfluss beachten |
| BAT: SoC                            | 13022  | 13022    | --            | 0.1 %   | UINT16 little  |                                                                  |
| BAT: Zähler Ladung von PV           | 13012  | 13012    | --            | 0.1 kWh | UINT32 mixed   |                                                                  |
| BAT: Zähler Gesamtladung            | 13026  | 13026    | --            | 0.1 kWh | UINT32 mixed   |                                                                  |
| BAT: Zähler Gesamtentladung         | 13040  | 13040    | --            | 0.1 kWh | UINT32 mixed   |                                                                  |
| Netz: Akt. Wirkleistung             | 13009  | 13009    | --            | -1 W    | INT_32 mixed   |                                                                  |
| Netz: Akt. Wirkleistung             | --     | --       | ? 5090 ? 5082 | 1 W     | INT_32 mixed   |                                                                  |
| Netz: Akt. Frequenz                 | 5035   | --       | 5035          | 0.1 Hz  | UINT_16 little |                                                                  |
| Netz: Akt. Frequenz                 | --     | 5035     | --            | 0.01 Hz | UINT_16 little |                                                                  |
| Netz: Akt. Leistungsfaktor          | 5034   | 5034     | 5034          | 0.001   | INT_16 little  | Nur über alle Phasen vorhanden                                   |
| Netz: Zähler Netzentnahme           | 13036  | 13036    | --            | 0.1 kWh | UINT_32 mixed  |                                                                  |
| Netz: Zähler Einspeisung            | 13045  | 13045    | --            | 0.1 kWh | UINT_32 mixed  |                                                                  |
| Meter: AC Wirkleistung Phase A      | 5602   | 5602     | 5084          | 1 W     | INT_32 mixed   | Im Unterschied zu 13009 Vorzeichen korrekt                       |
| Meter: AC Wirkleistung Phase B      | 5604   | 5604     | 5086          | 1 W     | INT_32 mixed   | Im Unterschied zu 13009 Vorzeichen korrekt                       |
| Meter: AC Wirkleistung Phase C      | 5606   | 5606     | 5088          | 1 W     | INT_32 mixed   | Im Unterschied zu 13009 Vorzeichen korrekt                       |
| Meter: AC Spannung Phase A          | 5740   | --       | --            | 0.1 V   | UINT_16 little |                                                                  |
| Meter: AC Spannung Phase B          | 5741   | --       | --            | 0.1 V   | UINT_16 little |                                                                  |
| Meter: AC Spannung Phase C          | 5742   | --       | --            | 0.1 V   | UINT_16 little |                                                                  |
| Meter: AC Strom Phase A             | 5743   | --       | --            | 0.01 A  | UINT_16 little | Immer positiv, auch bei Einspeisung                              |
| Meter: AC Strom Phase B             | 5744   | --       | --            | 0.01 A  | UINT_16 little | Immer positiv, auch bei Einspeisung                              |
| Meter: AC Strom Phase C             | 5745   | --       | --            | 0.01 A  | UINT_16 little | Immer positiv, auch bei Einspeisung                              |