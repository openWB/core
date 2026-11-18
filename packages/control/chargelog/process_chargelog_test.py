from control.chargelog.process_chargelog import get_totals_of_filtered_log_data


def _entry(costs: float, tariff_split=None) -> dict:
    data = {"range_charged": 10, "imported_since_mode_switch": 1000, "power": 1000, "costs": costs}
    if tariff_split is not None:
        data["tariff_split"] = tariff_split
    return {"time": {"time_charged": "0:30"}, "data": data}


def test_totals_tariff_split():
    log_data = {"entries": [
        _entry(1.0),  # Eintrag ohne Aufteilung (ältere Version, dynamischer Tarif)
        _entry(2.0, {"NT": {"energy": 1000.1, "costs": 0.25}, "Standardpreis": {"energy": 500, "costs": 0.15}}),
        _entry(3.0, {"NT": {"energy": 2000.2, "costs": 0.5}}),
        _entry(4.0, {"NT": {"energy": None}}),  # unbrauchbarer Eintrag wird übersprungen
    ]}

    totals = get_totals_of_filtered_log_data(log_data)

    assert totals["costs"] == 10.0
    assert totals["tariff_split"] == {"NT": {"energy": 3000.3, "costs": 0.75},
                                      "Standardpreis": {"energy": 500, "costs": 0.15}}


def test_totals_without_tariff_split():
    totals = get_totals_of_filtered_log_data({"entries": [_entry(1.0), _entry(2.0)]})

    assert totals["costs"] == 3.0
    assert "tariff_split" not in totals
