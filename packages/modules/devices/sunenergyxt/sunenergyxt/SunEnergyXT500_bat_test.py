#!/usr/bin/env python3
"""Unit tests for SunEnergyXT 500 Series battery module."""
import pytest
import requests_mock as req_mock

from unittest.mock import MagicMock, patch
from modules.devices.sunenergyxt.sunenergyxt.bat import SunEnergyXTBat
from modules.devices.sunenergyxt.sunenergyxt.config import (
    SunEnergyXT,
    SunEnergyXTBatSetup,
    SunEnergyXTConfiguration,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_URL = "http://192.168.1.100"


def _make_bat() -> SunEnergyXTBat:
    """Create a SunEnergyXTBat instance with mocked stores."""
    device_config = SunEnergyXT(
        configuration=SunEnergyXTConfiguration(ip_address="192.168.1.100")
    )
    component_config = SunEnergyXTBatSetup()
    bat = SunEnergyXTBat(component_config, device_config=device_config)

    # Mock internal helpers so no real HA infrastructure is needed
    bat.sim_counter = MagicMock()
    bat.sim_counter.sim_count.return_value = (1000.0, 500.0)
    bat.store = MagicMock()
    bat.fault_state = MagicMock()
    bat._base_url = BASE_URL
    bat._gs_max = 800  # Fallback-Wert wie in initialize()

    return bat


# ---------------------------------------------------------------------------
# update() – Parsing SC / PB / IS
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_update_parses_soc_and_power(self, requests_mock):
        """update() liest SC (SoC) und PB (Batteriepower) korrekt aus."""
        bat = _make_bat()
        requests_mock.get(
            f"{BASE_URL}/read",
            json={"state": {"reported": {"SC": 75, "PB": -500, "IS": 800}}}
        )

        bat.update()

        bat.store.set.assert_called_once()
        bat_state = bat.store.set.call_args[0][0]
        assert bat_state.soc == 75
        assert bat_state.power == -500.0

    def test_update_sets_gs_max_from_is(self, requests_mock):
        """update() setzt self._gs_max dynamisch aus IS."""
        bat = _make_bat()
        requests_mock.get(
            f"{BASE_URL}/read",
            json={"state": {"reported": {"SC": 50, "PB": 0, "IS": 2400}}}
        )

        bat.update()

        assert bat._gs_max == 2400

    def test_update_keeps_fallback_if_is_zero(self, requests_mock):
        """update() behält Fallback-_gs_max wenn IS=0 geliefert wird."""
        bat = _make_bat()
        requests_mock.get(
            f"{BASE_URL}/read",
            json={"state": {"reported": {"SC": 50, "PB": 0, "IS": 0}}}
        )

        bat.update()

        assert bat._gs_max == 800  # Fallback bleibt

    def test_update_handles_flat_json(self, requests_mock):
        """update() akzeptiert auch flaches JSON ohne 'state'/'reported'."""
        bat = _make_bat()
        requests_mock.get(
            f"{BASE_URL}/read",
            json={"SC": 42, "PB": 300, "IS": 800}
        )

        bat.update()

        bat_state = bat.store.set.call_args[0][0]
        assert bat_state.soc == 42
        assert bat_state.power == 300.0

    def test_update_uses_simcount(self, requests_mock):
        """update() ruft sim_counter.sim_count() auf und übergibt Werte."""
        bat = _make_bat()
        bat.sim_counter.sim_count.return_value = (2000.0, 1000.0)
        requests_mock.get(
            f"{BASE_URL}/read",
            json={"state": {"reported": {"SC": 80, "PB": -1000, "IS": 800}}}
        )

        bat.update()

        bat.sim_counter.sim_count.assert_called_once_with(-1000.0)
        bat_state = bat.store.set.call_args[0][0]
        assert bat_state.imported == 2000.0
        assert bat_state.exported == 1000.0


# ---------------------------------------------------------------------------
# set_power_limit() – MM/GS Steuerung
# ---------------------------------------------------------------------------

class TestSetPowerLimit:
    def test_none_sets_automatic_mode(self, requests_mock):
        """power_limit=None → MM=1, GS=0 (Self-Consumption)."""
        bat = _make_bat()
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(None)

        assert requests_mock.last_request.json() == {"state": {"MM": 1, "GS": 0}}

    def test_zero_stops_discharge(self, requests_mock):
        """power_limit=0 → MM=0, GS=0 (Entladung gesperrt)."""
        bat = _make_bat()
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(0)

        assert requests_mock.last_request.json() == {"state": {"MM": 0, "GS": 0}}

    def test_positive_discharges(self, requests_mock):
        """power_limit>0 → MM=0, GS=+p (Entladen)."""
        bat = _make_bat()
        bat._gs_max = 800
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(500)

        assert requests_mock.last_request.json() == {"state": {"MM": 0, "GS": 500}}

    def test_negative_charges(self, requests_mock):
        """power_limit<0 → MM=0, GS=-p (Laden)."""
        bat = _make_bat()
        bat._gs_max = 800
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(-600)

        assert requests_mock.last_request.json() == {"state": {"MM": 0, "GS": -600}}

    def test_discharge_capped_at_gs_max(self, requests_mock):
        """Entladeleistung wird auf _gs_max (IS) begrenzt."""
        bat = _make_bat()
        bat._gs_max = 800
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(9999)  # Weit über Limit

        payload = requests_mock.last_request.json()
        assert payload["state"]["GS"] == 800

    def test_charge_capped_at_gs_max(self, requests_mock):
        """Ladeleistung wird auf _gs_max (IS) begrenzt."""
        bat = _make_bat()
        bat._gs_max = 2400
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(-9999)  # Weit über Limit

        payload = requests_mock.last_request.json()
        assert payload["state"]["GS"] == -2400

    def test_gs_max_reflects_pro_model(self, requests_mock):
        """Nach update() mit IS=2400 (Pro) wird 2400W als Limit genutzt."""
        bat = _make_bat()
        bat._gs_max = 2400  # Wie nach update() mit IS=2400
        requests_mock.post(f"{BASE_URL}/write", json={})

        bat.set_power_limit(-2400)

        payload = requests_mock.last_request.json()
        assert payload["state"]["GS"] == -2400


# ---------------------------------------------------------------------------
# power_limit_controllable()
# ---------------------------------------------------------------------------

def test_power_limit_controllable():
    """power_limit_controllable() muss True zurückgeben."""
    bat = _make_bat()
    assert bat.power_limit_controllable() is True
