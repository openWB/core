import struct
from types import SimpleNamespace

import paho.mqtt.client as mqtt
import pytest

from src.authenticator import AuthConfig, Authenticator
from src.broker_access import BrokerAccess, Principal, TRUSTED, UserSession, _AckClient
from src.parameter_handler import ParameterHandler, ReadView, dispatch_read


class FakeDaemon:
    def __init__(self):
        self.raw_value_cache = {
            "openWB/chargepoint/1/get/power": 1000,
            "openWB/chargepoint/1/control_parameter/limit": {"message": "x", "limiting_value": "y"},
            "openWB/io/states/0/get/digital_input": {"DI1": True},
        }
        self.charge_template_cache = {}
        self.lowest_ids = {'chargepoint': 1, 'io': 0}
        self.all_ids = {'chargepoint': {1}, 'io': {0}}
        self.total_sums = {'chargepoint': {'power': 1000.0}}
        self.user_management_active = True

    @staticmethod
    def _normalize_io_output_type(output_type):
        return None

    def _get_io_output_map(self, io_id, output_type):
        raise AssertionError("the view must serve this itself")


def test_read_view_records_only_cached_topics_that_were_read():
    view = ReadView(FakeDaemon())

    result, _ = dispatch_read(ParameterHandler(view), {'get_chargepoint_power': '1'}, {}, False)

    assert result == {'chargepoint_1': {'power': 1000.0}}
    assert view.topics == {"openWB/chargepoint/1/get/power"}


def test_read_view_records_io_input_and_limit():
    view = ReadView(FakeDaemon())

    dispatch_read(ParameterHandler(view), {'get_io_input_all': 'auto', 'get_chargepoint_limit': '1'}, {}, False)

    assert view.topics == {"openWB/io/states/0/get/digital_input", "openWB/chargepoint/1/control_parameter/limit"}


def test_read_view_records_every_contributing_topic_of_a_total():
    daemon = FakeDaemon()
    daemon.raw_value_cache["openWB/chargepoint/2/get/power"] = 5
    view = ReadView(daemon)

    dispatch_read(ParameterHandler(view), {'get_chargepoint_power': 'total'}, {}, False)

    assert view.topics == set()
    assert view.alternatives == [("openWB/chargepoint/get/power",
                                  {"openWB/chargepoint/1/get/power", "openWB/chargepoint/2/get/power"})]


def test_total_is_readable_with_the_sum_role_or_with_all_single_roles():
    daemon = FakeDaemon()
    daemon.raw_value_cache["openWB/chargepoint/2/get/power"] = 5
    daemon.raw_value_cache["openWB/chargepoint/get/power"] = 1005
    view = ReadView(daemon)
    dispatch_read(ParameterHandler(view), {'get_chargepoint_power': 'total'}, {}, False)
    single = {"openWB/chargepoint/1/get/power", "openWB/chargepoint/2/get/power"}

    assert view.blocking_topics(single) == []  # sum role only
    assert view.blocking_topics({"openWB/chargepoint/get/power"}) == []  # all single roles
    assert view.blocking_topics({"openWB/chargepoint/get/power", "openWB/chargepoint/2/get/power"}) == [
        "openWB/chargepoint/get/power"]


def make_auth(tester, **config):
    return Authenticator(AuthConfig(tokens=['secret'], users={'local': 'pw'}, **config), tester)


def test_disabled_auth_is_trusted():
    auth = Authenticator(AuthConfig(enabled=False), lambda u, p: False)
    assert auth.authenticate({}, None, False) is TRUSTED


def test_token_and_local_user_are_trusted():
    auth = make_auth(lambda u, p: False)
    assert auth.authenticate({}, 'secret', False) is TRUSTED
    assert auth.authenticate({'token': 'secret'}, None, False) is TRUSTED
    assert auth.authenticate({'username': 'local', 'password': 'pw'}, None, False) is TRUSTED
    assert auth.authenticate({'username': 'local', 'password': 'bad'}, None, False) is None


def test_broker_user_keeps_broker_permissions():
    auth = make_auth(lambda u, p: (u, p) == ('bob', 'x'))
    principal = auth.authenticate({'username': 'bob', 'password': 'x'}, None, False)
    assert principal == Principal(username='bob', password='x')
    assert principal.trusted is False


def test_wrong_credentials_are_not_downgraded_to_anonymous():
    auth = make_auth(lambda u, p: u == '')
    assert auth.authenticate({'username': 'bob', 'password': 'wrong'}, None, False) is None


def test_no_credentials_is_anonymous_if_the_broker_allows_it():
    assert make_auth(lambda u, p: True).authenticate({}, None, False) == Principal()
    assert make_auth(lambda u, p: False).authenticate({}, None, False) is None


def test_https_is_required_for_credentials_if_configured():
    auth = make_auth(lambda u, p: True, require_https=True)
    assert auth.authenticate({'username': 'bob', 'password': 'x'}, None, False) is None
    assert auth.authenticate({'username': 'bob', 'password': 'x'}, None, True) is not None


class FakeProbeClient:
    """Delivers the retained messages of `visible` right after the subscription."""
    visible = set()
    connects = 0

    def __init__(self, protocol=None):
        self.on_connect = None
        self.on_message = None

    def tls_set(self, **kwargs):
        pass

    def tls_insecure_set(self, value):
        pass

    def username_pw_set(self, username, password):
        pass

    def connect(self, host, port, keepalive=60):
        FakeProbeClient.connects += 1

    def loop_start(self):
        self.on_connect(self, None, {}, 0)

    def subscribe(self, topics):
        for topic, _ in topics:
            if topic in FakeProbeClient.visible:
                self.on_message(self, None, SimpleNamespace(topic=topic))

    def disconnect(self):
        pass

    def loop_stop(self):
        pass


def make_access():
    FakeProbeClient.connects = 0
    return BrokerAccess(timeout=0.05, read_timeout=0.05, client_factory=FakeProbeClient)


def test_read_is_denied_for_topics_the_broker_does_not_deliver():
    FakeProbeClient.visible = {"a"}
    access = make_access()

    assert access.denied_topics(Principal(username='u', password='p'), ["a", "b"]) == ["b"]
    assert access.denied_topics(Principal(username='u', password='p'), ["a"]) == []


def test_read_result_is_cached_per_credentials():
    FakeProbeClient.visible = {"a"}
    access = make_access()
    good = Principal(username='u', password='p')

    access.denied_topics(good, ["a"])
    access.denied_topics(good, ["a"])
    assert FakeProbeClient.connects == 1

    FakeProbeClient.visible = set()
    # a different password must not reuse the cached result of the correct one
    assert access.denied_topics(Principal(username='u', password='other'), ["a"]) == ["a"]


def test_puback_reason_code_is_captured():
    client = _AckClient(protocol=mqtt.MQTTv5)
    client._in_packet = {'packet': struct.pack("!HB", 7, 0x87), 'remaining_length': 3}

    client._handle_pubackcomp("PUBACK")

    assert client.puback_reasons == {7: 0x87}


def test_publish_raises_permission_error_if_refused():
    client = SimpleNamespace(puback_reasons={3: 0x87}, disconnect=lambda: None, loop_stop=lambda: None)
    info = SimpleNamespace(mid=3, wait_for_publish=lambda timeout: None, is_published=lambda: True)
    client.publish = lambda *a, **k: info
    session = UserSession(client, 1)

    with pytest.raises(PermissionError):
        session.publish("openWB/set/x", "1")
