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


def log_print_tree(title=""):
    print(f"{title}:\n")
    logging_tree.printout()
    print("\n")


def print_logger(title: str, this_logger: logging.Logger) -> logging.Logger:
    print(f"\nLogger fields for {title}")
    print(f"{title}: Logger: ", this_logger)
    if hasattr(this_logger, "name"):
        print(f"{title}: Name: {this_logger.name}")
    else:
        print("Name: None")
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
            print(f"{title}: Handler.formatter: ", this_logger.formatter)
        else:
            print(f"{title}: handlers.formatter: None")
    else:
        print(f"{title}: Logger.handlers: None")
    return this_logger.manager.root


def reset_logging_handlers():
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


@pytest.fixture(scope="function")
def logger_attributes_before_after__fixture_func():
    test_log = print_logger("Logger (before)", logging.Logger)
    yield test_log
    print_logger("Logger (after)", logging.Logger)


@pytest.fixture(scope="function")
def root_logger_attributes_before_after__fixture_func(
    logger_attributes_before_after__fixture_func,
):
    root_log = print_logger("root (before)", logging.Logger.root)
    yield root_log
    print_logger("root (after)", logging.Logger.root)


@pytest.fixture(scope="function")
def log_class_root_virgin(root_logger_attributes_before_after__fixture_func):
    """Undo any custom RootLogger"""
    original_logger_class = logging.getLoggerClass()
    logging.setLoggerClass(logging.RootLogger)
    # force Rootlogger to be of our preferred class for future instantiation
    # Undo Pelican's forced FatalLogger root class
    logging.getLogger().__class__ = logging.RootLogger
    # Blow away all the 38+ loggers outside of Pelican
    logging.root.manager.loggerDict = {}
    # reset_logging_handlers()  # TODO gotta put this somewhere else

    yield

    logging.setLoggerClass(original_logger_class)


@pytest.fixture(scope="function")
def log_class_original__fixture_func(
    log_class_root_virgin, root_logger_attributes_before_after__fixture_func
):
    """Restore a root instance of a virgin logging.Logger class"""

    # logging.basicConfig(force=True) does NOT work on the root logger
    reset_logging_handlers()
    assert logging.getLogger().handlers == []

    # Prove that we got virgin "ROOT" logging again
    test_log = root_logger_attributes_before_after__fixture_func
    print("test_log: ", id(test_log), test_log)

    # first, replace the Root logging class
    logging.getLogger().__class__ = logging.RootLogger
    assert logging.RootLogger == logging.root.__class__

    # Then set the RootLogger default to WARNING
    logging.root = logging.RootLogger(level=logging.WARNING)
    assert "<RootLogger root (WARNING)>" == str(logging.root)

    assert logging.getLogger().name == "root"
    assert not logging.getLogger().hasHandlers()
    assert logging.getLogger().propagate
    assert logging.getLogger().handlers == []
    assert logging.getLogger().filters == []
    assert logging.getLogger().parent is None
    # There is no "level" in root logger.

    logging.root.manager.loggerDict = {}
    assert logging.root.manager.loggerDict == {}

    assert "<class 'logging.RootLogger'>" == str(logging.getLogger().root.__class__)

    # Defer this instantiation of a Logger class toward the next fixture

    yield

    reset_logging_handlers()
    print(
        "\n3 logging.getLogger().root.__class__: ", logging.getLogger().root.__class__
    )


