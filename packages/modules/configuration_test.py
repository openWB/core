from pathlib import Path
from unittest.mock import Mock, patch

from modules.configuration import pub_configurable
from modules import configuration
from test_utils.test_environment import running_on_github


def test_pub_configurable(monkeypatch):
    # setup
    if running_on_github():
        # run test on github
        mock_packages_path = Mock(name="get packages path", return_value=Path("/home/runner/work/core/core/packages"))
        monkeypatch.setattr(configuration, "_get_packages_path", mock_packages_path)
    with patch('logging.Logger.exception') as log:
        # execution
        pub_configurable()
        # evaluation
        assert 0 == log.call_count
