#
#  Focused on settings.py/load_source(), specifically syntax error handling
#
# Minimum version: Python 3.6 (tempfile.mkdtemp())
# Minimum version: Pytest 4.0, Python 3.8+
#
# To see collection/ordering of a fixture for a specific function, execute:
#
#  pytest -n0 --setup-plan \
#  test_settings_syntax.py::TestSettingsSyntax::test_load_source_syntax_indent


import contextlib
import copy
import errno
import inspect
import locale
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

import filelock
import pytest

from pelican.settings import (
    load_source,
)

TMP_DIRNAME_SUFFIX = "pelican"

# Valid Python file extension
EXT_PYTHON = ".py"
EXT_PYTHON_DISABLED = ".disabled"

# DIRSPEC_: where all the test config files are stored
# we hope that current working directory is always in pelican/pelican/tests
DIRSPEC_CURRENT: str = os.getcwd()
DIRSPEC_DATADIR: str = "settings" + os.sep
DIRSPEC_RELATIVE: str = DIRSPEC_DATADIR  # reuse 'tests/settings/' as scratch area

# PC_ = Pelican Configuration or PELICANCONF or pelicanconf
# FILENAME_: file name without the extension
PC_FILENAME_DEFAULT = "pelicanconf"
PC_FILENAME_VALID = "pelicanconf-valid"
PC_FILENAME_NOTFOUND = "pelicanconf-not-found"
PC_FILENAME_UNREADABLE = "pelicanconf-unreadable"
PC_FILENAME_SYNTAX_ERROR = "pelicanconf-syntax-error"

# MODNAME_ = Module name
PC_MODNAME_DEFAULT = "pelicanconf"  # used if module_name is blank
PC_MODNAME_VALID = "pelicanconf_valid"
PC_MODNAME_NOT_FOUND = "pelicanconf_not_found"
PC_MODNAME_UNREADABLE = "pelicanconf_unreadable"
PC_MODNAME_DOTTED = "non_existing_module.cannot_get_there"  # there is a period
PC_MODNAME_SYNTAX_ERROR = "pelicanconf_syntax_error"
PC_MODNAME_SYS_BUILTIN = "calendar"

# Iterators, for fixtures
PC_MODULES_EXPECTED = {PC_MODNAME_SYS_BUILTIN}
PC_MODULES_TEST = {
    PC_MODNAME_DEFAULT,
    PC_MODNAME_VALID,
    PC_MODNAME_NOT_FOUND,
    PC_MODNAME_UNREADABLE,
    PC_MODNAME_DOTTED,
    PC_MODNAME_SYNTAX_ERROR,
}

TMP_FILENAME_SUFFIX = PC_FILENAME_DEFAULT

# FULLNAME_: filename + extension
PC_FULLNAME_VALID: str = PC_FILENAME_VALID + EXT_PYTHON
PC_FULLNAME_NOTFOUND: str = PC_FILENAME_NOTFOUND + EXT_PYTHON
PC_FULLNAME_UNREADABLE: str = PC_FILENAME_UNREADABLE + EXT_PYTHON
PC_FULLNAME_SYNTAX_ERROR: str = PC_FILENAME_SYNTAX_ERROR + EXT_PYTHON
# BLOB_: a file trying to hide from ruff/black syntax checkers for our syntax tests
BLOB_FULLNAME_SYNTAX_ERROR = PC_FULLNAME_SYNTAX_ERROR + EXT_PYTHON_DISABLED

# DIRNAME_: a construct of where to find config file for specific test
PC_DIRNAME_NOTFOUND: str = "no-such-directory"
PC_DIRNAME_NOACCESS: str = "unreadable-directory"

# DIRSPEC_: the full directory path

# Our test files
BLOB_FILESPEC_UNREADABLE = Path(DIRSPEC_DATADIR) / PC_FULLNAME_UNREADABLE
BLOB_FILESPEC_SYNTAX_ERROR = Path(DIRSPEC_DATADIR) / str(
    PC_FULLNAME_SYNTAX_ERROR + EXT_PYTHON_DISABLED
)

# PATH_: the final path for unit tests here
# FILESPEC_: the full path + filename + extension
# REL_: relative path
RO_FILESPEC_REL_VALID_PATH = Path(DIRSPEC_DATADIR) / PC_FULLNAME_VALID
RO_FILESPEC_REL_SYNTAX_ERROR_PATH = Path(DIRSPEC_DATADIR) / PC_FULLNAME_SYNTAX_ERROR
RO_FILESPEC_REL_NOTFOUND_PATH = Path(DIRSPEC_DATADIR) / PC_FULLNAME_NOTFOUND
# FILESPEC_REL_UNREADABLE_PATH = Path(DIRSPEC_RELATIVE) / PC_FULLNAME_UNREADABLE

