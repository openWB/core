"""HTTP surface for simpleAPI: request parsing, auth, and the read/write/raw
response contract that third-party integrations (Home Assistant, node-red)
already rely on."""
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlsplit

from .authenticator import AuthConfig, Authenticator
from .parameter_handler import (
    ParameterHandler,
    dispatch_read,
    dispatch_write,
    extract_read_params,
    extract_write_params,
    format_raw_output,
    COMPLEX_PARAMETERS,
)

log = logging.getLogger("simpleAPI")


def _php_stringify(value: Any) -> str:
    """Approximates PHP's echo-time string conversion for raw-mode output
    (bool True/False -> "1"/"", None -> "", arrays -> "Array")."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return '1' if value else ''
    if isinstance(value, (dict, list)):
        return 'Array'
    return str(value)


def _single_param_value(params: Dict[str, list]) -> Dict[str, str]:
    return {k: (v[-1] if v else '') for k, v in params.items()}


class SimpleAPIRequestHandler(BaseHTTPRequestHandler):
    server_version = "openWB-simpleAPI/1.0"

    def log_message(self, fmt, *args):
        log.debug(f"{self.address_string()} - {fmt % args}")

    def _is_https(self) -> bool:
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
            body = payload if isinstance(payload, (bytes, bytearray)) else _php_stringify(payload).encode('utf-8')
        else:
            body = json.dumps(payload).encode('utf-8')

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        if self.server.api_config.get('cors_enabled', False):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, '', raw=True)

    def do_GET(self):
        params = _single_param_value(parse_qs(urlsplit(self.path).query, keep_blank_values=True))
        self._handle(params)

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else b''
        post_params = _single_param_value(parse_qs(body.decode('utf-8'), keep_blank_values=True))
        get_params = _single_param_value(parse_qs(urlsplit(self.path).query, keep_blank_values=True))
        merged = {**get_params, **post_params}
        self._handle(merged)

    def _handle(self, params: Dict[str, str]):
        debug = bool(self.server.config.get('debug', False)) or params.get('debug') == 'true'
        try:
            if not self.server.authenticator.authenticate(params, self._bearer_token(), self._is_https()):
                self._send(401, {'success': False, 'message': 'Authentication failed'})
                return

            if 'list_components' in params:
                self._send(200, self.server.parameter_handler.list_components())
                return

            write_params = extract_write_params(params)
            if write_params:
                result = dispatch_write(self.server.parameter_handler, write_params, params)
                if params.get('raw') == 'true':
                    text = 'OK' if result['success'] else f"ERROR: {result.get('message', 'Unknown error')}"
                    self._send(200, text, raw=True)
                else:
                    self._send(200, result)
                return

            read_params = extract_read_params(params)
            if read_params:
                result, debug_info = dispatch_read(self.server.parameter_handler, read_params, params, debug)
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
                else:
                    if len(read_params) == 1 and next(iter(read_params)) == 'get_lastlivevaluesjson':
                        self._send(200, format_raw_output(result, 'get_lastlivevaluesjson'), raw=True)
                    elif not result:
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
                 authenticator: Authenticator, config: Dict):
        super().__init__(server_address, SimpleAPIRequestHandler)
        self.daemon_ref = daemon
        self.parameter_handler = parameter_handler
        self.authenticator = authenticator
        self.config = config
        self.api_config = config.get('api', {})


def build_http_server(daemon, config: Dict) -> SimpleAPIServer:
    http_config = config.get('http', {})
    host = http_config.get('host', '127.0.0.1')
    port = http_config.get('port', 8099)

    auth_config = AuthConfig.from_dict(config.get('auth', {}))
    mqtt_params = {
        'host': config['host'],
        'port': config['port'],
        'use_tls': config['use_tls'],
        'validate_cert': config.get('validate_cert', False),
    }
    authenticator = Authenticator(auth_config, mqtt_params)
    parameter_handler = ParameterHandler(daemon)

    return SimpleAPIServer((host, port), daemon, parameter_handler, authenticator, config)
