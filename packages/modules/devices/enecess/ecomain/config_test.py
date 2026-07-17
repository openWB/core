from dataclass_utils import dataclass_from_dict
import pytest

from modules.devices.enecess.ecomain import counter, inverter
from modules.devices.enecess.ecomain.config import (
    EcoMainCounterSetup,
    EcoMainInverterSetup,
    validate_inverter_configuration,
)
from modules.devices.enecess.vendor import vendor_descriptor


def test_nested_channels_are_deserialized():
    setup = dataclass_from_dict(EcoMainInverterSetup, {
        "name": "PV",
        "type": "inverter",
        "id": 7,
        "configuration": {
            "phase_count": 3,
            "invert": False,
            "channels": [
                {"phase": 3, "source": 2, "channel": 10},
                {"phase": 1, "source": 0, "channel": 1},
                {"phase": 2, "source": 1, "channel": 4},
            ],
        },
    })
    channels = validate_inverter_configuration(setup.configuration)
    assert [(item.phase, item.source, item.channel) for item in channels] == [
        (1, 0, 1), (2, 1, 4), (3, 2, 10)
    ]


@pytest.mark.parametrize("configuration", [
    {"phase_count": 2, "channels": [{"phase": 1, "source": 0, "channel": 1}]},
    {"phase_count": 1, "channels": []},
    {"phase_count": 3, "channels": [
        {"phase": 1, "source": 0, "channel": 1},
        {"phase": 1, "source": 0, "channel": 2},
        {"phase": 3, "source": 0, "channel": 3},
    ]},
    {"phase_count": 3, "channels": [
        {"phase": 1, "source": 0, "channel": 1},
        {"phase": 2, "source": 0, "channel": 1},
        {"phase": 3, "source": 0, "channel": 3},
    ]},
    {"phase_count": 1, "channels": [{"phase": 1, "source": 4, "channel": 1}]},
    {"phase_count": 1, "channels": [{"phase": 1, "source": 0, "channel": 11}]},
])
def test_invalid_inverter_configuration_is_rejected(configuration):
    setup = dataclass_from_dict(EcoMainInverterSetup, {
        "name": "PV", "type": "inverter", "id": 7, "configuration": configuration
    })
    with pytest.raises(ValueError):
        validate_inverter_configuration(setup.configuration)


def test_vendor_is_discovered_as_enecess():
    configuration = vendor_descriptor.configuration_factory()
    assert configuration.type == "enecess"
    assert configuration.vendor == "enecess"


@pytest.mark.parametrize(("module", "setup_class", "component_type"), [
    (counter, EcoMainCounterSetup, "counter"),
    (inverter, EcoMainInverterSetup, "inverter"),
])
def test_component_descriptors_are_discoverable(module, setup_class, component_type):
    descriptor = module.component_descriptor
    assert descriptor.configuration_factory is setup_class
    assert descriptor.configuration_factory().type == component_type
