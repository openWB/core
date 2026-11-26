"""HTTP surface for simpleAPI: request parsing, auth, and the read/write/raw
response contract that third-party integrations (Home Assistant, node-red)
already rely on."""
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlsplit

from .authenticator import AuthConfig, Authenticator
from . import php_json
from .broker_access import BrokerAccess, Principal
from .parameter_handler import (
    ParameterHandler,
    ReadView,
    dispatch_read,
    dispatch_write,
    extract_read_params,
    extract_write_params,
    format_raw_output,
    php_echo,
    COMPLEX_PARAMETERS,
)

log = logging.getLogger("simpleAPI")


def _single_param_value(params: Dict[str, list]) -> Dict[str, str]:
    return {k: (v[-1] if v else '') for k, v in params.items()}


class SimpleAPIRequestHandler(BaseHTTPRequestHandler):
    server_version = "openWB-simpleAPI/1.0"

    def log_message(self, fmt, *args):
        log.debug(f"{self.address_string()} - {fmt % args}")

    def _is_https(self) -> bool:
        """The scheme comes from the Apache proxy in front (it replaces whatever the client sent). A request that
        did not arrive from the local proxy is never treated as HTTPS."""
        if self.client_address[0] not in ('127.0.0.1', '::1'):
            return False
        return self.headers.get('X-Forwarded-Proto', '').lower() == 'https'

    def _bearer_token(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return None
        prefix = 'bearer '
        if auth_header.lower().startswith(prefix):
            return auth_header[len(prefix):].strip()
        return None

    def _send(self, status: int, payload: Any, raw: bool = False):
        if raw:
            body = payload if isinstance(payload, (bytes, bytearray)) else php_echo(payload).encode('utf-8')
        else:
            body = php_json.dumps(payload).encode('utf-8')

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        # the web root's .htaccess added these to the PHP responses; the proxied backend has to do it itself
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        if self.server.api_config.get('cors_enabled', False):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, '', raw=True)

    def do_GET(self):
        params = _single_param_value(parse_qs(urlsplit(self.path).query, keep_blank_values=True))
        self._handle(params)

    do_HEAD = do_GET

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else b''
        post_params = _single_param_value(parse_qs(body.decode('utf-8'), keep_blank_values=True))
        get_params = _single_param_value(parse_qs(urlsplit(self.path).query, keep_blank_values=True))
        merged = {**get_params, **post_params}
        self._handle(merged)

    def _deny_unreadable(self, principal: Principal, view: ReadView, debug: bool) -> bool:
        """Answers 403 and returns True if the caller may not read every topic behind the response."""
        denied = set(self.server.broker_access.denied_topics(principal, view.probe_topics()))
        denied = view.blocking_topics(denied)
        if not denied:
            return False
        log.info(f"simpleAPI read denied for user '{principal.username or 'anonymous'}': {denied[:3]}")
        body = {'success': False, 'message': 'Permission denied'}
        if debug:
            body['denied_topics'] = denied
        self._send(403, body)
        return True

    def _write_as(self, principal: Principal, write_params: Dict[str, Any], params: Dict[str, str]) -> Dict[str, Any]:
        """Runs the write with the caller's own broker connection, so the broker's ACLs decide."""
        try:
            session = self.server.broker_access.open_session(principal)
        except PermissionError as exc:
            return {'success': False, 'message': str(exc)}
        try:
            with self.server.daemon_ref.http_write(session):
                return dispatch_write(self.server.parameter_handler, write_params, params)
        finally:
            session.close()

    def _handle(self, params: Dict[str, str]):
        debug = bool(self.server.config.get('debug', False)) or params.get('debug') == 'true'
        try:
            principal = self.server.authenticator.authenticate(params, self._bearer_token(), self._is_https())
            if principal is None:
                self._send(401, {'success': False, 'message': 'Authentication failed'})
                return
            enforce_acl = self.server.enforces_broker_acl(principal)

            if 'list_components' in params:
                view = ReadView(self.server.daemon_ref)
                result = ParameterHandler(view).list_components()
                if enforce_acl:
                    view.record_components()
                    if self._deny_unreadable(principal, view, debug):
                        return
                self._send(200, result)
                return

            write_params = extract_write_params(params)
            if write_params:
                if enforce_acl:
                    result = self._write_as(principal, write_params, params)
                else:
                    with self.server.daemon_ref.http_write():
                        result = dispatch_write(self.server.parameter_handler, write_params, params)
                if params.get('raw') == 'true':
                    text = 'OK' if result['success'] else f"ERROR: {result.get('message', 'Unknown error')}"
                    self._send(200, text, raw=True)
                else:
                    self._send(200, result)
                return

            read_params = extract_read_params(params)
            if read_params:
                view = ReadView(self.server.daemon_ref)
                result, debug_info = dispatch_read(ParameterHandler(view), read_params, params, debug)
                if debug:
                    credentials = ("username" in params and "password" in params)
                    debug_info.insert(0, f"Using MQTT credentials from parameters: username={params['username']}"
                                      if credentials else
                                      "No credentials provided via parameters, using config or anonymous access")
                if enforce_acl and self._deny_unreadable(principal, view, debug):
                    return
                if debug and debug_info:
                    result = {'debug_info': debug_info, **result}

                if params.get('raw') == 'true':
                    if len(read_params) > 1:
                        self._send(400, {
                            'success': False,
                            'message': 'Raw output (raw=true) is only allowed for single parameter requests',
                            'error': 'Multiple parameters detected: ' + ', '.join(read_params.keys()),
                        })
                        return
                    param_name = next(iter(read_params))
                    if param_name in COMPLEX_PARAMETERS:
                        self._send(400, {
                            'success': False,
                            'message': 'Raw output (raw=true) is not supported for complex parameters',
                            'error': f"Parameter '{param_name}' returns multiple values. "
                                     "Use specific single-value parameters instead.",
                            'suggestion': 'Try parameters like get_counter_power, get_counter_voltage_p1, etc.',
                        })
                        return
                    self._send(200, format_raw_output(result, param_name), raw=True)
                elif list(read_params) == ['get_lastlivevaluesjson']:
                    # the stored JSON string is sent as it is, even without raw=true
                    self._send(200, format_raw_output(result, 'get_lastlivevaluesjson'), raw=True)
                else:
                    if not result:
                        self._send(200, [])
                    else:
                        self._send(200, result)
                return

            self._send(400, {'success': False, 'message': 'No valid parameters provided'})
        except Exception as exc:
            log.exception("Unhandled error processing simpleAPI request")
            self._send(500, {
                'success': False,
                'message': 'Internal server error',
                'error': str(exc) if debug else 'An error occurred',
            })


