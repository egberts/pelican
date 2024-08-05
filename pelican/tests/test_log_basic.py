# File: test_log_basic.py
# Test: pytest
# Description:
#
#   Devil is in the Details:
#
#   No matter how hard you try, because any test file resides under the
#   Pelican source package, this pytest script will ALWAYS pick up and preload
#   the Pelican `FatalLogger` logging.Logger class (that `pelican/__init.py__`
#   created from `log.init` (in `log.py`, aka `init_logging()`) before running any
#   of log-related tests given below in this file.
#
#   This test deals ONLY with the installed Pelican package (as opposed to
#   uninstalled Pelican package).
#
# Some overviews to reiterate here:
#
#  *  logging.Logger is a singleton-class;
#  *  logging.Logger uses same instance throughout the entire package until its
#       rootLogger gets swapped out (like our FatalLogger class).
#  *  logging.root.manager is the same for ALL subclasses of the logging class.
#  *  Zeroizing the logging.root.manager is tricky to do, it keeps coming back
#       by some Python modules.
#  *  level only is used by its Logger subclass (and do not propagate upward)
#
#
import logging

import logging_tree
import pytest

# from pelican.log import init as init_pelican_logger


# Always check for `.level` attribute in int type using logging.Logger class


def log_print_tree(title="") -> None:
    print(f"{title}:\n")
    logging_tree.printout()
    print("\n")


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


def reset_logging_handlers() -> None:
    """Clear out all classes of FatalLogging, setuptool.logging, ..."""
    # logging.basicConfig(force=True) only works AFTER instantiating
    #   the NON-ROOT logging.getLogger(), hence the need for this function
    #   to perform BEFORE the Logger class instantiation.
    #

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    loggers.append(logging.getLogger())  # for the root logger
    print("List of logging handlers being removed: ", loggers)
    for logger in loggers:
        handlers = logger.handlers[:]
        # print('LogHandlers: ', handlers)
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(logging.NOTSET)
        logger.propagate = True


def all_subclasses(cls) -> set:
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


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
    logging.root.level = logging.WARNING
    return a_root_logger_class


##########################################################################
#  Fixtures
##########################################################################
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
    # logging.RootLogger.root.__class__ == previous_root_logger_class


@pytest.fixture(scope="function")
def reset_root_logger_to_python__fixture_func():
    old_root_logger = restore_root_logger_to_python()

    yield

    logging.setLoggerClass(old_root_logger)


@pytest.fixture(scope="function")
def init_logger_display_attributes_before_after__fixture_func(

):
    this_log_class = logging.getLogger()
    print_logger("Logger (before)", this_log_class)
    yield this_log_class
    print_logger("Logger (after)", this_log_class)


@pytest.fixture(scope="function")
def restore_logger_python(
    init_logger_display_attributes_before_after__fixture_func
):
    """Undo any custom RootLogger"""
    #previous_logger_class = logging.getLoggerClass()
    #previous_root_logger_class = logging.getLoggerClass().root.__class__
    #native_root_logger_class = logging.RootLogger
    #logging.setLoggerClass(native_root_logger_class)
    ## force Rootlogger to be of our preferred class for future instantiation
    ## Undo Pelican's forced FatalLogger root class
    #logging.getLogger().__class__ = native_root_logger_class
    ## Blow away all the 38+ loggers outside of Pelican
    #logging.root.manager.loggerDict = {}

    #yield native_root_logger_class

    #logging.setLoggerClass(previous_logger_class)
    pass


