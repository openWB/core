"""
Modified Version of the Fronius API:
https://github.com/MaStr/batcontrol

This module provides a class `FroniusWR` for handling Fronius GEN24 Inverters.
It includes methods for interacting with the inverter's API, managing battery
configurations, and controlling various inverter settings.

The Fronius Web-API is a bit quirky, which is reflected in the code.

The Web-Login form does send a first request without authentication, which
returns a nonce. This nonce is then used to create a digest for the login
request.

Parts of the information can be called without authentication, but some
settings require authentication. We tackle a 401 as a signal to login again
and retry the request.

Yes, the Webfrontend does send the password on each authenticated request hashed
with MD5, nounce etc.

"""
import time
import os
import logging
import json
import hashlib
from dataclasses import dataclass
import requests
from packaging import version

logger = logging.getLogger(__name__)
logger.info('Loading Fronius bat control API module')


def hash_utf8(x, algorithm="MD5"):
    """Hash a string or bytes object.

    Args:
        x: String or bytes to hash
        algorithm: Hash algorithm to use ("MD5" or "SHA256")
    """
    if isinstance(x, str):
        x = x.encode("utf-8")

    if algorithm.upper() == "SHA256":
        return hashlib.sha256(x).hexdigest()
    else:  # Default to MD5 for backward compatibility
        return hashlib.md5(x).hexdigest()


class MockResponse:
    """ Mock response object to return when no update is needed """

    def __init__(self):
        self.text = '{"writeSuccess": ["timeofuse"]}'
        self.status_code = 200


@dataclass
class FroniusApiConfig:
    """Configuration for Fronius API endpoints and behavior."""
    from_version: version.Version
    to_version: version.Version
    version_path: str
    powerflow_path: str
    storage_path: str
    config_battery_path: str
    config_powerunit_path: str
    config_solar_api_path: str
    config_timeofuse_path: str
    commands_login_path: str
    commands_logout_path: str
    auth_algorithm: str = "SHA256"  # Authentication algorithm: "MD5" or "SHA256"


# Alle Konfigurationen in einer Liste
API_CONFIGS = [
    FroniusApiConfig(
        from_version=version.parse("0.0.0"),
        to_version=version.parse("1.28.7-1"),
        version_path='/status/version',
        powerflow_path='/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
        storage_path='/solar_api/v1/GetStorageRealtimeData.cgi',
        config_battery_path='/config/batteries',
        config_powerunit_path='/config/setup/powerunit',
        config_solar_api_path='/config/solar_api',
        config_timeofuse_path='/config/timeofuse',
        commands_login_path='/commands/Login',
        commands_logout_path='/commands/Logout',
        auth_algorithm="MD5",
    ),
    FroniusApiConfig(
        from_version=version.parse("1.28.7-1"),
        to_version=version.parse("1.36"),
        version_path='/status/version',
        powerflow_path='/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
        storage_path='/solar_api/v1/GetStorageRealtimeData.cgi',
        config_battery_path='/config/batteries',
        config_powerunit_path='/config/powerunit',
        config_solar_api_path='/config/solar_api',
        config_timeofuse_path='/config/timeofuse',
        commands_login_path='/commands/Login',
        commands_logout_path='/commands/Logout',
        auth_algorithm="MD5",
    ),
    FroniusApiConfig(
        from_version=version.parse("1.36"),
        to_version=version.parse("1.38.6-1"),
        version_path='/api/status/version',
        powerflow_path='/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
        storage_path='/solar_api/v1/GetStorageRealtimeData.cgi',
        config_battery_path='/api/config/batteries',
        config_powerunit_path='/api/config/powerunit',
        config_solar_api_path='/api/config/solar_api',
        config_timeofuse_path='/api/config/timeofuse',
        commands_login_path='/api/commands/Login',
        commands_logout_path='/api/commands/Logout',
        auth_algorithm="MD5",
    ),
    FroniusApiConfig(
        from_version=version.parse("1.38.6-1"),
        to_version=version.parse("9999.99.99"),
        version_path='/api/status/version',
        powerflow_path='/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
        storage_path='/solar_api/v1/GetStorageRealtimeData.cgi',
        config_battery_path='/api/config/batteries',
        config_powerunit_path='/api/config/powerunit',
        config_solar_api_path='/api/config/solar_api',
        config_timeofuse_path='/api/config/timeofuse',
        commands_login_path='/api/commands/Login',
        commands_logout_path='/api/commands/Logout',
        auth_algorithm="SHA256",
    ),
]