@pytest.fixture(scope="function")
def instantiate_logger_class_original__fixture_func(log_class_original__fixture_func):
    """First step to instantiating a Logger class"""
    assert logging.root.manager.loggerDict == {}

    # Make sure there is no root logger, like Pelican FatalLogging
    assert logging.RootLogger == logging.Logger.root.__class__
    assert type == logging.Logger.__class__
    # this is the stage after 'import logging' (except for logging.Manager)
    assert logging.RootLogger == logging.getLogger().__class__

    # extraneous asserts?
    assert logging.RootLogger == logging.root.__class__
    assert logging.root.manager.loggerDict == {}

    # logging.basicConfig(force=True) does NOT work on the root logger
    # logging.basicConfig(force=True) only works AFTER instantiating logging.getLogger()

    # Make sure it is 'logging.Logger()' class before instantiation
    # TODO: What assert can I use here at this point after RootLogger restoration?

    # the instantiation stage of Logger()
    # TODO: Somehow, getLogger() is pulling in pelican.log.fatalLogger instead of
    #  rootLogger() here.  logging.manager.getLogger(), that is who.
    #  more specifically, logging.root.manager.loggerDict[]
    #  PyCharm is also top-hooking Logger class from
    #   /opt/pycharm/pycharm-community-2023.1/plugins/python-ce/helpers/typeshed/stdlib/logging/__init.pyi
    #  PyCharm logging also subclass logging.Logger via
    #    /usr/lib/python3.11/logging/__init__.py
    assert logging.getLogger(__name__).__class__ == logging.Logger
    logging.basicConfig(level=logging.WARNING, force=True)
    assert logging.getLogger(__name__).__class__ == logging.Logger
    test_logger: logging.Logger = logging.getLogger(__name__)
    assert logging.getLogger(__name__).__class__ == logging.Logger

    assert isinstance(test_logger, logging.Logger)

    # It is interesting to note that `name=` in logging.getLogger can look up
    # previous instantiations of Logger subclasses and classes.
    print("test_logger.__class__: ", test_logger.__class__)
    print(
        "logging.getLogger(__name__).__class__: ", logging.getLogger(__name__).__class__
    )
    assert test_logger.__class__ == logging.getLogger(__name__).__class__
    print("test_logger.__class__: ", test_logger.__class__)

    # logging.setLoggerClass(logging.Logger)

    assert logging.getLogger(__name__).__class__ == logging.Logger
    assert str(logging.getLogger(__name__)) == "<Logger root (WARNING)>"

    # CRITICAL: Newly-created logging.Logger class are always initialized at
    # level NOTSET; still logs the WARNINGs or higher (starts
    # filtering at INFO or lower)
    assert logging.NOTSET == test_logger.level
    assert logging.WARNING == test_logger.getEffectiveLevel()
    assert (
        logging.getLoggerClass(__name__).root.__class__
        == logging.RootLogger(logging.WARNING).__class__
    )
    # basicLogging(level=) changes levels for both

    print("3 logger.root.manager.loggerDict[]: ", logging.root.manager.loggerDict)
    yield test_logger

    # deleting a logging.Logger class is not permanent, permanent but do it anyway
    # hence, restore things back to the way it were before next unit test.
    test_logger.setLevel(logging.NOTSET)
    assert logging.WARNING == test_logger.getEffectiveLevel()


@pytest.fixture(scope="function")
def instantiate_logger_class_pelican__fixture_func(log_class_original__fixture_func):
    """First step to instantiating a Logger class"""
    # Make sure there is no root logger, like Pelican FatalLogging
    assert logging.RootLogger == logging.Logger.root.__class__
    assert type == logging.Logger.__class__
    # this is the stage after 'import logging'
    # assert pelican.log.FatalLogger == logging.getLogger().__class__

    # CRITICAL: Newly-created logging.Logger class are always initialized at
    # level NOTSET; still logs the WARNINGs or higher (starts
    # filtering at INFO or lower)
    # assert logging.NOTSET == test_log.level
    # assert logging.WARNING == test_log.getEffectiveLevel()
    # basicLogging(level=) changes levels for both

    # deleting a logging.Logger class is not permanent, permanent but do it anyway
    # hence, restore things back to the way it were before next unit test.
    # test_log.setLevel(logging.NOTSET)
    # assert logging.WARNING == test_log.getEffectiveLevel()


# A special `logging.getLoggerClass()` is passed to the `TestLogBasic`
# ensuring that the original `logger` is used here (and not this file):
#### class TestLogBasic(logging.getLoggerClass()):


