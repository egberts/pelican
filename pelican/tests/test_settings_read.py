#
# Unit test for `read_settings()` of settings.py
#

# Work with the surprising aspect that config_file argument can
# be a `None` value in read_settings().
#
# Primary purpose is to have a hard-coded default to fall back on.

import copy
import locale
import logging
import os
import sys

# from os.path import abspath, dirname, join
from pathlib import Path

import pytest

from pelican.settings import (
    DEFAULT_CONFIG,
    Settings,
    read_settings,
)

DEFAULT_CONF_FILENAME = "default_conf.py"

logger = logging.Logger(name="test_settings_read", level=0)


@pytest.fixture(scope="session")
def fixture_session_locale():
    """Support the locale"""
    old_locale = locale.setlocale(locale.LC_ALL)
    locale.setlocale(locale.LC_ALL, "C")

    yield

    locale.setlocale(locale.LC_ALL, old_locale)


@pytest.fixture(scope="module")
def fixture_module_get_tests_dir_abs_path():
    """Get the absolute directory path of `tests` subdirectory

    This pytest module-wide fixture will provide a full directory
    path to this `test_settings_read.py` file.

    This fixture gets evoked exactly once (file-wide) due to `scope=module`.

    :return: Returns the Path of the tests directory
    :rtype: pathlib.Path"""
    abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce

    return abs_tests_dirpath


def absolute_settings_path_setting(
    base_path: Path, settings: Settings, item: str, subdir: str
):
    if settings[item] is not None and settings[item] != "":
        abs_path = base_path / subdir
    settings[item] = str(abs_path)


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


def make_it_pass_settings(previous: Settings, current: Settings):
    # Do we have a problem stomping some defaults to pass this test, is this ok?
    previous["PLUGINS"] = []
    if previous["THEME"] is not None:
        abs_pelican_path = Path(Path(__file__).parent).parent
        abs_theme_path = abs_pelican_path / "themes" / previous["THEME"]
        previous["THEME"] = str(abs_theme_path)
    # if previous['PATH'] == ".":
    #     previous['PATH'] = Path(previous['PATH']).absolute()
    return previous, current