# SyntaxError placement for use with settings/pelicanconf-syntax-error.py
SM_UT_SYNTAX1_LINENO = 5
SM_UT_SYNTAX1_OFFSET = 1

load_source_argument_count = 2

# Code starts here
logging.basicConfig(level=0)
log = logging.getLogger(__name__)
logging.root.setLevel(logging.DEBUG)
log.propagate = True

args = inspect.getfullargspec(load_source)
if ("name" not in args.args) and (args.args.__len__ != load_source_argument_count):
    # Skip this entire test file if load_source() only supports 1 argument
    pytest.skip(
        "this class is only used with load_source() having "
        "support for a 'module_name' argument"
    )

# We need an existing Python system built-in module for testing load_source.
if PC_MODNAME_SYS_BUILTIN not in sys.modules:
    pytest.exit(
        errno.EACCES,
        "PC_MODNAME_SYS_BUILTIN variable MUST BE an existing system "
        "builtin module; this test is aborted",
    )

# Oppositional, PC_MODNAME_DEFAULT must NOT be a pre-existing system built-in module
if PC_MODNAME_DEFAULT in sys.modules:
    # We are not authorized to tamper outside our test area
    pytest.exit(
        errno.EACCES,
        f" Cannot reuses a system built-in module {PC_MODNAME_DEFAULT};"
        " this test is aborted",
    )


##########################################################################
#  session-based and module-based fixtures
##########################################################################
@pytest.fixture(scope="session", autouse=True)
def fixture_session_module_integrity(fixture_session_lock):
    """Ensure that `sys.modules` is intact after all unit tests in this module"""
    saved_sys_modules = sys.modules
    yield
    if not (saved_sys_modules == sys.modules):
        raise AssertionError(f"Entire {__file__} failed to preserve sys.modules.")


@pytest.fixture(scope="session")
def fixture_session_lock(tmp_path_factory):
    """Provide a locking file specific to this test session (per pytest)"""
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / "serial.lock"
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        os.remove(path=lock_file)


@pytest.fixture(scope="session")
def fixture_session_locale():
    """Load/unload the locale"""
    old_locale = locale.setlocale(locale.LC_ALL)
    locale.setlocale(locale.LC_ALL, "C")

    yield

    locale.setlocale(locale.LC_ALL, old_locale)


@pytest.fixture(scope="module")
def fixture_module_get_tests_dir_abs_path():
    """Get the absolute directory path of `tests` subdirectory

    This pytest module-wide fixture will provide a full directory
    path to this `test_settings_syntax.py`.

    Note: used to assist in locating the `settings` directory underneath it.

    This fixture gets evoked exactly once (file-wide) due to `scope=module`.

    :return: Returns the Path of the tests directory
    :rtype: pathlib.Path"""
    abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce
    yield Path(abs_tests_dirpath)


##########################################################################
#  module-specific (test_settings_syntax.py) functions
##########################################################################


def module_expected_in_sys_modules(module_name: str) -> bool:
    if module_name in sys.modules:
        return True
    raise AssertionError(f"Module {module_name} no longer is in sys.modules[].")


def module_not_expected_in_sys_modules(module_name: str) -> bool:
    if module_name not in sys.modules:
        return True
    raise AssertionError(f"Module {module_name} unexpectedly now in sys.modules[].")


def check_module_integrity():
    # Check if any modules were left behind by previous unit test(s).
    for not_expected_module in PC_MODULES_TEST:
        module_not_expected_in_sys_modules(not_expected_module)

    # Now check that we did not lose any critical/built-in module.
    for expected_module in PC_MODULES_EXPECTED:
        module_expected_in_sys_modules(expected_module)