def get_api_config(fw_version: version) -> FroniusApiConfig:
    """Get the API configuration for the given firmware version."""
    for config in API_CONFIGS:
        if config.from_version <= fw_version < config.to_version:
            return config
    raise RuntimeError(
        f"Keine API Konfiguration fuer Firmware-Version {fw_version}")


class FroniusWR:
    """ Class for Handling Fronius GEN24 Inverters """

    def __init__(self, config: dict) -> None:

        # We are doing three login tests during first login.
        # As MD5 was the default on the old firmware, the latest
        # retries should be MD5.
        self.usable_password_hash_methods = [
            "SHA256",  # First try: SHA256
            "MD5",     # Second try: MD5
            "MD5"      # Third try: MD5 again (retry with same method)
        ]
        self._last_password_hash_method_index = -1
        self.password_hash = None
        self.subsequent_login = False
        self.ncvalue_num = 1
        self.cnonce = hashlib.md5(os.urandom(8)).hexdigest()
        self.login_attempts = 0
        self.address = str(config.get('address', None))
        self.nonce = 0
        self.user = str(config.get('user', None))
        self.password = str(config.get('password', None))

        # Fronius API IDs - configurable with defaults
        self.controller_id = str(config.get('fronius_controller_id', '0'))
        self.fronius_version = self.get_firmware_version()
        self.api_config = get_api_config(self.fronius_version)

        # Verify that the configured IDs are valid
        self._verify_fronius_ids()
        self.set_solar_api_active(True)

        self.set_allow_grid_charging(True)

        self.prev_time_of_use = None
        self._time_of_use_expires = 0

    def get_firmware_version(self) -> version:
        """ Get the firmware version of the inverter."""
        response = None

        # This stays as a hardcoded path for now
        # since 1.36 /api/status/version
        path = '/api/status/version'

        # Try to get the version from the new path
        try:
            response = self.send_request(
                path, method='GET', payload={}, auth=False)
        except RuntimeError:
            # If it fails, try the old path
            path = '/status/version'
            response = self.send_request(
                path, method='GET', payload={}, auth=False)

        if not response:
            raise RuntimeError('Failed to retrieve firmware version')
        version_dict = json.loads(response.text)
        version_string = version_dict["swrevisions"]["GEN24"]
        logger.info('Fronius firmware version: %s', version_string)
        return version.parse(version_string)

    def get_powerunit_config(self):
        """ Get additional PowerUnit configuration for backup power.
        Returns: dict with backup power configuration
        """
        path = self.api_config.config_powerunit_path
        response = self.send_request(path, auth=True)
        if not response:
            logger.error(
                'Failed to get power unit configuration. Returning empty dict'
            )
            return {}
        result = json.loads(response.text)
        return result

    def set_allow_grid_charging(self, value: bool):
        """ Switches grid charging on (true) or off."""
        if value:
            payload = '{"HYB_EVU_CHARGEFROMGRID": true}'
        else:
            payload = '{"HYB_EVU_CHARGEFROMGRID": false}'
        path = self.api_config.config_battery_path
        response = self.send_request(
            path, method='POST', payload=payload, auth=True)
        response_dict = json.loads(response.text)
        expected_write_successes = ['HYB_EVU_CHARGEFROMGRID']
        for expected_write_success in expected_write_successes:
            if expected_write_success not in response_dict['writeSuccess']:
                raise RuntimeError(f'failed to set {expected_write_success}')
        return response

    def set_solar_api_active(self, value: bool):
        """ Switches Solar.API on (true) or off. Solar.API is required to get SOC values."""
        if value:
            payload = '{"SolarAPIv1Enabled": true}'
        else:
            payload = '{"SolarAPIv1Enabled": false}'
        path = self.api_config.config_solar_api_path
        response = self.send_request(
            path, method='POST', payload=payload, auth=True)
        response_dict = json.loads(response.text)
        expected_write_successes = ['SolarAPIv1Enabled']
        for expected_write_success in expected_write_successes:
            if expected_write_success not in response_dict['writeSuccess']:
                raise RuntimeError(f'failed to set {expected_write_success}')
        return response

    def get_time_of_use(self):
        """ Get time of use configuration from inverter with 15-minute caching."""
        now = time.time()
        if (self.prev_time_of_use is None or now > self._time_of_use_expires):
            self._time_of_use_expires = now + 910
            # Fetch fresh time of use configuration from inverter
            logger.debug("Fetching fresh time of use configuration from inverter")
            path = self.api_config.config_timeofuse_path
            response = self.send_request(path, auth=True)
            if not response:
                return None
            result = json.loads(response.text)['timeofuse']

            # Save the result
            self.prev_time_of_use = result
            return result
        else:
            logger.debug("Returning previous time of use configuration")
            return self.prev_time_of_use

    def set_mode_self_regulation(self):
        """ Set the inverter to discharge the battery."""
        timeofuselist = []
        response = self.set_time_of_use(timeofuselist)
        return response

    def set_mode_avoid_discharge(self):
        """ Set the inverter to avoid discharging the battery."""
        timeofuselist = [{'Active': True,
                          'Power': int(0),
                          'ScheduleType': 'DISCHARGE_MAX',
                          "TimeTable": {"Start": "00:00", "End": "23:59"},
                          "Weekdays":
                          {"Mon": True,
                           "Tue": True,
                           "Wed": True,
                           "Thu": True,
                           "Fri": True,
                           "Sat": True,
                           "Sun": True}
                          }]
        return self.set_time_of_use(timeofuselist)

    def set_mode_force_charge(self, chargerate=500):
        """ Set the inverter to charge the battery with a specific power from GRID."""
        # activate timeofuse rules
        timeofuselist = [{'Active': True,
                          'Power': int(chargerate),
                          'ScheduleType': 'CHARGE_MIN',
                          "TimeTable": {"Start": "00:00", "End": "23:59"},
                          "Weekdays":
                          {"Mon": True,
                           "Tue": True,
                           "Wed": True,
                           "Thu": True,
                           "Fri": True,
                           "Sat": True,
                           "Sun": True}
                          }]
        return self.set_time_of_use(timeofuselist)

    def set_mode_force_discharge(self, dischargerate=500):
        """ Set the inverter to discharge the battery with a specific power"""
        # activate timeofuse rules
        timeofuselist = [{'Active': True,
                          'Power': int(dischargerate),
                          'ScheduleType': 'DISCHARGE_MAX',
                          "TimeTable": {"Start": "00:00", "End": "23:59"},
                          "Weekdays":
                          {"Mon": True,
                           "Tue": True,
                           "Wed": True,
                           "Thu": True,
                           "Fri": True,
                           "Sat": True,
                           "Sun": True}
                          }]
        return self.set_time_of_use(timeofuselist)

    def _compare_timeofuse_essentials(self, current_timeofuse, new_timeofuse):
        """Compare only ScheduleType and Power values of timeofuse configurations."""
        if len(current_timeofuse) != len(new_timeofuse):
            return False

        for i, (current_item, new_item) in enumerate(zip(current_timeofuse, new_timeofuse)):
            # Compare only ScheduleType and Power values
            if (current_item.get('ScheduleType') != new_item.get('ScheduleType') or
                    current_item.get('Power') != new_item.get('Power')):
                logger.debug("Time of use item %d differs in essential values: "
                             "ScheduleType current=%s vs new=%s, "
                             "Power current=%s vs new=%s",
                             i, current_item.get(
                                 'ScheduleType'), new_item.get('ScheduleType'),
                             current_item.get('Power'), new_item.get('Power'))
                return False

        return True

    def set_time_of_use(self, timeofuselist):
        """ Set the planned battery charge/discharge schedule."""
        # Get current time of use configuration to check if update is needed
        current_timeofuse = self.get_time_of_use()

        # Compare only ScheduleType and Power values to avoid unnecessary updates
        if current_timeofuse is not None and \
           self._compare_timeofuse_essentials(current_timeofuse, timeofuselist):
            logger.debug("Time of use configuration (ScheduleType and Power) is"
                         " already identical, skipping update")
            # Return a mock response object to maintain compatibility
            return MockResponse()

        config = {
            'timeofuse': timeofuselist
        }
        payload = json.dumps(config)
        path = self.api_config.config_timeofuse_path
        logger.info("Updating time of use configuration")
        response = self.send_request(
            path, method='POST', payload=payload, auth=True
        )
        if not response:
            raise RuntimeError('Failed to set time of use configuration')
        response_dict = json.loads(response.text)
        expected_write_successes = ['timeofuse']
        for expected_write_success in expected_write_successes:
            if expected_write_success not in response_dict['writeSuccess']:
                raise RuntimeError(f'failed to set {expected_write_success}')

        # Invalidate the cache after successfully updating the configuration
        if self.prev_time_of_use is not None:
            logger.debug("Invalidating previous time of use after update")
            self.prev_time_of_use = None
            self._time_of_use_expires = 0
        return response

    def _verify_fronius_ids(self):
        """
        Verify that the configured controller_id is valid.

        This method makes test calls to the Fronius API to ensure the configured
        ID exists in the actual API responses. If verification fails, it logs
        the complete JSON response to help with debugging.
        """
        # Verify controller_id by checking storage data
        try:
            logger.info('Verifying Fronius controller_id: %s',
                        self.controller_id)
            path = self.api_config.storage_path
            response = self.send_request(path)
            if response:
                result = json.loads(response.text)
                data = result.get('Body', {}).get('Data', {})

                if self.controller_id not in data:
                    logger.error(
                        'Configured controller_id "%s" not found in Fronius API response.',
                        self.controller_id
                    )
                    logger.error(
                        'Available controller IDs: %s',
                        list(data.keys())
                    )
                    logger.error(
                        'Complete Storage Data JSON response:\n%s',
                        json.dumps(data, indent=2)
                    )
                    raise RuntimeError(
                        f'Invalid fronius_controller_id "{self.controller_id}". '
                        f'Available IDs: {list(data.keys())}'
                    )

                # Also verify that the Controller key exists within the data
                controller_data = data.get(self.controller_id, {})
                if 'Controller' not in controller_data:
                    logger.error(
                        'Controller data not found for controller_id "%s"',
                        self.controller_id
                    )
                    logger.error(
                        'Complete data for controller_id "%s":\n%s',
                        self.controller_id,
                        json.dumps(controller_data, indent=2)
                    )
                    raise RuntimeError(
                        f'No Controller data found for fronius_controller_id "{self.controller_id}"'
                    )
                logger.info(
                    'Controller ID "%s" verified successfully', self.controller_id)
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(
                'Failed to verify controller_id due to unexpected response format: %s',
                e
            )
            if response:
                logger.error('Complete API response:\n%s', response.text)
            raise RuntimeError(
                f'Failed to verify fronius_controller_id "{self.controller_id}": {e}'
            )

    def send_request(self, path, method='GET', payload="", params=None, headers=None, auth=False):
        """Send a HTTP REST request to the inverter.

            auth = This request needs to be run with authentication.
            is_login = This request is a login request. Do not retry on 401.
        """
        logger.debug("Sending request to %s", path)
        if not headers:
            headers = {}
        for i in range(3):
            # Try tp send the request, if it fails, try to login and resend
            response = self.__send_one_http_request(
                path, method, payload, params, headers, auth)
            if response.status_code == 200:
                if auth:
                    self.__retrieve_auth_from_response(response)
                return response
            # 401 - unauthorized , relogin
            # 403 - is forbidden, what happens at 01.00 in the night
            if response.status_code in (401, 403):
                self.__retrieve_auth_from_response(response)
                self.login()
            else:
                raise RuntimeError(
                    f"[Inverter] Request {i} failed with {response.status_code}-"
                    f"{response.reason}. \n"
                    f"\t path:{path}, \n\tparams:{params} \n\theaders {headers} \n"
                    f"\tnonce {self.nonce} \n"
                    f"\tpayload {payload}"
                )
        return None

    def __send_one_http_request(self, path, method='GET', payload="",
                                params=None, headers=None, auth=False):
        """ Send one HTTP Request to the backend.
            This method does not handle application errors, only connection errors.
        """
        if not headers:
            headers = {}
        url = 'http://' + self.address + path
        fullpath = path
        if params:
            fullpath += '?' + \
                "&".join(
                    [f'{k+"="+str(params[k])}' for k in params.keys()])
        if auth:
            headers['Authorization'] = self.get_auth_header(
                method=method, path=fullpath)
            logger.debug("Fronius Bat Auth: Requesting %s , header: %s", fullpath, headers)

        for i in range(3):
            # 3 retries if connection can't be established
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                return response
            except requests.exceptions.ConnectionError as err:
                logger.error(
                    "Connection to Inverter failed on %s. (%d) "
                    "Retrying in 60 seconds, Error %s",
                    self.address,
                    i,
                    err
                )
                time.sleep(60)

        logger.error('Request failed without response.')
        raise RuntimeError(
            f"\turl:{url}, \n\tparams:{params} \n\theaders {headers} \n"
            f"\tnonce {self.nonce} \n"
            f"\tpayload {payload}"
        )

    def login(self):
        """Login to Fronius API"""
        logger.debug("Fronius Bat Auth: Logging in")
        path = self.api_config.commands_login_path
        self.cnonce = hashlib.md5(os.urandom(8)).hexdigest()
        self.ncvalue_num = 1
        self.login_attempts = 0
        for i in range(3):
            self.login_attempts += 1
            response = self.__send_one_http_request(path, auth=True)
            if response.status_code == 200:
                if not self.subsequent_login:
                    self.__store_latest_password_hash_method()
                self.subsequent_login = True
                logger.info('Fronius Bat Auth: Login successful %s', response)
                logger.debug("Fronius Bat Auth: Response: %s", response.headers)
                self.__retrieve_auth_from_response(response)
                self.login_attempts = 0
                return
            elif response.status_code == 401:
                self.__retrieve_auth_from_response(response)

            logger.error(
                'Fronius Bat Auth: Login -%d- failed, Response: %s', i, response)
            logger.error('Fronius Bat Auth: Response: %s ; %s', response.headers, response)
            if self.subsequent_login:
                logger.info(
                    "Fronius Bat Auth: Retrying login in 10 seconds")
                time.sleep(10)
        if self.login_attempts >= 3:
            logger.info(
                'Fronius Bat Auth: Login failed 3 times .. aborting'
            )
            raise RuntimeError(
                'Fronius Bat Auth: Login failed repeatedly .. wrong credentials?'
            )

    def logout(self):
        """Logout from Fronius API"""
        path = self.api_config.commands_logout_path
        response = self.send_request(path, auth=True)
        if not response:
            logger.warning('Fronius Bat Auth: Logout failed. No response from server')
        if response.status_code == 200:
            logger.info('Fronius Bat Auth: Logout successful')
        else:
            logger.info('Fronius Bat Auth: Logout failed')
        return response

    def __retrieve_auth_from_response(self, response):
        """Get & store the authentication parts from response auth header.
            - nc
            - cnonce
            - nonce
        """
        auth_dict = self.__split_response_auth_header(response)
        if auth_dict.get('nc'):
            self.ncvalue_num = int(auth_dict['nc']) + 1
        else:
            self.ncvalue_num = 1
        if auth_dict.get('cnonce'):
            self.cnonce = auth_dict['cnonce']
        if auth_dict.get('nonce'):
            self.nonce = auth_dict['nonce']

        logger.debug("Fronius Bat Auth: nc: %s, cnonce: %s, nonce: %s",
                     self.ncvalue_num,
                     self.cnonce,
                     self.nonce
                     )

    def __split_response_auth_header(self, response):
        """ Split the response header into a dictionary."""
        auth_dict = {}
        # stupid API bug: nonce headers with different capitalization at different end points
        if 'X-WWW-Authenticate' in response.headers:
            auth_string = response.headers['X-WWW-Authenticate']
        elif 'X-Www-Authenticate' in response.headers:
            auth_string = response.headers['X-Www-Authenticate']
        elif 'Authentication-Info' in response.headers:
            auth_string = response.headers['Authentication-Info']
        else:
            # Return an empty dict to work with Fronius below 1.35.4-1
            logger.debug('Fronius Bat Auth: No authentication header found in response')
            return auth_dict

        # Remove quotes and split by comma
        auth_list = auth_string.replace('"', '').split(',')
        logger.debug("Fronius Bat Auth: Authentication header: %s", auth_list)
        auth_dict = {}
        for item in auth_list:
            # Strip whitespace from each item and check if it contains '='
            item = item.strip()
            if '=' in item:
                key, value = item.split("=", 1)  # Split only on first '='
                key = key.strip()
                value = value.strip()
                auth_dict[key] = value
                logger.debug(
                    "Fronius Bat Auth: Authentication header key-value pair - %s: %s", key, value)
        return auth_dict

    def get_auth_header(self, method, path) -> str:
        """Create the Authorization header for the request."""
        nonce = self.nonce
        realm = 'Webinterface area'
        ncvalue = f"{self.ncvalue_num:08d}"
        cnonce = self.cnonce
        user = self.user
        password = self.password
        algorithm = self.api_config.auth_algorithm
        password_algorithm = algorithm

        password_algorithm = self.__get_password_hash_method()

        if len(self.user) < 4:
            raise RuntimeError("User needed for Authorization")
        if len(self.password) < 4:
            raise RuntimeError("Password needed for Authorization")

        a1 = f"{user}:{realm}:{password}"
        a2 = f"{method}:{path}"
        ha1 = hash_utf8(a1, password_algorithm)
        ha2 = hash_utf8(a2, algorithm)
        noncebit = f"{nonce}:{ncvalue}:{cnonce}:auth:{ha2}"
        respdig = hash_utf8(f"{ha1}:{noncebit}", algorithm)
        auth_header = f'Digest username="{user}", realm="{realm}", nonce="{nonce}", uri="{path}", '
        auth_header += f'algorithm="{algorithm}", qop=auth, nc={ncvalue}, cnonce="{cnonce}", '
        auth_header += f'response="{respdig}"'
        return auth_header

    def __get_password_hash_method(self) -> str:
        """ Figure out the password hash method during first login."""
        # If we already found a working method, use it
        if self.password_hash is not None:
            return self.password_hash

        # Index is initialized to -1. Increment to get the next method.
        password_algorithm = ""
        if self.api_config.auth_algorithm == "SHA256":
            self._last_password_hash_method_index += 1
            if self._last_password_hash_method_index >= len(self.usable_password_hash_methods):
                self._last_password_hash_method_index = 0
            password_algorithm = self.usable_password_hash_methods[
                self._last_password_hash_method_index
            ]
            logger.debug(
                "Fronius Bat Auth: Trying password hash method %s", password_algorithm)
        else:
            # Fallback to MD5 only for older firmwares
            password_algorithm = "MD5"
            # Set password_hash immediately for MD5 since there's only one option
            # Setting this here prevents __store_latest_password_hash_method from changing it later
            self.password_hash = password_algorithm

        return password_algorithm

    def __store_latest_password_hash_method(self):
        """ Save the password hash method to use after a successful login."""
        if self.password_hash is not None:
            # We already have a working method, do not change it
            return
        self.password_hash = self.usable_password_hash_methods[
            self._last_password_hash_method_index
        ]
        logger.debug("Fronius Bat Auth: Password hash method set to %s",
                     self.password_hash)

    def set_config(self, address, user, password):
        """ Update config."""
        if self.address != address:
            self.address = address
        if self.user != user:
            self.user = user
        if self.password != password:
            self.password = password
