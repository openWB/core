# Before using MyNISSAN EU

This experimental integration has practical test reports for the **Leaf ZE1**
in Europe. Other Nissan models are unverified. It reads data already stored by
Nissan and does not wake the vehicle; a successful request can return old data.

**Service access.** This is an unofficial client, not a Nissan-approved
integration. Specific permission for this app-API access has not been
established. Nissan's account and service terms are separate from this code's
open-source license; the experimental label does not resolve that question.
Login or API changes can interrupt operation. Consult the terms applicable
to your account; [Nissan's terms index](https://www.nissan.de/rechtliches/agb.html)
provides the published German service terms.

**Account data.** The browser sends entered details to your wallbox; it contacts
the Nissan login/data services over HTTPS. Saving settings stores credentials
in ordinary openWB configuration, which can be present in MQTT and backups,
without encryption added by this module. Password masking does not protect
storage, and an HTTP settings page does not encrypt browser-to-wallbox traffic.
The connection test itself does not save account settings or update charging.

**Logs and sharing.** Detailed SoC logs contain vehicle values and times.
The reviewed Core debug-log filtering can also leave account identifiers or
password fragments visible. Keep settings, backups and logs private; do not
attach them to public issues or send them to cloud assistants. Use detailed
logging only for a bounded diagnostic session.

**Other data paths and removal.** This module adds no developer analytics.
Existing Cloud, MQTT bridges, remote access and backup services have separate
data paths; their effective recipients and retention were not verified here.
Removing the module does not erase saved settings or old logs/backups, and
restoring a backup can restore old credentials. Keep needed recovery backups
protected. See [privacy and diagnostic data](privacy.md) for the reviewed paths
and limits; this information is not a GDPR compliance certification.
