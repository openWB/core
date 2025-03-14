import functools
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import threading
import typing_extensions
import re
import io
import os
import shutil

FORMAT_STR_DETAILED = '%(asctime)s - {%(name)s:%(lineno)s} - {%(levelname)s:%(threadName)s} - %(message)s'
FORMAT_STR_SHORT = '%(asctime)s - %(message)s'
RAMDISK_PATH = str(Path(__file__).resolve().parents[2]) + '/ramdisk/'
PERSISTENT_LOG_PATH = str(Path(__file__).resolve().parents[2]) + '/data/log/'
NUMBER_OF_LOGFILES = 3

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


class InMemoryLogHandler(logging.Handler):
    def __init__(self, base_handler=None):
        super().__init__()
        self.base_handler = base_handler
        self.log_stream = io.StringIO()
        self.has_warning_or_error = False

    def emit(self, record):
        if self.base_handler is None or self.base_handler.filter(record):
            msg = self.format(record)
            self.log_stream.write(msg + '\n')
            if record.levelno >= logging.WARNING:
                self.has_warning_or_error = True

    def get_logs(self):
        return self.log_stream.getvalue()

    def clear(self):
        self.log_stream = io.StringIO()
        self.has_warning_or_error = False


def clear_in_memory_log_handler(logger_name: str = None) -> None:
    global in_memory_log_handlers
    if logger_name is None:
        # Clear all in-memory log handlers
        for handler in in_memory_log_handlers.values():
            handler.clear()
    else:
        # Clear specified in-memory log handler
        if logger_name in in_memory_log_handlers:
            in_memory_log_handlers[logger_name].clear()


def write_logs_to_file(logger_name: str = None) -> None:
    global in_memory_log_handlers

    def rotate_logs(base_path: str, name: str):
        # Rotate the log files
        for i in range(NUMBER_OF_LOGFILES-1, 0, -1):
            src = os.path.join(base_path, f'{name}.previous{i}.log')
            dst = os.path.join(base_path, f'{name}.previous{i+1}.log')
            if os.path.exists(src):
                shutil.move(src, dst)
        # Move the current log to previous1
        current_log = os.path.join(base_path, f'{name}.current.log')
        if os.path.exists(current_log):
            shutil.move(current_log, os.path.join(base_path, f'{name}.previous1.log'))

    def combine_logs(base_path: str, name: str):
        latest_log_path = os.path.join(base_path, f'{name}.latest.log')
        with open(latest_log_path, 'w') as latest_log:
            for i in range(NUMBER_OF_LOGFILES-1, -1, -1):
                log_file = os.path.join(
                    base_path, f'{name}.previous{i}.log') if i > 0 else os.path.join(base_path, f'{name}.current.log')
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        latest_log.write(f.read())

    if logger_name is None:
        # Write logs for all in-memory log handlers
        for name, handler in in_memory_log_handlers.items():
            logs = handler.get_logs()
            if logs:
                rotate_logs(RAMDISK_PATH, name)
                with open(os.path.join(RAMDISK_PATH, f'{name}.current.log'), 'w') as f:
                    f.write(logs)
                combine_logs(RAMDISK_PATH, name)
    else:
        # Write logs for specified in-memory log handler
        if logger_name in in_memory_log_handlers:
            handler = in_memory_log_handlers[logger_name]
            logs = handler.get_logs()
            if logs:
                rotate_logs(RAMDISK_PATH, logger_name)
                with open(os.path.join(RAMDISK_PATH, f'{logger_name}.current.log'), 'w') as f:
                    f.write(logs)
                combine_logs(RAMDISK_PATH, logger_name)


