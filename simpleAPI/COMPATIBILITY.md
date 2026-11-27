# simpleAPI: differences to the PHP implementation

The HTTP API of the Python implementation takes the same requests and gives the same answers as the PHP one (same
parameters, same JSON structure and text format, same status codes, same MQTT commands). This file lists the
places where it is different on purpose. A difference that is not listed here is a bug.

## Changed on purpose

| Area | PHP | Python |
|---|---|---|
| Non-numeric values for `chargecurrent`, `minimal_permanent_current`, `minimal_pv_soc`, `max_price_eco`, `instant_charging_amount`, `pv_charging_amount`, `instant_charging_soc`, `pv_charging_soc`, `vehicle`, `manual_soc`, `bat_power_reserve` | `abc` became `0`, `12abc` became `12`, `7,5` became `7`, the request succeeded (`max_price_eco=abc` ended in a PHP error) | refused with `success: false` (`Invalid ... value: abc`), nothing is published. Numbers (`6.5`, `1e1`) work as before, `55.9` as SoC is truncated to `55` |
| `chargepoint_lock` | every non-empty text except `0` locked, `false` locked, too | `true`, `1`, `yes`, `on` lock, everything else unlocks |
| Single reads of booleans (`get_chargepoint_plug_state`, `..._charge_state`, `get_battery_power_limit_controllable`) | `false` was answered as `true` | the correct value |
| Analog IO output with a value that is no number or boolean | the text was published | refused |
| Several template parameters in one request (`set_chargemode` together with `chargecurrent`, ...) | the later one overwrote the earlier ones | all of them are applied |
| Wrong `username`/`password` with user management on | answered like an anonymous request (HTTP 200, no data, writes refused by the broker) | HTTP 401 |
| Wrong `username`/`password` together with a valid `token` | the token is used | refused, credentials are never silently downgraded |
| `bat_mode`, `bat_power_reserve` | also needed a chargepoint ID (failed without any chargepoint) | global settings, no chargepoint ID |
| `auto` for counters | the lowest counter ID | the grid counter of the hierarchy (not always the lowest ID) |
| Values that were passed on as the raw MQTT text (`soc_timestamp`, `vehicle_id`, `rfid_timestamp` in `get_chargepoint_all`, `rfid` and other texts that are JSON `null`) | strings (`"1700000000"`, `"null"`) | JSON types (number, `null`) |
| Empty objects (`get_io_output_all` of a device without outputs) | `[]` | `{}` |
| Array reads of chargepoints (`..._voltages`, `..._currents`, `..._powers`) for an unknown ID | tried the data of chargepoint 0 when the topic was missing | answer with nothing (`[]`), no fallback |
| Password hashes of local users in `simpleapi_config.json` | everything PHP's `password_verify()` knows | bcrypt |
| POST body | any form data (`multipart/form-data`, too) | `application/x-www-form-urlencoded` |

## New

`get_home_consumption`, `get_counter_local_power`, `get_battery_state_str`, `get_battery_max_charge_power`,
`get_battery_max_discharge_power`, `get_consumer_temperatures`, `get_consumer_set_power`, `get_consumer_state`,
`get_consumer_plug_state`, `get_consumer_rfid`, `get_consumer_rfid_timestamp`, the matching fields in the `all` reads and
`minimal_pv_soc` in `get_chargepoint_all`. `HEAD` requests are answered like `GET`.

## Permissions with user management

- **HTTP API, like PHP:** the broker decides with the roles of the caller (`chargepoint-<id>-access`, ... as in the
  UI). The daemon itself has an unrestricted local connection, so for every request the broker is asked with the
  caller's credentials: reads must be delivered to the caller (otherwise HTTP 403), writes are published through the
  caller's own connection and refused if the broker refuses them (`Not authorized to publish ...`). The result of the
  check is cached for 30 s; it costs about 165 ms on the first request and about 20 ms afterwards. Tokens and users
  of `simpleapi_config.json` are trusted and skip the check.
- **MQTT set topics (`openWB/simpleAPI/set/#`), unchanged:** only the role `full-access` may publish there. The daemon
  then writes with its own connection, so whoever may use these topics may change every chargepoint.
- Open question: general simpleAPI roles (read / write), so that limited users can use simpleAPI without the roles of
  the UI?

## Configuration

Tokens, local users and `require_https` are read from `/home/openwb/simpleapi_config.json`, outside of the web root
(it is part of the backup and restore). `data/config/simpleapi_config.json` is only the default that `atreboot.sh`
copies there. Apache sets `X-Forwarded-Proto` for the backend, which only trusts it from the local proxy.

There is nothing to migrate: the old settings lived in the tracked files `simpleAPI/config/config.php` and
`data/config/simpleAPI_mqtt_config.json`, an update (`git checkout --force`, `git reset --hard`) discards edits there
and the backup did not contain them. Whoever had entered tokens or users has to enter them again.

## Response format

Status codes, CORS headers and the JSON structure are the same. The JSON text is written like PHP's `json_encode()`
did (no spaces after `,` and `:`, `/` as `\/`, whole floats without fraction: `230`, not `230.0`), and the
`Cache-Control`, `Pragma` and `Expires` headers that the `.htaccess` added to the PHP answers are sent by the backend.

## Python 3.13 (Trixie)

`passlib` has no bcrypt backend on Python 3.13 without the `bcrypt` package (the `crypt` module was removed). Affects
`helpermodules/mosquitto_dynsec` (user-management tokens) and bcrypt hashes of local simpleAPI users;
`upstream/trixie-next` has no `bcrypt` in `requirements.txt`. simpleAPI refuses such a login cleanly.
