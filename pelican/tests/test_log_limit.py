import logging
import pytest
import re
from collections import defaultdict
from contextlib import contextmanager
import pelican
from pelican import logger  # only way to get current Pelican Logger
# from pelican.tests.support import LogCountHandler
import rich
import rich.logging

# __all__ = ["LogCountHandler"]

import sys

print(sys.executable)
print("\n".join(sys.path))


def dump_log(this_logger: logging.Logger):
    print("\nlogger: ", str(this_logger))


def _reset_limit_filter():
    """Empty the Pelican Limit Log filter"""
    pelican.log.LimitFilter._ignore = set()
    pelican.log.LimitFilter._raised_messages = set()
    pelican.log.LimitFilter._threshold = 5
    pelican.log.LimitFilter._group_count = defaultdict(int)


EXPECTED_DEBUG_ITER = 1
EXPECTED_DEBUGS = (1 * EXPECTED_DEBUG_ITER)
EXPECTED_INFO_ITER = 1
EXPECTED_INFOS = (1 * EXPECTED_INFO_ITER)
EXPECTED_WARNING_ITER = 6
EXPECTED_WARNINGS_MSG1 = (1 * EXPECTED_WARNING_ITER)
EXPECTED_WARNINGS_MSG2 = (1 * EXPECTED_WARNING_ITER)
PASSING_LIMIT_THRESHOLD = pelican.log.LimitFilter._threshold - 1  # NOQA
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


def do_logging(test_logger):
    """Populate log content"""
    for i in range(EXPECTED_CRITICAL_ITER):
        test_logger.critical("A pseudo message of 'we are crashing'")

    for i in range(EXPECTED_INFO_ITER):
        test_logger.info("Unit testing log")
    for i in range(EXPECTED_WARNING_ITER):
        test_logger.warning("Log %s", i)
        test_logger.warning(
            f"Another log {i!s}",
            extra={'limit_msg': 'A generic message for too many warnings'}
        )
    for i in range(EXPECTED_ERROR_ITER):
        test_logger.error("Flooding error repeating")
    for i in range(EXPECTED_DEBUG_ITER):
        test_logger.debug("Unit testing Log @ debug level")


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


def restore_root_logger_to_python() -> logging.RootLogger.__class__:
    # Python logging does root-reset as:
    #    root = RootLogger(WARNING)
    #    Logger.root = root
    #    Logger.manager = Manager(Logger.root)

    # But there is no way to save the manager, just to create a new Manager()
    # But there is no way to save the handlers, just to create a new Handlers()
    previous_logger_subclass = logging.getLoggerClass()
    # Need to ascertain that root is literally a RootLogger
    # and not a subclass of any
    assert previous_logger_subclass.__subclasses__() == []
    # previous_manager = logging.Manager(logging.Logger.root)
    a_root_logger_class = logging.getLoggerClass().root.__class__
    assert issubclass(previous_logger_subclass, previous_logger_subclass)
    native_root_logger_class = logging.RootLogger

    logging.setLoggerClass(native_root_logger_class)
    # force Rootlogger to be of our preferred class for future instantiation
    # Undo Pelican's forced FatalLogger root class
    logging.getLogger().__class__ = native_root_logger_class

    # Blow away all the 38+ loggers outside of Pelican
    logging.root.manager.loggerDict = {}
    logging.root.level = None  # This is the signature virgin RootLogger
    return a_root_logger_class


