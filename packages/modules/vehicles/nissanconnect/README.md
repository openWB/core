# Nissan – MyNISSAN EU (experimental)

This module reads data stored by Nissan's European MyNISSAN service and provides
openWB with battery state of charge, the original battery measurement time,
and range and odometer values when available. Existing openWB scheduling,
display and charging control consume these values through the standard vehicle
interface.

**Tested in practice with the Leaf ZE1; other models are unverified.**
Read [Before using MyNISSAN EU](docs/user-information.md) for service-access and
privacy information. This is an unofficial integration; specific permission for
this app-API access has not been established.

## Compatibility

- A European MyNISSAN account must work in the official app and have an associated
  vehicle. NissanConnect EV and the existing `leaf` module use a different API.
- The client has no Leaf model-code filter. Another vehicle must provide the
  same required battery fields through these EU endpoints; presence in the
  MyNISSAN app alone does not establish compatibility. Other regions are unverified.
- Login changes, additional consent or MFA can interrupt access. Complete any
  required account steps in the official app; the module does not automate them.
- Practical reports cover a 2019 Leaf ZE1 and openWB 2.2.3 at Core revision
  `3ced7f9cef3c70980ee1fab670f0d0717d1809ca`. They do not separately establish
  odometer accuracy, sustained token renewal or every charging-limit scenario.
- The Python module requires Python 3.9+. The settings connection test additionally
  requires the matching settings build, Linux, PHP 7.4+ with `proc_open`, and
  Python at `/usr/bin/python3`. No new Python package is required by this module.

## Configuration

Choose **Nissan – MyNISSAN EU (experimental)** in the vehicle's SoC settings.
The internal module type is `nissanconnect`; saved custom names are preserved.

| Field | Meaning |
| --- | --- |
| `user_id` | MyNISSAN account email address |
| `password` | MyNISSAN account password |
| `vin` | Optional for a single vehicle; required to select among multiple vehicles |

A single associated vehicle is selected automatically. Ambiguous selection or an
unknown VIN produces an error. Configure query intervals using the normal openWB
vehicle settings. **Test connection** queries the current form values without
saving settings or updating charging control; save separately to enable them.

## Data freshness and errors

Queries read cached server data. They do not wake the vehicle, request a fresh
vehicle measurement or send charging commands. A successful query can return an
old measurement; the module preserves its timestamp rather than inventing one.
The pinned Status page displays that measurement time, not the latest HTTP request.

Invalid battery data produces an error. After a successful battery query, the
module automatically attempts to retrieve the odometer, subject to retry pauses
and the request budget. There is no separate user setting to enable it. When
Nissan supplies a valid value, it is passed to openWB in kilometres for the
existing Status page, charge-log and CSV consumers. Missing or invalid odometer
data, or a failed odometer query, does not invalidate a valid SoC result. Missing
or invalid range data likewise leaves a valid battery result usable.

The odometer comes from `totalMileage`. Its measurement time is unavailable and
must not be inferred from the battery timestamp or the time of retrieval.

Core decides whether to accept a measurement, calculate SoC from metered energy
or expose an error. The module does not add a charging interlock or override
Core's zero-SoC error policy. See [diagnostics and error behavior](docs/diagnostics.md)
for scheduling, timestamp rejection, retry delays and the known refresh indicator.
SoC DEBUG logs also report this vehicle module's request totals for the last
24 hours, since local midnight and since observation started, with the start
timestamp and coverage flags.
The counters reset when the module is restarted or recreated; separate settings
connection tests are excluded from these totals.

## Development and offline tests

The [source map](docs/source-map.md) describes `src`, `tests`, `tools` and `docs`
and the stable integration entry points. Tests use synthetic responses and
block real network access. From the Core repository root, with Python 3.9+,
pytest and Flake8 installed:

```sh
PYTHONPATH=packages python -m pytest -q packages/modules/vehicles/nissanconnect/tests \
  --confcutdir=packages/modules/vehicles/nissanconnect/tests
python -m flake8 packages/modules/vehicles/nissanconnect
```

The companion `openWB/openwb-ui-settings` repository owns the Vue form, both PHP
sources under `public/modules/vehicles/nissanconnect/` and their UI/PHP tests.
Its regular build copies the PHP sources unchanged to their deployed URLs.
See that repository's `docs/nissanconnect-source-map.md`,
`tests/nissanconnect/README.md` and pinned `docs/nissanconnect-2.2.3.md` guide.
Module tests do not replace complete Core CI or live vehicle validation.

## Optional private-terminal query

On a development computer, run the tool yourself in a private terminal:

```sh
python -I -B packages/modules/vehicles/nissanconnect/tools/probe.py
```

It asks for confirmation, reads account details using hidden input and displays
cached battery/odometer results. It refuses redirected output and recognizable
agent sessions; these checks cannot detect all recording or monitoring. Keep
credentials and results out of public issues, Git and cloud-assistant sessions.
The tool does not connect to a wallbox or save openWB settings.

## Contribution and attribution

This integration was initiated and contributed by [wippofax](https://github.com/wippofax).

Core owns the Python module; settings owns the form and PHP endpoints. Review
changes together and state the tested versions and limitations. Built settings
assets do not belong in the Core source contribution.

See [NOTICE.md](NOTICE.md) for source attribution and the retained MIT notice,
and [privacy and diagnostic data](docs/privacy.md) for data flows and the
inherited Core logging limitation. An open-source license does not grant
permission to access Nissan's service.
