from unittest.mock import Mock

from helpermodules import pub

MESSAGES = [pub.PubMessage("openWB/set/a", {"x": 1}),
            pub.PubMessage("openWB/set/b", "10.0.0.2", no_json=True),
            pub.PubMessage("openWB/set/c", None, retain=False)]


def test_pub_multiple_uses_one_connection_for_remote_host(monkeypatch):
    multiple = Mock()
    monkeypatch.setattr(pub.publish, "multiple", multiple)

    pub.pub_multiple(MESSAGES, hostname="10.0.0.5")

    multiple.assert_called_once_with([
        {"topic": "openWB/set/a", "payload": '{"x": 1}', "qos": 0, "retain": True},
        {"topic": "openWB/set/b", "payload": "10.0.0.2", "qos": 0, "retain": True},
        {"topic": "openWB/set/c", "payload": "null", "qos": 0, "retain": False},
    ], hostname="10.0.0.5", port=1883)


def test_pub_multiple_uses_internal_publisher_for_localhost(monkeypatch, mock_pub):
    multiple = Mock()
    monkeypatch.setattr(pub.publish, "multiple", multiple)

    pub.pub_multiple(MESSAGES)

    multiple.assert_not_called()
    assert [(call.args[0], call.args[1], call.kwargs["no_json"], call.kwargs["retain"])
            for call in mock_pub.pub.call_args_list] == [("openWB/set/a", {"x": 1}, False, True),
                                                         ("openWB/set/b", "10.0.0.2", True, True),
                                                         ("openWB/set/c", None, False, False)]
