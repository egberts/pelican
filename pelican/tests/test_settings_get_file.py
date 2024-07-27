#
#  Unit tests for `get_settings_from_file()` in settings.py
#
# def get_settings_from_file(conf_file: str, reload: bool) -> Settings:
"""Loads module from a file then clones dictionary of settings from that module.

:param conf_file: Attempts to load a module using a file specification (absolute or
                 relative) then returns a clone-duplicate of its settings found in
                 the module.  If no module (`None`) is given, then default module
                 name is used.
:param conf_file: A file specification (absolute or relative) that points to the
                 Python script file containing the keyword/value assignment settings.
:param reload:  A bool value to check if module is already preloaded
                    before doing a reload.
:return: Returns a dictionary of Settings found in that Python module.
:rtype: Settings"""

import contextlib
import copy
import locale
import logging
import os
import sys
from pathlib import Path

import filelock
import pytest

from pelican.settings import (
    DEFAULT_CONFIG,
    Settings,
    get_settings_from_file,
)

# PC_ = Pelican Configuration or PELICANCONF or pelicanconf
# MODNAME_ = Module name
PC_MODNAME_DEFAULT = "pelicanconf"  # used if module_name is blank

# FILENAME_: file name without the extension
PC_FILENAME_DEFAULT = "pelicanconf"  # after any PyPA canonicalization


logger = logging.Logger(name=__file__, level=0)


@pytest.fixture(scope="session")
def fixture_session_locale():
    """Support the locale"""
    old_locale = locale.setlocale(locale.LC_ALL)
    locale.setlocale(locale.LC_ALL, "C")

    yield

    locale.setlocale(locale.LC_ALL, old_locale)


@pytest.fixture(scope="session")
def fixture_session_lock(tmp_path_factory):
    """Provide a locking file specific to this test session (per pytest)"""
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / "serial.lock"
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        os.remove(path=lock_file)


@pytest.fixture(scope="session", autouse=True)
def fixture_session_module_integrity(fixture_session_lock):
    """Ensure that `sys.modules` is intact after all unit tests in this module"""
    saved_sys_modules = sys.modules
    yield
    if not (saved_sys_modules == sys.modules):
        raise AssertionError(f"Entire {__file__} failed to preserve sys.modules.")


@pytest.fixture(scope="module")
def fixture_module_get_tests_dir_abs_path():
    """Get the absolute directory path of `tests` subdirectory

    This pytest module-wide fixture will provide a full directory
    path to this `test_settings_module.py` file.

    Note: used to assist in locating the `settings` directory underneath it.

    This fixture gets evoked exactly once (file-wide) due to `scope=module`.

    :return: Returns the Path of the `tests/` directory
    :rtype: pathlib.Path"""
    abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce
    yield Path(abs_tests_dirpath)


def assert_difference_in_settings(previous: Settings, current: Settings):
    if previous != current:
        # Break down the difference(s)
        for this_item in previous:
            if this_item not in current:
                logger.error(f"Item {this_item} not in current settings: ")
            logger.error(f"  Previous item {this_item}: '{previous[this_item]}'.")
            assert this_item in current
        for this_item in current:
            if this_item not in previous:
                logger.error(f"Item {this_item} not in previous settings: ")
            logger.error(f"  Current item {this_item}: '{current[this_item]}'.")
            assert this_item in previous
        # Break down the difference(s)
        for this_item in previous:
            if previous[this_item] != current[this_item]:
                logger.error(
                    f"Item {this_item} not the same between previous "
                    "and current settings: "
                )
                logger.error(f"  Previous item {this_item}: '{previous[this_item]}'.")
                logger.error(f"  Current item {this_item}: '{current[this_item]}'.")
            assert previous[this_item] == current[this_item]


def module_expected_in_sys_modules(module_name: str) -> bool:
    """Ensure that its module is still in `sys.modules`."""
    if module_name in sys.modules:
        return True
    raise AssertionError(f"Module {module_name} no longer is in sys.modules[].")


def module_not_expected_in_sys_modules(module_name: str) -> bool:
    """Not expecting its module left behind in `sys.modules`."""
    if module_name not in sys.modules:
        return True
    raise AssertionError(f"Module {module_name} unexpectedly now in sys.modules[].")


class TestSettingsGetFile:
    """get_settings_from_file()"""

    @pytest.fixture(scope="class")
    def fixture_cls_get_settings_dir_abs_path(
        self, fixture_module_get_tests_dir_abs_path
    ) -> Path:
        """Get the absolute directory path of `tests/settings` subdirectory

        This pytest class-wide fixture will provide the full directory
        path of the `settings` subdirectory containing all the pelicanconf.py files.

        This fixture gets evoked exactly once within its entire class due
        to `scope=class`.

        :return: Returns the absolute Path of the tests directory
        :rtype: pathlib.Path"""
        settings_dirpath: Path = fixture_module_get_tests_dir_abs_path / "settings"
        return settings_dirpath

    def test_no_argument(self):
        with pytest.raises(TypeError) as sample:
            get_settings_from_file()
        assert sample.type == TypeError

    def test_none_argument(self):
        with pytest.raises(TypeError) as sample:
            get_settings_from_file(None)  # NOQA: RUF100
        assert sample.type == TypeError

    def test_default_argument(
        self,
        fixture_cls_get_settings_dir_abs_path,
        fixture_session_module_integrity,
        fixture_session_lock,
    ):
        previous: Settings = copy.deepcopy(DEFAULT_CONFIG)
        default_conf = fixture_cls_get_settings_dir_abs_path / "pelicanconf-default.py"
        if not default_conf.is_file():
            logger.error(f"Unable to read this configuration {default_conf} file.")
        # cheat
        content_path = "content"
        if previous["PATH"] is not None:
            content_path = Path(Path(Path(__file__).parent).parent).parent / "content"
        previous["PATH"] = str(content_path)
        if previous["THEME"] is not None:
            theme_path = "notmyidea"
            previous["THEME"] = theme_path

        current: Settings = get_settings_from_file(str(default_conf))

        assert_difference_in_settings(previous, current)
        assert previous == current

        if module_expected_in_sys_modules("pelicanconf-default"):  # TODO Issue #09001
            del sys.modules["pelicanconf-default"]
        module_not_expected_in_sys_modules("pelicanconf-default")


if __name__ == "__main__":
    # if executing this file alone, it tests this file alone.
    # Can execute from any current working directory
    pytest.main([__file__])

    # more, complex variants of pytest.
    # pytest.main([__file__, "-n0", "-rAw", "--capture=no", "--no-header"])
    # pytest.main([__file__, "-n0"])  # single-process, single-thread

# Python: Minimum required versions: 3.6  # vermin (v1.6.0)
# Python: Incompatible versions:     2
