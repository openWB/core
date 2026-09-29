# Porsche Connect – SoC-Modul für openWB

Liest den Ladestand (SoC), die Reichweite und den Kilometerstand eines Porsche
mit **Porsche Connect** aus (z. B. Macan EV ab 2024, Taycan, Cayenne E3,
Panamera G2, 911 ab 992, 718). Die Werte stehen openWB u. a. fürs
PV-Überschussladen bis zu einem Ziel-SoC zur Verfügung.

## Voraussetzungen

- Aktives **Porsche-Connect-Abo** für das Fahrzeug.
- **My-Porsche-Zugangsdaten** (Porsche ID = E-Mail + Passwort).

## Einrichtung in openWB

1. Software-Integration → Fahrzeuge → beim Fahrzeug als **SoC-Modul** „Porsche
   Connect" wählen.
2. Eintragen:
   - **E-Mail** und **Passwort** der Porsche ID.
   - **VIN** (optional). Leer lassen, wenn nur **ein** Fahrzeug im Konto ist;
     bei mehreren Fahrzeugen ist die VIN Pflicht.
3. Speichern. Der SoC wird beim nächsten Abfragezyklus aktualisiert.

## Wichtige Hinweise / Grenzen

- **Inoffiziell:** Diese Schnittstelle ist nicht von Porsche freigegeben
  (`official=False`). Porsche kann Login oder API jederzeit ändern.
- **Captcha:** Verlangt Auth0 ein Captcha, kann sich das Modul nicht anmelden.
  Dann einmal in der My-Porsche-App/-Website (idealerweise aus demselben Netz)
  anmelden und es danach erneut versuchen.
- **Schonender Abruf:** Es wird der zuletzt vom Fahrzeug übertragene Stand
  (`get_stored_overview`-Äquivalent) gelesen; das Auto wird dafür **nicht
  geweckt**. Der SoC kann daher etwas nachlaufen.
- **Token:** Access-/Refresh-Token werden unter
  `data/modules/porsche/token_<vehicle_id>.json` zwischengespeichert, damit nicht
  bei jedem Zyklus ein voller Login (mit Captcha-Risiko) nötig ist.

## Herkunft

Login-Flow (Auth0 „Identifier First") und Endpunkte sind portiert aus der
Community-Bibliothek [pyporscheconnectapi](https://github.com/CJNE/pyporscheconnectapi)
(Apache-2.0), hier als schlanke synchrone `requests`-Implementierung ohne
zusätzliche Abhängigkeiten.

## Test

Unit-Tests (gemocktes HTTP, keine echten Zugangsdaten nötig):

```bash
PYTHONPATH=packages python -m pytest packages/modules/vehicles/porsche/porsche_test.py --noconftest
```
