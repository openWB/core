import logging


log = logging.getLogger(__name__)


class ErrorCounterContext:
    def __init__(self, exceeded_msg: str, max_errors: int = 2, hide_exception: bool = False):
        self.max_errors = max_errors
        self.hide_exception = hide_exception
        self.__error_counter = 0
        self.__exceeded_msg = exceeded_msg

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if exception:
            self.__error_counter += 1
            log.error(exception)
            if self.hide_exception is False or self.__error_counter >= self.max_errors:
                raise exception
        return True

    def error_counter_exceeded(self) -> bool:
        if self.__error_counter > self.max_errors:
            log.error(self.__exceeded_msg)
            return True
        else:
            return False

    def reset_error_counter(self):
        self.__error_counter = 0