def setup_logging() -> None:
    def mb_to_bytes(megabytes: int) -> int:
        return megabytes * 1000000

    global in_memory_log_handlers
    in_memory_log_handlers = {name: InMemoryLogHandler() for name in ["main", "internal_chargepoint"]}
    # to do: add smarthome and soc to in_memory_log_handlers, needs updates in individual thread calls

    # Main logger
    main_file_handler = RotatingFileHandler(RAMDISK_PATH + 'main.log', maxBytes=mb_to_bytes(5.5), backupCount=4)
    main_file_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    main_file_handler.addFilter(RedactingFilter())
    in_memory_log_handlers["main"] = InMemoryLogHandler(main_file_handler)
    in_memory_log_handlers["main"].setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    logging.basicConfig(level=logging.DEBUG, handlers=[main_file_handler, in_memory_log_handlers["main"]])
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "soc"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "Internal Chargepoint"))
    logging.getLogger().handlers[0].addFilter(functools.partial(filter_neg, "smarthome"))

    # Chargelog logger
    chargelog_log = logging.getLogger("chargelog")
    chargelog_log.propagate = False
    chargelog_file_handler = RotatingFileHandler(
        RAMDISK_PATH + 'chargelog.log', maxBytes=mb_to_bytes(2), backupCount=1)
    chargelog_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    chargelog_file_handler.addFilter(RedactingFilter())
    chargelog_log.addHandler(chargelog_file_handler)

    # Data migration logger
    data_migration_log = logging.getLogger("data_migration")
    data_migration_log.propagate = False
    data_migration_file_handler = RotatingFileHandler(
        PERSISTENT_LOG_PATH + 'data_migration.log', maxBytes=mb_to_bytes(1), backupCount=1)
    data_migration_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    data_migration_file_handler.addFilter(RedactingFilter())
    data_migration_log.addHandler(data_migration_file_handler)

    # MQTT logger
    mqtt_log = logging.getLogger("mqtt")
    mqtt_log.propagate = False
    mqtt_file_handler = RotatingFileHandler(RAMDISK_PATH + 'mqtt.log', maxBytes=mb_to_bytes(3), backupCount=1)
    mqtt_file_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    mqtt_file_handler.addFilter(RedactingFilter())
    mqtt_log.addHandler(mqtt_file_handler)

    # Smarthome logger
    smarthome_log_handler = RotatingFileHandler(RAMDISK_PATH + 'smarthome.log', maxBytes=mb_to_bytes(1), backupCount=1)
    smarthome_log_handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    smarthome_log_handler.addFilter(functools.partial(filter_pos, "smarthome"))
    smarthome_log_handler.addFilter(RedactingFilter())
    logging.getLogger().addHandler(smarthome_log_handler)

    # SoC logger
    soc_log_handler = RotatingFileHandler(RAMDISK_PATH + 'soc.log', maxBytes=mb_to_bytes(2), backupCount=1)
    soc_log_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    soc_log_handler.addFilter(functools.partial(filter_pos, "soc"))
    soc_log_handler.addFilter(RedactingFilter())
    in_memory_log_handlers["soc"] = InMemoryLogHandler(soc_log_handler)
    in_memory_log_handlers["soc"].setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    logging.getLogger().addHandler(soc_log_handler)
    logging.getLogger().addHandler(in_memory_log_handlers["soc"])

    # Internal chargepoint logger
    internal_chargepoint_log_handler = RotatingFileHandler(RAMDISK_PATH + 'internal_chargepoint.log',
                                                           maxBytes=mb_to_bytes(1),
                                                           backupCount=1)
    internal_chargepoint_log_handler.setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    internal_chargepoint_log_handler.addFilter(functools.partial(filter_pos, "Internal Chargepoint"))
    internal_chargepoint_log_handler.addFilter(RedactingFilter())
    in_memory_log_handlers["internal_chargepoint"] = InMemoryLogHandler(internal_chargepoint_log_handler)
    in_memory_log_handlers["internal_chargepoint"].setFormatter(logging.Formatter(FORMAT_STR_DETAILED))
    logging.getLogger().addHandler(internal_chargepoint_log_handler)
    logging.getLogger().addHandler(in_memory_log_handlers["internal_chargepoint"])

    # Urllib3 logger
    urllib3_log = logging.getLogger("urllib3.connectionpool")
    urllib3_log.propagate = True

    logging.getLogger("pymodbus").setLevel(logging.WARNING)
    logging.getLogger("uModbus").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    def threading_excepthook(args):
        logging.getLogger(__name__).error("Uncaught exception in threading.excepthook:", exc_info=(
            args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = threading_excepthook

    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        logging.getLogger(__name__).error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
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
