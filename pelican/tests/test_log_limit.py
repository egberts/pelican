import logging
import unittest
from collections import defaultdict
from contextlib import contextmanager

from pelican import log
from pelican.tests.support import LogCountHandler

__all__ = ["LogCountHandler"]


def _reset_limit_filter():
    """Empty the Pelican Limit Log filter"""
    log.LimitFilter._ignore = set()
    log.LimitFilter._raised_messages = set()
    log.LimitFilter._threshold = 5
    log.LimitFilter._group_count = defaultdict(int)


def do_logging(self):
    """Populate log content"""
    self.logger.critical("A pseudo message of 'we are crashing'")
    self.logger.info("Unit testing log")
    for i in range(5):
        self.logger.warning("Log %s", i)
        self.logger.warning("Another log %s", i)
    self.logger.debug("Unit testing Log @ debug level")


class TestLogBasic(unittest.TestCase):
    """Basic Log Test"""

    def setUp(self):
        super().setUp()
        # Add a custom counter of log output
        self.logger = logging.getLogger(__name__)
        self.handler = LogCountHandler()
        self.logger.addHandler(self.handler)
        # Check level of nested logHandlers/logFilters
        # We do not want negotiated getEffectiveLevel() here
        self.original_log_level = self.logger.level
        # This level should be 0 (logging.NOTSET); crap out if otherwise
        self.assertEqual(0, self.original_log_level, "log level is no longer NOTSET.")

    def tearDown(self):
        self.logger.setLevel(self.original_log_level)
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

            self.logger.info("Unit testing Log")

            # all log contents are in self.handler.buffer[]
            self.assertEqual(1, self.handler.count_logs())

    def test_flood_log_output(self):
        """Basic count of log messages"""
        flood_count = 825
        with self.reset_logger():
            self.logger.setLevel(1)

            for i in range(flood_count):
                self.logger.info(f"Log {i}")

            self.assertEqual(flood_count, self.handler.count_logs())

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
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()
            self.logger.setLevel(0)

    def test_below_level(self):
        """Logging below a given label level"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            self.logger.debug("Ignored debug log @ INFO level")

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
            self.logger.info("Log lone info")

            self.assertEqual(1, self.handler.count_logs())

    def test_above_level_increment(self):
        """Logging above a given level - 1"""
        self.logger.setLevel(logging.DEBUG - 1)

        with self.reset_logger():
            self.logger.debug("Log lone debug")

            self.assertEqual(1, self.handler.count_logs())

    def test_level_segregation(self):
        """Each boundary of level, +/- 1"""
        self.logger.setLevel(logging.WARNING)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(1, self.handler.count_logs(level=logging.CRITICAL))
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(0, self.handler.count_logs(level=logging.INFO))
            self.assertEqual(0, self.handler.count_logs(level=logging.ERROR))
            self.assertEqual(0, self.handler.count_logs(level=0))
            self.assertEqual(0, self.handler.count_logs(level=1))
            self.assertEqual(0, self.handler.count_logs(level=9))
            self.assertEqual(0, self.handler.count_logs(level=11))
            self.assertEqual(0, self.handler.count_logs(level=19))
            self.assertEqual(0, self.handler.count_logs(level=21))
            self.assertEqual(0, self.handler.count_logs(level=29))
            self.assertEqual(0, self.handler.count_logs(level=31))
            self.assertEqual(0, self.handler.count_logs(level=39))
            self.assertEqual(0, self.handler.count_logs(level=41))
            self.assertEqual(0, self.handler.count_logs(level=49))
            self.assertEqual(0, self.handler.count_logs(level=51))

    def test_ignores_regex(self):
        """Filter, using test regex (test-on-test)"""
        self.logger.setLevel(logging.WARNING)

        with self.reset_logger():
            do_logging(self)

            self.assertEqual(2, self.handler.count_logs(r"Log [34]"))
            self.assertEqual(1, self.handler.count_logs(r"Log [36]"))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            self.assertEqual(10, self.handler.count_logs(r".+o.+", logging.WARNING))
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(11, self.handler.count_logs())


class TestLogLimitPattern(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
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
        super().tearDown()

    @contextmanager
    def reset_logger(self):
        try:
            yield None
        finally:
            _reset_limit_filter()
            self.handler.flush()

    # TODO  Could not we add a unit test to ignore just only the pattern and not level?

    def test_exact_pattern(self):
        """Filter by exact pattern"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs("Log 3", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(9, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(10, self.handler.count_logs())

    def test_template_word(self):
        """Filter by word template"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            # This pattern ignores out everything that has a word before ' log '
            log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

            do_logging(self)

            self.assertEqual(5, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(11, self.handler.count_logs())

    def test_template_digit_one(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(r"Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(9, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(10, self.handler.count_logs())

    def test_template_digit_all(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(self)

            self.assertEqual(0, self.handler.count_logs(r"Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(11, self.handler.count_logs())

    def test_both_template_and_exact_pattern(self):
        """Filter, using all attributes"""
        self.logger.setLevel(logging.WARNING)  # presumptive default level

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(self)

            self.assertEqual(4, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                0, self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(0, self.handler.count_logs(level=logging.INFO))
            self.assertEqual(4, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(0, self.handler.count_logs(level=logging.ERROR))
            self.assertEqual(1, self.handler.count_logs(level=logging.CRITICAL))
            self.assertEqual(5, self.handler.count_logs())


class TestLogLimitPatternInfoLevel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
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

            self.assertEqual(0, self.handler.count_logs(r"Log 3", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(9, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(11, self.handler.count_logs())

    def test_template_word(self):
        """Filter by word template"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            # This pattern ignores out everything that has a word before ' log '
            log.LimitFilter._ignore.add((logging.WARNING, "\w log "))

            do_logging(self)

            self.assertEqual(5, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(12, self.handler.count_logs())

    def test_template_digit(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.INFO)

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(self)

            self.assertEqual(5, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(12, self.handler.count_logs())

    def test_both_template_and_exact_pattern(self):
        """Filter, using all attributes"""
        self.logger.setLevel(logging.INFO)  # presumptive default level

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(self)

            self.assertEqual(4, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                0, self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(0, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(1, self.handler.count_logs(level=logging.INFO))
            self.assertEqual(4, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(0, self.handler.count_logs(level=logging.ERROR))
            self.assertEqual(1, self.handler.count_logs(level=logging.CRITICAL))
            self.assertEqual(6, self.handler.count_logs())


class TestLogLimitPatternDebugLevel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.logger = logging.getLogger(__name__)
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
                5, self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(1, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(9, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(12, self.handler.count_logs())

    def test_template_word(self):
        """Filter by word template"""
        self.logger.setLevel(logging.DEBUG)

        with self.reset_logger():
            # This pattern ignores out everything that has a word before ' log '
            log.LimitFilter._ignore.add((logging.WARNING, "\w log "))

            do_logging(self)

            self.assertEqual(5, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(1, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(13, self.handler.count_logs())

    def test_template_digit(self):
        """Filter by digit template"""
        self.logger.setLevel(logging.DEBUG)

        with self.reset_logger():
            # This pattern ignores out everything that starts with `Log `
            log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(self)

            self.assertEqual(5, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                5, self.handler.count_logs(r"Another log \d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(1, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(10, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(13, self.handler.count_logs())

    def test_both_template_and_exact_pattern(self):
        """Filter, using all attributes"""
        self.logger.setLevel(logging.DEBUG)  # presumptive default level

        with self.reset_logger():
            log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(self)

            self.assertEqual(4, self.handler.count_logs("Log \\d", logging.WARNING))
            self.assertEqual(
                0, self.handler.count_logs("Another log \\d", logging.WARNING)
            )
            # total log buffer dataset check
            self.assertEqual(1, self.handler.count_logs(level=logging.DEBUG))
            self.assertEqual(1, self.handler.count_logs(level=logging.INFO))
            self.assertEqual(4, self.handler.count_logs(level=logging.WARNING))
            self.assertEqual(0, self.handler.count_logs(level=logging.ERROR))
            self.assertEqual(1, self.handler.count_logs(level=logging.CRITICAL))
            self.assertEqual(7, self.handler.count_logs())
