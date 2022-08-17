from pathlib import Path
from unittest.mock import Mock, patch

from modules.configuration import pub_configurable
from modules import configuration


def test_pub_configurable(monkeypatch):
    # setup
    if str(configuration._get_packages_path()) == "/home/runner/work/core/core/packages":
        # run test on github
        mock_packages_path = Mock(name="get packages path", return_value=Path("/home/runner/work/core/core/packages"))
        monkeypatch.setattr(configuration, "_get_packages_path", mock_packages_path)
    with patch('logging.Logger.exception') as log:
        # execution
        pub_configurable()
        # evaluation
        assert 0 == log.call_count
