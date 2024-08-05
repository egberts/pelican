
import contextlib
import filelock
import logging
import os
import pytest
import re
import rich
import rich.logging

import pelican
from pelican import logger

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


def do_logging(test_logger: logging.Logger):
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
    test_logger = logger  # global variable inside pelican.__init__.logger
    assert test_logger.__class__.__subclasses__() == []
    return test_logger


##########################################################################
#  Fixtures
##########################################################################
@pytest.fixture(scope="session")
def serial_lock__fixture_session(tmp_path_factory):
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / "serial.lock"
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        os.remove(path=lock_file)


@pytest.fixture(scope="function")
def serialize_functions__fixture_func(serial_lock__fixture_session):
    """mark function test as serial/sequential ordering

    Include `serial` in the function's argument list ensures
    that no other test(s) also having `serial` in its argument list
    shall run."""
    with serial_lock__fixture_session.acquire(poll_interval=0.1):
        yield


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


class TestLogInitArgumentLevel:
    """Exercise level argument in pelican.log.init()"""

    # def init(
    #     level=None,
    #     fatal="",
    #     handler=DEFAULT_LOG_HANDLER,
    #     name=None,
    #     logs_dedup_min_level=None,
    # ):
    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_argument_level_none(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level=None)
            assert True
        except any:
            assert False

    def test_argument_level_syntax_list(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level={})
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_level_syntax_dict(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level=[])
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_level_int_valid(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level=0)
            assert True
        except any:
            assert False

    def test_argument_level_str_valid_critical(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level="CRITICAL")
            assert True
        except any:
            assert False

    def test_argument_level_str_valid_error(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level="ERROR")
            assert True
        except any:
            assert False

    def test_argument_level_str_valid_warning(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level="WARNING")
            assert True
        except any:
            assert False

    def test_argument_level_str_valid_info(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level="INFO")
            assert True
        except any:
            assert False

    def test_argument_level_str_valid_debug(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level="DEBUG")
            assert True
        except any:
            assert False

    def test_argument_level_str_invalid(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level="CriTiCaL")  # to fail
            assert False
        except ValueError:
            assert True
        except any:
            assert False

    def test_log_init_level_syntax_set(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level=())
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_log_init_level_syntax_list(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level=[])
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_log_init_level_syntax_dict(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(level={})
            assert False
        except TypeError:
            assert True
        except any:
            assert False


class TestLogInitArgumentFatal:
    """Exercise level argument in pelican.log.init()"""

    # def init(
    #     level=None,
    #     fatal="",
    #     handler=DEFAULT_LOG_HANDLER,
    #     name=None,
    #     logs_dedup_min_level=None,
    # ):
    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_argument_fatal_str_valid_blank(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal="")
            assert True
        except any:
            assert False

    def test_argument_fatal_str_valid_warning(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal="warning")
            assert True
        except any:
            assert False

    def test_argument_fatal_str_valid_warning_error(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal="warning-error")
            assert True
        except any:
            assert False

    def test_argument_fatal_none(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal=None)
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_fatal_syntax_int(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal=1)
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_fatal_syntax_bool(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal=True)
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_fatal_syntax_list(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal={})
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_fatal_syntax_dict(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal=[])
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_argument_fatal_syntax_set(
        self,
        capture_log,
        reset_root_logger_to_pelican__fixture_func
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        try:
            pelican.log.init(fatal=())
            assert False
        except TypeError:
            assert True
        except any:
            assert False


class TestLogInitArgumentHandler:

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_argument_handler_none(
        self,
        reset_root_logger_to_pelican__fixture_func
    ):
        try:
            pelican.log.init(handler=None)
            assert True
        except any:
            assert False

    def test_argument_handler_invalid(
        self,
        reset_root_logger_to_pelican__fixture_func
    ):
        try:
            pelican.log.init(handler=[])
            assert False
        except TypeError:
            assert True


class TestLogInitArgumentName:
    """Exercise level argument in pelican.log.init()"""

    # def init(
    #     level=None,
    #     fatal="",
    #     handler=DEFAULT_LOG_HANDLER,
    #     name=None,
    #     logs_dedup_min_level=None,
    # ):
    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_init_argument_name_none_valid(self):
        try:
            pelican.log.init(name=None)
            assert True
        except any:
            assert False

    def test_init_argument_name_str_valid(self):
        try:
            pelican.log.init(name="test_module")
            assert True
        except any:
            assert False

    def test_init_argument_name_syntax_int(self):
        try:
            pelican.log.init(name=1234)
            assert False
        except TypeError:
            assert True

    def test_init_argument_name_syntax_list(self):
        try:
            pelican.log.init(name=[])
            assert False
        except TypeError:
            assert True

    def test_init_argument_name_syntax_dict(self):
        try:
            pelican.log.init(name={})
            assert False
        except TypeError:
            assert True

    def test_init_argument_name_syntax_set(self):
        try:
            pelican.log.init(name=())
            assert False
        except TypeError:
            assert True
        except any:
            assert False

    def test_init_argument_name_str_invalid(self, capture_log):
        try:
            pelican.log.init(name="*a.b.c.d")
            assert False
        except TypeError:
            assert True


class TestLogInitArgumentDedups:

    def count_logs(self, pattern=None, level=None):
        """Matches a regex pattern from start

        If you wanted anywhere in a string, use:

            pattern = r'.+my_pattern'
        """
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
        self._caplog.clear()

    def test_hit_repeating_errors(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        serialize_functions__fixture_func
    ):
        logger_name = __name__
        pelican.log.init(
            level=logging.INFO,
            name=logger_name,
            logs_dedup_min_level=logging.CRITICAL
        )
        test_log: logging.Logger = pelican.logger
        target_pattern = "Flooding error repeating"
        with self._caplog.at_level(logging.WARNING):
            self._caplog.clear()

            do_logging(test_log)

        assert self.count_logs(level=logging.ERROR, pattern=target_pattern) == 1

    def test_miss_limit_threshold(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        serialize_functions__fixture_func
    ):
        new_threshold = 7
        pelican.log.init(
            level=logging.WARNING,
            name=None,  # using 'None'
            logs_dedup_min_level=logging.ERROR
        )
        test_log: logging.Logger = pelican.logger
        original_threshold = pelican.log.LimitFilter._threshold
        pelican.log.LimitFilter._threshold = new_threshold
        with self._caplog.at_level(logging.WARNING):
        #    self._caplog.clear()
            target_pattern = "A generic message"
            do_logging(test_log)

        total_expected = (
            EXPECTED_CRITICALS +
            EXPECTED_WARNINGS_MSG1 +
            (
                EXPECTED_WARNINGS_MSG2_LIMIT -
                (original_threshold - new_threshold + 1)
            ) +
            WARNING_LIMIT_EMITTED +
            EXPECTED_ERRORS_CAPPED
        )
        assert len(self._caplog.record_tuples) == total_expected
        assert self.count_logs(
            pattern=target_pattern) == 0, ("generic message unexpectedly in log; "
                                           "threshold failed")

        pelican.log.LimitFilter._threshold = original_threshold

    def test_hit_limit_threshold(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        serialize_functions__fixture_func
    ):
        new_threshold = 6
        pelican.log.init(
            level=logging.WARNING,
            name=None,  # first time using 'None'
            logs_dedup_min_level=logging.ERROR
        )
        test_log: logging.Logger = pelican.logger
        original_threshold = pelican.log.LimitFilter._threshold
        pelican.log.LimitFilter._threshold = new_threshold
        with self._caplog.at_level(logging.WARNING):
            self._caplog.clear()

            target_pattern = "A generic message"
            do_logging(test_log)

        total_expected = (
            EXPECTED_CRITICALS +
            EXPECTED_WARNINGS_MSG1 +
            (
                EXPECTED_WARNINGS_MSG2_LIMIT -
                (original_threshold - new_threshold)
            ) +
            WARNING_LIMIT_EMITTED +
            EXPECTED_ERRORS_CAPPED
        )
        assert len(self._caplog.record_tuples) == total_expected
        assert self.count_logs(pattern=target_pattern) == 1, \
            "generic message not in log; threshold failed"

        pelican.log.LimitFilter._threshold = original_threshold

    def test_over_the_limit_threshold(
        self,
        capture_log,
        display_reset_root_logger_to_python__fixture_func,
        serialize_functions__fixture_func
    ):
        new_threshold = 5
        pelican.log.init(
            level=logging.WARNING,
            name=None,  # First time using 'None'
            logs_dedup_min_level=logging.ERROR
        )
        test_log: logging.Logger = pelican.logger
        original_threshold = pelican.log.LimitFilter._threshold
        pelican.log.LimitFilter._threshold = new_threshold
        with self._caplog.at_level(logging.WARNING):
            self._caplog.clear()

            target_pattern = "A generic message"
            do_logging(test_log)

        total_expected = (
            EXPECTED_CRITICALS +
            EXPECTED_WARNINGS_MSG1 +
            (
                EXPECTED_WARNINGS_MSG2_LIMIT +
                (new_threshold - original_threshold)
            ) +
            WARNING_LIMIT_EMITTED +
            EXPECTED_ERRORS_CAPPED
        )
        assert len(self._caplog.record_tuples) == total_expected
        assert self.count_logs(pattern=target_pattern) == 1, ("generic message not in "
                                                              "log; threshold failed")

        pelican.log.LimitFilter._threshold = original_threshold
