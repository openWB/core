#!/usr/bin/env python3
from modules.common.component_type import ComponentDescriptor
from modules.devices.benning.benning.config import BenningInverterSetup


component_descriptor = ComponentDescriptor(configuration_factory=BenningInverterSetup)
