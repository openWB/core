import pytest

from modules.common.tariff_errors import PermanentTariffError
from modules.electricity_pricing.flexible_tariffs.westfalen_wind import tariff
from modules.electricity_pricing.flexible_tariffs.westfalen_wind.config import WestfalenWindTariff


def test_missing_credentials_are_a_permanent_error():
    with pytest.raises(PermanentTariffError, match="Benutzername und Passwort"):
        tariff.validate_token(WestfalenWindTariff())


def test_login_uses_the_token_url_without_redirect(requests_mock):
    # ohne abschließenden Slash leitet der Server per HTTP um, dabei würde das Passwort im Klartext gesendet
    assert tariff.TOKEN_URL.endswith("/public/tokens/")
    requests_mock.post(tariff.TOKEN_URL, json={"access_token": "a", "refresh_token": "r", "expires": 3600})
    config = WestfalenWindTariff()
    config.configuration.username = "user"
    config.configuration.password = "secret"

    tariff._authenticate(config)  # pyright: ignore[reportPrivateUsage]

    assert config.configuration.token.access_token == "a"
