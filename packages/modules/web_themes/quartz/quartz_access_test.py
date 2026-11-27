"""Does the Quartz web theme work with user management (mosquitto dynamic security)?

Static part (always runs): every topic and command Quartz uses must be covered by the roles shipped in
data/config/mosquitto/public, otherwise the feature is unusable for every user but the admin.

Live part (needs mosquitto + its dynamic security plugin + paho, otherwise skipped): an isolated broker is started with
the shipped default-dynamic-security.json. Publishing with QoS 0 gets no answer when the broker refuses it, so what
arrives is observed through an admin client.
  MOSQUITTO_BIN / MOSQUITTO_DYNSEC_SO point to the binary and the plugin if they are not found automatically.
"""
import glob
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[4]
ROLE_DIR = ROOT / "data/config/mosquitto/public"
SRC = Path(__file__).resolve().parent / "source/src"
STORE = SRC / "stores/mqtt-store.ts"

# Topics Quartz uses that no role but full-access allows; the same gap exists in Koala and needs a role change.
KNOWN_ROLE_GAPS = {"openWB/set/vehicle/+/get/force_soc_update"}


def _roles() -> dict:
    default = json.loads((ROLE_DIR / "default-dynamic-security.json").read_text())
    roles = {r["rolename"]: r["acls"] for r in default["roles"]}
    for template in json.loads((ROLE_DIR / "role-templates.json").read_text()):
        roles[template["rolename"].replace("<id>", "N")] = [
            dict(acl, topic=acl["topic"].replace("<id>", "+")) for acl in template["acls"]]
    return roles


def _matches(pattern: str, topic: str) -> bool:
    """MQTT topic filter match; a '+' in the used topic stands for an id and fits '+' or a number."""
    p, t = pattern.split("/"), topic.split("/")
    for i, seg in enumerate(p):
        if seg == "#":
            return True
        if i >= len(t):
            return False
        if seg == "+":
            continue
        if t[i] == "+":
            if re.fullmatch(r"\d+", seg):
                continue
            return False
        if seg != t[i]:
            return False
    return len(p) == len(t)


def _allowed_by(topic: str, acltype: str) -> list:
    return [name for name, acls in _roles().items() if name not in ("full-access", "dynsec-admin")
            and any(a["acltype"] == acltype and a["allow"] and _matches(a["topic"], topic) for a in acls)]


def _source_files():
    return [f for f in SRC.rglob("*") if f.suffix in (".ts", ".vue") and ".test." not in f.name]


def _used_topics():
    literal = re.compile(r"""(?P<q>[`'"])(?P<t>openWB/[^`'"\n]*)(?P=q)""")
    reads, writes = set(), set()
    for f in _source_files():
        for line in f.read_text().splitlines():
            for m in literal.finditer(line):
                topic = re.sub(r"\$\{[^}]*\}", "+", m.group("t"))
                if topic in ("openWB/", "openWB/set/", "openWB/set/..."):
                    continue
                if topic.startswith("openWB/set/command/"):
                    continue
                if topic.startswith("openWB/set/"):
                    writes.add(topic)
                else:
                    reads.add(topic)
                    # updateTopic(topic, value, path, true) republishes to the matching openWB/set/ topic
                    if re.search(r"updateTopic\(.*,\s*true\)\s*$", line):
                        writes.add(topic.replace("openWB/", "openWB/set/", 1))
    return reads, writes


def _commands() -> set:
    """Commands sent directly, and the plan commands that the store keeps in a table."""
    texts = [f.read_text() for f in _source_files()]
    direct = {m.group(1) for t in texts for m in re.finditer(r"sendCommand\(\s*'(\w+)'", t)}
    tabled = {m.group(1) for t in texts for m in re.finditer(r"'((?:add|remove)ChargeTemplate\w+)'", t)}
    return direct | tabled


