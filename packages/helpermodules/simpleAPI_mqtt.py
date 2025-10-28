#!/usr/bin/env python3
"""
SimpleMQTT API Daemon

Transforms complex MQTT topic structures into simplified API topics.
Listens to openWB/* topics and republishes them under openWB/simpleAPI/* 
with JSON/tuple expansion and ID simplification.
"""

import argparse
import json
import logging
import time
import sys
import ssl
from typing import Dict, Any, Optional, Set
from pathlib import Path
import paho.mqtt.client as mqtt # type: ignore
import re


class SimpleMQTTDaemon:
    """Main daemon class for SimpleMQTT API transformation."""
    
    def __init__(self, host: str = "localhost", port: int = 1883, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 use_tls: bool = False, config_file: Optional[str] = None):
        """Initialize the daemon with MQTT connection parameters."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        
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
        
        # Setup logging
        self._setup_logging()
        
        # Load additional config from file if provided
        if config_file:
            self._load_config_file(config_file)
    
    def _setup_logging(self):
        """Configure logging for the daemon."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_config_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.error(f"Configuration file not found: {config_file}")
                sys.exit(1)
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Override instance variables with config file values
            self.host = config.get('host', self.host)
            self.port = config.get('port', self.port)
            self.username = config.get('username', self.username)
            self.password = config.get('password', self.password)
            self.use_tls = config.get('use_tls', self.use_tls)
            
            # Set log level if specified in config
            log_level = config.get('log_level', 'INFO')
            numeric_level = getattr(logging, log_level.upper(), logging.INFO)
            logging.getLogger().setLevel(numeric_level)
            
            self.logger.info(f"Loaded configuration from {config_file}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file {config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_file}: {e}")
            sys.exit(1)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful MQTT connection."""
        if rc == 0:
            self.logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            # Subscribe to specific openWB component topics
            client.subscribe("openWB/bat/#", qos=0)
            client.subscribe("openWB/pv/#", qos=0)
            client.subscribe("openWB/chargepoint/#", qos=0)
            client.subscribe("openWB/counter/#", qos=0)
            
            # Subscribe to simpleAPI set topics for write operations
            client.subscribe("openWB/simpleAPI/set/#", qos=0)
            
            self.logger.info("Subscribed to openWB component topics (bat, pv, chargepoint, counter) and simpleAPI set topics")
        else:
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection (code: {rc}). Attempting to reconnect...")
            self._reconnect()
        else:
            self.logger.info("Clean MQTT disconnection")
    
    def _reconnect(self):
        """Attempt to reconnect to MQTT broker with delay."""
        reconnect_attempts = 0
        max_attempts = 100  # Prevent infinite loops
        
        while reconnect_attempts < max_attempts:
            try:
                reconnect_attempts += 1
                self.logger.info(f"Reconnection attempt {reconnect_attempts}/{max_attempts} in 10 seconds...")
                time.sleep(10)
                
                self.client.reconnect()
                self.logger.info("Successfully reconnected to MQTT broker")
                break
                
            except Exception as e:
                self.logger.error(f"Reconnection attempt {reconnect_attempts} failed: {e}")
                
        if reconnect_attempts >= max_attempts:
            self.logger.critical("Maximum reconnection attempts exceeded. Exiting.")
            sys.exit(1)
    
    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            self.logger.debug(f"Received: {topic} = {payload}")
            
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
            self.logger.error(f"Error processing message {msg.topic}: {e}")
    
    def _transform_and_publish(self, original_topic: str, payload: str):
        """Transform original topic to simpleAPI format and publish if value changed."""
        try:
            # Parse the payload
            parsed_payload = self._parse_payload(payload)
            
            # Generate transformed topics
            transformed_topics = self._generate_simple_topics(original_topic, parsed_payload)
            
            # Publish each transformed topic if value changed
            for topic, value in transformed_topics.items():
                self._publish_if_changed(topic, value)
                
        except Exception as e:
            self.logger.error(f"Error transforming topic {original_topic}: {e}")
    
    def _parse_payload(self, payload: str) -> Any:
        """Parse payload as JSON, tuple, or raw value."""
        payload = payload.strip()
        
        # Try to parse as JSON
        if payload.startswith('{') or payload.startswith('['):
            try:
                return json.loads(payload)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Invalid JSON payload: {payload} - {e}")
                return payload
        
        # Try to parse as Python literal (for tuples/lists)
        if payload.startswith('(') or payload.startswith('['):
            try:
                import ast
                return ast.literal_eval(payload)
            except (ValueError, SyntaxError) as e:
                self.logger.warning(f"Invalid literal payload: {payload} - {e}")
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
        
        # Handle different value types
        self._expand_value_to_topics(simple_base, parsed_value, result)
        
        # Generate simplified topics for lowest IDs
        simplified_topics = self._generate_simplified_topics(simple_base, parsed_value)
        result.update(simplified_topics)
        
        return result
    
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
            # Raw value
            result[base_topic] = value
    
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
            self.logger.debug(f"Published: {topic} = {str_value}")
        except Exception as e:
            self.logger.error(f"Failed to publish {topic}: {e}")
    
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
                self.logger.debug(f"Cached charge_template for chargepoint {chargepoint_id}")
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse charge_template JSON for {topic}: {e}")
        except Exception as e:
            self.logger.error(f"Error caching charge_template for {topic}: {e}")
    
    def _handle_write_operation(self, topic: str, payload: str):
        """Handle write operations from simpleAPI set topics."""
        try:
            self.logger.info(f"Write operation: {topic} = {payload}")
            
            # Parse the set topic to extract operation details
            topic_parts = topic.replace('openWB/simpleAPI/set/', '').split('/')
            
            if len(topic_parts) < 2:
                self.logger.error(f"Invalid set topic format: {topic}")
                return
            
            operation = topic_parts[0]
            
            if operation == 'chargepoint':
                self._handle_chargepoint_operation(topic_parts, payload)
            elif operation == 'bat_mode':
                self._handle_bat_mode_operation(payload)
            else:
                self.logger.error(f"Unknown operation: {operation}")
                
        except Exception as e:
            self.logger.error(f"Error handling write operation {topic}: {e}")
    
    def _handle_chargepoint_operation(self, topic_parts: list, payload: str):
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
                self.logger.error("No chargepoint ID found and no lowest ID available")
                return
        else:
            self.logger.error(f"Invalid chargepoint topic format: {'/'.join(topic_parts)}")
            return
        
        self.logger.debug(f"Chargepoint operation: ID={chargepoint_id}, parameter={parameter}, value={payload}")
        
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
            self.logger.error(f"Unknown chargepoint parameter: {parameter}")
    
    def _get_charge_template(self, chargepoint_id: str) -> Optional[Dict[str, Any]]:
        """Get charge_template for a chargepoint, either from cache or request it."""
        if chargepoint_id in self.charge_template_cache:
            return self.charge_template_cache[chargepoint_id].copy()
        
        self.logger.warning(f"No cached charge_template for chargepoint {chargepoint_id}")
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
            self.logger.error(f"Invalid chargemode: {mode}")
            return
        
        internal_mode = mode_mapping[mode]
        charge_template = self._get_charge_template(chargepoint_id)
        
        if charge_template is None:
            self.logger.error(f"No charge_template available for chargepoint {chargepoint_id}")
            return
        
        # Modify the chargemode.selected value
        charge_template['chargemode']['selected'] = internal_mode
        
        # Publish the modified template
        target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"
        self._publish_json(target_topic, charge_template)
        self.logger.info(f"Set chargemode to {mode} ({internal_mode}) for chargepoint {chargepoint_id}")
    
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
            self.logger.info(f"Set charge current to {current_value}A for chargepoint {chargepoint_id}")
            
        except ValueError:
            self.logger.error(f"Invalid current value: {current}")
    
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
            self.logger.info(f"Set minimal PV SoC to {soc_value}% for chargepoint {chargepoint_id}")
            
        except ValueError:
            self.logger.error(f"Invalid SoC value: {soc}")
    
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
            self.logger.info(f"Set minimal permanent current to {current_value}A for chargepoint {chargepoint_id}")
            
        except ValueError:
            self.logger.error(f"Invalid current value: {current}")
    
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
            self.logger.info(f"Set max ECO price to {price_value} for chargepoint {chargepoint_id}")
            
        except ValueError:
            self.logger.error(f"Invalid price value: {price}")
    
    def _set_chargepoint_lock(self, chargepoint_id: str, lock_state: str):
        """Set chargepoint lock state."""
        try:
            lock_value = lock_state.lower() in ('true', '1', 'yes', 'on')
            target_topic = f"openWB/set/chargepoint/{chargepoint_id}/set/manual_lock"
            
            self.client.publish(target_topic, str(lock_value).lower(), qos=0, retain=True)
            self.logger.info(f"Set chargepoint {chargepoint_id} lock to {lock_value}")
            
        except Exception as e:
            self.logger.error(f"Error setting chargepoint lock: {e}")
    
    def _handle_bat_mode_operation(self, payload: str):
        """Handle battery mode operation."""
        valid_modes = ['min_soc_bat_mode', 'ev_mode', 'bat_mode']
        
        if payload not in valid_modes:
            self.logger.error(f"Invalid bat_mode: {payload}. Valid values: {valid_modes}")
            return
        
        target_topic = "openWB/set/general/chargemode_config/pv_charging/bat_mode"
        self.client.publish(target_topic, payload, qos=0, retain=True)
        self.logger.info(f"Set bat_mode to {payload}")
    
    def _publish_json(self, topic: str, data: Dict[str, Any]):
        """Publish JSON data to a topic."""
        try:
            json_payload = json.dumps(data)
            self.client.publish(topic, json_payload, qos=0, retain=True)
            self.logger.debug(f"Published JSON to {topic}")
        except Exception as e:
            self.logger.error(f"Failed to publish JSON to {topic}: {e}")
    
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
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def run(self):
        """Start the daemon main loop."""
        if not self.connect():
            sys.exit(1)
        
        self.logger.info("SimpleMQTT API Daemon started")
        
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
            self.client.disconnect()
            sys.exit(0)


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="SimpleMQTT API Daemon")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--username", help="MQTT username")
    parser.add_argument("--password", help="MQTT password")
    parser.add_argument("--tls", action="store_true", help="Use TLS/SSL")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run daemon
    daemon = SimpleMQTTDaemon(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        use_tls=args.tls,
        config_file=args.config
    )
    
    daemon.run()


if __name__ == "__main__":
    main()