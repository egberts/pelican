
import logging
import pelican
from pelican import logger
import pytest
import rich
import rich.logging


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


class TestLogInitBasic:

    def test_argument_handlers_invalid(
        self,
        reset_root_logger_to_pelican__fixture_func
    ):
        try:
            pelican.log.init(handler=[])
            assert False
        except SyntaxError:
            assert True