def test_quartz_reads_are_covered_by_a_role():
    reads, _ = _used_topics()
    uncovered = sorted(t for t in reads if not _allowed_by(t, "publishClientReceive"))
    assert not uncovered, f"no role lets a user receive: {uncovered}"


def test_quartz_writes_are_covered_by_a_role():
    _, writes = _used_topics()
    uncovered = sorted(t for t in writes if t not in KNOWN_ROLE_GAPS and not _allowed_by(t, "publishClientSend"))
    assert not uncovered, f"no role lets a user publish: {uncovered}"


def test_known_role_gaps_are_still_gaps():
    """Fails when a gap got closed, so the entry can be removed."""
    for topic in KNOWN_ROLE_GAPS:
        assert not _allowed_by(topic, "publishClientSend"), f"{topic} is allowed now, drop it from KNOWN_ROLE_GAPS"


def test_command_topic_carries_the_command_name():
    """Roles allow openWB/set/command/+/todo/<command> and setdata drops a command whose topic does not end in
    the command name as soon as user management is active."""
    store = STORE.read_text()
    assert re.search(r"openWB/set/command/\$\{clientId\}/todo/\$\{command\}", store), \
        "sendCommand must publish to openWB/set/command/<clientId>/todo/<command>"


# what the UI shows only when a topic arrives, and what it then lets the user change: every role that receives the
# first must also be allowed to write the second, otherwise a user sees controls that are always refused
CONTROL_GATES = [
    ("openWB/chargepoint/+/set/manual_lock", ["openWB/set/chargepoint/+/set/manual_lock",
                                              "openWB/set/chargepoint/+/config/ev",
                                              "openWB/set/chargepoint/+/set/charge_template"]),
    ("openWB/consumer/+/usage", ["openWB/set/consumer/+/usage"]),
    ("openWB/vehicle/+/soc_module/calculated_soc_state",
     ["openWB/set/vehicle/+/soc_module/calculated_soc_state/manual_soc"]),
    ("openWB/system/security/access/ActiveBatControlConfiguration",
     ["openWB/set/general/chargemode_config/bat/mode", "openWB/set/bat/config/manual_mode"]),
]


@pytest.mark.parametrize("gate,writes", CONTROL_GATES)
def test_roles_that_get_the_control_topic_may_write_what_it_controls(gate, writes):
    receivers = set(_allowed_by(gate, "publishClientReceive"))
    assert receivers, f"no role receives {gate}"
    for write in writes:
        missing = receivers - set(_allowed_by(write, "publishClientSend"))
        assert not missing, f"{sorted(missing)} receive {gate} but may not write {write}"


def test_every_command_is_allowed_for_some_role():
    assert {"getDailyLog", "addChargeTemplateTimeChargingPlan"} <= _commands()
    for command in _commands():
        assert _allowed_by(f"openWB/set/command/+/todo/{command}", "publishClientSend"), \
            f"no role allows the command {command}"


# --- live part ---

def _find(binary_env, candidates):
    path = os.environ.get(binary_env)
    if path and Path(path).exists():
        return path
    for pattern in candidates:
        for found in glob.glob(pattern):
            return found
    return None


MOSQUITTO = _find("MOSQUITTO_BIN", ["/usr/sbin/mosquitto"]) or shutil.which("mosquitto")
DYNSEC = _find("MOSQUITTO_DYNSEC_SO", ["/usr/lib/*/mosquitto_dynamic_security.so",
                                       "/usr/lib/mosquitto_dynamic_security.so"])
try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None
live = pytest.mark.skipif(not (MOSQUITTO and DYNSEC and mqtt), reason="mosquitto, dynsec plugin or paho missing")

PRIVATE_SAMPLES = ["openWB/chargepoint/3/get/power", "openWB/chargepoint/4/get/power",
                   "openWB/graph/lastlivevaluesJson", "openWB/bat/get/power", "openWB/system/device/1/config",
                   "openWB/optional/ep/get/prices"]
PUBLIC_SAMPLES = ["openWB/system/version", "openWB/system/security/user_management_active"]


