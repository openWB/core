import datetime
from unittest.mock import MagicMock, Mock
import pytest

from helpermodules import pub


@pytest.fixture(autouse=True)
def mock_today(monkeypatch) -> None:
    datetime_mock = MagicMock(wraps=datetime.datetime)
    datetime_mock.today.return_value = datetime.datetime(2022, 5, 16, 8, 40, 52)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)


@pytest.fixture(autouse=True)
def mock_pub(monkeypatch) -> None:
    pub_mock = Mock()
    pub_mock.pub.return_value = None
    monkeypatch.setattr(pub, 'PubSingleton', pub_mock)
