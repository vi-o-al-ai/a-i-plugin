"""Logging: <package dir>/ClaudeLive.log (rotating, 1 MB x 3) plus a mirror of
WARNING and above into Live's Log.txt through ControlSurface.log_message.

Every line carries the "[ClaudeLive]" prefix so it is easy to grep.
"""
import logging
import logging.handlers
import os
import tempfile

LOGGER_NAME = "ClaudeLive"
PREFIX = "[ClaudeLive]"
LOG_FILENAME = "ClaudeLive.log"
MAX_BYTES = 1000000
BACKUP_COUNT = 3

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


class ControlSurfaceHandler(logging.Handler):
    """Mirrors records into Live's Log.txt via ControlSurface.log_message."""

    def __init__(self, control_surface, level=logging.WARNING):
        logging.Handler.__init__(self, level)
        self._control_surface = control_surface

    def emit(self, record):
        try:
            text = "%s %s: %s" % (PREFIX, record.levelname, record.getMessage())
            if record.exc_info and self.formatter is not None:
                text += "\n" + self.formatter.formatException(record.exc_info)
            self._control_surface.log_message(text)
        except Exception:
            # Logging must never raise into the tick loop.
            pass


def _make_file_handler(path):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    return logging.handlers.RotatingFileHandler(
        path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")


def default_log_path():
    return os.path.join(PACKAGE_DIR, LOG_FILENAME)


def setup_logger(control_surface=None, log_file=None, level="INFO"):
    """(Re)configure and return the package logger. Safe to call repeatedly."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    logger.propagate = False
    numeric = getattr(logging, str(level).upper(), logging.INFO)
    if not isinstance(numeric, int):
        numeric = logging.INFO
    logger.setLevel(numeric)

    formatter = logging.Formatter("%(asctime)s %(levelname)-7s " + PREFIX + " %(message)s")

    file_handler = None
    candidates = [log_file or default_log_path(), os.path.join(tempfile.gettempdir(), LOG_FILENAME)]
    file_error = None
    for candidate in candidates:
        try:
            file_handler = _make_file_handler(candidate)
            break
        except Exception as exc:  # unwritable location
            file_error = exc
            file_handler = None
    if file_handler is not None:
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric)
        logger.addHandler(file_handler)
        logger.log_path = file_handler.baseFilename
    else:
        logger.log_path = None

    if control_surface is not None and hasattr(control_surface, "log_message"):
        mirror = ControlSurfaceHandler(control_surface)
        mirror.setFormatter(formatter)
        logger.addHandler(mirror)

    if file_handler is None and file_error is not None:
        logger.warning("could not open a log file: %s", file_error)
    return logger


def get_logger():
    return logging.getLogger(LOGGER_NAME)
