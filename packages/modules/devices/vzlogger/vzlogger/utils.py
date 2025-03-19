import json
from typing import Dict


def parse_line(data: Dict, line: int) -> float:
    text = json.dumps(data, indent=4)  # pretty print | jq .|cat -n
    splitted_text = text.split("\n")  # Liste: ein Eintrag pro Zeile
    return float(splitted_text[line-1].strip(" ,"))  # Float aus Zeile parsen, bei 1 anfangen zu zählen
