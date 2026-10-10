# Privacy and diagnostic data

See [Before using MyNISSAN EU](user-information.md) for the short user notice.
This technical description covers module behavior and source-reviewed openWB
data paths. It is not verification of an installation or a GDPR/BDSG compliance
assessment. Inherited Core observations refer to revision
`3ced7f9cef3c70980ee1fab670f0d0717d1809ca`.

## Data paths

| Data | Processing and storage |
| --- | --- |
| Entered username, password and optional VIN | Browser form and existing Vue configuration store; an unsaved test sends them to the same-origin PHP endpoint and then worker stdin. The component adds no local/session storage; parent state and browser autofill remain separate. |
| Saved account configuration | Ordinary Core configuration, including `openWB/vehicle/<id>/soc_module/config`, retained MQTT state and persistence, permitted subscribers and backups. No module-level encryption or expiry is added. |
| Login data, cookies and tokens | Python client memory and fixed Nissan/OneID/Kamereon HTTPS services in `src/api.py`. Changing configuration creates a new client; process exit releases references but does not promise secure memory erasure. |
| Selected account/vehicle identifiers | Client memory and authenticated API requests. They are excluded from module diagnostics; no response cache is written by the client. |
| SoC, battery time, range and odometer when available | Parsed results, native `CarState`, existing Core state/MQTT, display, applicable histories and backups. Core owns their lifecycle. |
| Query diagnostics and request totals | Client memory; scheduled DEBUG summary; selected fields returned by the settings test. Values and times can reveal vehicle activity even without identifiers. |
| Test cooldown metadata | Expiry times, a random HMAC key and keyed normalized-account digests in `openwb-nissanconnect-test/state` under the PHP temporary directory; account countdowns also exist in component memory. The digests are pseudonymous, not anonymous. |

The private-terminal probe reads hidden input and prints results locally. It
does not use MQTT or the settings endpoint. Its terminal/agent checks cannot
prevent screen sharing, recording or host inspection.

## Transport and access

Nissan connections verify HTTPS certificates. Python `urllib` can inherit
environment/system proxies and trusts the host certificate configuration.
The browser-to-wallbox connection uses the settings page's HTTP/HTTPS transport;
password masking and same-origin POST do not encrypt HTTP.

The endpoint has no separate authentication. Origin, content-type and Fetch
Metadata checks restrict browser cross-site submissions; a direct HTTP client
can supply those headers. Web-server/MQTT access controls remain installation
responsibilities. This module adds no developer analytics or model-provider
destination. Existing Cloud, MQTT bridges, remote access, proxies, monitoring and
backup services have their own recipients and retention.

The inspected local broker bridge exports `soc_module/#` and `get/#` to the
public broker; access depends on its ACLs. An ordinary external status bridge
can export `openWB/vehicle/#`, including configuration. The Cloud generator uses
a different control path. This source review establishes neither that all
credentials are uploaded to Cloud nor that they always remain local.

## Logs and retention

Module diagnostics exclude credentials, identifiers, tokens, URLs and raw
responses. The settings worker disables logging; PHP discards worker stderr,
returns fixed errors and uses `Cache-Control: no-store`. Server/proxy logging of
request bodies is outside module control.

Request totals retain request timestamps and a cumulative count in the native
vehicle module's memory, with a bounded event count. Restart or module recreation
discards that history. No additional state file or MQTT topic is introduced.
Logged totals and their coverage times follow the same private-log lifecycle as
the other query diagnostics; they can reveal query activity. Separate settings
tests do not read or combine the native module's request history.

**Inherited Core debug-log redaction is incomplete.** At the inspected version,
shared MQTT handlers log payloads, the central filter does not mask `user_id` or
`vin` by default, and an escaped quotation mark in a JSON password can leave a
suffix visible. This was reproduced with synthetic input, not a real account.
The module's own safe summaries and three UI console-payload removals do not
fix shared backend logging. Keep logs private and use detailed logging for
bounded diagnosis; do not weaken a password to accommodate a log parser.

Log rotation is size/event based, not a guaranteed deletion deadline. Reducing
the log level does not remove existing records, exports or backups. Treat their
sharing as a separate disclosure; do not submit private logs to issues or cloud
assistants.

The settings test does not save account settings or vehicle responses to disk.
Its temporary state contains a local key, account digests and expiry times.
Expired accounts are pruned on load and persisted on the next successful write;
an early return can leave expired records on disk. No timer guarantees deletion
after five minutes. Provider pauses are capped at 24 hours; state is bounded to
1024 active account entries and 128 KiB.

The endpoint checks Linux UID, a trusted temporary parent, a real 0700 directory
and regular 0600 state file owned by that UID. It rejects unsafe modes, symlinks,
multiple hard links and descriptor/path mismatches without silently repairing
or deleting them. Root and other code using the same UID remain outside this
boundary. Linux filesystem and synthetic HTTP checks have passed; that does not
establish permissions or isolation on every installation.

## Backups and removal

Normal openWB backups can include configuration, MQTT databases, broker settings,
logs and histories. In the inspected backup script, encryption depends on a
configured key file; compression and checksums alone provide no confidentiality.
No actual user's backup encryption or remote retention was inspected.

Removing module files does not remove saved credentials. Replacing the active
configuration does not erase old logs, SD images, database snapshots, exported
settings, password-manager copies or previously shared data. Restoring a backup
can restore old credentials. Protect retained recovery copies and account for
their lifecycle separately. Battery and odometer values share these existing
storage/access boundaries; the odometer has no known measurement timestamp.
