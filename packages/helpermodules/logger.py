import functools
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
from pathlib import Path
import queue
import sys
import threading
import typing_extensions
import re

FORMAT_STR_DETAILED = '%(asctime)s - {%(name)s:%(lineno)s} - {%(levelname)s:%(threadName)s} - %(message)s'
FORMAT_STR_SHORT = '%(asctime)s - %(message)s'
RAMDISK_PATH = str(Path(__file__).resolve().parents[2]) + '/ramdisk/'
PERSISTENT_LOG_PATH = str(Path(__file__).resolve().parents[2]) + '/data/log/'

KNOWN_SENSITIVE_FIELDS = [
    'password', 'secret', 'token', 'apikey', 'access_token',
    'refresh_token', 'accesstoken', 'refreshtoken'
]
REDACTION_PATTERNS = [
    (r'({field})[=:]([^\s&]+)', r'\1=***REDACTED***'),  # field=value, i.e. for URL query parameters
    (r'"{field}":\s*"(.*?)"', r'"{field}": "***REDACTED***"'),  # "field": "value", JSON formatted data
    (r'\'{field}\':\s*\'(.*?)\'', r"'{field}': '***REDACTED***'")  # 'field': 'value', JSON formatted data
]


def redact_sensitive_info(message: str, additional_fields: list = None) -> str:
    """
    Redacts sensitive information from the given message.

    This function replaces occurrences of known sensitive fields and their values
    in the message with a redaction placeholder (***REDACTED***). The fields to be
    redacted are defined in the KNOWN_SENSITIVE_FIELDS list. The function uses
    predefined patterns to identify and replace the sensitive information.

    Args:
        message (str): The log message to be redacted.

    Returns:
        str: The redacted log message.
    """
    fields_to_redact = KNOWN_SENSITIVE_FIELDS + (additional_fields or [])
    for field in fields_to_redact:
        for pattern, replacement in REDACTION_PATTERNS:
            pattern = pattern.replace('{field}', field)
            replacement = replacement.replace('{field}', field)
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    return message