class TestLogBasic:
    def test_surround(self, root_logger_attributes_before_after__fixture_func):
        root_logger_attributes_before_after__fixture_func

    def test_init_root(self, log_class_original__fixture_func):
        print(logging_tree.printout())

    def test_current_root_details(self, log_class_root_virgin):
        print_logger("root (before)", logging.Logger.root)

    def test_current_logger_details(self):
        print_logger("current", logging.Logger)

    def test_log_level_set(self, log_class_original__fixture_func):
        """Understand All This Before Log UUT"""
        test_log = log_class_original__fixture_func
        # Newly created LogLogger class should be NOTSET yet operate at WARNING
        assert logging.NOTSET == test_log.level
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.WARNING)

        test_log.setLevel(logging.NOTSET)
        assert logging.NOTSET == test_log.level
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.WARNING)

        test_log.setLevel(logging.DEBUG)
        assert test_log.level == logging.DEBUG
        assert logging.DEBUG == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.DEBUG)

        test_log.setLevel(logging.INFO)
        assert test_log.level == logging.INFO
        assert logging.INFO == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.INFO)

        test_log.setLevel(logging.WARNING)
        assert test_log.level == logging.WARNING
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.WARNING)

        not test_log.setLevel(logging.ERROR)
        assert test_log.level == logging.ERROR
        assert logging.ERROR == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.ERROR)

        test_log.setLevel(logging.CRITICAL)
        assert test_log.level == logging.CRITICAL
        assert logging.CRITICAL == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.CRITICAL)

        test_log.setLevel(level=logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(logging.WARNING)

        test_log.setLevel(level=1)
        assert test_log.level == 1
        assert 1 == test_log.getEffectiveLevel()
        assert test_log.isEnabledFor(1)

        test_log.setLevel(logging.NOTSET)
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert logging.NOTSET == test_log.level
        assert test_log.isEnabledFor(logging.WARNING)

    def test_log_level_basic_config(
        self, instantiate_logger_class_original__fixture_func
    ):
        test_log = instantiate_logger_class_original__fixture_func
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert logging.NOTSET == test_log.level

        logging.basicConfig(level=logging.INFO)
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert test_log.level == logging.NOTSET

        logging.basicConfig(level=logging.INFO)
        test_log.setLevel(level=logging.DEBUG)
        assert test_log.level == logging.DEBUG
        assert logging.DEBUG == test_log.getEffectiveLevel()

        test_log.setLevel(level=logging.INFO)
        assert test_log.level == logging.INFO
        assert logging.INFO == test_log.getEffectiveLevel()

        test_log.setLevel(level=logging.WARNING)
        assert test_log.level == logging.WARNING
        assert logging.WARNING == test_log.getEffectiveLevel()

        test_log.setLevel(level=logging.ERROR)
        assert test_log.level == logging.ERROR
        assert logging.ERROR == test_log.getEffectiveLevel()

        test_log.setLevel(level=logging.CRITICAL)
        assert test_log.level == logging.CRITICAL
        assert logging.CRITICAL == test_log.getEffectiveLevel()

        test_log.setLevel(level=logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert logging.WARNING == test_log.getEffectiveLevel()

        test_log.setLevel(level=1)
        assert test_log.level == 1
        assert 1 == test_log.getEffectiveLevel()

        logging.info("info")

    def test_log_level_set(self, instantiate_logger_class_original__fixture_func):
        test_log = instantiate_logger_class_original__fixture_func
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert logging.NOTSET == test_log.level

        test_log.setLevel(logging.NOTSET)
        assert logging.WARNING == test_log.getEffectiveLevel()
        assert logging.NOTSET == test_log.level

        test_log.setLevel(logging.DEBUG)
        assert test_log.level == logging.DEBUG
        assert logging.DEBUG == test_log.getEffectiveLevel()

        test_log.setLevel(logging.INFO)
        assert test_log.level == logging.INFO
        assert logging.INFO == test_log.getEffectiveLevel()

        test_log.setLevel(logging.WARNING)
        assert test_log.level == logging.WARNING
        assert logging.WARNING == test_log.getEffectiveLevel()

        not test_log.setLevel(logging.ERROR)
        assert test_log.level == logging.ERROR
        assert logging.ERROR == test_log.getEffectiveLevel()

        test_log.setLevel(logging.CRITICAL)
        assert test_log.level == logging.CRITICAL
        assert logging.CRITICAL == test_log.getEffectiveLevel()

        test_log.setLevel(level=logging.NOTSET)
        assert test_log.level == logging.NOTSET
        assert logging.WARNING == test_log.getEffectiveLevel()

        test_log.setLevel(level=1)
        assert test_log.level == 1
        assert 1 == test_log.getEffectiveLevel()

        logging.info("info")