def initialize_pelican_logger() -> logging.Logger.__class__:
    # Python logging does root-reset as:
    #    root = RootLogger(WARNING)
    #    Logger.root = root
    #    Logger.manager = Manager(Logger.root)
    restore_root_logger_to_python()

    # derived from pelican.log.__main__
    test_console = rich.console.Console()
    logging.setLoggerClass(pelican.log.FatalLogger)
    logging.getLogger().__class__ = pelican.log.FatalLogger
    target_level = logging.WARNING
    pelican.log.init(
        level=target_level,
        fatal="",
        name=None,
        handler=rich.logging.RichHandler(console=test_console)
    )
    # pelican.log.FatalLogger.warnings_fatal = pelican.log.fatal.startswith("warning")
    # pelican.log.FatalLogger.errors_fatal = bool(fatal)
    # log_format: str = "%(message)s"
    # logging.basicConfig(
    #     level=target_level,
    #     format=log_format,
    #     datefmt="[%H:%M:%S]",
    #     handlers=[pelican.log.init.handler] if pelican.log.init.handler else [],
    # )
    # logger = logging.getLogger(name)
    # if target_level:
    #     pelican.log.init.logger.setLevel(level)
    # if pelican.log.init.logs_dedup_min_level:
    #     pelican.log.LimitFilter.LOGS_DEDUP_MIN_LEVEL =
    #         pelican.log.init.logs_dedup_min_level
    test_logger = logger   # global variable inside pelican.__init__.logger
    assert test_logger.__class__.__subclasses__() == []
    return test_logger


##########################################################################
#  Fixtures
##########################################################################
@pytest.fixture(scope="function")
def display_attributes_around_pelican_root_logger__fixture_func():
    # FACT: logging.getLoggerClass().root.__class__ is .getLogger() instance
    print_logger("Pelican Root (before)", logging.root)
    yield
    print_logger("Pelican Root (after)", logging.root)


@pytest.fixture(scope="function")
def reset_root_logger_to_pelican__fixture_func():
    """Undo any custom RootLogger"""
    original_logger_class = logging.getLoggerClass()
    console = rich.console.Console()
    pelican.log.init(
        level=logging.WARNING,
        fatal="",
        handler=pelican.log.RichHandler(console=console),
        name=None,
        logs_dedup_min_level=None
    )
    test_pelican_logger = pelican.logger  # access Pelican global `logger` variable
    yield test_pelican_logger

    logging.setLoggerClass(original_logger_class)


@pytest.fixture(scope="function")
def display_reset_root_logger_to_pelican__fixture_func(
    display_attributes_around_python_root_logger__fixture_func
):
    original_logger_class = logging.getLoggerClass()
    console = rich.console.Console()
    pelican.log.init(
        level=logging.WARNING,
        fatal="",
        handler=pelican.log.RichHandler(console=console),
        name=None,
        logs_dedup_min_level=None
    )
    test_pelican_logger = pelican.logger  # access Pelican global `logger` variable
    yield test_pelican_logger

    logging.setLoggerClass(original_logger_class)


@pytest.fixture(scope="function")
def new_pelican_logger(
    reset_root_logger_to_pelican__fixture_func
):
    # At this point, it is a virgin Pelican __init__ startup,
    # right after loading the logging module
    # Correct error for an unused Logger
    test_logger = logging.getLogger()

    yield test_logger


@pytest.fixture(scope="function")
def display_attributes_around_python_root_logger__fixture_func():
    # FACT: logging.getLoggerClass().root.__class__ is .getLogger() instance
    print_logger("root (before)", logging.root)
    yield
    print_logger("root (after)", logging.root)


@pytest.fixture(scope="function")
def reset_root_logger_to_python__fixture_func():
    """Undo any custom RootLogger"""
    old_root_logger = restore_root_logger_to_python()

    yield

    logging.setLoggerClass(old_root_logger)


@pytest.fixture(scope="function")
def display_reset_root_logger_to_python__fixture_func(
    display_attributes_around_python_root_logger__fixture_func
):
    old_root_logger = restore_root_logger_to_python()

    yield

    logging.setLoggerClass(old_root_logger)


@pytest.fixture(scope="function")
def new_test_logger(
    reset_root_logger_to_python__fixture_func
):
    # At this point, it is a virgin Python CLI startup,
    # right after loading the logging module
    try:
        logging.getLogger("any_name_should_fail")
        raise AssertionError("Not a clean empty Logger")
    except ValueError:
        # Correct error for an unused Logger
        test_logger = logging.getLogger()

    yield test_logger


