import time

import jwt

from modules.common import req
from modules.vehicles.tronity.api import create_session
from modules.vehicles.tronity.config import TronityVehicleSocConfiguration


def test_create_session_uses_session_with_default_timeout():
    # Ein bereits gueltiger Token vermeidet den Token-Request-Zweig (der wuerde ueber
    # write_token_mqtt() einen echten Pub()/MQTT-Broker ansprechen).
    valid_token = jwt.encode({"exp": time.time() + 3600}, "test-secret-key-that-is-at-least-32-bytes-long",
                             algorithm="HS256")
    config = TronityVehicleSocConfiguration(
        vehicle_id="vid", client_id="id", client_secret="secret", access_token=valid_token)

    session = create_session(config, vehicle=1)

    # Regression: create_session nutzte frueher eine rohe requests.Session ohne Timeout -
    # dadurch konnte ein haengender Tronity-Request den SoC-Abruf dauerhaft blockieren
    # (https://github.com/openWB/core/discussions/3938). Jedes andere Fahrzeugmodul nutzt
    # bereits req.get_http_session() (5s Default-Timeout).
    assert isinstance(session, req.CustomSession)
    assert session.default_timeout == 5
