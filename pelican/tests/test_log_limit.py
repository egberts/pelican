import logging
import pytest
import unittest
from collections import defaultdict
from contextlib import contextmanager

from pelican import log, logger
from pelican.tests.support import LogCountHandler

__all__ = ["LogCountHandler"]

import sys

print(sys.executable)
print("\n".join(sys.path))


def dump_log(this_logger: logging.Logger):
    print("\nlogger: ", str(this_logger))


def _reset_limit_filter():
    """Empty the Pelican Limit Log filter"""
    log.LimitFilter._ignore = set()
    log.LimitFilter._raised_messages = set()
    log.LimitFilter._threshold = 5
    log.LimitFilter._group_count = defaultdict(int)


EXPECTED_DEBUG_ITER = 1
EXPECTED_DEBUGS = (1 * EXPECTED_DEBUG_ITER)
EXPECTED_INFO_ITER = 1
EXPECTED_INFOS = (1 * EXPECTED_INFO_ITER)
EXPECTED_WARNING_ITER = 6
EXPECTED_WARNINGS_MSG1 = (1 * EXPECTED_WARNING_ITER)
EXPECTED_WARNINGS_MSG2 = (1 * EXPECTED_WARNING_ITER)
PASSING_LIMIT_THRESHOLD = log.LimitFilter._threshold - 1  # NOQA
EXPECTED_WARNINGS_MSG2_LIMIT = min(
    (1 * EXPECTED_WARNING_ITER),
    PASSING_LIMIT_THRESHOLD)
EXPECTED_WARNINGS = EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2
EXPECTED_WARNINGS_LIMIT = EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2_LIMIT
WARNING_LIMIT_EMITTED = 1
EXPECTED_ERROR_ITER = 6
EXPECTED_ERRORS = (1 * EXPECTED_ERROR_ITER)
EXPECTED_ERRORS_CAPPED = 1
EXPECTED_CRITICAL_ITER = 1
EXPECTED_CRITICALS = (1 * EXPECTED_CRITICAL_ITER)
EXPECTED_TOTAL_LOG = (
    EXPECTED_DEBUGS +
    EXPECTED_INFOS +
    EXPECTED_WARNINGS_LIMIT +
    WARNING_LIMIT_EMITTED +
    EXPECTED_ERRORS_CAPPED +
    EXPECTED_CRITICALS
)


def do_logging(self):
    """Populate log content"""
    for i in range(EXPECTED_CRITICAL_ITER):
        self.logger.critical("A pseudo message of 'we are crashing'")

    for i in range(EXPECTED_INFO_ITER):
        self.logger.info("Unit testing log")
    for i in range(EXPECTED_WARNING_ITER):
        self.logger.warning("Log %s", i)
        self.logger.warning(
            f"Another log {i!s}",
            extra={'limit_msg': 'A generic message for too many warnings'}
        )
    for i in range(EXPECTED_ERROR_ITER):
        self.logger.error("Flooding error repeating")
    for i in range(EXPECTED_DEBUG_ITER):
        self.logger.debug("Unit testing Log @ debug level")


def print_logger(title: str, this_logger: logging.Logger) -> logging.Logger:
    print(f"\n\nLogger fields for '{title}':")
    print(f"{title}: Logger: ", this_logger)
    if hasattr(this_logger, "name"):
        print(f"{title}: Name: {this_logger.name}")
    else:
        print("Name: None")
    if hasattr(this_logger, "level"):
        level_name = logging.getLevelName(this_logger.level)
        print(f"{title}: Level: {level_name} ({this_logger.level})")
    else:
        print("Level: None")
    print(f"{title}: Logger.manager: ", this_logger.manager)
    print(f"{title}: Logger.manager.loggerClass: ", this_logger.manager.loggerClass)
    print(f"{title}: Logger.manager.root: ", this_logger.manager.root)
    print(f"{title}: Logger.manager.loggerDict: ", this_logger.manager.loggerDict)
    print(f"{title}: Logger.root:", this_logger.root)
    if hasattr(this_logger, "parent"):
        print(f"{title}: Logger.parent:", this_logger.parent)
    else:
        print(f"{title}: Logger.parent: None")
    if hasattr(this_logger, "propagate"):
        print(f"{title}: Logger.propagate: ", this_logger.propagate)
    else:
        print(f"{title}: Logger.propagate: None")
    if hasattr(this_logger, "filters"):
        print(f"{title}: Logger.filters: ", this_logger.filters)
    else:
        print(f"{title}: Logger.filters: None")
    if hasattr(this_logger, "handlers"):
        print(f"{title}: Logger.handlers: ", this_logger.handlers)
        print(f"{title}: Handler.level: ", this_logger.level)
        print(f"{title}: Handler.filters: ", this_logger.filters)
        if hasattr(this_logger.handlers, "formatter"):
            print(f"{title}: Handler.formatter: ", this_logger.formatter)  # NOQA
        else:
            print(f"{title}: handlers.formatter: None")
    else:
        print(f"{title}: Logger.handlers: None")
    return this_logger.manager.root