class TestLogBasic:
    """Basic Log Test"""
    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_one_log_output(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """One count of log messages"""
        test_log = new_test_logger
        test_log.setLevel(1)
        expected_count = 1
        pattern_str = "Unit testing log"
        with self._caplog.at_level(logging.INFO):
            self._caplog.clear()
            for i in range(expected_count):
                test_log.info(pattern_str)
            actual_count = 0

            for rec in self._caplog.messages:
                if pattern_str == rec:
                    actual_count = actual_count + 1

            assert expected_count == actual_count

    def test_flood_log_output(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger

    ):
        """Basic count of log messages"""
        target_level = 1
        expected_count = 825
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(logging.INFO):
            self._caplog.clear()
            for i in range(expected_count):
                test_log.info(f"Log {i}")

        actual_count = 0
        for rec in self._caplog.messages:
            if "Log " in rec:
                actual_count = actual_count + 1

        assert target_level == test_log.level
        assert target_level == test_log.getEffectiveLevel()
        assert expected_count == actual_count

    def test_flood_mixed_log_output(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Basic count of log messages"""
        target_level = 1
        expected_count = 100
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            for i in range(expected_count):
                test_log.debug(f"Log {i}")
                test_log.info(f"Log {i}")
                test_log.warning(f"Log {i}")
                test_log.error(f"Log {i}")
                test_log.critical(f"Log {i}")

            actual_count = 0
            for rec in self._caplog.messages:
                if "Log " in rec:
                    actual_count = actual_count + 1
            assert (expected_count * 5) == actual_count


class TestLogLevel:

    def count_logs(self, msg=None, level=None):
        count = 0
        for logger_name, log_lvl, log_msg in self._caplog.record_tuples[:]:
            if (
                (msg is None or re.match(msg, log_msg)) and
                (level is None or log_lvl == level)
            ):
                print(f'name: {logger_name} lvl: {log_lvl} msg: "{log_msg}"')
                count = count + 1
        return count

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_below_level(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Logging below a given label level"""
        expected_count = 0
        target_level = logging.INFO
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            test_log.debug("Ignored this debug log @ INFO level")

        actual_count = 0
        for rec in self._caplog.messages:
            if "Ignored this debug log " in rec:
                actual_count = actual_count + 1

        assert actual_count == expected_count

    def test_below_level_increment(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Logging under a given level + 1"""
        expected_count = 0
        target_level = logging.DEBUG + 1
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            test_log.debug("Ignored this debug log @ slightly above DEBUG+1")

            actual_count = 0
            for rec in self._caplog.messages:
                if "Ignored this debug log " in rec:
                    actual_count = actual_count + 1
            assert actual_count == expected_count

    def test_above_level(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Logging above given level"""
        expected_count = 1
        target_level = logging.DEBUG
        test_log = new_test_logger
        test_log.setLevel(target_level)
        pattern_test = "this info log appears @ DEBUG level"
        with self._caplog.at_level(logging.INFO):
            self._caplog.clear()

            test_log.info(pattern_test)

            actual_count = 0
            for rec in self._caplog.messages:
                if pattern_test == rec:
                    actual_count = actual_count + 1
            assert actual_count == expected_count

    def test_above_level_increment(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Logging above a given level - 1"""
        expected_count = 1
        target_level = (logging.DEBUG - 1)
        test_log = new_test_logger
        test_log.setLevel(target_level)
        pattern_test = "this DEBUG log appears slight over DEBUG-1 level"
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            test_log.debug(pattern_test)

            actual_count = 0
            for rec in self._caplog.messages:
                if pattern_test == rec:
                    actual_count = actual_count + 1
            assert actual_count == expected_count

    def test_level_segregation_at_debug(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        target_level = logging.DEBUG
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            do_logging(test_log)

        """Each boundary of level, +/- 1"""
        assert (0 == self.count_logs(level=0))
        assert 0 == self.count_logs(level=1)
        assert 0 == self.count_logs(level=9)
        assert EXPECTED_DEBUGS == self.count_logs(level=logging.DEBUG)
        assert 0 == self.count_logs(level=11)
        assert 0 == self.count_logs(level=19)
        assert EXPECTED_INFOS == self.count_logs(level=logging.INFO)
        assert 0 == self.count_logs(level=21)
        assert 0 == self.count_logs(level=29)
        assert (
            (
                EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2
            ) ==
            self.count_logs(level=logging.WARNING)
        )
        assert 0 == self.count_logs(level=31)
        assert 0 == self.count_logs(level=39)
        assert EXPECTED_ERRORS == self.count_logs(level=logging.ERROR)
        assert 0 == self.count_logs(level=41)
        assert 0 == self.count_logs(level=49)
        assert EXPECTED_CRITICALS == self.count_logs(level=logging.CRITICAL)
        assert 0 == self.count_logs(level=51)

    def test_level_segregation_at_info(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Each boundary of level, +/- 1"""
        target_level = logging.INFO
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            do_logging(test_log)

        """Each boundary of level, +/- 1"""
        assert (0 == self.count_logs(level=0))
        assert 0 == self.count_logs(level=1)
        assert 0 == self.count_logs(level=9)
        assert 0 == self.count_logs(level=logging.DEBUG)
        assert 0 == self.count_logs(level=11)
        assert 0 == self.count_logs(level=19)
        assert EXPECTED_INFOS == self.count_logs(level=logging.INFO)
        assert 0 == self.count_logs(level=21)
        assert 0 == self.count_logs(level=29)
        assert (
            (
                EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2
            ) ==
            self.count_logs(level=logging.WARNING)
        )
        assert 0 == self.count_logs(level=31)
        assert 0 == self.count_logs(level=39)
        assert EXPECTED_ERRORS == self.count_logs(level=logging.ERROR)
        assert 0 == self.count_logs(level=41)
        assert 0 == self.count_logs(level=49)
        assert EXPECTED_CRITICALS == self.count_logs(level=logging.CRITICAL)
        assert 0 == self.count_logs(level=51)

    def test_level_segregation_at_warning(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Each boundary of level, +/- 1"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            do_logging(test_log)

        """Each boundary of level, +/- 1"""
        assert (0 == self.count_logs(level=0))
        assert 0 == self.count_logs(level=1)
        assert 0 == self.count_logs(level=9)
        assert 0 == self.count_logs(level=logging.DEBUG)
        assert 0 == self.count_logs(level=11)
        assert 0 == self.count_logs(level=19)
        assert 0 == self.count_logs(level=logging.INFO)
        assert 0 == self.count_logs(level=21)
        assert 0 == self.count_logs(level=29)
        assert (
            (
                EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2
            ) ==
            self.count_logs(level=logging.WARNING)
        )
        assert 0 == self.count_logs(level=31)
        assert 0 == self.count_logs(level=39)
        assert EXPECTED_ERRORS == self.count_logs(level=logging.ERROR)
        assert 0 == self.count_logs(level=41)
        assert 0 == self.count_logs(level=49)
        assert EXPECTED_CRITICALS == self.count_logs(level=logging.CRITICAL)
        assert 0 == self.count_logs(level=51)

    def test_level_segregation_at_error(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Each boundary of level, +/- 1"""
        target_level = logging.ERROR
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            do_logging(test_log)

        """Each boundary of level, +/- 1"""
        assert (0 == self.count_logs(level=0))
        assert 0 == self.count_logs(level=1)
        assert 0 == self.count_logs(level=9)
        assert 0 == self.count_logs(level=logging.DEBUG)
        assert 0 == self.count_logs(level=11)
        assert 0 == self.count_logs(level=19)
        assert 0 == self.count_logs(level=logging.INFO)
        assert 0 == self.count_logs(level=21)
        assert 0 == self.count_logs(level=29)
        assert 0 == self.count_logs(level=logging.WARNING)
        assert 0 == self.count_logs(level=31)
        assert 0 == self.count_logs(level=39)
        assert EXPECTED_ERRORS == self.count_logs(level=logging.ERROR)
        assert 0 == self.count_logs(level=41)
        assert 0 == self.count_logs(level=49)
        assert EXPECTED_CRITICALS == self.count_logs(level=logging.CRITICAL)
        assert 0 == self.count_logs(level=51)

    def test_ignores_regex(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using test regex (test-on-test)"""
        target_level = logging.INFO
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            do_logging(test_log)

            assert self.count_logs(r"Log [34]") == 2
            assert self.count_logs(r"Log [36]") == 1
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            assert (
                self.count_logs(r".+o.+", logging.WARNING) ==
                (EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2)
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            assert self.count_logs(level=logging.WARNING) == EXPECTED_WARNINGS
            assert self.count_logs(level=logging.ERROR) == 6
            assert (
                self.count_logs() ==
                (
                    EXPECTED_CRITICALS +
                    EXPECTED_INFOS +
                    (EXPECTED_WARNINGS_MSG1 + EXPECTED_WARNINGS_MSG2) +
                    EXPECTED_ERRORS
                )
            )


class TestLogUninstalledLimit:
    """Pattern Check; FatalLogger(LimitLogger) is not installed yet"""
    def count_logs(self, pattern=None, level=None):
        count = 0
        for logger_name, log_lvl, log_msg in self._caplog.record_tuples[:]:
            if (
                (level is None or log_lvl == level) and
                (pattern is None or re.match(pattern, log_msg))
            ):
                print(f'name: {logger_name} lvl: {log_lvl} msg: "{log_msg}"')
                count = count + 1
        return count

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_dataset_check_entire(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.INFO
        test_log = new_test_logger
        test_log.setLevel(target_level)
        expected_total = (
            EXPECTED_CRITICALS +
            (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                WARNING_LIMIT_EMITTED
            ) +
            EXPECTED_ERRORS
        )
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs() == expected_total

    def test_dataset_all_another(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2
            )
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs(level=logging.WARNING) == expected_warnings

    def test_dataset_filter_all_log(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger

    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs(level=logging.DEBUG) == 0

    def test_dataset_all_log_warning(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger

    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2_LIMIT,
            )

    def test_dataset_all_log_filtered(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs("Log 3", logging.WARNING) == 1

    def test_exact_pattern(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs("Log 3", logging.WARNING) == 1
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            assert (
                self.count_logs(level=logging.WARNING) ==
                EXPECTED_WARNINGS
            )
            assert (
                self.count_logs(level=logging.ERROR) ==
                EXPECTED_ERRORS
            )
            total_expected = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == total_expected

    def test_exact_pattern_another_log_5(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )

    def test_template_word(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by word template"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            # This pattern ignores out everything that has a word before ' log '
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG1
            )
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2
            )
            assert self.count_logs(level=logging.WARNING) == expected_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total

    def test_template_digit_one(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by digit template"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with (self._caplog.at_level(target_level)):
            self._caplog.clear()
            # This pattern ignores out everything that starts with `Log `
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(test_log)

            assert self.count_logs(r"Log \\d", logging.WARNING) == 0
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            # expected_warnings = EXPECTED_WARNINGS_LIMIT - 1 + WARNING_LIMIT_EMITTED
            expected_warnings = EXPECTED_WARNINGS
            assert self.count_logs(level=logging.WARNING) == expected_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                # WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total

    def test_regex_template_digit_all(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by digit template"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            # This pattern ignores out everything that starts with `Log `
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(test_log)

            assert (
                self.count_logs(r"Log \\d", logging.WARNING) ==
                (EXPECTED_WARNINGS_MSG1 - EXPECTED_WARNINGS_MSG1)
            )
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            total_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2  # +
                # EXPECTED_WARNINGS_MSG2_LIMIT +
                # WARNING_LIMIT_EMITTED
            )
            assert self.count_logs(level=logging.WARNING) == total_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                # EXPECTED_WARNINGS_LIMIT +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS  # +
                # WARNING_LIMIT_EMITTED
            )
            assert self.count_logs() == expected_total

    def test_filter_warnings_detect_debug_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                EXPECTED_WARNINGS_MSG1
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0

    def test_filter_warnings_detect_info_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                (EXPECTED_WARNINGS_MSG1 - 1),
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.INFO) == 0

    def test_filter_warnings_detect_warning_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            expected_total = (
                # (EXPECTED_WARNINGS_MSG1 - 1) +
                (EXPECTED_WARNINGS_MSG1 - 0) +
                # EXPECTED_WARNINGS_MSG2_LIMIT +
                EXPECTED_WARNINGS_MSG2  # +
                # WARNING_LIMIT_EMITTED
            )
            assert (
                self.count_logs(level=logging.WARNING) ==
                expected_total
            )

    def test_filter_warnings_detect_error_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS

    def test_filter_warnings_detect_critical_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert (
                self.count_logs(level=logging.CRITICAL) ==
                EXPECTED_CRITICALS
            )

    def test_filter_warnings_detect_dataset_all(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            expected_total = (
                EXPECTED_CRITICALS +
                # EXPECTED_WARNINGS_LIMIT +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total


class TestLogInstalledLimit:
    """Pattern Check; FatalLogger(LimitLogger) IS INSTALLED """
    def count_logs(self, pattern=None, level=None):
        count = 0
        for logger_name, log_lvl, log_msg in self._caplog.record_tuples[:]:
            if (
                (level is None or log_lvl == level) and
                (pattern is None or re.match(pattern, log_msg))
            ):
                print(f'name: {logger_name} lvl: {log_lvl} msg: "{log_msg}"')
                count = count + 1
        return count

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_dataset_check_entire(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.INFO
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        expected_total = (
            EXPECTED_CRITICALS +
            (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                WARNING_LIMIT_EMITTED
            ) +
            EXPECTED_ERRORS
        )
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs() == expected_total

    def test_dataset_all_another(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2
            )
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs(level=logging.WARNING) == expected_warnings

    def test_dataset_filter_all_log(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs(level=logging.DEBUG) == 0

    def test_dataset_all_log_warning(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger

    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2_LIMIT,
            )

    def test_dataset_all_log_filtered(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs("Log 3", logging.WARNING) == 1

    def test_exact_pattern(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs("Log 3", logging.WARNING) == 1
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            assert (
                self.count_logs(level=logging.WARNING) ==
                EXPECTED_WARNINGS
            )
            assert (
                self.count_logs(level=logging.ERROR) ==
                EXPECTED_ERRORS
            )
            total_expected = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == total_expected

    def test_exact_pattern_another_log_5(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )

    def test_template_word(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by word template"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            # This pattern ignores out everything that has a word before ' log '
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG1
            )
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2
            )
            assert self.count_logs(level=logging.WARNING) == expected_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total

    def test_template_digit_one(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by digit template"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with (self._caplog.at_level(target_level)):
            self._caplog.clear()
            # This pattern ignores out everything that starts with `Log `
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(test_log)

            assert self.count_logs(r"Log \\d", logging.WARNING) == 0
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            # expected_warnings = EXPECTED_WARNINGS_LIMIT - 1 + WARNING_LIMIT_EMITTED
            expected_warnings = EXPECTED_WARNINGS
            assert self.count_logs(level=logging.WARNING) == expected_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                # WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total

    def test_regex_template_digit_all(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter by digit template"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            # This pattern ignores out everything that starts with `Log `
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(test_log)

            assert (
                self.count_logs(r"Log \\d", logging.WARNING) ==
                (EXPECTED_WARNINGS_MSG1 - EXPECTED_WARNINGS_MSG1)
            )
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            total_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2  # +
                # EXPECTED_WARNINGS_MSG2_LIMIT +
                # WARNING_LIMIT_EMITTED
            )
            assert self.count_logs(level=logging.WARNING) == total_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                # EXPECTED_WARNINGS_LIMIT +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS  # +
                # WARNING_LIMIT_EMITTED
            )
            assert self.count_logs() == expected_total

    def test_filter_warnings_detect_debug_only(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                EXPECTED_WARNINGS_MSG1
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0

    def test_filter_warnings_detect_info_only(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                (EXPECTED_WARNINGS_MSG1 - 1),
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.INFO) == 0

    def test_filter_warnings_detect_warning_only(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            expected_total = (
                # (EXPECTED_WARNINGS_MSG1 - 1) +
                (EXPECTED_WARNINGS_MSG1 - 0) +
                # EXPECTED_WARNINGS_MSG2_LIMIT +
                EXPECTED_WARNINGS_MSG2  # +
                # WARNING_LIMIT_EMITTED
            )
            assert (
                self.count_logs(level=logging.WARNING) ==
                expected_total
            )

    def test_filter_warnings_detect_error_only(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS

    def test_filter_warnings_detect_critical_only(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert (
                self.count_logs(level=logging.CRITICAL) ==
                EXPECTED_CRITICALS
            )

    def test_filter_warnings_detect_dataset_all(
        self,
        capture_log,
        display_reset_root_logger_to_pelican__fixture_func,
        new_pelican_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_pelican_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            expected_total = (
                EXPECTED_CRITICALS +
                # EXPECTED_WARNINGS_LIMIT +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total


class TestLogLimitPatternInfoLevel:
    """Pattern Check; FatalLogger(LimitLogger); Info level"""
    # What exact area of level am I testing for? Logger.level or Limit.level?
    # This here is "Limit" so focus on Limit level then
    def count_logs(self, pattern=None, level=None):
        count = 0
        for logger_name, log_lvl, log_msg in self._caplog.record_tuples[:]:
            if (
                (level is None or log_lvl == level) and
                (pattern is None or re.match(pattern, log_msg))
            ):
                print(f'name: {logger_name} lvl: {log_lvl} msg: "{log_msg}"')
                count = count + 1
        return count

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_dataset_check_entire(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.INFO
        test_log = new_test_logger
        test_log.setLevel(target_level)
        expected_total = (
            EXPECTED_CRITICALS +
            (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                WARNING_LIMIT_EMITTED
            ) +
            EXPECTED_ERRORS
        )
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs() == expected_total

    def test_dataset_all_another(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2
            )
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs(level=logging.WARNING) == expected_warnings

    def test_dataset_filter_all_log(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger

    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs(level=logging.DEBUG) == 0

    def test_dataset_all_log_warning(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger

    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2_LIMIT,
            )

    def test_dataset_all_log_filtered(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs("Log 3", logging.WARNING) == 1

    def test_exact_pattern(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert self.count_logs("Log 3", logging.WARNING) == 1
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            assert (
                self.count_logs(level=logging.WARNING) ==
                EXPECTED_WARNINGS
            )
            assert (
                self.count_logs(level=logging.ERROR) ==
                EXPECTED_ERRORS
            )
            total_expected = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == total_expected

    def test_exact_pattern_another_log_5(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by exact pattern"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))  # NOOP

            do_logging(test_log)

            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )

    def test_template_word(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by word template"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            # This pattern ignores out everything that has a word before ' log '
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG1
            )
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            expected_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2
            )
            assert self.count_logs(level=logging.WARNING) == expected_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total

    def test_template_digit_one(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by digit template"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with (self._caplog.at_level(target_level)):
            self._caplog.clear()
            # This pattern ignores out everything that starts with `Log `
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

            do_logging(test_log)

            assert self.count_logs(r"Log \\d", logging.WARNING) == 0
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            # expected_warnings = EXPECTED_WARNINGS_LIMIT - 1 + WARNING_LIMIT_EMITTED
            expected_warnings = EXPECTED_WARNINGS
            assert self.count_logs(level=logging.WARNING) == expected_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2 +
                # WARNING_LIMIT_EMITTED +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total

    def test_regex_template_digit_all(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter by digit template"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()

            # This pattern ignores out everything that starts with `Log `
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

            do_logging(test_log)

            assert (
                self.count_logs(r"Log \\d", logging.WARNING) ==
                (EXPECTED_WARNINGS_MSG1 - EXPECTED_WARNINGS_MSG1)
            )
            assert (
                self.count_logs(r"Another log \d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0
            total_warnings = (
                EXPECTED_WARNINGS_MSG1 +
                EXPECTED_WARNINGS_MSG2  # +
                # EXPECTED_WARNINGS_MSG2_LIMIT +
                # WARNING_LIMIT_EMITTED
            )
            assert self.count_logs(level=logging.WARNING) == total_warnings
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS
            expected_total = (
                EXPECTED_CRITICALS +
                # EXPECTED_WARNINGS_LIMIT +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS  # +
                # WARNING_LIMIT_EMITTED
            )
            assert self.count_logs() == expected_total

    def test_filter_warnings_detect_debug_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                EXPECTED_WARNINGS_MSG1
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.DEBUG) == 0

    def test_filter_warnings_detect_info_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert self.count_logs("Log \\d", logging.WARNING) == \
                (EXPECTED_WARNINGS_MSG1 - 1)
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.INFO) == 0

    def test_filter_warnings_detect_warning_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            expected_total = (
                # (EXPECTED_WARNINGS_MSG1 - 1) +
                (EXPECTED_WARNINGS_MSG1 - 0) +
                # EXPECTED_WARNINGS_MSG2_LIMIT +
                EXPECTED_WARNINGS_MSG2  # +
                # WARNING_LIMIT_EMITTED
            )
            assert (
                self.count_logs(level=logging.WARNING) ==
                expected_total
            )

    def test_filter_warnings_detect_error_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert self.count_logs(level=logging.ERROR) == EXPECTED_ERRORS

    def test_filter_warnings_detect_critical_only(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            assert (
                self.count_logs(level=logging.CRITICAL) ==
                EXPECTED_CRITICALS
            )

    def test_filter_warnings_detect_dataset_all(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        new_test_logger
    ):
        """Filter, using all attributes"""
        target_level = logging.WARNING
        test_log = new_test_logger
        test_log.setLevel(target_level)
        with self._caplog.at_level(target_level):
            self._caplog.clear()
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

            do_logging(test_log)

            assert (
                self.count_logs("Log \\d", logging.WARNING) ==
                # (EXPECTED_WARNINGS_MSG1 - 1)
                (EXPECTED_WARNINGS_MSG1 - 0)
            )
            assert (
                self.count_logs("Another log \\d", logging.WARNING) ==
                # EXPECTED_WARNINGS_MSG2_LIMIT
                EXPECTED_WARNINGS_MSG2
            )
            # total log buffer dataset check
            expected_total = (
                EXPECTED_CRITICALS +
                # EXPECTED_WARNINGS_LIMIT +
                EXPECTED_WARNINGS +
                EXPECTED_ERRORS
            )
            assert self.count_logs() == expected_total


class TestLogLimitPatternInfoLevel:
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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, r"\w log "))

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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

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


class TestLogLimitPatternDebugLevel:
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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))

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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "\\w log "))

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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log \\d"))

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
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Log 3"))
            pelican.log.LimitFilter._ignore.add((logging.WARNING, "Another log %s"))

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
