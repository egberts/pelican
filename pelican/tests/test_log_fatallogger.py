
import logging
import logging_tree
import pelican.log
import pytest


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


def assert_my_root_fatal_logger(new_pelican_logger_instance) -> None:
    assert new_pelican_logger_instance.name == "root"
    assert new_pelican_logger_instance.level == logging.WARNING
    assert new_pelican_logger_instance.manager is not None
    assert new_pelican_logger_instance.manager.loggerClass is None
    assert (str(new_pelican_logger_instance.manager.root) ==
            "<FatalLogger root (WARNING)>")
    assert new_pelican_logger_instance.manager.loggerDict is not []
    assert str(new_pelican_logger_instance.root) == "<FatalLogger root (WARNING)>"
    assert new_pelican_logger_instance.root is not {}
    assert new_pelican_logger_instance.parent is None
    assert new_pelican_logger_instance.propagate is True
    assert new_pelican_logger_instance.filters == []
    idx_nullhandler = None
    idx_nullhandler_lvl = None
    for handle in new_pelican_logger_instance.handlers[:]:
        idx_handler = str(handle)
        if "NullHandle" in str(handle):
            idx_nullhandler = idx_handler
            idx_nullhandler_lvl = handle.level
    assert idx_nullhandler
    assert idx_nullhandler_lvl == logging.NOTSET
    # TODO: Gotta do something about filters and formatters in handlers
    # assert fatal_logger_instant.handlers[].filters == []
    # assert fatal_logger_instant.handlers[].formatter is None


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


class TestLogFatalLogger:

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_logging_tree(self):
        print(logging_tree.printout())

    def test_print_current_logger(self):
        print_logger("current Logger: ", logging.getLogger())

    def test_print_current_root(self):
        print_logger("current RootLogger:", logging.root)

    def test_instantiate_fatal_logger_again(
        self,
    ):
        # Setup, FatalLogger/RootLogger class always default to WARNING
        assert logging.root.level is logging.WARNING
        print_logger("original Logger", logging.getLogger())
        pelican.log.init(level=logging.WARNING)
        print_logger("blank after pelican.log.init:", logging.getLogger())

        new_pelican_logger_instance = logging.getLogger()
        print_logger("fatalLogger:", new_pelican_logger_instance)

        assert_my_root_fatal_logger(new_pelican_logger_instance)

    def test_instantiate_fatal_logger_first_time(
        self,
        reset_root_logger_to_python__fixture_func,
    ):
        # the signature of a virgin rootLogger, as-is, at startup
        assert logging.root.level is None

        # Action
        logging.setLoggerClass(pelican.log.FatalLogger)
        # force root logger to be of our preferred Root class
        logging.getLogger().__class__ = pelican.log.FatalLogger
        pelican.log.init(level=logging.WARNING)
        print_logger("blank after pelican.log.init:", logging.getLogger())
        new_pelican_logger_instance = logging.getLogger()
        print_logger("fatalLogger:", new_pelican_logger_instance)

        # Assert
        assert_my_root_fatal_logger(new_pelican_logger_instance)

    def test_disable_switch(
        self,
        capture_log
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        previous_disable_setting = logging.root.disabled
        logging.root.disabled = True   # Turn off FatalLogger
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()

            logging.critical("Nothing should not get logged")

        assert len(self._caplog.messages) == 0

        logging.root.disabled = previous_disable_setting


class TestLogFataLoggerEarlyExit:
    def test_errors_are_fatal(
        self,
        reset_root_logger_to_python__fixture_func
    ):
        logger_name = "test_log_fatal_logger"
        logging.setLoggerClass(pelican.log.FatalLogger)
        # force root logger to be of our preferred class
        logging.getLogger().__class__ = pelican.log.FatalLogger

        test_logger = logging.getLogger(logger_name)
        pelican.log.init(
            level=logging.ERROR,
            name=logger_name,
            fatal="warnings"
        )
        with pytest.raises(RuntimeError) as sample:
            test_logger.error("this should cause an exception")

        assert sample.type == RuntimeError


class TestLogFatalDisabled:

    @pytest.fixture(scope="function")
    def capture_log(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

    def test_quiet_mode(
        self,
        capture_log
    ):
        assert logging.root.__class__ == pelican.log.FatalLogger
        previous_disable_setting = logging.root.disabled
        logging.root.disabled = True   # Turn off FatalLogger
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()

            logging.critical("Nothing should not get logged")

        assert len(self._caplog.messages) == 0

        logging.root.disabled = previous_disable_setting


if __name__ == '__main__':
    pytest.main()
