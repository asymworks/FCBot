"""FreeCAD Bot Logging Configuration.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import logging
import os
import sys

DEFAULT_FORMAT = '[%(asctime)s] %(color)s%(levelname)s in %(package)s.%(module)s: %(message)s%(color_reset)s'  # noqa: E501

# Log Colors
GREY = "\x1b[30;20m"
GREEN = "\x1b[32;20m"
YELLOW = "\x1b[33;20m"
RED = "\x1b[31;20m"
BOLD_RED = "\x1b[31;1m"
RESET = "\x1b[0m"

COLORS = {
    logging.DEBUG: GREY,
    logging.INFO: GREEN,
    logging.WARNING: YELLOW,
    logging.ERROR: RED,
    logging.CRITICAL: BOLD_RED,
}

class PackageInjectorMixin(object):
    """Inject the Python Package Dotted Path into the logger record.

    Implements caching by creating a `_package_cache` attribute on the LogFormatter
    object and indexing on file path.
    """
    def _injectPackage(self, record: logging.LogRecord) -> logging.LogRecord:

        # Initialize the Cache
        if not hasattr(self, '_package_cache'):
            self._package_cache = dict()

        if not record.pathname:
            record.package = None
            return record

        if record.pathname in self._package_cache:
            record.package = self._package_cache[record.pathname]
            return record

        self._package_cache[record.pathname] = None

        # Find the path of this file relative to some search path
        abs_pathname = os.path.abspath(record.pathname)
        rel_pathname = None
        for import_path in sys.path:
            abs_imp_path = os.path.abspath(import_path)
            if os.path.commonpath([abs_imp_path, abs_pathname]) == abs_imp_path:
                rel_pathname = os.path.relpath(abs_pathname, abs_imp_path)
                break

        # If there is no search path that leads to this file, it's not a package
        if not rel_pathname:
            record.package = None
            return record

        # Store the package as a dotted-path
        record.package = os.path.dirname(rel_pathname).replace('/', '.')
        self._package_cache[record.pathname] = record.package

        return record


class FCBotLogFormatter(logging.Formatter, PackageInjectorMixin):
    """FreeCAD Bot Logging Formatter.
    
    Render color log messages that include the full module dotted path.
    """
    def format(self, record):
        '''
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a string
        formatting operation which yields the returned string. Before
        formatting the dictionary, a couple of preparatory steps are carried
        out.  The message attribute of the record is computed using
        :meth:`python:logging.LogRecord.getMessage`.  If the formatting string
        uses the time (as determined by a call to
        :meth:`python:logging.LogRecord.usesTime`),
        :meth:`python:logging.LogRecord.formatTime` is called to format the
        event time.
        '''
        record = self._injectPackage(record)
        record.color = COLORS.get(record.levelno, GREY)
        record.color_reset = RESET

        return super(FCBotLogFormatter, self).format(record)


def init_logging(level: int|str) -> logging.Logger:
    """Initialize the Logging Subsystem."""
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(FCBotLogFormatter(DEFAULT_FORMAT))

    logger.addHandler(handler)
    logger.debug('Logging Initialized')

    return logger