class TestLogBasic(unittest.TestCase):
    """Basic Log Test"""

    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        print("logging.getLoggerClass(): ", logging.getLoggerClass())
        print("logging.getLogRecordFactory(): ", logging.getLogRecordFactory())
        self.assertEqual(logging.WARNING, self.logger.getEffectiveLevel())
        self.assertEqual(logging.NOTSET, self.logger.level)
        # Add a custom counter of log output
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.NOTSET)
        self.assertEqual(logging.NOTSET, self.handler.level)
        self.assertEqual(
            logging.WARNING,
            self.logger.getEffectiveLevel(),
            "log level is no longer effective level.",
        )

        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        dump_log(self.logger)

    def tearDown(self):
        self.logger.setLevel(self.original_log_level)
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()

    def test_one_log_output(self):
        """One count of log messages"""
        with self.reset_logger():
            self.logger.setLevel(1)
            info_log_count = 1

            for i in range(info_log_count):
                self.logger.info("Unit testing Log")

            # all log contents are in self.handler.buffer[]
            self.assertEqual(info_log_count, self.handler.count_logs())

    def test_flood_log_output(self):
        """Basic count of log messages"""
        flood_count = 825
        with self.reset_logger():
            target_level = 1
            self.logger.setLevel(target_level)

            for i in range(flood_count):
                self.logger.info(f"Log {i}")

            self.assertEqual(flood_count, self.handler.count_logs())
            self.assertEqual(target_level, self.logger.level)
            self.assertEqual(logging.NOTSET, self.handler.level)
            self.assertEqual(target_level, self.logger.getEffectiveLevel())

    def test_flood_mixed_log_output(self):
        """Basic count of log messages"""
        flood_count = 100
        with self.reset_logger():
            self.logger.setLevel(1)

            for i in range(flood_count):
                self.logger.debug(f"Log {i}")
                self.logger.info(f"Log {i}")
                self.logger.warning(f"Log {i}")
                self.logger.error(f"Log {i}")
                self.logger.critical(f"Log {i}")

            self.assertEqual(flood_count * 5, self.handler.count_logs())


