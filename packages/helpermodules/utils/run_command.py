import logging
import subprocess

log = logging.getLogger(__name__)


def run_shell_command(command, process_exception: bool = False):
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, text=True)
        output, _ = result.communicate()
        return output
    except subprocess.CalledProcessError as e:
        if process_exception:
            log.debug(e.stdout)
            log.exception(e.stderr)
        else:
            raise e


def run_command(command, process_exception: bool = False):
    # if return is non-zero a CalledProcessError is raised
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if process_exception:
            if e.output is not None:
                log.exception(e.output)
            if e.stderr is not None:
                log.exception(e.stderr)
        else:
            raise e