class RedactingFilter(logging.Filter):
    """
    A logging filter that redacts sensitive information from log messages.

    This filter replaces occurrences of known sensitive fields and their values
    in the log message with a redaction placeholder (***REDACTED***). The fields to be
    redacted are defined in the KNOWN_SENSITIVE_FIELDS list. Additional fields to be
    redacted can be specified using the 'redact_fields' key in the 'extra' parameter
    when logging.

    Example:
        log.debug("sample data with redaction=" + dumps(data, indent=4), extra={'redact_fields': 'username,password'})

    Args:
        name (str): The name of the filter.
    """
    def __init__(self, name: str = ''):
        super().__init__(name)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Redacts sensitive information from the log record's message.

        This method formats the log message with its arguments, applies the redaction
        logic to replace sensitive information, and updates the log record's message.

        Args:
            record (logging.LogRecord): The log record to be filtered.
            extra (dict, optional): Additional fields to be redacted, specified using the 'redact_fields' key.

        Returns:
            bool: True to indicate that the log record should be processed.
        """

        message = record.getMessage()  # required for lazy formatting like urllib3

        additional_fields = getattr(record, 'redact_fields', '')
        fields_to_redact = KNOWN_SENSITIVE_FIELDS + [
            field.strip() for field in additional_fields.split(',') if field.strip()]
        record.msg = redact_sensitive_info(message, fields_to_redact)
        record.args = ()
        return True


def filter_neg(name: str, record) -> bool:
    if name in record.threadName:
        return False
    return True


def filter_pos(name: str, record) -> bool:
    if name in record.threadName:
        return True
    return False


def setup_logging() -> None:
    def mb_to_bytes(megabytes: int) -> int:
        return megabytes * 1000000

    # Main logger
    log_queue = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    main_file_handler = RotatingFileHandler(RAMDISK_PATH + 'main.log', maxBytes=mb_to_bytes(5.5), backupCount=4)
    main_file_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    main_file_handler.addFilter(RedactingFilter())
    logging.basicConfig(level=logging.DEBUG, handlers=[queue_handler])
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "soc"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "Internal Chargepoint"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "smarthome"))
    main_listener = logging.handlers.QueueListener(log_queue, main_file_handler)
    main_listener.start()

    # Chargelog logger
    chargelog_queue = queue.Queue()
    chargelog_queue_handler = logging.handlers.QueueHandler(chargelog_queue)
    chargelog_log = logging.getLogger("chargelog")
    chargelog_log.propagate = False
    chargelog_file_handler = RotatingFileHandler(
        RAMDISK_PATH + 'chargelog.log', maxBytes=mb_to_bytes(2), backupCount=1)
    chargelog_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    chargelog_file_handler.addFilter(RedactingFilter())
    chargelog_log.addHandler(chargelog_queue_handler)
    chargelog_listener = logging.handlers.QueueListener(chargelog_queue, chargelog_file_handler)
    chargelog_listener.start()

    # Data migration logger
    data_migration_queue = queue.Queue()
    data_migration_queue_handler = logging.handlers.QueueHandler(data_migration_queue)
    data_migration_log = logging.getLogger("data_migration")
    data_migration_log.propagate = False
    data_migration_file_handler = RotatingFileHandler(
        PERSISTENT_LOG_PATH + 'data_migration.log', maxBytes=mb_to_bytes(1), backupCount=1)
    data_migration_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    data_migration_file_handler.addFilter(RedactingFilter())
    data_migration_log.addHandler(data_migration_queue_handler)
    data_migration_listener = logging.handlers.QueueListener(data_migration_queue, data_migration_file_handler)
    data_migration_listener.start()

    # MQTT logger
    mqtt_queue = queue.Queue()
    mqtt_queue_handler = logging.handlers.QueueHandler(mqtt_queue)
    mqtt_log = logging.getLogger("mqtt")
    mqtt_log.propagate = False
    mqtt_file_handler = RotatingFileHandler(RAMDISK_PATH + 'mqtt.log', maxBytes=mb_to_bytes(3), backupCount=1)
    mqtt_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    mqtt_file_handler.addFilter(RedactingFilter())
    mqtt_log.addHandler(mqtt_queue_handler)
    mqtt_listener = logging.handlers.QueueListener(mqtt_queue, mqtt_file_handler)
    mqtt_listener.start()

    # Steuve control command logger
    steuve_control_command_queue = queue.Queue()
    steuve_control_command_queue_handler = logging.handlers.QueueHandler(steuve_control_command_queue)
    steuve_control_command_log = logging.getLogger("steuve_control_command")
    steuve_control_command_log.propagate = False
    steuve_control_command_file_handler = RotatingFileHandler(
        PERSISTENT_LOG_PATH + 'steuve_control_command.log', maxBytes=mb_to_bytes(80), backupCount=1)
    steuve_control_command_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    steuve_control_command_log.addHandler(steuve_control_command_queue_handler)
    steuve_control_command_listener = logging.handlers.QueueListener(steuve_control_command_queue, steuve_control_command_file_handler)
    steuve_control_command_listener.start()

    # Smarthome logger
    smarthome_queue = queue.Queue()
    smarthome_queue_handler = logging.handlers.QueueHandler(smarthome_queue)
    smarthome_log_handler = RotatingFileHandler(RAMDISK_PATH + 'smarthome.log', maxBytes=mb_to_bytes(1), backupCount=1)
    smarthome_log_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    smarthome_log_handler.addFilter(functools.partial(filter_pos, "smarthome"))
    smarthome_log_handler.addFilter(RedactingFilter())
    logging.getLogger().addHandler(smarthome_queue_handler)
    smarthome_listener = logging.handlers.QueueListener(smarthome_queue, smarthome_log_handler)
    smarthome_listener.start()

    # SoC logger
    soc_queue = queue.Queue()
    soc_queue_handler = logging.handlers.QueueHandler(soc_queue)
    soc_log_handler = RotatingFileHandler(RAMDISK_PATH + 'soc.log', maxBytes=mb_to_bytes(2), backupCount=1)
    soc_log_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    soc_log_handler.addFilter(functools.partial(filter_pos, "soc"))
    soc_log_handler.addFilter(RedactingFilter())
    logging.getLogger().addHandler(soc_queue_handler)
    soc_listener = logging.handlers.QueueListener(soc_queue, soc_log_handler)
    soc_listener.start()

    # Internal chargepoint logger
    internal_chargepoint_queue = queue.Queue()
    internal_chargepoint_queue_handler = logging.handlers.QueueHandler(internal_chargepoint_queue)
    internal_chargepoint_log_handler = RotatingFileHandler(RAMDISK_PATH + 'internal_chargepoint.log',
                                                           maxBytes=mb_to_bytes(1),
                                                           backupCount=1)
    internal_chargepoint_log_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    internal_chargepoint_log_handler.addFilter(functools.partial(filter_pos, "Internal Chargepoint"))
    internal_chargepoint_log_handler.addFilter(RedactingFilter())
    logging.getLogger().addHandler(internal_chargepoint_queue_handler)
    internal_chargepoint_listener = logging.handlers.QueueListener(internal_chargepoint_queue, internal_chargepoint_log_handler)
    internal_chargepoint_listener.start()

    # urllib3 logger
    urllib3_queue = queue.Queue()
    urllib3_queue_handler = logging.handlers.QueueHandler(urllib3_queue)
    urllib3_log = logging.getLogger("urllib3.connectionpool")
    urllib3_log.propagate = True
    urllib3_file_handler = RotatingFileHandler(RAMDISK_PATH + 'soc.log', maxBytes=mb_to_bytes(2), backupCount=1)
    urllib3_file_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    urllib3_file_handler.addFilter(RedactingFilter())
    urllib3_file_handler.addFilter(functools.partial(filter_pos, "soc"))
    urllib3_log.addHandler(urllib3_queue_handler)
    urllib3_listener = logging.handlers.QueueListener(urllib3_queue, urllib3_file_handler)
    urllib3_listener.start()

    logging.getLogger("pymodbus").setLevel(logging.WARNING)
    logging.getLogger("uModbus").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    def threading_excepthook(args):
        with open(RAMDISK_PATH+"thread_errors.log", "a") as f:
            f.write("Uncaught exception in thread:\n")
            f.write(f"Type: {args.exc_type}\n")
            f.write(f"Value: {args.exc_value}\n")
            import traceback
            traceback.print_tb(args.exc_traceback, file=f)
    threading.excepthook = threading_excepthook

    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        with open(RAMDISK_PATH+"thread_errors.log", "a") as f:
            f.write("Uncaught exception:\n")
            f.write(f"Type: {exc_type}\n")
            f.write(f"Value: {exc_value}\n")
            f.write(f"Traceback:{exc_traceback}\n")
    sys.excepthook = handle_unhandled_exception


log = logging.getLogger(__name__)


class ModifyLoglevelContext:
    def __init__(self, logger: logging.Logger, new_loglevel: int):
        self.logger = logger
        self.new_loglevel = new_loglevel

    def __enter__(self):
        self.previous_loglevel = self.logger.level
        self.logger.setLevel(self.new_loglevel)

    def __exit__(self, exception_type, exception, exception_traceback) -> typing_extensions.Literal[False]:
        self.logger.setLevel(self.previous_loglevel)
        # no exception handling
        return False