class TestLogLevel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
        dump_log(self.logger)
        dump_log(self.logger)
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        dump_log(self.handler)
        # Check level of nested logHandlers/logFilters
        # We do not want negotiated getEffectiveLevel() here
        self.assertEqual(self.logger.level, logging.NOTSET)
        self.assertEqual(self.handler.level, logging.NOTSET)

        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        self.assertEqual(0, self.original_log_level, "log level is no longer NOTSET.")

    def tearDown(self):
        _reset_limit_filter()
        self.logger.setLevel(self.original_log_level)
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()
            self.logger.setLevel(logging.NOTSET)

    def test_below_level(self):
        """Logging below a given label level"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            self.logger.debug("Ignored this debug log @ INFO level")

            self.assertEqual(0, self.handler.count_logs())

    def test_below_level_increment(self):
        """Logging under a given level + 1"""
        self.logger.setLevel(logging.DEBUG + 1)

        with self.reset_logger():
            self.logger.debug("Ignored this debug log @ slightly above DEBUG+1")

            self.assertEqual(0, self.handler.count_logs())

    def test_above_level(self):
        """Logging above given level"""
        self.logger.setLevel(10)
        with self.reset_logger():
            self.logger.info("this info log appears @ DEBUG level")

            self.assertEqual(1, self.handler.count_logs())

    def test_above_level_increment(self):
        """Logging above a given level - 1"""
        self.logger.setLevel(logging.DEBUG - 1)

        with self.reset_logger():
            self.logger.debug("this DEBUG log appears slight over DEBUG-1 level")

            self.assertEqual(1, self.handler.count_logs())

    def test_level_segregation_at_debug(self):
        """Each boundary of level, +/- 1"""
        self.logger.setLevel(logging.DEBUG)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(level=0))
            self.assertEqual(0, self.handler.count_logs(level=1))
            self.assertEqual(0, self.handler.count_logs(level=9))
            self.assertEqual(
                EXPECTED_DEBUGS,
                self.handler.count_logs(level=logging.DEBUG)
            )
            self.assertEqual(0, self.handler.count_logs(level=11))
            self.assertEqual(0, self.handler.count_logs(level=19))
            self.assertEqual(
                EXPECTED_INFOS,
                self.handler.count_logs(level=logging.INFO)
            )
            self.assertEqual(0, self.handler.count_logs(level=21))
            self.assertEqual(0, self.handler.count_logs(level=29))
            self.assertEqual(
                EXPECTED_WARNINGS_LIMIT + WARNING_LIMIT_EMITTED,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(0, self.handler.count_logs(level=31))
            self.assertEqual(0, self.handler.count_logs(level=39))
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            self.assertEqual(0, self.handler.count_logs(level=41))
            self.assertEqual(0, self.handler.count_logs(level=49))
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )
            self.assertEqual(0, self.handler.count_logs(level=51))

    def test_level_segregation_at_info(self):
        """Each boundary of level, +/- 1"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(level=0))
            self.assertEqual(0, self.handler.count_logs(level=1))
            self.assertEqual(0, self.handler.count_logs(level=9))
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(0, self.handler.count_logs(level=11))
            self.assertEqual(0, self.handler.count_logs(level=19))
            self.assertEqual(
                EXPECTED_INFOS,
                self.handler.count_logs(level=logging.INFO)
            )
            self.assertEqual(0, self.handler.count_logs(level=21))
            self.assertEqual(0, self.handler.count_logs(level=29))
            self.assertEqual(
                EXPECTED_WARNINGS_LIMIT + WARNING_LIMIT_EMITTED,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(0, self.handler.count_logs(level=31))
            self.assertEqual(0, self.handler.count_logs(level=39))
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            self.assertEqual(0, self.handler.count_logs(level=41))
            self.assertEqual(0, self.handler.count_logs(level=49))
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )
            self.assertEqual(0, self.handler.count_logs(level=51))

    def test_level_segregation_at_warning(self):
        """Each boundary of level, +/- 1"""
        self.logger.setLevel(logging.WARNING)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(level=0))
            self.assertEqual(0, self.handler.count_logs(level=1))
            self.assertEqual(0, self.handler.count_logs(level=9))
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(0, self.handler.count_logs(level=11))
            self.assertEqual(0, self.handler.count_logs(level=19))
            self.assertEqual(0, self.handler.count_logs(level=logging.INFO))
            self.assertEqual(0, self.handler.count_logs(level=21))
            self.assertEqual(0, self.handler.count_logs(level=29))
            self.assertEqual(
                EXPECTED_WARNINGS_LIMIT + WARNING_LIMIT_EMITTED,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(0, self.handler.count_logs(level=31))
            self.assertEqual(0, self.handler.count_logs(level=39))
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
                )
            self.assertEqual(0, self.handler.count_logs(level=41))
            self.assertEqual(0, self.handler.count_logs(level=49))
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )
            self.assertEqual(0, self.handler.count_logs(level=51))

    def test_level_segregation_at_error(self):
        """Each boundary of level, +/- 1"""
        self.logger.setLevel(logging.ERROR)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(level=0))
            self.assertEqual(0, self.handler.count_logs(level=1))
            self.assertEqual(0, self.handler.count_logs(level=9))
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(0, self.handler.count_logs(level=11))
            self.assertEqual(0, self.handler.count_logs(level=19))
            self.assertEqual(0, self.handler.count_logs(level=logging.INFO))
            self.assertEqual(0, self.handler.count_logs(level=21))
            self.assertEqual(0, self.handler.count_logs(level=29))
            self.assertEqual(0, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(0, self.handler.count_logs(level=31))
            self.assertEqual(0, self.handler.count_logs(level=39))
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            self.assertEqual(0, self.handler.count_logs(level=41))
            self.assertEqual(0, self.handler.count_logs(level=49))
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )
            self.assertEqual(0, self.handler.count_logs(level=51))

    def test_ignores_regex(self):
        """Filter, using test regex (test-on-test)"""
        self.logger.setLevel(logging.WARNING)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(2, self.handler.count_logs(r"Log [34]"))
            self.assertEqual(1, self.handler.count_logs(r"Log [36]"))
            self.assertEqual(
                4, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            self.assertEqual(11, self.handler.count_logs(r".+o.+", logging.WARNING))
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(11, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(6, self.handler.count_logs(level=logging.ERROR))
            self.assertEqual(18, self.handler.count_logs())


class TestLogLimitPattern(unittest.TestCase):
    def setUp(self):

        super().setUp()
        self.logger = logging.getLogger(__name__)
        dump_log(self.logger)
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        # Check level of nested logHandlers/logFilters
        # We do not want negotiated getEffectiveLevel() here
        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        self.assertEqual(0, self.original_log_level, "log level is no longer NOTSET.")
        self.logger.setLevel(logging.WARNING)  # that do not work
        self.assertEqual(
            logging.WARNING, self.logger.level, "log level is no longer WARNING."
        )
        dump_log(self.logger)

    def tearDown(self):
        _reset_limit_filter()
        self.logger.setLevel(self.original_log_level)
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()

    # TODO  Could not we add a unit test to ignore just only the pattern and not level?

    def test_dataset_check_entire(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)
        expected_total = (
            EXPECTED_CRITICALS +
            (EXPECTED_WARNINGS_MSG1 - 1) +
            EXPECTED_WARNINGS_MSG2_LIMIT +
            WARNING_LIMIT_EMITTED +
            EXPECTED_ERRORS
        )

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(expected_total, self.handler.count_logs())

    def test_dataset_all_another(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_LIMIT,
                self.handler.count_logs(level=logging.WARNING)
            )

    def test_dataset_filter_all_log(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))

    def test_dataset_all_log_warning(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )

    def test_dataset_all_log_filtered(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs("Log 3", logging.WARNING))

    def test_exact_pattern(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs("Log 3", logging.WARNING))
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(
                EXPECTED_WARNINGS_LIMIT,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            total_expected = (
                EXPECTED_CRITICALS +
                (EXPECTED_WARNINGS_MSG1 - 1) +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            self.assertEqual(total_expected, self.handler.count_logs())

    def test_exact_pattern_another_log_5(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level
        dump_log(self.logger)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )

    def test_template_word(self):
        """Filter by word template"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            # This pattern ignores out everything that has a word before ' log '
            log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 - 1 +
                EXPECTED_WARNINGS_MSG2
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_LIMIT +
                WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_template_digit_one(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(r"Log \\d", logging.WARNING))
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            expected_warnings = EXPECTED_WARNINGS_LIMIT - 1 + WARNING_LIMIT_EMITTED
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                (EXPECTED_WARNINGS_MSG1 - 1) +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_regex_template_digit_all(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with (self.reset_logger()):
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(self)

            self.assertEqual(
                (EXPECTED_WARNINGS_MSG1 - EXPECTED_WARNINGS_MSG1),
                self.handler.count_logs(r"Log \\d", logging.WARNING))
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            total_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                total_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_LIMIT +
                EXPECTED_ERRORS +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_filter_warnings_detect_debug_only(self):
        """Filter, using all attributes"""

        with self.reset_logger():
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING

            do_logging(self)

            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            self.assertEqual(
                EXPECTED_WARNINGS_MSG1 - 1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))

    def test_filter_warnings_detect_info_only(self):
        """Filter, using all attributes"""

        with self.reset_logger():
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING

            do_logging(self)

            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            self.assertEqual(
                (EXPECTED_WARNINGS_MSG1 - 1),
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.INFO))

    def test_filter_warnings_detect_warning_only(self):
        """Filter, using all attributes"""

        with self.reset_logger():
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING

            do_logging(self)

            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            self.assertEqual(
                (EXPECTED_WARNINGS_MSG1 - 1),
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            expected_total = (
                (EXPECTED_WARNINGS_MSG1 - 1) +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_total,
                self.handler.count_logs(level=logging.WARNING)
            )

    def test_filter_warnings_detect_error_only(self):
        """Filter, using all attributes"""

        with self.reset_logger():
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING

            do_logging(self)

            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            self.assertEqual(
                EXPECTED_WARNINGS_MSG1 - 1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
                )

    def test_filter_warnings_detect_critical_only(self):
        """Filter, using all attributes"""

        with self.reset_logger():
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING

            do_logging(self)

            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            self.assertEqual(
                (EXPECTED_WARNINGS_MSG1 - 1),
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )

    def test_filter_warnings_detect_dataset_all(self):
        """Filter, using all attributes"""

        with self.reset_logger():
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))
            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING

            do_logging(self)

            self.logger.setLevel(logging.WARNING)  # presumptive default level
            self.logger.level = logging.WARNING
            self.assertEqual(
                (EXPECTED_WARNINGS_MSG1 - 1),
                self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_LIMIT +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())


class TestLogLimitPatternInfoLevel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
        dump_log(self.logger)
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        # Check level of nested logHandlers/logFilters
        # We do not want negotiated getEffectiveLevel() here
        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        self.assertEqual(0, self.original_log_level, "log level is no longer NOTSET.")

    def tearDown(self):
        _reset_limit_filter()
        self.logger.setLevel(self.original_log_level)
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()

    def test_exact_pattern(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(
                0,
                self.handler.count_logs(r"Log 3", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(
                EXPECTED_WARNINGS_LIMIT,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_WARNINGS_MSG1 - 1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            self.assertEqual(
                expected_total,
                self.handler.count_logs()
            )

    def test_template_word(self):
        """Filter by word template"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            # This pattern ignores out everything that has a word before ' log '
            log.LimitFilter._ignore.add((logging.WARNING, r"\w log "))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
                )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_DEBUGS +
                (
                    EXPECTED_WARNINGS_MSG1 +
                    EXPECTED_WARNINGS_MSG2_LIMIT
                ) +
                EXPECTED_ERRORS
            )
            self.assertEqual(
                expected_total,
                self.handler.count_logs()
            )

    def test_template_digit(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR))
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_both_template_and_exact_pattern(self):
        """Filter, using all attributes"""
        self.logger.setLevel(logging.INFO)  # presumptive default level

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1 - 1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(
                EXPECTED_INFOS,
                self.handler.count_logs(level=logging.INFO)
            )
            expected_warnings = (
                (EXPECTED_WARNINGS_MSG1 - 1) +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                (
                    (EXPECTED_WARNINGS_MSG1 - 1) +
                    EXPECTED_WARNINGS_MSG2_LIMIT
                ) +
                WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            self.assertEqual(self.handler.count_logs(), expected_total)


class TestLogLimitPatternDebugLevel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
        dump_log(self.logger)
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        # Check level of nested logHandlers/logFilters
        # We do not want negotiated getEffectiveLevel() here
        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        self.assertEqual(0, self.original_log_level, "log level is no longer NOTSET.")

    def tearDown(self):
        _reset_limit_filter()
        self.logger.setLevel(self.original_log_level)
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()

    def test_exact_pattern(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.DEBUG)

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(r"Log 3", logging.WARNING))
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(
                EXPECTED_DEBUGS,
                self.handler.count_logs(level=logging.DEBUG)
            )
            expected_warnings = (
                (EXPECTED_WARNINGS_MSG1 - 1) +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_DEBUGS +
                (
                    (EXPECTED_WARNINGS_MSG1 - 1) +
                    EXPECTED_WARNINGS_MSG2_LIMIT +
                    WARNING_LIMIT_EMITTED
                ) +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_template_word(self):
        """Filter by word template"""
        self.logger.setLevel(logging.DEBUG)

        with self.reset_logger():
            # This pattern ignores out everything that has a word before ' log '
            log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(
                EXPECTED_DEBUGS,
                self.handler.count_logs(level=logging.DEBUG)
            )
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_DEBUGS +
                (
                    EXPECTED_WARNINGS_MSG1 +
                    EXPECTED_WARNINGS_MSG2_LIMIT +
                    WARNING_LIMIT_EMITTED
                ) +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_template_digit(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.DEBUG)

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(
                EXPECTED_DEBUGS,
                self.handler.count_logs(level=logging.DEBUG)
            )
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT +
                WARNING_LIMIT_EMITTED
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_DEBUGS +
                (
                    EXPECTED_WARNINGS_MSG1 +
                    EXPECTED_WARNINGS_MSG2_LIMIT +
                    WARNING_LIMIT_EMITTED
                ) +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())

    def test_both_template_and_exact_pattern(self):
        """Filter, using all attributes"""
        self.logger.setLevel(logging.DEBUG)  # presumptive default level

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(self)

            self.assertEqual(
                EXPECTED_WARNINGS_MSG1 - 1,
                self.handler.count_logs("Log \\d", logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_WARNINGS_MSG2_LIMIT,
                self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(
                EXPECTED_DEBUGS,
                self.handler.count_logs(level=logging.DEBUG)
            )
            self.assertEqual(
                EXPECTED_INFOS,
                self.handler.count_logs(level=logging.INFO)
            )
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2_LIMIT
            )
            self.assertEqual(
                expected_warnings,
                self.handler.count_logs(level=logging.WARNING)
            )
            self.assertEqual(
                EXPECTED_ERRORS,
                self.handler.count_logs(level=logging.ERROR)
            )
            self.assertEqual(
                EXPECTED_CRITICALS,
                self.handler.count_logs(level=logging.CRITICAL)
            )
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_INFOS +
                EXPECTED_DEBUGS +
                (
                    EXPECTED_WARNINGS_MSG1 +
                    EXPECTED_WARNINGS_MSG2_LIMIT
                ) +
                EXPECTED_ERRORS
            )
            self.assertEqual(expected_total, self.handler.count_logs())


