import json
import os
import tempfile
from unittest.mock import Mock

from helpermodules.utils import json_file_handler
from helpermodules.utils.json_file_handler import write_and_check

import pytest


@pytest.mark.parametrize("load_return, expected_content", [
    ([{"new_key": "new_value"}], {"new_key": "new_value"}),
    ([ValueError("Ungültige Daten"), {"new_key": "new_value"}], {"new_key": "new_value"}),
    ([ValueError("Ungültige Daten"), ValueError("Ungültige Daten")], {"key": "value"})
])
def test_backup_restore_and_corrupt_data_handling(load_return, expected_content, monkeypatch):
    mock_json_load = Mock(side_effect=load_return)
    monkeypatch.setattr(json_file_handler.json, "load", mock_json_load)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name
    try:
        with open(file_path, 'w') as file:
            json.dump({"key": "value"}, file)
        write_and_check(file_path, {"new_key": "new_value"})
        with open(file_path, 'r') as file:
            # mocked auch hier json.load, obwohl monkeypatch für json_file_handler.json.load
            restored_content = json.loads(file.read())
            assert restored_content == expected_content
    finally:
        # Löschen Sie die temporären Dateien
        os.remove(file_path)
        if os.path.exists(file_path + ".bak"):
            os.remove(file_path + ".bak")
