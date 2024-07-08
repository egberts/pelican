# Minimum version: Python 3.6 (tempfile.mkdtemp())


# We crapped out; mktemp, et. al. cannot be done within setUp()
# mktemp, et. al. MUST BE performed within each procedure
# until then, we cannot parallel-test this entire file, only 1-process test

import errno
import inspect
import locale
import logging
import ntpath
import os
import posixpath
import shutil
import stat
import sys
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest
from _pytest.logging import LogCaptureHandler, _remove_ansi_escape_sequences  # NOQA

from pelican.settings import (
    load_source,
)
from pelican.tests.support import unittest

# Valid Python file extension
EXT_PYTHON = ".py"
EXT_PYTHON_DISABLED = ".disabled"

# DIRSPEC_: where all the test config files are stored
# we hope that current working directory is always in pelican/pelican/tests
DIRSPEC_CURRENT: str = os.getcwd()
DIRSPEC_RELATIVE: str = "settings" + os.sep

# PC_ = Pelican Configuration or PELICANCONF or pelicanconf
# MODNAME_ = Module name
PC_MODNAME_ACTUAL = "pelicanconf"
PC_MODNAME_NOT_EXIST = "pelicanconf-not-exist"
PC_MODNAME_INVALID = "non-existing-module.cannot-get-there"  # there is a period
PC_MODNAME_SYS_BUILTIN = "calendar"

# FILENAME_: file name without the extension
PC_FILENAME_VALID = "pelicanconf-valid"
PC_FILENAME_NOTFOUND = "pelicanconf-not-found"
PC_FILENAME_UNREADABLE = "pelicanconf-unreadable"
PC_FILENAME_SYNTAX_ERROR = "pelicanconf-syntax-error"

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

# PATH_: the final path for unit tests here
# FILESPEC_: the full path + filename + extension
# REL_: relative path
FILESPEC_REL_VALID = DIRSPEC_RELATIVE + PC_FULLNAME_VALID
PATH_FILESPEC_REL_NOTFOUND = Path(DIRSPEC_RELATIVE + PC_FULLNAME_NOTFOUND)
PATH_FILESPEC_REL_UNREADABLE = Path(DIRSPEC_RELATIVE + PC_FULLNAME_UNREADABLE)
PATH_FILESPEC_REL_SYNTAX_ERROR = Path(DIRSPEC_RELATIVE + PC_FULLNAME_SYNTAX_ERROR)

# DIRSPEC_: the full directory path
PATH_DIRSPEC_REL_NOACCESS = Path(DIRSPEC_RELATIVE + PC_DIRNAME_NOACCESS)
PATH_DIRSPEC_REL_NOTFOUND = Path(DIRSPEC_RELATIVE + PC_DIRNAME_NOTFOUND)

BLOB_FILESPEC_UNREADABLE = Path(DIRSPEC_RELATIVE + PC_FULLNAME_UNREADABLE)

load_source_argument_count = 2

# Code starts here
logging.basicConfig(level=0)
log = logging.getLogger(__name__)
logging.root.setLevel(logging.DEBUG)
log.propagate = True


def remove_read_permissions(path):
    """Remove read permissions from this path, keeping all other permissions intact.

    Params:
        path:  The path whose permissions to alter.
    """
    no_user_reading = ~stat.S_IRUSR
    no_group_reading = ~stat.S_IRGRP
    no_other_reading = ~stat.S_IROTH
    no_reading = no_user_reading & no_group_reading & no_other_reading

    current_permissions = stat.S_IMODE(os.lstat(path).st_mode)
    os.chmod(path, current_permissions & no_reading)


def dot_path(pth):
    """Corner-case to deal with filespec starting with a period symbol

    eal with dotted notation different for PosixPath and NtPath"""
    """Return path str that may start with '.' if relative."""
    if pth.is_absolute():
        return os.fsdecode(pth)
    if isinstance(pth, PureWindowsPath):
        return ntpath.join(".", pth)
    elif isinstance(pth, PurePosixPath):
        return posixpath.join(".", pth)
    else:
        return os.path.join(".", pth)


# We need an existing Python system built-in module for testing load_source.
if PC_MODNAME_SYS_BUILTIN not in sys.modules:
    pytest.exit(
        errno.EACCES,
        "PC_MODNAME_SYS_BUILTIN variable MUST BE an existing system "
        "builtin module; this test is aborted",
    )

# Oppositional, PC_MODNAME_ACTUAL must NOT be a pre-existing system built-in module
if PC_MODNAME_ACTUAL in sys.modules:
    # We are not authorized to tamper outside our test area
    pytest.exit(
        errno.EACCES,
        f" Cannot resuse a system built-in module {PC_MODNAME_ACTUAL};"
        " this test is aborted",
    )


