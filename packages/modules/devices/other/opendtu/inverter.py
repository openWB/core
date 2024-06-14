#!/usr/bin/env python3
from modules.common.component_type import ComponentDescriptor
from modules.devices.other.opendtu.config import OpenDTUInverterSetup


component_descriptor = ComponentDescriptor(configuration_factory=OpenDTUInverterSetup)
