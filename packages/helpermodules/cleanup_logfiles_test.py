from pathlib import Path
from unittest.mock import Mock

from helpermodules import logger


def test_cleanup_logfiles(monkeypatch):
    # setup
    if str(logger._get_parent_path()) == "/home/runner/work/core/core":
        # run test on github
        mock_packages_path = Mock(name="get parent path", return_value=Path("/home/runner/work/core/core"))
        monkeypatch.setattr(logger, "_get_parent_path", mock_packages_path)
        (logger._get_parent_path()/"ramdisk").mkdir(mode=0o755, parents=True, exist_ok=True)
    log_path = logger._get_parent_path()/"ramdisk"/"test.log"
    with open(log_path, "w") as file:
        for i in range(0, 10100):
            file.write("Test\n")
    with open(log_path, "r") as file:
        lines = file.readlines()
    assert len(lines) == 10100

    # execution
    logger.cleanup_logfiles()
    with open(log_path, "r") as file:
        lines = file.readlines()

    # evaluation
    assert len(lines) == 10000

    # clean up
    log_path.unlink()
