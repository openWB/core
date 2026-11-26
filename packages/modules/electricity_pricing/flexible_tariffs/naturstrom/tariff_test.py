import pytest

from modules.common.tariff_errors import PermanentTariffError
from modules.electricity_pricing.flexible_tariffs.naturstrom import tariff
from modules.electricity_pricing.flexible_tariffs.naturstrom.config import (NaturstromTariff,
                                                                            NaturstromToken)

TOKEN_URL = f"{tariff.BASE_URL}/api/public-auth/oauth2/token"


def _config(**token) -> NaturstromTariff:
    config = NaturstromTariff()
    config.configuration.token = NaturstromToken(**token)
    return config


def test_missing_refresh_token_is_a_permanent_error():
    with pytest.raises(PermanentTariffError, match="authentifizieren"):
        tariff.validate_token(_config())


def test_invalid_refresh_token_is_a_permanent_error(requests_mock):
    # Antwort des Servers auf einen ungültigen Refresh Token: HTTP 400 invalid_grant
    requests_mock.post(TOKEN_URL, status_code=400, json={"error": "invalid_grant"})

    with pytest.raises(PermanentTariffError, match="authentifizieren"):
        tariff.validate_token(_config(refresh_token="invalid"))


def test_server_error_during_the_token_refresh_is_not_permanent(requests_mock):
    requests_mock.post(TOKEN_URL, status_code=503)

    with pytest.raises(Exception, match="Token-Erneuerung fehlgeschlagen") as error:
        tariff.validate_token(_config(refresh_token="token"))

    assert not isinstance(error.value, PermanentTariffError)