def _client(port, username=None, password=None):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"t{time.time_ns()}") \
        if hasattr(mqtt, "CallbackAPIVersion") else mqtt.Client(client_id=f"t{time.time_ns()}")
    if username:
        client.username_pw_set(username, password)
    client.received = []
    client.on_message = lambda c, u, msg: c.received.append((msg.topic, msg.payload))
    client.connect("127.0.0.1", port, 30)
    client.loop_start()
    return client


def _settle():
    time.sleep(0.6)


@pytest.fixture(scope="module")
def broker(tmp_path_factory):
    work = tmp_path_factory.mktemp("broker")
    shutil.copy(ROLE_DIR / "default-dynamic-security.json", work / "dynsec.json")
    ports = []
    for _ in range(2):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            ports.append(sock.getsockname()[1])
    port, backend_port = ports
    # like the shipped config: the user-facing listener has the plugin, the backend's local one is open
    (work / "mosquitto.conf").write_text(
        f"per_listener_settings true\npersistence false\n"
        f"listener {backend_port} 127.0.0.1\nallow_anonymous true\n"
        f"listener {port} 127.0.0.1\nallow_anonymous true\n"
        f"plugin {DYNSEC}\nplugin_opt_config_file {work / 'dynsec.json'}\n")
    log = open(work / "broker.log", "w")
    process = subprocess.Popen([MOSQUITTO, "-c", str(work / "mosquitto.conf")], stdout=log, stderr=subprocess.STDOUT)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.5).close()
            break
        except OSError:
            time.sleep(0.1)
    admin = _client(port, "admin", "openwb")
    admin.subscribe([("$CONTROL/dynamic-security/v1/response", 0), ("openWB/set/#", 0)])
    roles = _roles()
    commands = []
    # chargepoint-<id>-access is only a template, user management creates the role per chargepoint
    commands.append({"command": "createRole", "rolename": "chargepoint-3-access"})
    for acl in roles["chargepoint-N-access"]:
        topic = acl["topic"].replace("+", "3", 1) if "chargepoint" in acl["topic"] else acl["topic"]
        commands.append({"command": "addRoleACL", "rolename": "chargepoint-3-access", "acltype": acl["acltype"],
                         "topic": topic, "priority": 0, "allow": acl["allow"]})
    commands += [
        {"command": "createClient", "username": "cpuser", "password": "pw",
         "roles": [{"rolename": r} for r in ("basic-theme-data", "basic-system-data", "basic-user-data",
                                             "chargepoint-3-access", "graph-access", "chart-access")]},
    ]
    admin.publish("$CONTROL/dynamic-security/v1", json.dumps({"commands": commands}))
    _settle()
    answers = [json.loads(p) for t, p in admin.received if t.startswith("$CONTROL")]
    errors = [r for a in answers for r in a["responses"] if r.get("error")]
    assert not errors, errors
    admin.received.clear()
    backend = _client(backend_port)
    admin.backend = backend
    yield port, admin
    backend.loop_stop()
    admin.loop_stop()
    process.terminate()
    process.wait(5)


def _publish_samples(admin, topics):
    for topic in topics:
        admin.backend.publish(topic, "1", retain=True)
    _settle()


@live
def test_anonymous_sees_only_public_data(broker):
    port, admin = broker
    _publish_samples(admin, PRIVATE_SAMPLES + PUBLIC_SAMPLES)
    anonymous = _client(port)
    anonymous.subscribe("openWB/#")
    _settle()
    seen = {t for t, _ in anonymous.received}
    assert not seen & set(PRIVATE_SAMPLES), f"anonymous received private topics: {seen & set(PRIVATE_SAMPLES)}"
    assert set(PUBLIC_SAMPLES) <= seen
    anonymous.loop_stop()