class TestSettingsReadNonModule:
    @pytest.fixture(scope="function")
    def fixture_func_read_settings(
        self, fixture_session_locale, fixture_module_get_tests_dir_abs_path
    ):
        self.PATH = fixture_module_get_tests_dir_abs_path
        default_conf = os.path.join(self.PATH, DEFAULT_CONF_FILENAME)
        self.settings = read_settings(default_conf, reload=False)

        yield

        del sys.modules["pelicanconf"]

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

    def test_no_arguments_pass(self):
        """No argument used; default configuration; passing mode"""
        # Do not be stomping on default settings in the code
        previous: Settings = copy.deepcopy(DEFAULT_CONFIG)

        current: Settings = read_settings()

        fudge_previous, fudge_current = make_it_pass_settings(previous, current)
        assert_difference_in_settings(fudge_previous, fudge_current)
        assert fudge_previous == fudge_current

    def test_no_config_file_pass(self):
        """`None` argument used; default configuration; passing mode"""
        # Do not be stomping on default settings in the code
        previous: Settings = copy.deepcopy(DEFAULT_CONFIG)

        current: Settings = read_settings(None)
        fudge_previous, fudge_current = make_it_pass_settings(previous, current)

        assert_difference_in_settings(fudge_previous, fudge_current)
        assert fudge_previous == fudge_current

    def test_no_config_file_multiple_load_pass(self):
        """`None` argument used; multiple default configuration; passing mode"""
        # Reload is a NO-OP since no valid file/module were given; this is a pass
        # Do not be stomping on default settings in the code
        previous: Settings = copy.deepcopy(DEFAULT_CONFIG)

        interim: Settings = read_settings(None)
        fudge_previous, fudge_interim = make_it_pass_settings(previous, interim)
        assert_difference_in_settings(fudge_previous, fudge_interim)

        current: Settings = read_settings(None)
        # do not change [fudge_]interim (just faux-change previous again)
        assert_difference_in_settings(fudge_interim, current)

        assert fudge_previous == current

    @pytest.mark.skip()  # TODO Issue #09004
    def test_no_config_file_reload_pass(self):
        """`None` argument used; reload; default configuration; passing mode"""
        # Reload is a NO-OP since no valid file/module were given; this is a pass
        # Do not be stomping on default settings in the code
        previous: Settings = copy.deepcopy(DEFAULT_CONFIG)

        interim: Settings = read_settings(None, reload=False)
        fudge_previous, fudge_interim = make_it_pass_settings(previous, interim)
        assert_difference_in_settings(fudge_previous, fudge_interim)

        current: Settings = read_settings(None, reload=True)
        # do not change [fudge_]interim (just faux-change previous again)
        assert_difference_in_settings(fudge_interim, current)

        assert fudge_previous == current

    def test_default_config_file_pass(
        self,
        fixture_module_get_tests_dir_abs_path,
        fixture_cls_get_settings_dir_abs_path,
    ):
        """`None` argument used; reload; default configuration; passing mode"""
        # Do not be stomping on default settings in the code
        previous = copy.deepcopy(DEFAULT_CONFIG)
        test_data_dir = fixture_module_get_tests_dir_abs_path
        settings_dir = fixture_cls_get_settings_dir_abs_path
        pelican_dir = test_data_dir.parent.parent
        default_config_file = test_data_dir / "settings" / "pelicanconf-default.py"
        absolute_settings_path_setting(pelican_dir, previous, "PATH", "content")
        absolute_settings_path_setting(settings_dir, previous, "OUTPUT_PATH", "output")
        absolute_settings_path_setting(settings_dir, previous, "CACHE_PATH", "cache")

        current: Settings = read_settings(default_config_file)

        assert_difference_in_settings(previous, current)
        assert previous == current

    def test_read_empty_settings(self):
        # Ensure an empty settings file results in default settings.
        settings = read_settings(None)
        expected = copy.deepcopy(DEFAULT_CONFIG)
        # Added by configure settings
        expected["FEED_DOMAIN"] = ""
        expected["ARTICLE_EXCLUDES"] = ["pages"]
        expected["PAGE_EXCLUDES"] = [""]
        self.maxDiff = None
        assert settings == expected

    def test_settings_return_independent(self):
        # Make sure that the results from one settings call doesn't
        # effect past or future instances.
        self.PATH = os.path.abspath(os.path.dirname(__file__))
        default_conf = os.path.join(self.PATH, "default_conf.py")
        settings = read_settings(default_conf)
        settings["SITEURL"] = "new-value"
        new_settings = read_settings(default_conf)
        assert new_settings["SITEURL"] != settings["SITEURL"]

    def test_defaults_not_overwritten(self):
        # This assumes 'SITENAME': 'A Pelican Blog'
        settings = read_settings(None)
        settings["SITENAME"] = "Not a Pelican Blog"
        assert settings["SITENAME"] != DEFAULT_CONFIG["SITENAME"]


class TestSettingsReadPast:
    @pytest.fixture(scope="function")
    def fixture_func_read_settings(
        self, fixture_session_locale, fixture_module_get_tests_dir_abs_path
    ):
        self.PATH = fixture_module_get_tests_dir_abs_path
        default_conf = os.path.join(self.PATH, DEFAULT_CONF_FILENAME)
        self.settings = read_settings(default_conf)

        yield

        del sys.modules["pelicanconf"]


if __name__ == "__main__":
    # if executing this file alone, it tests this file alone.
    # Can execute from any current working directory
    pytest.main([__file__])

    # more, complex variants of pytest.
    # pytest.main([__file__, "-n0", "-rAw", "--capture=no", "--no-header"])
    # pytest.main([__file__, "-n0"])  # single-process, single-thread

# Python: Minimum required versions: 3.6  (vermin v1.6.0)
# Python: Incompatible versions:     2