class SimpleAPIServer(ThreadingHTTPServer):
    def __init__(self, server_address, daemon, parameter_handler: ParameterHandler,
                 authenticator: Authenticator, broker_access: BrokerAccess, config: Dict):
        super().__init__(server_address, SimpleAPIRequestHandler)
        self.daemon_ref = daemon
        self.parameter_handler = parameter_handler
        self.authenticator = authenticator
        self.broker_access = broker_access
        self.config = config
        self.api_config = config.get('api', {})

    def enforces_broker_acl(self, principal: Principal) -> bool:
        """Broker users are limited to what the broker lets them see and change. Without user management the
        broker grants everything anyway, so the extra round trips are skipped - but only once that is known."""
        return not principal.trusted and self.daemon_ref.user_management_active is not False


def build_http_server(daemon, config: Dict) -> SimpleAPIServer:
    http_config = config.get('http', {})
    host = http_config.get('host', '127.0.0.1')
    port = http_config.get('port', 8099)

    auth_config = AuthConfig.from_dict(config.get('auth', {}))
    broker_access = BrokerAccess.from_config(config.get('auth', {}).get('broker', {}))

    def broker_login(username: str, password: str) -> bool:
        # without user management the broker accepts everybody, so there is nothing to ask it
        if daemon.user_management_active is False:
            return True
        return broker_access.check_credentials(username, password)

    authenticator = Authenticator(auth_config, broker_login)
    parameter_handler = ParameterHandler(daemon)

    return SimpleAPIServer((host, port), daemon, parameter_handler, authenticator, broker_access, config)