class TestLogBasic:

    def test_logging_tree(self):
        print(logging_tree.printout())

    def test_print_current_logger(self):
        print_logger("current Logger: ", logging.getLogger())

    def test_print_current_root(self):
        print_logger("current RootLogger:", logging.root)

    def test_reset_to_python_root_logger_warning(
        self,
        reset_root_logger_to_python__fixture_func
    ):
        assert logging.root.level == logging.WARNING
        assert logging.root.manager.loggerClass is None
        assert logging.root.manager.root.__class__ is logging.RootLogger
        assert logging.root.name == "root"
        # trust that pytest/PyCharm provides good default handlers
        assert logging_tree.printout() is None

    def test_reset_to_python_root_logger_manager_class(
        self,
        reset_root_logger_to_python__fixture_func
    ):
        assert logging.root.manager.loggerClass is None

    def test_reset_to_python_root_logger_manager_root(
        self,
        reset_root_logger_to_python__fixture_func
    ):
        assert logging.root.manager.root.__class__ is logging.RootLogger

    def test_reset_to_python_root_logger_name(
        self,
        reset_root_logger_to_python__fixture_func
    ):
        assert logging.root.name == "root"

    def test_display_reset_around_root_logger_printout(
        self,
        display_reset_root_logger_to_python__fixture_func,
    ):
        # trust that pytest/PyCharm provides good default handlers
        assert logging_tree.printout() is None

    def test_around_root(
        self,
        display_reset_root_logger_to_python__fixture_func,

    ):
        """Ensure that a fresh root library is truly empty"""
        # Why would a root logger NOT have a level?
        assert logging.root.level == logging.WARNING
        assert logging.root.manager.loggerClass is None
        assert logging.root.manager.root.__class__ is logging.RootLogger
        assert logging.root.name == "root"
        # trust that pytest/PyCharm provides good default handlers
        assert logging_tree.printout() is None

    def test_surround(
        self,
        display_attributes_around_python_root_logger__fixture_func
    ):
        pass

    def test_current_root_details(
        self,
        display_reset_root_logger_to_python__fixture_func
    ):
        print_logger("root (before)", logging.Logger.root)

    def test_current_logger_details(self):
        print_logger("current", logging.Logger)

    def test_log_level_set_sliding_scale(self):
        """Understand All This Before Log UUT"""
        # Pelican assumes default WARNING from virgin rootLogger here
        # Python logging assumes default WARNING from virgin rootLogger here
        assert logging.root.level == logging.WARNING
        test_log = logging.getLogger()
        # Newly created LogLogger class should be NOTSET yet operate at WARNING
        assert test_log.level == logging.WARNING
        assert test_log.getEffectiveLevel() == logging.WARNING
        assert test_log.isEnabledFor(logging.WARNING)

        test_log.setLevel(logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert test_log.getEffectiveLevel() == logging.NOTSET
        assert test_log.isEnabledFor(logging.WARNING)

        test_log.setLevel(logging.DEBUG)
        assert test_log.level == logging.DEBUG
        assert test_log.getEffectiveLevel() == logging.DEBUG
        assert test_log.isEnabledFor(logging.DEBUG)

        test_log.setLevel(logging.INFO)
        assert test_log.level == logging.INFO
        assert test_log.getEffectiveLevel() == logging.INFO
        assert test_log.isEnabledFor(logging.INFO)

        test_log.setLevel(logging.WARNING)
        assert test_log.level == logging.WARNING
        assert test_log.getEffectiveLevel() == logging.WARNING
        assert test_log.isEnabledFor(logging.WARNING)

        not test_log.setLevel(logging.ERROR)
        assert test_log.level == logging.ERROR
        assert test_log.getEffectiveLevel() == logging.ERROR
        assert test_log.isEnabledFor(logging.ERROR)

        test_log.setLevel(logging.CRITICAL)
        assert test_log.level == logging.CRITICAL
        assert test_log.getEffectiveLevel() == logging.CRITICAL
        assert test_log.isEnabledFor(logging.CRITICAL)

        test_log.setLevel(level=logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert test_log.getEffectiveLevel() == logging.NOTSET
        assert test_log.isEnabledFor(logging.WARNING)

        test_log.setLevel(level=1)
        assert test_log.level == 1
        assert test_log.getEffectiveLevel() == 1
        assert test_log.isEnabledFor(1)

        test_log.setLevel(logging.NOTSET)
        assert test_log.getEffectiveLevel() == logging.NOTSET
        assert test_log.level == logging.NOTSET
        assert test_log.isEnabledFor(logging.WARNING)

    def test_log_level_basic_config(
        self, reset_root_logger_to_python__fixture_func
    ):
        assert logging.root.level != logging.INFO
        logging.basicConfig(level=logging.INFO, force=True)
        assert logging.root.level == logging.INFO

        test_log = logging.getLogger()
        assert test_log.getEffectiveLevel() == logging.INFO
        assert test_log.level == logging.INFO

        logging.basicConfig(level=logging.INFO)
        test_log.setLevel(level=logging.DEBUG)
        assert test_log.level == logging.DEBUG
        assert test_log.getEffectiveLevel() == logging.DEBUG

        test_log.setLevel(level=logging.INFO)
        assert test_log.level == logging.INFO
        assert test_log.getEffectiveLevel() == logging.INFO

        test_log.setLevel(level=logging.WARNING)
        assert test_log.level == logging.WARNING
        assert test_log.getEffectiveLevel() == logging.WARNING

        test_log.setLevel(level=logging.ERROR)
        assert test_log.level == logging.ERROR
        assert test_log.getEffectiveLevel() == logging.ERROR

        test_log.setLevel(level=logging.CRITICAL)
        assert test_log.level == logging.CRITICAL
        assert test_log.getEffectiveLevel() == logging.CRITICAL

        test_log.setLevel(level=logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert test_log.getEffectiveLevel() == logging.NOTSET

        test_log.setLevel(level=1)
        assert test_log.level == 1
        assert test_log.getEffectiveLevel() == 1

        logging.info("info")

    def test_log_level_set(
        self,
        reset_root_logger_to_python__fixture_func
    ):
        test_log = logging.getLogger()
        assert test_log.getEffectiveLevel() == logging.WARNING
        assert test_log.level == logging.WARNING

        test_log.setLevel(logging.NOTSET)
        assert test_log.getEffectiveLevel() == logging.NOTSET
        assert test_log.level == logging.NOTSET

        test_log.setLevel(logging.DEBUG)
        assert test_log.level == logging.DEBUG
        assert test_log.getEffectiveLevel() == logging.DEBUG

        test_log.setLevel(logging.INFO)
        assert test_log.level == logging.INFO
        assert test_log.getEffectiveLevel() == logging.INFO

        test_log.setLevel(logging.WARNING)
        assert test_log.level == logging.WARNING
        assert test_log.getEffectiveLevel() == logging.WARNING

        not test_log.setLevel(logging.ERROR)
        assert test_log.level == logging.ERROR
        assert test_log.getEffectiveLevel() == logging.ERROR

        test_log.setLevel(logging.CRITICAL)
        assert test_log.level == logging.CRITICAL
        assert test_log.getEffectiveLevel() == logging.CRITICAL

        test_log.setLevel(level=logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert test_log.getEffectiveLevel() == logging.NOTSET

        test_log.setLevel(level=1)
        assert test_log.level == 1
        assert 1 == test_log.getEffectiveLevel()

        logging.info("info")