##########################################################################
#  All about the handling of module name
##########################################################################
class TestSettingsSyntax:
    """load_source() with focus on Syntax Handling"""

    ##########################################################################
    #  Per-class fixtures with focus on module name
    ##########################################################################

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Save the console output by logger"""
        self._caplog = caplog

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

    @pytest.fixture(scope="class")
    def fixture_cls_get_settings_dir_rel_path(
        self, fixture_module_get_tests_dir_abs_path
    ) -> Path:
        """Get the relative directory path of `tests/settings` subdirectory

        This pytest class-wide fixture will provide the relative directory
        path of the `settings` subdirectory containing all the pelicanconf.py files,
        based off of its own current working directory.

        This fixture gets evoked exactly once within its entire class due
        to `scope=class`.

        :return: Returns the relative Path of the tests directory
        :rtype: pathlib.Path"""
        settings_dirpath: Path = (
            fixture_module_get_tests_dir_abs_path / "settings"
        )  # TODO work your relative magic here
        return settings_dirpath

    ##########################################################################
    #  Function-specific (per unit test) fixtures with focus on module name
    ##########################################################################

    @pytest.fixture(scope="function")
    def fixture_func_module_integrity(self, fixture_session_lock):
        check_module_integrity()
        yield
        check_module_integrity()

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
        fixture_session_locale,  # temporary directory could have internationalization
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
    def fixture_func_create_tmp_dir_rel_path(
        # TODO work your magic here for relative path
        self,
        fixture_session_locale,  # temporary directory could have internationalization
        fixture_cls_get_settings_dir_abs_path,
        # redundant to specify other dependencies of sub-fixtures here such as:
        #   fixture_cls_get_settings_dir_abs_path
    ):
        """Template the temporary directory, in relative path format

        This pytest function-wide fixture will provide the template name of
        the temporary directory in relative path format.

        This fixture executes exactly once every time a test case function references
        this via `scope=function`."""
        temporary_dir_path: Path = Path(
            tempfile.mkdtemp(
                dir=fixture_cls_get_settings_dir_abs_path, suffix=TMP_DIRNAME_SUFFIX
            )
        )

        yield temporary_dir_path

    ######################################################################
    #  fixture_func_ut_wrap is a wrapper of all fixtures commonly
    #  needed by all unit function/test cases
    ######################################################################
    @pytest.fixture(scope="function")
    def fixture_func_ut_wrap(
        self,
        fixture_session_locale,  # internationalization
        fixture_session_lock,  # serialization of unit test cases
        fixture_func_module_integrity,  # sys.modules
        fixture_cls_get_settings_dir_abs_path,  # tests/settings
        # each test declares their own fixture_func_create_tmp_dir_[rel|abs]_path
    ):
        yield

    ##########################################################################
    #  Test cases with focus on syntax handling of Python file
    ##########################################################################

    def test_load_source_module_str_rel_syntax_error_fail(
        self, fixture_func_create_tmp_dir_rel_path, fixture_func_ut_wrap
    ):
        """syntax error, relative path, str type; failing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        default_module = (
            "pelicanconf-syntax-error"  # TODO Issue #09001 # PC_MODNAME_DEFAULT
        )
        module_not_expected_in_sys_modules(default_module)
        # copy "pseudo-script" file into 'settings/pelicanXXXXX/(here)'
        # An essential avoidance of ruff/black's own syntax-error asserts
        blob: str = str(BLOB_FILESPEC_SYNTAX_ERROR)
        # Set up temporary relative "settings/pelicanXXXXXX/(here)"
        tmp_rel_dirspec_path: Path = fixture_func_create_tmp_dir_rel_path
        syntax_err_rel_filespec_str: str = str(
            tmp_rel_dirspec_path / PC_FULLNAME_SYNTAX_ERROR
        )
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(blob, syntax_err_rel_filespec_str)

        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            with pytest.raises(IndentationError) as sample:
                # ignore return value due to sys.exit()
                load_source(default_module, path=syntax_err_rel_filespec_str)

            assert sample.type == IndentationError
            assert sample.value.lineno == SM_UT_SYNTAX1_LINENO
            assert sample.value.offset == SM_UT_SYNTAX1_OFFSET
        # assert "unexpected indent" in self._caplog.text  (future)

        if module_expected_in_sys_modules(default_module):  # TODO Issue #09001
            del sys.modules[default_module]
        module_not_expected_in_sys_modules(default_module)
        Path(syntax_err_rel_filespec_str).unlink(missing_ok=False)

    def test_load_source_module_str_abs_syntax_error_fail(
        self, fixture_func_create_tmp_dir_abs_path, fixture_func_ut_wrap
    ):
        """ "syntax error; absolute path, str type; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        default_module = PC_MODNAME_DEFAULT
        module_not_expected_in_sys_modules(default_module)
        # identify blob of  "pseudo-script" file (ruff/black avoidance of syntax-error)
        blob: str = str(Path(DIRSPEC_RELATIVE) / BLOB_FULLNAME_SYNTAX_ERROR)
        # Set up temporary absolute "/$TEMPDIR/pelicanXXXXXX/(here)"
        tmp_abs_dirspec_path: Path = fixture_func_create_tmp_dir_abs_path
        syntax_err_abs_filespec_str: str = str(
            tmp_abs_dirspec_path / PC_FULLNAME_SYNTAX_ERROR
        )
        # despite tempdir, check if file does NOT exist
        if Path(syntax_err_abs_filespec_str).exists():
            # Bad test setup, assert out
            raise AssertionError(
                f"File {syntax_err_abs_filespec_str} should not " "exist in tempdir"
            )
        # Copy mangled pseudo-Python file into temporary absolute area as a Python file
        shutil.copyfile(blob, syntax_err_abs_filespec_str)

        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            with pytest.raises(IndentationError) as sample:
                # ignore return value due to sys.exit()
                load_source(default_module, syntax_err_abs_filespec_str)
            assert sample.type == IndentationError
            assert sample.value.lineno == SM_UT_SYNTAX1_LINENO
            assert sample.value.offset == SM_UT_SYNTAX1_OFFSET
        # assert "unexpected indent" in self._caplog.text  # TODO Issue #09004

        # Cleanup
        if module_expected_in_sys_modules(default_module):
            del sys.modules[default_module]
        Path(syntax_err_abs_filespec_str).unlink(missing_ok=False)

    def test_load_source_module_path_rel_syntax_error_fail(
        self,
        fixture_func_ut_wrap,
        fixture_func_create_tmp_dir_rel_path,
    ):
        """Syntax error; valid relative file, Path type; valid module; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        default_module = PC_MODNAME_DEFAULT
        module_not_expected_in_sys_modules(default_module)
        # identify blob of  "pseudo-script" file (ruff/black avoidance of syntax-error)
        blob: str = str(Path(DIRSPEC_RELATIVE) / BLOB_FULLNAME_SYNTAX_ERROR)
        # Set up temporary relative "settings/pelicanXXXXXX/(here)"
        tmp_rel_dirspec_path: Path = fixture_func_create_tmp_dir_rel_path
        syntax_err_rel_filespec_path: Path = (
            tmp_rel_dirspec_path / PC_FULLNAME_SYNTAX_ERROR
        )
        # despite tempdir, check if file does NOT exist
        if syntax_err_rel_filespec_path.exists():
            # Bad test setup, assert out
            raise AssertionError(
                f"File {syntax_err_rel_filespec_path!s} should not " "exist in tempdir"
            )
        # Copy mangled pseudo-Python file into temporary absolute area as a Python file
        shutil.copyfile(blob, syntax_err_rel_filespec_path)

        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            with pytest.raises(IndentationError) as sample:
                # ignore return value due to sys.exit()
                load_source(default_module, path=syntax_err_rel_filespec_path)
            assert sample.type == IndentationError
        assert sample.value.lineno == SM_UT_SYNTAX1_LINENO
        assert sample.value.offset == SM_UT_SYNTAX1_OFFSET
        # assert "unexpected indent" in self._caplog.text  # TODO Issue #09004

        if module_expected_in_sys_modules(default_module):
            del sys.modules[default_module]
        Path(syntax_err_rel_filespec_path).unlink(missing_ok=True)

    def test_load_source_module_path_abs_syntax_error_fail(
        self,
        fixture_func_ut_wrap,
        fixture_func_create_tmp_dir_abs_path,
    ):
        """Syntax error; valid absolute file, Path type; valid module; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        default_module = PC_MODNAME_DEFAULT
        module_not_expected_in_sys_modules(default_module)
        # Set up temporary absolute "/$TEMPDIR/pelicanXXXXXX/(here)"
        tmp_abs_dirspec_path: Path = fixture_func_create_tmp_dir_abs_path
        syntax_err_abs_filespec_path: Path = (
            tmp_abs_dirspec_path / PC_FULLNAME_SYNTAX_ERROR
        )
        # copy "pseudo-script" file to '/tmp' (ruff/black avoidance of syntax-error)
        blob = Path(DIRSPEC_DATADIR) / BLOB_FULLNAME_SYNTAX_ERROR
        # despite tempdir, check if file does NOT exist
        if Path(syntax_err_abs_filespec_path).exists():
            # Bad test setup, assert out
            raise AssertionError(
                f"File {syntax_err_abs_filespec_path} should not " "exist in tempdir"
            )
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(blob, syntax_err_abs_filespec_path)

        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            with pytest.raises(IndentationError) as sample:
                load_source(default_module, syntax_err_abs_filespec_path)

            assert sample.type == IndentationError
            assert sample.value.lineno == SM_UT_SYNTAX1_LINENO
            assert sample.value.offset == SM_UT_SYNTAX1_OFFSET
        # assert "unexpected indent" in self._caplog.text  # TODO Issue #09004

        # Cleanup temporary
        if module_expected_in_sys_modules(default_module):
            del sys.modules[default_module]
        Path(syntax_err_abs_filespec_path).unlink(missing_ok=False)


if __name__ == "__main__":
    # if executing this file alone, it tests this file alone.
    # Can execute from any current working directory
    pytest.main([__file__])

    # more, complex variants of pytest.
    # pytest.main([__file__, "-n0", "-rAw", "--capture=no", "--no-header"])
    # pytest.main([__file__, "-n0"])  # single-process, single-thread
