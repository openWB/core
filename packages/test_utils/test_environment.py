
from pathlib import Path


def running_on_github():
    return str(Path(__file__).resolve().parents[2]/"packages") == "/home/runner/work/core/core/packages"
