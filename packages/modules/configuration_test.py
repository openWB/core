from pathlib import Path
import sys
import traceback
from unittest.mock import Mock, patch
import pytest

from control import data
from modules.configuration import pub_configurable
from modules import configuration
from test_utils.test_environment import running_on_github


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


def test_pub_configurable(monkeypatch, mock_data):
    # setup
    captured_exceptions = []

    def _capture_exception(*args, **kwargs):
        _, exception, tb = sys.exc_info()
        traceback_info = traceback.extract_tb(tb) if tb is not None else []
        last_frame = traceback_info[-1] if traceback_info else None
        captured_exceptions.append({
            "logger_args": args,
            "logger_kwargs": kwargs,
            "exception": repr(exception) if exception is not None else None,
            "traceback_origin": {
                "file": last_frame.filename,
                "line": last_frame.lineno,
                "function": last_frame.name,
                "code": last_frame.line,
            } if last_frame is not None else None
        })

    if running_on_github():
        # run test on github
        mock_packages_path = Mock(name="get packages path", return_value=Path("/home/runner/work/core/core/packages"))
        monkeypatch.setattr(configuration, "_get_packages_path", mock_packages_path)
    with patch('logging.Logger.exception', side_effect=_capture_exception) as log:
        # execution
        pub_configurable()
        # evaluation
        assert log.call_count == 0, f"Unerwartete Exception(s) in configuration: {captured_exceptions}"
