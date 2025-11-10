#!/usr/bin/env python3
"""
SimpleMQTT API Daemon

Transforms complex MQTT topic structures into simplified API topics.
Listens to openWB/* topics and republishes them under openWB/simpleAPI/*
with JSON/tuple expansion and ID simplification.
"""

import json
import logging
from logging.handlers import RotatingFileHandler
import time
import sys
import ssl
from typing import Dict, Any, Optional
from pathlib import Path
import paho.mqtt.client as mqtt
import re

FORMAT_STR_SHORT = '%(asctime)s - %(message)s'
RAMDISK_PATH = str(Path(__file__).resolve().parents[1]) + '/ramdisk/'

log = logging.getLogger("simpleAPI")
log.propagate = False
file_handler = RotatingFileHandler(RAMDISK_PATH + 'simple_api.log', maxBytes=500000, backupCount=1)  # 0.5 MB
file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
log.addHandler(file_handler)

CONFIG_FILE_PATH = "/var/www/html/openWB/data/config/simpleAPI_mqtt_config.json"


class SimpleMQTTDaemon:
    """Main daemon class for SimpleMQTT API transformation."""

    def __init__(self, config_file: str):
        """Initialize the daemon with MQTT connection parameters."""
        self._load_config_file(config_file)

        # Cache for tracking value changes
        self.value_cache: Dict[str, Any] = {}

        # Cache for tracking lowest IDs per component type
        self.lowest_ids: Dict[str, int] = {}

        # Cache for storing current charge_template configurations
        self.charge_template_cache: Dict[str, Dict[str, Any]] = {}

        # MQTT client setup
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _load_config_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                log.error(f"Configuration file not found: {config_file}")
                sys.exit(1)

            with open(config_file, 'r') as f:
                config = json.load(f)

            # Override instance variables with config file values
            try:
                self.host = config['host']
                self.port = config['port']
                self.username = config['username']
                self.password = config['password']
                self.use_tls = config['use_tls']
            except KeyError as e:
                log.exception(f"Missing required config parameter: {e}")
                sys.exit(1)

            # Set log level if specified in config
            log_level = config.get('log_level', 'INFO')
            numeric_level = getattr(logging, log_level.upper(), logging.INFO)
            log.setLevel(numeric_level)

            log.info(f"Loaded configuration from {config_file}")
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in config file {config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            log.error(f"Failed to load config file {config_file}: {e}")
            sys.exit(1)

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful MQTT connection."""
        if rc == 0:
            log.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            # Subscribe to specific openWB component topics
            client.subscribe("openWB/bat/#", qos=0)
            client.subscribe("openWB/pv/#", qos=0)
            client.subscribe("openWB/chargepoint/#", qos=0)
            client.subscribe("openWB/counter/#", qos=0)

            # Subscribe to simpleAPI set topics for write operations
            client.subscribe("openWB/simpleAPI/set/#", qos=0)

            log.info(
                "Subscribed to openWB component topics (bat, pv, chargepoint, counter) and simpleAPI set topics")
        else:
            log.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        if rc != 0:
            log.warning(f"Unexpected MQTT disconnection (code: {rc}). Attempting to reconnect...")
            self._reconnect()
        else:
            log.info("Clean MQTT disconnection")

    def _reconnect(self):
        """Attempt to reconnect to MQTT broker with delay."""
        reconnect_attempts = 0
        max_attempts = 100  # Prevent infinite loops

        while reconnect_attempts < max_attempts:
            try:
                reconnect_attempts += 1
                log.info(f"Reconnection attempt {reconnect_attempts}/{max_attempts} in 10 seconds...")
                time.sleep(10)

                self.client.reconnect()
                log.info("Successfully reconnected to MQTT broker")
                break

            except Exception as e:
                log.error(f"Reconnection attempt {reconnect_attempts} failed: {e}")

        if reconnect_attempts >= max_attempts:
            log.critical("Maximum reconnection attempts exceeded. Exiting.")
            sys.exit(1)

    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            log.debug(f"Received: {topic} = {payload}")

            # Handle write operations (simpleAPI set topics)
            if topic.startswith('openWB/simpleAPI/set/'):
                self._handle_write_operation(topic, payload)
                return

            # Skip if this is already a simpleAPI topic to avoid loops
            if '/simpleAPI/' in topic:
                return

            # Cache charge_template configurations for later use
            if '/set/charge_template' in topic:
                self._cache_charge_template(topic, payload)

            # Transform and publish the message
            self._transform_and_publish(topic, payload)

        except Exception as e:
            log.error(f"Error processing message {msg.topic}: {e}")

    def _transform_and_publish(self, original_topic: str, payload: str):
        """Transform original topic to simpleAPI format and publish if value changed."""
        try:
            log.debug(f"DEBUG: Processing original topic: {original_topic}")

            # Parse the payload
            parsed_payload = self._parse_payload(payload)

            # Generate transformed topics
            transformed_topics = self._generate_simple_topics(original_topic, parsed_payload)

            log.debug(
                f"DEBUG: Generated {len(transformed_topics)} transformed topics: "
                f"{list(transformed_topics.keys())}"
            )

            # Publish each transformed topic if value changed
            for topic, value in transformed_topics.items():
                self._publish_if_changed(topic, value)

        except Exception as e:
            log.error(f"Error transforming topic {original_topic}: {e}")

    def _parse_payload(self, payload: str) -> Any:
        """Parse payload as JSON, tuple, or raw value."""
        payload = payload.strip()

        # Try to parse as JSON
        if payload.startswith('{') or payload.startswith('['):
            try:
                return json.loads(payload)
            except json.JSONDecodeError as e:
                log.warning(f"Invalid JSON payload: {payload} - {e}")
                return payload

        # Try to parse as Python literal (for tuples/lists)
        if payload.startswith('(') or payload.startswith('['):
            try:
                import ast
                return ast.literal_eval(payload)
            except (ValueError, SyntaxError) as e:
                log.warning(f"Invalid literal payload: {payload} - {e}")
                return payload

        # Try to parse as number
        try:
            if '.' in payload:
                return float(payload)
            else:
                return int(payload)
        except ValueError:
            pass

        # Try to parse boolean
        if payload.lower() in ('true', 'false'):
            return payload.lower() == 'true'

        # Return as string if null
        if payload.lower() == 'null':
            return None

        # Return as raw string
        return payload

    def _generate_simple_topics(self, original_topic: str, parsed_value: Any) -> Dict[str, Any]:
        """Generate simpleAPI topics from original topic and parsed value."""
        result = {}

        # Convert original topic to simpleAPI base
        simple_base = original_topic.replace('openWB/', 'openWB/simpleAPI/')

        # Extract component info for ID tracking
        self._track_component_ids(original_topic)

        # Apply chargepoint-specific transformations
        if '/chargepoint/' in simple_base:
            simple_base = self._transform_chargepoint_topic(simple_base)
            if simple_base is None:  # Topic should be filtered out
                return result

        # Handle different value types
        self._expand_value_to_topics(simple_base, parsed_value, result)

        # Generate simplified topics for lowest IDs
        simplified_topics = self._generate_simplified_topics(simple_base, parsed_value)
        result.update(simplified_topics)

        return result

    def _transform_chargepoint_topic(self, simple_base: str) -> Optional[str]:
        """Transform chargepoint topics according to simplified structure."""

        log.debug(f"DEBUG: _transform_chargepoint_topic input: {simple_base}")

        # FIRST: Handle connected_vehicle transformations (both /get/ and direct)
        # This must happen BEFORE any other filtering
        if '/connected_vehicle/config/chargemode' in simple_base:
            log.debug(f"DEBUG: Found chargemode pattern, transforming: {simple_base}")
            original = simple_base
            simple_base = re.sub(r'/get/connected_vehicle/config/chargemode$', '/chargemode', simple_base)
            log.debug(f"DEBUG: After first regex: {simple_base}")
            simple_base = re.sub(r'/connected_vehicle/config/chargemode$', '/chargemode', simple_base)
            log.debug(f"DEBUG: After second regex: {simple_base}")
            if original != simple_base:
                log.debug(f"DEBUG: Charge mode transformation successful: {original} -> {simple_base}")
        elif '/connected_vehicle/info/name' in simple_base:
            log.debug(f"DEBUG: Found vehicle name pattern, transforming: {simple_base}")
            simple_base = re.sub(r'/get/connected_vehicle/info/name$', '/vehicle_name', simple_base)
            simple_base = re.sub(r'/connected_vehicle/info/name$', '/vehicle_name', simple_base)

        # Keep only config topics that are in the allowed list
        if '/config/' in simple_base and not re.search(r'/(chargemode|vehicle_name)$', simple_base):
            allowed_config_paths = [
                'configuration/ip_address', 'configuration/duo_num', 'ev', 'name',
                'type', 'template', 'connected_phases', 'phase_1',
                'auto_phase_switch_hw', 'control_pilot_interruption_hw', 'id', 'ocpp_chargebox_id'
            ]

            # Extract the config path part
            config_match = re.search(r'/config/(.+)$', simple_base)
            if config_match:
                config_path = config_match.group(1)
                if config_path in allowed_config_paths:
                    return simple_base  # Keep this config topic

            return None  # Filter out other config topics

        # Handle set topics with special mappings
        if '/set/' in simple_base:
            # set/manual_lock -> manual_lock
            simple_base = re.sub(r'/set/manual_lock$', '/manual_lock', simple_base)

            # set/current -> evse_current
            simple_base = re.sub(r'/set/current$', '/evse_current', simple_base)

            # Filter out all other set topics (like charge_template, log, etc.)
            if '/set/' in simple_base:
                return None

        # Handle get topics - remove /get/ prefix
        if '/get/' in simple_base:
            simple_base = simple_base.replace('/get/', '/')

            # Filter out unwanted topics - but exclude already transformed ones
            if not re.search(r'/(chargemode|vehicle_name)$', simple_base):
                unwanted_patterns = [
                    r'/connected_vehicle/(info|config|soc)/',
                    r'/max_evse_current$',
                    r'/current_branch$',
                    r'/current_commit$'
                ]

                for pattern in unwanted_patterns:
                    if re.search(pattern, simple_base):
                        return None
        else:
            # For non-get topics, also filter out remaining connected_vehicle topics
            # but exclude the ones we already transformed
            if not re.search(r'/(chargemode|vehicle_name)$', simple_base):
                if re.search(r'/connected_vehicle/', simple_base):
                    log.debug(f"DEBUG: Filtering out connected_vehicle topic: {simple_base}")
                    return None

        log.debug(f"DEBUG: _transform_chargepoint_topic output: {simple_base}")
        return simple_base

    def _track_component_ids(self, topic: str):
        """Track component IDs to determine lowest IDs."""
        # Pattern to match topics with numeric IDs
        pattern = r'openWB/(\w+)/(\d+)/'
        match = re.match(pattern, topic)

        if match:
            component_type = match.group(1)
            component_id = int(match.group(2))

            if component_type not in self.lowest_ids:
                self.lowest_ids[component_type] = component_id
            else:
                self.lowest_ids[component_type] = min(self.lowest_ids[component_type], component_id)

    def _expand_value_to_topics(self, base_topic: str, value: Any, result: Dict[str, Any]):
        """Expand complex values (JSON, tuples) into individual topics."""
        if isinstance(value, dict):
            # Handle JSON objects
            for key, val in value.items():
                new_topic = f"{base_topic}/{key}"
                self._expand_value_to_topics(new_topic, val, result)
        elif isinstance(value, (list, tuple)):
            # Handle arrays/tuples with 1-based indexing
            for i, val in enumerate(value, 1):
                new_topic = f"{base_topic}/{i}"
                self._expand_value_to_topics(new_topic, val, result)
        else:
            # Raw value - apply chargepoint transformations to final topics
            final_topic = base_topic
            if '/chargepoint/' in base_topic:
                transformed = self._transform_chargepoint_topic(base_topic)
                if transformed is not None:
                    final_topic = transformed
                else:
                    return  # Topic should be filtered out

            result[final_topic] = value

    def _generate_simplified_topics(self, simple_topic: str, parsed_value: Any) -> Dict[str, Any]:
        """Generate topics without IDs for components with lowest IDs."""
        result = {}

        # Pattern to match simpleAPI topics with numeric IDs
        pattern = r'openWB/simpleAPI/(\w+)/(\d+)/(.*)'
        match = re.match(pattern, simple_topic)

        if match:
            component_type = match.group(1)
            component_id = int(match.group(2))
            remaining_path = match.group(3)

            # Check if this is the lowest ID for this component type
            if component_type in self.lowest_ids and self.lowest_ids[component_type] == component_id:
                simplified_base = f"openWB/simpleAPI/{component_type}/{remaining_path}"

                # Apply chargepoint transformations to simplified topics as well
                if component_type == 'chargepoint':
                    simplified_base = self._transform_chargepoint_topic(simplified_base)
                    if simplified_base is None:
                        return result

                self._expand_value_to_topics(simplified_base, parsed_value, result)

        return result

    def _publish_if_changed(self, topic: str, value: Any):
        """Publish topic only if value has changed."""
        # Convert value to string for comparison and publishing
        str_value = str(value) if value is not None else "null"

        # Check if value changed
        if topic in self.value_cache and self.value_cache[topic] == str_value:
            return  # No change, don't publish

        # Update cache and publish
        self.value_cache[topic] = str_value

        try:
            self.client.publish(topic, str_value, qos=0, retain=True)
            log.debug(f"Published: {topic} = {str_value}")
        except Exception as e:
            log.error(f"Failed to publish {topic}: {e}")

    def _cache_charge_template(self, topic: str, payload: str):
        """Cache charge_template configurations for write operations."""
        try:
            # Extract chargepoint ID from topic
            pattern = r'openWB/chargepoint/(\d+)/set/charge_template'
            match = re.match(pattern, topic)

            if match:
                chargepoint_id = match.group(1)
                charge_template = json.loads(payload)
                self.charge_template_cache[chargepoint_id] = charge_template
                log.debug(f"Cached charge_template for chargepoint {chargepoint_id}")

        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse charge_template JSON for {topic}: {e}")
        except Exception as e:
            log.error(f"Error caching charge_template for {topic}: {e}")

    def _handle_write_operation(self, topic: str, payload: str):
        """Handle write operations from simpleAPI set topics."""
        try:
            # Skip processing if payload is empty (cleared set topic)
            if not payload or payload.strip() == "":
                log.debug(f"Skipping empty set topic: {topic}")
                return

            log.info(f"Write operation: {topic} = {payload}")

            # Parse the set topic to extract operation details
            topic_remainder = topic.replace('openWB/simpleAPI/set/', '')

            # Check for instant_charging_limit operations first (can be with or without chargepoint ID)
            if 'instant_charging_limit_soc' in topic_remainder:
                success = self._handle_instant_charging_limit_soc_operation(payload)
                if success:
                    self._clear_set_topic(topic)
                return
            elif 'instant_charging_limit_amount' in topic_remainder:
                success = self._handle_instant_charging_limit_amount_operation(payload)
                if success:
                    self._clear_set_topic(topic)
                return
            elif 'instant_charging_limit' in topic_remainder:
                success = self._handle_instant_charging_limit_operation(payload)
                if success:
                    self._clear_set_topic(topic)
                return

            topic_parts = topic_remainder.split('/')

            if len(topic_parts) < 1:
                log.error(f"Invalid set topic format: {topic}")
                return

            operation = topic_parts[0]

            if operation == 'chargepoint':
                success = self._handle_chargepoint_operation(topic_parts, payload)
                if success:
                    self._clear_set_topic(topic)
            elif operation == 'bat_mode':
                success = self._handle_bat_mode_operation(payload)
                if success:
                    self._clear_set_topic(topic)
            else:
                log.error(f"Unknown operation: {operation}")

        except Exception as e:
            log.error(f"Error handling write operation {topic}: {e}")

    def _clear_set_topic(self, topic: str):
        """Clear a set topic after successful operation."""
        try:
            self.client.publish(topic, "", qos=0, retain=True)
            log.debug(f"Cleared set topic: {topic}")
        except Exception as e:
            log.error(f"Failed to clear set topic {topic}: {e}")

    def _handle_chargepoint_operation(self, topic_parts: list, payload: str) -> bool:
        """Handle chargepoint-specific write operations."""
        # Determine chargepoint ID
        if len(topic_parts) >= 3 and topic_parts[1].isdigit():
            # Explicit ID provided: chargepoint/3/parameter
            chargepoint_id = topic_parts[1]
            parameter = topic_parts[2]
        elif len(topic_parts) >= 2:
            # No ID provided: chargepoint/parameter - use lowest ID
            if 'chargepoint' in self.lowest_ids:
                chargepoint_id = str(self.lowest_ids['chargepoint'])
                parameter = topic_parts[1]
            else:
                log.error("No chargepoint ID found and no lowest ID available")
                return False
        else:
            log.error(f"Invalid chargepoint topic format: {'/'.join(topic_parts)}")
            return False

        log.debug(f"Charge point operation: ID={chargepoint_id}, parameter={parameter}, value={payload}")

        if parameter == 'chargemode':
            self._set_chargemode(chargepoint_id, payload)
        elif parameter == 'chargecurrent':
            self._set_chargecurrent(chargepoint_id, payload)
        elif parameter == 'minimal_pv_soc':
            self._set_minimal_pv_soc(chargepoint_id, payload)
        elif parameter == 'minimal_permanent_current':
            self._set_minimal_permanent_current(chargepoint_id, payload)
        elif parameter == 'max_price_eco':
            self._set_max_price_eco(chargepoint_id, payload)
        elif parameter == 'chargepoint_lock':
            self._set_chargepoint_lock(chargepoint_id, payload)
        else:
            log.error(f"Unknown chargepoint parameter: {parameter}")
            return False

        return True

    def _get_charge_template(self, chargepoint_id: str) -> Optional[Dict[str, Any]]:
        """Get charge_template for a chargepoint, either from cache or request it."""
        if chargepoint_id in self.charge_template_cache:
            return self.charge_template_cache[chargepoint_id].copy()

        log.warning(f"No cached charge_template for chargepoint {chargepoint_id}")
        return None

    def _set_chargemode(self, chargepoint_id: str, mode: str):
        """Set chargemode for a chargepoint."""
        # Mapping from simple values to internal values
        mode_mapping = {
            'instant': 'instant_charging',
            'pv': 'pv_charging',
            'eco': 'eco_charging',
            'stop': 'stop',
            'target': 'scheduled_charging'
        }

        if mode not in mode_mapping:
            log.error(f"Invalid chargemode: {mode}")
            return

        internal_mode = mode_mapping[mode]
        charge_template = self._get_charge_template(chargepoint_id)

        if charge_template is None:
            log.error(f"No charge_template available for chargepoint {chargepoint_id}")
            return

        # Modify the chargemode.selected value
        charge_template['chargemode']['selected'] = internal_mode

        # Publish the modified template
        target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
        self._publish_json(target_topic, charge_template)
        log.info(f"Set chargemode to {mode} ({internal_mode}) for chargepoint {chargepoint_id}")

    def _set_chargecurrent(self, chargepoint_id: str, current: str):
        """Set charge current for instant charging."""
        try:
            current_value = int(current)
            charge_template = self._get_charge_template(chargepoint_id)

            if charge_template is None:
                return

            charge_template['chargemode']['instant_charging']['current'] = current_value

            target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
            self._publish_json(target_topic, charge_template)
            log.info(f"Set charge current to {current_value}A for chargepoint {chargepoint_id}")

        except ValueError:
            log.error(f"Invalid current value: {current}")

    def _set_minimal_pv_soc(self, chargepoint_id: str, soc: str):
        """Set minimal EV SoC for PV charging."""
        try:
            soc_value = int(soc)
            charge_template = self._get_charge_template(chargepoint_id)

            if charge_template is None:
                return

            charge_template['chargemode']['pv_charging']['min_soc'] = soc_value

            target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
            self._publish_json(target_topic, charge_template)
            log.info(f"Set minimal PV SoC to {soc_value}% for chargepoint {chargepoint_id}")

        except ValueError:
            log.error(f"Invalid SoC value: {soc}")

    def _set_minimal_permanent_current(self, chargepoint_id: str, current: str):
        """Set minimal permanent current for PV charging."""
        try:
            current_value = int(current)
            charge_template = self._get_charge_template(chargepoint_id)

            if charge_template is None:
                return

            charge_template['chargemode']['pv_charging']['min_current'] = current_value

            target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
            self._publish_json(target_topic, charge_template)
            log.info(f"Set minimal permanent current to {current_value}A for chargepoint {chargepoint_id}")

        except ValueError:
            log.error(f"Invalid current value: {current}")

    def _set_max_price_eco(self, chargepoint_id: str, price: str):
        """Set maximum price for ECO charging."""
        try:
            price_value = float(price)
            charge_template = self._get_charge_template(chargepoint_id)

            if charge_template is None:
                return

            charge_template['chargemode']['eco_charging']['max_price'] = price_value

            target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
            self._publish_json(target_topic, charge_template)
            log.info(f"Set max ECO price to {price_value} for chargepoint {chargepoint_id}")

        except ValueError:
            log.error(f"Invalid price value: {price}")

    def _set_chargepoint_lock(self, chargepoint_id: str, lock_state: str):
        """Set chargepoint lock state."""
        try:
            lock_value = lock_state.lower() in ('true', '1', 'yes', 'on')
            target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/manual_lock"

            self.client.publish(target_topic, str(lock_value).lower(), qos=0, retain=True)
            log.info(f"Set chargepoint {chargepoint_id} lock to {lock_value}")

        except Exception as e:
            log.error(f"Error setting chargepoint lock: {e}")

    def _handle_bat_mode_operation(self, payload: str) -> bool:
        """Handle battery mode operation."""
        valid_modes = ['min_soc_bat_mode', 'ev_mode', 'bat_mode']

        if payload not in valid_modes:
            log.error(f"Invalid bat_mode: {payload}. Valid values: {valid_modes}")
            return False

        target_topic = "openWB/set/general/chargemode_config/pv_charging/bat_mode"
        self.client.publish(target_topic, payload, qos=0, retain=True)
        log.info(f"Set bat_mode to {payload}")
        return True

    def _handle_instant_charging_limit_operation(self, payload: str) -> bool:
        """Handle instant charging limit type operation."""
        valid_limits = ['none', 'soc', 'amount']

        if payload not in valid_limits:
            log.error(f"Invalid instant_charging_limit: {payload}. Valid values: {valid_limits}")
            return False

        # Get chargepoint ID (use lowest if not specified)
        if 'chargepoint' in self.lowest_ids:
            chargepoint_id = str(self.lowest_ids['chargepoint'])
        else:
            log.error("No chargepoint ID found for instant_charging_limit operation")
            return False

        charge_template = self._get_charge_template(chargepoint_id)
        if charge_template is None:
            log.error(f"No charge_template available for chargepoint {chargepoint_id}")
            return False

        # Modify the instant_charging.limit.selected value
        charge_template['chargemode']['instant_charging']['limit']['selected'] = payload

        # Publish the modified template
        target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
        self._publish_json(target_topic, charge_template)
        log.info(f"Set instant_charging_limit to {payload} for chargepoint {chargepoint_id}")
        return True

    def _handle_instant_charging_limit_soc_operation(self, payload: str) -> bool:
        """Handle instant charging limit SoC operation."""
        try:
            soc_value = int(payload)
            if soc_value < 0 or soc_value > 100:
                log.error(f"Invalid SoC value: {soc_value}. Must be between 0 and 100")
                return False
        except ValueError:
            log.error(f"Invalid SoC value: {payload}. Must be an integer")
            return False

        # Get chargepoint ID (use lowest if not specified)
        if 'chargepoint' in self.lowest_ids:
            chargepoint_id = str(self.lowest_ids['chargepoint'])
        else:
            log.error("No chargepoint ID found for instant_charging_limit_soc operation")
            return False

        charge_template = self._get_charge_template(chargepoint_id)
        if charge_template is None:
            log.error(f"No charge_template available for chargepoint {chargepoint_id}")
            return False

        # Modify the instant_charging.limit.soc value
        charge_template['chargemode']['instant_charging']['limit']['soc'] = soc_value

        # Publish the modified template
        target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
        self._publish_json(target_topic, charge_template)
        log.info(f"Set instant_charging_limit_soc to {soc_value}% for chargepoint {chargepoint_id}")
        return True

    def _handle_instant_charging_limit_amount_operation(self, payload: str) -> bool:
        """Handle instant charging limit amount operation."""
        try:
            amount_value = int(payload)
            if amount_value < 1 or amount_value > 50:
                log.error(f"Invalid amount value: {amount_value}. Must be between 1 and 50")
                return False

            # Convert to internal value (multiply by 1000)
            internal_amount = amount_value * 1000
        except ValueError:
            log.error(f"Invalid amount value: {payload}. Must be an integer")
            return False

        # Get chargepoint ID (use lowest if not specified)
        if 'chargepoint' in self.lowest_ids:
            chargepoint_id = str(self.lowest_ids['chargepoint'])
        else:
            log.error("No chargepoint ID found for instant_charging_limit_amount operation")
            return False

        charge_template = self._get_charge_template(chargepoint_id)
        if charge_template is None:
            log.error(f"No charge_template available for chargepoint {chargepoint_id}")
            return False

        # Modify the instant_charging.limit.amount value
        charge_template['chargemode']['instant_charging']['limit']['amount'] = internal_amount

        # Publish the modified template
        target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
        self._publish_json(target_topic, charge_template)
        log.info(
            f"Set instant_charging_limit_amount to {amount_value} kWh "
            f"({internal_amount} Wh) for chargepoint {chargepoint_id}"
        )
        return True

    def _publish_json(self, topic: str, data: Dict[str, Any]):
        """Publish JSON data to a topic."""
        try:
            json_payload = json.dumps(data)
            self.client.publish(topic, json_payload, qos=0, retain=True)
            log.debug(f"Published JSON to {topic}")
        except Exception as e:
            log.error(f"Failed to publish JSON to {topic}: {e}")

    def connect(self):
        """Establish connection to MQTT broker."""
        try:
            # Setup TLS if requested
            if self.use_tls:
                self.client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                                    cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS,
                                    ciphers=None)

            # Setup authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            # Connect to broker
            self.client.connect(self.host, self.port, 60)
            return True

        except Exception as e:
            log.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def run(self):
        """Start the daemon main loop."""
        if not self.connect():
            sys.exit(1)

        log.info("SimpleMQTT API Daemon started")

        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            log.info("Received interrupt signal, shutting down...")
            self.client.disconnect()
            sys.exit(0)


def main():
    daemon = SimpleMQTTDaemon(config_file=CONFIG_FILE_PATH)
    daemon.run()


if __name__ == "__main__":
    main()
