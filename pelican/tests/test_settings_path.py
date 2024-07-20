#
#  Focused on settings.py/load_source(), specifically pathlib.Path type
#
# To see collection/ordering of a fixture for a specific function, execute:
#
#  pytest -n0 --setup-plan \
#  test_settings_path.py::TestSettingsLoadSourcePath::test_load_source_arg_missing_fail
#

# Developer Note: RUFF wants '# NOQA: RUF100'
# Developer Note: PyCharm wants '# : RUF100'
# Developer Note: RUFF says PyCharm is a no-go; stay with RUFF,
#                 ignore PyCharm's NOQA orange warnings

import contextlib
import copy
import locale
import logging
import os
import shutil
import tempfile
from pathlib import Path

import filelock
import pytest
from _pytest.logging import LogCaptureHandler, _remove_ansi_escape_sequences  # NOQA

from pelican.settings import (
    load_source,
)

TMP_DIRNAME_SUFFIX = "pelican"

DIRSPEC_RELATIVE = "settings" + os.sep

EXT_PYTHON = ".py"
# EXT_PYTHON_DISABLED = ".disabled"

PC_MODNAME_ACTUAL = "pelicanconf"

# FILENAME_: file name without the extension
PC_FILENAME_DEFAULT = PC_MODNAME_ACTUAL
PC_FILENAME_VALID = "pelicanconf-valid"


# FULLNAME_: filename + extension
PC_FULLNAME_DEFAULT: str = PC_FILENAME_DEFAULT + EXT_PYTHON
PC_FULLNAME_VALID: str = PC_FILENAME_VALID + EXT_PYTHON

logging.basicConfig(level=0)
log = logging.getLogger(__name__)
logging.root.setLevel(logging.DEBUG)
log.propagate = True

# Note: Unittest test setUp/tearDown got replaced by Pytest and its fixtures.
#
# Pytest provides four levels of fixture scopes:
#
#   * Function (Set up and tear down once for each test function)
#   * Class (Set up and tear down once for each test class)
#   * Module (Set up and tear down once for each test module/file)
#   * Session (Set up and tear down once for each test session i.e. comprising
#              one or more test files)
#
# The order of `def` fixtures/functions declarations within a source file
# does not matter, all `def`s can be in forward-reference order or
# backward-referencable.
#
# Weird thing about putting fixture(s) inside a function/procedure argument list
# is that the ordering of its argument DOES NOT matter: this is a block programming
# thing, not like most procedural programming languages.
#
# To see collection/ordering of fixtures, execute:
#
#    pytest -n0 --setup-plan \
#        test_settings_config.py::TestSettingsConfig::test_cs_abs_tmpfile
#
#
# Using class in pytest is a way of aggregating similar test cases together.


@pytest.fixture(scope="session")
def fixture_session_lock(tmp_path_factory):
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / "serial.lock"
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        os.remove(path=lock_file)


@pytest.fixture(scope="module")
def fixture_module_get_tests_dir_abs_path():
    """Get the absolute directory path of `tests` subdirectory

    This pytest module-wide fixture will provide a full directory
    path of this `test_settings_config.py`.

    Note: used to assist in locating the `settings` directory underneath it.

    This fixture gets evoked exactly once (file-wide) due to `scope=module`.

    :return: Returns the Path of the tests directory
    :rtype: pathlib.Path"""
    abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce
    return abs_tests_dirpath


