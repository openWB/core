#!/usr/bin/env python3
from modules.common.component_type import ComponentDescriptor
from modules.devices.zendure.zendure.config import ZendureInverterSetup


component_descriptor = ComponentDescriptor(configuration_factory=ZendureInverterSetup)
