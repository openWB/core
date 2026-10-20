import pytest

from modules.vehicles.byd import api, soc
from modules.vehicles.byd.config import Byd, BydConfiguration


@pytest.fixture(autouse=True)
def _clear_caches():
    api._fingerprint_cache.clear()
    yield


def test_create_vehicle_seeds_account_cache_with_persisted_fingerprint():
    config = Byd(configuration=BydConfiguration(username="user@example.com", vin="VIN1",
                                                device_fingerprint='{"imei": "already-persisted"}'))

    soc.create_vehicle(config, 1)

    assert api._fingerprint_cache["user@example.com"] == '{"imei": "already-persisted"}'


def test_create_vehicle_does_not_seed_cache_without_persisted_fingerprint():
    config = Byd(configuration=BydConfiguration(username="user@example.com", vin="VIN1"))

    soc.create_vehicle(config, 1)

    assert "user@example.com" not in api._fingerprint_cache