class TestSettingsLoadSourcePath:
    """load_source(), path()"""

    # Provided a file, it should read it, replace the default values,
    # append new values to the settings (if any), and apply basic settings
    # optimizations.

    @pytest.fixture(scope="class")
    def fixture_cls_get_settings_dir_abs_path(
        self, fixture_module_get_tests_dir_abs_path
    ) -> Path:
        """Get the absolute directory path of `tests/settings` subdirectory

        This pytest class-wide fixture will provide the full directory
        path of the `settings` subdirectory containing all the pelicanconf.py files.

        This fixture gets evoked exactly once within its entire class due
        to `scope=class`.

        :return: Returns the Path of the tests directory
        :rtype: pathlib.Path"""
        settings_dirpath: Path = fixture_module_get_tests_dir_abs_path / "settings"
        return settings_dirpath

    @pytest.fixture(scope="function")
    def fixture_func_serial(self, fixture_session_lock):
        """mark function test as serial/sequential ordering

        Include `serial` in the function's argument list ensures
        that no other test(s) also having `serial` in its argument list
        shall run."""
        with fixture_session_lock.acquire(poll_interval=0.1):
            yield

    @pytest.fixture(scope="function")
    def fixture_func_create_tmp_dir_abs_path(
        self,
        fixture_cls_get_settings_dir_abs_path,
        # redundant to specify other dependencies of sub-fixtures here such as:
        #   fixture_cls_get_settings_dir_abs_path
    ):
        """Template the temporary directory

        This pytest function-wide fixture will provide the template name of
        the temporary directory.

        This fixture executes exactly once every time a test case function references
        this via `scope=function`."""
        temporary_dir_path: Path = Path(
            tempfile.mkdtemp(
                dir=fixture_cls_get_settings_dir_abs_path, suffix=TMP_DIRNAME_SUFFIX
            )
        )
        # An insurance policy in case a unit test modified the temporary_dir_path var.
        original_tmp_dir_path = copy.deepcopy(temporary_dir_path)

        yield temporary_dir_path

        shutil.rmtree(original_tmp_dir_path)

    @pytest.fixture(scope="function")
    def fixture_func_ut_wrap(self, fixture_func_create_tmp_dir_abs_path):
        """Unit test wrapper"""
        # old setUp() portion
        self.old_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, "C")
        # each unit test will do the reading of settings
        self.DIRSPEC_ABSOLUTE_TMP = fixture_func_create_tmp_dir_abs_path

        yield
        # old tearDown() portion
        locale.setlocale(locale.LC_ALL, self.old_locale)

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    # Emptiness
    def test_load_source_arg_missing_fail(self):
        """missing arguments; failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source()  # NOQA: RUF100
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    def test_load_source_path_str_one_none_fail(self):
        """one None argument; failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source(None)  # NOQA: RUF100
        assert sample.type == TypeError

    def test_load_source_path_str_one_blank_fail(self):
        """one blank string argument; failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source("")  # NOQA: RUF100
        assert sample.type == TypeError

    def test_load_source_path_str_one_label_name_blank_fail(self):
        """label name, blank string argument; failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source(name="")
        assert sample.type == TypeError

    def test_load_source_path_str_blank_fail(self):
        """blank string argument; failing mode"""
        with pytest.raises(IsADirectoryError) as sample:
            load_source("", "")
        assert sample.type == IsADirectoryError

    def test_load_source_path_arg_str_blank_fail(self):
        """argument name with blank str; failing mode"""
        with pytest.raises(IsADirectoryError) as sample:
            load_source(name="", path="")
        assert sample.type == IsADirectoryError

    def test_load_source_wrong_arg_fail(self):
        """wrong argument name (variant 1); failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source(no_such_arg="reject this")  # NOQA: RUF100
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    def test_load_source_arg_unexpected_fail(self):
        """wrong argument name (variant 2), failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source(pathway="reject this")  # NOQA: RUF100
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    # Module Names, Oh My!
    def test_load_source_module_arg_unexpected_list_fail(self):
        """invalid dict argument type; failing mode"""
        module_list = {}
        with pytest.raises(TypeError) as sample:
            load_source(module_name=module_list)  # NOQA: RUF100
        assert sample.type == TypeError

    def test_load_source_module_path_arg_missing_fail(self):
        """invalid list argument type; failing mode"""
        module_str = ""
        with pytest.raises(TypeError) as sample:
            load_source(module_name=module_str)  # NOQA: RUF100
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    # All About The Paths
    def test_load_source_path_unexpected_type_list_fail(self):
        """invalid dict argument type with argument name; failing mode"""
        path_list = {}
        with pytest.raises(TypeError) as sample:
            load_source(path=path_list)  # NOQA: RUF100
        assert sample.type == TypeError

    def test_load_source_path_unexpected_type_dict_fail(self):
        """invalid list argument type w/ argument name=; failing mode"""
        path_dict = []
        with pytest.raises(TypeError) as sample:
            load_source(path=path_dict)  # NOQA: RUF100
        assert sample.type == TypeError

    def test_load_source_path_unexpected_type_tuple_fail(self):
        """invalid tuple argument type w/ argument name=; failing mode"""
        path_tuple = ()
        with pytest.raises(TypeError) as sample:
            load_source(path=path_tuple)  # NOQA: RUF100
        assert sample.type == TypeError


if __name__ == "__main__":
    # if executing this file alone, it tests this file alone.
    # Can execute from any current working directory
    pytest.main([__file__])

    # more, complex variants of pytest.
    # pytest.main([__file__, "-n0", "-rAw", "--capture=no", "--no-header"])
    # pytest.main([__file__, "-n0"])  # single-process, single-thread