class TestSettingsModuleName(unittest.TestCase):
    """Exercises both the path and module_name arguments"""

    def setUp(self):
        self.old_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, "C")

        # Something interesting ...:
        # below logic only works with ALL classes within a file
        # and does not work within a selective class.
        # So logic within this setUp() is file-wide, not per-class.
        tempy = tempfile.mkdtemp("pelican")

        self.DIRSPEC_ABSOLUTE_TMP = Path(tempy)
        # ABS_: absolute path
        self.PATH_FILESPEC_ABS_VALID = self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_VALID
        self.PATH_FILESPEC_ABS_NOTFOUND = (
            self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_NOTFOUND
        )
        self.PATH_FILESPEC_ABS_UNREADABLE = (
            self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_UNREADABLE
        )
        self.PATH_FILESPEC_ABS_SYNTAX_ERROR = (
            self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_SYNTAX_ERROR
        )
        self.PATH_DIRSPEC_ABS_NOACCESS = self.DIRSPEC_ABSOLUTE_TMP / PC_DIRNAME_NOACCESS
        self.PATH_DIRSPEC_ABS_NOTFOUND = self.DIRSPEC_ABSOLUTE_TMP / PC_DIRNAME_NOTFOUND

        args = inspect.getfullargspec(load_source)
        if (
            "module_name" not in args.args
            and args.args.__len__ != load_source_argument_count
        ):
            # Skip this entire test file if load_source() only supports 1 argument
            pytest.skip(
                "this class is only used with load_source() having "
                "support for a 'module_name' argument"
            )

    def tearDown(self):
        # delete temporary directory?
        return

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """add support for performing assert in caplog.text output"""
        self._caplog = caplog

    # Blank arguments test series, by path argument, str type
    def test_load_source_str_all_blank_fail(self):
        """load_source; arguments all blank; path str; failing mode"""
        """Supply blank string to each arguments and fail"""
        module_name = ""
        filespec_blank: str = ""
        module_spec = load_source(filespec_blank, module_name)
        assert module_spec is None

    # Proper combinatorial - Focusing firstly on the path argument using str type
    def test_load_source_str_rel_dotted_fail(self):
        """load_source; dotted directory; path str; blank module; failing mode"""
        module_name = ""
        str_filespec_dotted: str = "."
        module_spec = load_source(str_filespec_dotted, module_name)
        assert module_spec is None

    def test_load_source_str_rel_parent_fail(self):
        """load_source; relative parent; path str; blank module; failing mode"""
        module_name = ""
        str_filespec_parent: str = ".."
        module_spec = load_source(str_filespec_parent, module_name)
        assert module_spec is None

    def test_load_source_str_anchor_fail(self):
        """load_source; anchor directory; path str; blank module; failing mode"""
        module_name = ""
        str_filespec_anchor: str = os.sep
        module_spec = load_source(str_filespec_anchor, module_name)
        assert module_spec is None

    def test_load_source_str_cwd_fail(self):
        """load_source; current working dir; path str; blank module; failing mode"""
        module_name = ""
        str_filespec_cwd: str = str(Path.cwd())
        module_spec = load_source(str_filespec_cwd, module_name)
        assert module_spec is None

    # Focusing on the path argument using Path type
    def test_load_source_path_all_blank_fail(self):
        """load_source; arguments all blank; path Path; blank module; failing mode"""
        """Supply blank string to each arguments and fail"""
        module_name = ""
        path_blank_filespec: Path = Path("")
        module_spec = load_source(path_blank_filespec, module_name)
        assert module_spec is None

    def test_load_source_path_dot_fail(self):
        """load_source; dotted directory; path Path; blank module; failing mode"""
        module_name = ""
        path_dotted_filespec: Path = Path(".")
        module_spec = load_source(path_dotted_filespec, module_name)
        assert module_spec is None

    def test_load_source_path_abs_anchor_fail(self):
        """load_source; anchor directory; path Path; blank module; failing mode"""
        module_name = ""
        path_filespec_anchor: Path = Path(os.sep)
        module_spec = load_source(path_filespec_anchor, module_name)
        assert module_spec is None

    def test_load_source_path_rel_parent_fail(self):
        """load_source; parent directory; path Path; blank module; failing mode"""
        module_name = ""
        path_filespec_parent: Path = Path("..")
        module_spec = load_source(path_filespec_parent, module_name)
        assert module_spec is None

    def test_load_source_path_abs_cwd_fail(self):
        """load_source; current working dir; path Path, blank module; failing mode"""
        module_name = ""
        blank_filespec: Path = Path.cwd()
        module_spec = load_source(blank_filespec, module_name)
        assert module_spec is None

    # Actually start to try using Pelican configuration file
    # but with no module_name
    def test_load_source_str_rel_valid_pass(self):
        """load_source; valid; relative path str; blank module; passing mode"""
        module_name = ""
        filespec_rel_valid: str = "." + os.sep + FILESPEC_REL_VALID
        module_spec = load_source(filespec_rel_valid, module_name)
        # check if PATH is defined inside a valid Pelican configuration settings file
        assert module_spec is not None
        assert hasattr(module_spec, "PATH"), (
            "The valid file did " "not provide a PATH object variable"
        )

    def test_load_source_str_abs_valid_pass(self):
        """load_source; valid; absolute path str; blank module; passing mode"""
        module_name = ""
        filespec_abs_valid: str = str(self.PATH_FILESPEC_ABS_VALID)
        shutil.copy(FILESPEC_REL_VALID, filespec_abs_valid)
        module_spec = load_source(filespec_abs_valid, module_name)
        # check if PATH is defined inside a valid Pelican configuration settings file
        assert module_spec is not None
        assert hasattr(module_spec, "PATH"), (
            "The valid file did " "not provide a PATH object variable"
        )

    def test_load_source_str_rel_not_found_fail(self):
        """load_source; relative not found; path str; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_rel_missing: str = str(PATH_FILESPEC_REL_NOTFOUND)
        # since load_source only returns None or Module, check STDERR for 'not found'
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_rel_missing, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " not found" in self._caplog.text
            assert module_spec is None

    def test_load_source_str_abs_not_found_fail(self):
        """load_source; absolute not found; path str; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_abs_missing: str = str(self.PATH_FILESPEC_ABS_NOTFOUND)
        # do not need to copy REL into ABS but need to ensure no ABS is there
        if self.PATH_FILESPEC_ABS_NOTFOUND.exists():
            # Ouch, to delete or to absolute fail?  We fail here, instead.
            AssertionError(f"Errant '{filespec_abs_missing} found; FAILED")
        # since load_source only returns None or Module, check STDERR for 'not found'
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_abs_missing, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " not found" in self._caplog.text
            assert module_spec is None

    def test_load_source_str_rel_no_access_fail(self):
        """load_source; relative not readable; path str; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_rel_noaccess: str = str(PATH_FILESPEC_REL_UNREADABLE)
        Path(filespec_rel_noaccess).touch()  # wonder if GitHub preserves no-read bit
        remove_read_permissions(filespec_rel_noaccess)
        # do not need to copy REL into ABS but need to ensure no ABS is there
        if os.access(filespec_rel_noaccess, os.R_OK):
            # Ouch, to change file perm bits or to absolute fail?  Fail here, instead.
            AssertionError(
                f"Errant '{filespec_rel_noaccess} unexpectedly " "readable; FAILED"
            )
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_rel_noaccess, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " is not readable" in self._caplog.text
            assert module_spec is None

    def test_load_source_str_abs_no_access_fail(self):
        """load_source; absolute not readable; path str; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_abs_noaccess: str = str(self.PATH_FILESPEC_ABS_UNREADABLE)
        Path(filespec_abs_noaccess).touch()
        remove_read_permissions(filespec_abs_noaccess)
        # do not need to copy REL into ABS but need to ensure no ABS is there
        if os.access(filespec_abs_noaccess, os.R_OK):
            # Ouch, to change file perm bits or to absolute fail?  Fail here, instead.
            AssertionError(
                f"Errant '{filespec_abs_noaccess} unexpectedly " "readable; FAILED"
            )
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_abs_noaccess, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " is not readable" in self._caplog.text
            assert module_spec is None

    # continue using the path argument, but starting with Path type,
    def test_load_source_path_rel_valid_pass(self):
        """load_source; valid; relative path Path; blank module; passing mode"""
        module_name = ""
        filespec_rel_valid: Path = Path(".") / os.sep / FILESPEC_REL_VALID
        module_spec = load_source(filespec_rel_valid, module_name)
        # check if PATH is defined inside a valid Pelican configuration settings file
        assert module_spec is not None
        assert hasattr(module_spec, "PATH"), (
            "The valid file did " "not provide a PATH object variable"
        )

    def test_load_source_path_abs_valid_pass(self):
        """load_source; valid; absolute path Path; blank module; passing mode"""
        module_name = ""
        filespec_abs_valid: Path = self.PATH_FILESPEC_ABS_VALID
        shutil.copy(FILESPEC_REL_VALID, filespec_abs_valid)
        module_spec = load_source(filespec_abs_valid, module_name)
        # check if PATH is defined inside a valid Pelican configuration settings file
        assert module_spec is not None
        assert hasattr(module_spec, "PATH"), (
            "The valid file did " "not provide a PATH object variable"
        )

    def test_load_source_path_rel_not_found_fail(self):
        """load_source; relative not found; path Path; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_rel_missing: Path = PATH_FILESPEC_REL_NOTFOUND
        # since load_source only returns None or Module, check STDERR for 'not found'
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_rel_missing, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " not found" in self._caplog.text
            assert module_spec is None

    def test_load_source_path_abs_not_found_fail(self):
        """load_source; absolute not found; path Path; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_abs_missing: Path = self.PATH_FILESPEC_ABS_NOTFOUND
        # do not need to copy REL into ABS but need to ensure no ABS is there
        if self.PATH_FILESPEC_ABS_NOTFOUND.exists():
            # Ouch, to delete or to absolute fail?  We fail here, instead.
            AssertionError(f"Errant '{filespec_abs_missing} found; FAILED")
        # since load_source only returns None or Module, check STDERR for 'not found'
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_abs_missing, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " not found" in self._caplog.text
            assert module_spec is None

    def test_load_source_path_rel_no_access_fail(self):
        """load_source; relative not readable; path Path; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_rel_noaccess: Path = PATH_FILESPEC_REL_UNREADABLE
        Path(filespec_rel_noaccess).touch()  # wonder if GitHub preserves no-read bit
        remove_read_permissions(filespec_rel_noaccess)
        # do not need to copy REL into ABS but need to ensure no ABS is there
        if os.access(filespec_rel_noaccess, os.R_OK):
            # Ouch, to change file perm bits or to absolute fail?  Fail here, instead.
            AssertionError(
                f"Errant '{filespec_rel_noaccess} unexpectedly " "readable; FAILED"
            )
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_rel_noaccess, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " is not readable" in self._caplog.text
            assert module_spec is None

    def test_load_source_path_abs_no_access_fail(self):
        """load_source; absolute not readable; path Path; blank module; failing mode"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        filespec_abs_noaccess: Path = self.PATH_FILESPEC_ABS_UNREADABLE
        Path(filespec_abs_noaccess).touch()
        remove_read_permissions(filespec_abs_noaccess)
        # do not need to copy REL into ABS but need to ensure no ABS is there
        if os.access(filespec_abs_noaccess, os.R_OK):
            # Ouch, to change file perm bits or to absolute fail?
            # Test setup fail here, Assert-hard.
            AssertionError(
                f"Errant '{filespec_abs_noaccess} unexpectedly " "readable; FAILED"
            )
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(filespec_abs_noaccess, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert " is not readable" in self._caplog.text
            assert module_spec is None

    # Everything afterward is all about the module_name

    # Start using module_name, but with valid (str type) path always
    # (will test valid module_name with invalid path afterward)
    def test_load_source_module_str_valid_pass(self):
        """load_source; valid module; path str; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        module_str = PC_MODNAME_ACTUAL
        file_location = str(FILESPEC_REL_VALID)
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(file_location, module_str)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert "Loaded module" in self._caplog.text
            assert module_spec is not None
            assert hasattr(module_spec, "PATH"), (
                "The valid file did not provide " "a PATH object variable"
            )

    def test_load_source_module_str_rel_syntax_error_fail(self):
        """load_source; syntax error; relative path str; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        module_str = PC_MODNAME_ACTUAL
        # copy "pseudo-script" file to '/tmp' (ruff/black avoidance of syntax-error)
        blob: str = str(DIRSPEC_RELATIVE) + BLOB_FULLNAME_SYNTAX_ERROR
        filespec_rel_syntax_err_str: str = DIRSPEC_RELATIVE + PC_FULLNAME_SYNTAX_ERROR
        # filespec_abs_syntax_err.unlink(missing_ok=True)  # TODO clean out old cruft
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(blob, filespec_rel_syntax_err_str)

        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                # ignore return value due to sys.exit()
                load_source(filespec_rel_syntax_err_str, module_name=module_str)
            assert "invalid syntax" in self._caplog.text
            assert sample.type == SystemExit
            assert sample.value.code == errno.ENOEXEC
        Path(filespec_rel_syntax_err_str).unlink(missing_ok=True)

    def test_load_source_module_str_abs_syntax_error_fail(self):
        """load_source; syntax error; absolute path str; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        module_str = PC_MODNAME_ACTUAL
        # copy "pseudo-script" file to '/tmp' (ruff/black avoidance of syntax-error)
        blob: str = str(DIRSPEC_RELATIVE) + BLOB_FULLNAME_SYNTAX_ERROR
        filespec_abs_syntax_err_str: str = str(
            self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_SYNTAX_ERROR
        )
        # filespec_abs_syntax_err.unlink(missing_ok=True)  # TODO clean out old cruft
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(blob, filespec_abs_syntax_err_str)

        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                # ignore return value due to sys.exit()
                load_source(filespec_abs_syntax_err_str, module_str)
            assert "invalid syntax" in self._caplog.text
            assert sample.type == SystemExit
            assert sample.value.code == errno.ENOEXEC
        Path(filespec_abs_syntax_err_str).unlink(missing_ok=True)

    # Start using module_name, but with valid (path type) path always
    def test_load_source_module_path_valid_pass(self):
        """load_source; valid module; path Path; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        module_str = PC_MODNAME_ACTUAL
        file_location = Path(FILESPEC_REL_VALID)
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(file_location, module_name=module_str)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert "Loaded module" in self._caplog.text
            assert module_spec is not None
            assert hasattr(module_spec, "PATH"), (
                "The valid file did not provide " "a PATH object variable"
            )

    def test_load_source_module_path_rel_syntax_error_fail(self):
        """load_source; syntax error; relative path Path; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        module_str = PC_MODNAME_ACTUAL
        # copy "pseudo-script" file to '/tmp' (ruff/black avoidance of syntax-error)
        blob: str = str(DIRSPEC_RELATIVE) + BLOB_FULLNAME_SYNTAX_ERROR
        filespec_rel_syntax_err_path: Path = Path(
            DIRSPEC_RELATIVE + PC_FULLNAME_SYNTAX_ERROR
        )
        # filespec_abs_syntax_err.unlink(missing_ok=True)  # TODO clean out old cruft
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(blob, filespec_rel_syntax_err_path)

        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                # ignore return value due to sys.exit()
                load_source(filespec_rel_syntax_err_path, module_name=module_str)
            assert "invalid syntax" in self._caplog.text
            assert sample.type == SystemExit
            assert sample.value.code == errno.ENOEXEC
        Path(filespec_rel_syntax_err_path).unlink(missing_ok=True)

    def test_load_source_module_path_abs_syntax_error_fail(self):
        """load_source; syntax error; absolute path Path; passing mode"""
        # In Pelican, module name shall always be 'pelicanconf'
        module_str = PC_MODNAME_ACTUAL
        # copy "pseudo-script" file to '/tmp' (ruff/black avoidance of syntax-error)
        blob: str = str(DIRSPEC_RELATIVE) + BLOB_FULLNAME_SYNTAX_ERROR
        filespec_abs_syntax_err_path: Path = (
            self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_SYNTAX_ERROR
        )
        # filespec_abs_syntax_err.unlink(missing_ok=True)  # TODO clean out old cruft
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(blob, filespec_abs_syntax_err_path)

        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                # ignore return value due to sys.exit()
                load_source(filespec_abs_syntax_err_path, module_name=module_str)
            assert "invalid syntax" in self._caplog.text
        assert sample.type == SystemExit
        assert sample.value.code == errno.ENOEXEC
        Path(filespec_abs_syntax_err_path).unlink(missing_ok=True)

    # Start misusing the module_name, but with valid (path type) path always
    def test_load_source_module_invalid(self):
        module_not_exist = PC_MODNAME_NOT_EXIST
        filespec_valid = Path(FILESPEC_REL_VALID)
        module_spec = load_source(filespec_valid, module_not_exist)
        # TODO Probably needs another assert here
        assert module_spec is not None

    def test_load_source_module_taken_by_builtin(self):
        module_name_taken_by_builtin = PC_MODNAME_SYS_BUILTIN
        filespec_valid = Path(FILESPEC_REL_VALID)
        # Taking Python system builtin module is always a hard exit
        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                module_spec = load_source(filespec_valid, module_name_taken_by_builtin)
                # assert "taken by builtin" in self._caplog.text  # TODO add caplog here
                assert module_spec is None
                assert sample.type == SystemExit
                assert sample.value.code == errno.ENOEXEC
            assert "reserved the module name" in self._caplog.text

    def test_load_source_module_invalid_str_fail(self):
        """load_source(), argument path str is blank, failing mode"""
        """ We do not want to let Pelican search all over the place using PYTHONPATH """
        module_spec = load_source(path="", module_name=PC_MODNAME_INVALID)
        # not sure if we need STDERR capture
        assert module_spec is None
        # pytest always assert this SystemExit, does not get here


if __name__ == "__main__":
    unittest.main()