@live
def test_user_reads_only_what_its_roles_allow(broker):
    port, admin = broker
    _publish_samples(admin, PRIVATE_SAMPLES)
    user = _client(port, "cpuser", "pw")
    user.subscribe("openWB/#")
    _settle()
    seen = {t for t, _ in user.received}
    assert "openWB/chargepoint/3/get/power" in seen
    assert "openWB/graph/lastlivevaluesJson" in seen
    for denied in ("openWB/chargepoint/4/get/power", "openWB/bat/get/power", "openWB/system/device/1/config"):
        assert denied not in seen
    user.loop_stop()


def _delivered(port, admin, user, topic):
    admin.received.clear()
    user.publish(topic, json.dumps({"command": topic.rsplit("/", 1)[-1], "data": {}}))
    _settle()
    return any(t == topic for t, _ in admin.received)


@live
def test_user_writes_only_what_its_roles_allow(broker):
    port, admin = broker
    user = _client(port, "cpuser", "pw")
    assert _delivered(port, admin, user, "openWB/set/chargepoint/3/set/manual_lock")
    assert not _delivered(port, admin, user, "openWB/set/chargepoint/4/set/manual_lock")
    assert not _delivered(port, admin, user, "openWB/set/bat/config/manual_mode")
    assert not _delivered(port, admin, user, "openWB/set/system/security/user_management_active")
    user.loop_stop()


@live
def test_commands_reach_the_backend_only_with_the_command_name_in_the_topic(broker):
    """What Quartz must do: openWB/set/command/<clientId>/todo/<command>. Without the suffix the broker refuses it."""
    port, admin = broker
    user = _client(port, "cpuser", "pw")
    assert _delivered(port, admin, user, "openWB/set/command/abc/todo/getDailyLog")
    assert not _delivered(port, admin, user, "openWB/set/command/abc/todo")
    assert not _delivered(port, admin, user, "openWB/set/command/abc/todo/systemReboot")
    user.loop_stop()


@live
def test_anonymous_cannot_write(broker):
    port, admin = broker
    anonymous = _client(port)
    assert not _delivered(port, admin, anonymous, "openWB/set/chargepoint/3/set/manual_lock")
    anonymous.loop_stop()


def _mosquitto_pub(port, topic, version, user="cpuser", password="pw"):
    result = subprocess.run(
        ["mosquitto_pub", "-h", "127.0.0.1", "-p", str(port), "-u", user, "-P", password, "-V", version, "-q", "1",
         "-t", topic, "-m", "1", "-d"], capture_output=True, text=True, timeout=20)
    return result.stdout + result.stderr


needs_pub = pytest.mark.skipif(not shutil.which("mosquitto_pub"), reason="mosquitto_pub missing")


@live
@needs_pub
def test_refused_publish_is_reported_to_an_mqtt5_client_only(broker):
    """Quartz relies on this: with MQTT 5 the broker answers a forbidden QoS 1/2 publish with reason code 135,
    with MQTT 3.1.1 it acknowledges it as if it had worked."""
    port, _ = broker
    assert "RC:135" in _mosquitto_pub(port, "openWB/set/bat/config/manual_mode", "mqttv5")
    assert "RC:135" not in _mosquitto_pub(port, "openWB/set/chargepoint/3/set/manual_lock", "mqttv5")
    assert "RC:135" not in _mosquitto_pub(port, "openWB/set/bat/config/manual_mode", "mqttv311")


@live
def test_wrong_password_is_refused_with_a_code_quartz_handles(broker):
    """Quartz (MQTT 5) removes the login cookie on the CONNACK reason codes 135 and 137."""
    port, _ = broker
    codes = []
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, protocol=mqtt.MQTTv5) \
        if hasattr(mqtt, "CallbackAPIVersion") else mqtt.Client(protocol=mqtt.MQTTv5)
    client.username_pw_set("cpuser", "wrong")
    client.on_connect = lambda c, u, f, rc, properties=None: codes.append(int(getattr(rc, "value", rc)))
    client.connect("127.0.0.1", port, 30)
    client.loop_start()
    _settle()
    client.loop_stop()
    assert codes and codes[0] in (135, 137), codes