class TestLogLimitThreshold(unittest.TestCase):

    def setUp(self):
        super().setUp()
        print_logger("pre-setUp: ", logging.Logger)  # NOQA
        self.logger = logging.getLogger(__name__)
        print_logger("pre-basicConfig: ", self.logger)
        logging.basicConfig(level=logging.DEBUG)
        print_logger("post-basicConfig: ", self.logger)
        print("logging.getLoggerClass(): ", logging.getLoggerClass())
        print("logging.getLogRecordFactory(): ", logging.getLogRecordFactory())
        self.assertEqual(logging.WARNING, self.logger.getEffectiveLevel())
        self.assertEqual(logging.NOTSET, self.logger.level)
        # Add a custom counter of log output
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.NOTSET)
        self.assertEqual(logging.NOTSET, self.handler.level)
        self.assertEqual(
            logging.WARNING,
            self.logger.getEffectiveLevel(),
            "log level is no longer effective level.",
        )

        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        print_logger("post-basicConfig: ", self.logger)
        dump_log(self.logger)

    def tearDown(self):
        self.logger.setLevel(self.original_log_level)
        self.logger.removeHandler(self.handler)
        del self.handler
        del self.logger
        super().tearDown()

    def test_hit_repeating_errors(self):
        logger_name = __name__
        log.init(
            level=logging.INFO,
            name=logger_name,
            logs_dedup_min_level=logging.CRITICAL
        )
        test_logger = self.logger

        with self.assertLogs(logger=test_logger, level=logging.WARNING) as test_log:
            do_logging(self)

        actual_flood_count = 0
        for rec in test_log.records:
            if rec.levelno == logging.ERROR:
                if rec.name == logger_name:
                    if rec.message == "Flooding error repeating":
                        actual_flood_count = actual_flood_count + 1
        self.assertEqual(1, actual_flood_count)

    def test_miss_limit_threshold(self):
        logger_name = __name__
        log.init(
            level=logging.WARNING,
            name=logger_name,
            logs_dedup_min_level=logging.ERROR
        )
        test_logger = self.logger
        original_threshold = log.LimitFilter._threshold
        log.LimitFilter._threshold = 7

        with self.assertLogs(logger=test_logger, level=logging.WARNING) as test_log:
            do_logging(self)

        found = False
        for rec in test_log.records[:]:
            if "generic message" in rec.message:
                found = True
        self.assertFalse(found, "generic message not in log; threshold failed")

        log.LimitFilter._threshold = original_threshold

    def test_hit_limit_threshold(self):
        logger_name = __name__
        log.init(
            level=logging.WARNING,
            name=logger_name,
            logs_dedup_min_level=logging.ERROR
        )
        test_logger = self.logger
        original_threshold = log.LimitFilter._threshold
        log.LimitFilter._threshold = 6

        with self.assertLogs(logger=test_logger, level=logging.WARNING) as test_log:
            do_logging(self)

        found = False
        for rec in test_log.records[:]:
            if "generic message" in rec.message:
                found = True
        self.assertTrue(found, "generic message not in log; threshold failed")

        log.LimitFilter._threshold = original_threshold

    def test_over_the_limit_threshold(self):
        logger_name = __name__
        log.init(
            level=logging.WARNING,
            name=logger_name,
            logs_dedup_min_level=logging.ERROR
        )
        test_logger = self.logger
        print_logger("before: ", test_logger)
        original_threshold = log.LimitFilter._threshold
        log.LimitFilter._threshold = 5

        with self.assertLogs(logger=test_logger, level=logging.WARNING) as test_log:
            do_logging(self)

        found = False
        for rec in test_log.records[:]:
            print('rec.message: "', rec.message, '"')
            if "generic message" in rec.message:
                found = True
        self.assertTrue(found, "generic message not in log; threshold failed")

        log.LimitFilter._threshold = original_threshold
