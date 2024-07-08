import errno
import locale
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureHandler, _remove_ansi_escape_sequences  # NOQA

from pelican.settings import (
    load_source,
)
from pelican.tests.support import unittest

DIRSPEC_RELATIVE = "settings" + os.sep

EXT_PYTHON = ".py"
EXT_PYTHON_DISABLED = ".disabled"

PC_MODNAME_ACTUAL = "pelicanconf"

# FILENAME_: file name without the extension
PC_FILENAME_DEFAULT = PC_MODNAME_ACTUAL
PC_FILENAME_VALID = "pelicanconf-valid"
PC_FILENAME_SYNTAX_ERROR = "pelicanconf-syntax-error"

# FULLNAME_: filename + extension
PC_FILENAME_DEFAULT: str = PC_FILENAME_DEFAULT + EXT_PYTHON
PC_FULLNAME_VALID: str = PC_FILENAME_VALID + EXT_PYTHON
PC_FULLNAME_SYNTAX_ERROR: str = PC_FILENAME_SYNTAX_ERROR + EXT_PYTHON

logging.basicConfig(level=0)
log = logging.getLogger(__name__)
logging.root.setLevel(logging.DEBUG)
log.propagate = True


class TestSettingsLoadSource(unittest.TestCase):
    """load_source"""

    # Provided a file, it should read it, replace the default values,
    # append new values to the settings (if any), and apply basic settings
    # optimizations.

    def setUp(self):
        self.old_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, "C")
        # each unit test will do the reading of settings
        tempy = tempfile.mkdtemp("pelican")
        self.DIRSPEC_ABSOLUTE_TMP = Path(tempy)

    def tearDown(self):
        locale.setlocale(locale.LC_ALL, self.old_locale)

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    # Emptiness
    def test_load_source_arg_missing_fail(self):
        """missing arguments; failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source()
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    def test_load_source_path_str_blank_fail(self):
        """blank string argument; failing mode"""
        module_type = load_source("")
        assert module_type is None

    def test_load_source_path_arg_str_blank_fail(self):
        """argument name with blank str; failing mode"""
        module_type = load_source(path="")
        assert module_type is None

    def test_load_source_wrong_arg_fail(self):
        """wrong argument name (variant 1); failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source(no_such_arg="reject this")
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    def test_load_source_arg_unexpected_fail(self):
        """wrong argument name (variant 2), failing mode"""
        with pytest.raises(TypeError) as sample:
            load_source(pathway="reject this")
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    # Module Names, Oh My!
    def test_load_source_module_arg_unexpected_list_fail(self):
        """invalid dict argument type; failing mode"""
        module_list = {}
        with pytest.raises(TypeError) as sample:
            load_source(module_name=module_list)
        assert sample.type == TypeError

    def test_load_source_module_path_arg_missing_fail(self):
        """invalid list argument type; failing mode"""
        module_str = ""
        with pytest.raises(TypeError) as sample:
            load_source(module_name=module_str)
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    # All About The Paths
    def test_load_source_path_unexpected_type_list_fail(self):
        """invalid dict argument type with argument name; failing mode"""
        path_list = {}
        with pytest.raises(TypeError) as sample:
            load_source(path=path_list)
        assert sample.type == TypeError

    def test_load_source_path_unexpected_type_dict_fail(self):
        """invalid list argument type w/ argument name=; failing mode"""
        path_dict = []
        with pytest.raises(TypeError) as sample:
            load_source(path=path_dict)
        assert sample.type == TypeError

    def test_load_source_path_unexpected_type_tuple_fail(self):
        """invalid tuple argument type w/ argument name=; failing mode"""
        path_tuple = ()
        with pytest.raises(TypeError) as sample:
            load_source(path=path_tuple)
        assert sample.type == TypeError

    def test_load_source_path_valid_pelicanconf_py_pass(self):
        """correct working function call; passing mode"""
        path: str = DIRSPEC_RELATIVE + PC_FULLNAME_VALID
        module_type = load_source(path)
        assert module_type is not None

    #    @log_function_details
    def test_load_source_path_pelicanconf_abc_syntax_error_fail(self):
        """syntax error; absolute path; str type; failing mode"""
        # copy "pseudo-script" file to '/tmp' (ruff/black avoidance of syntax-error)
        path: str = DIRSPEC_RELATIVE + PC_FULLNAME_SYNTAX_ERROR + EXT_PYTHON_DISABLED
        tmp_path: Path = self.DIRSPEC_ABSOLUTE_TMP / PC_FULLNAME_SYNTAX_ERROR
        Path(tmp_path).unlink(missing_ok=True)  # clean out old cruft
        # Copy mangled pseudo-Python file into temporary area as a Python file
        shutil.copyfile(path, tmp_path)
        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                load_source(tmp_path)  # ignore return value due to sys.exit()
            assert "invalid syntax" in self._caplog.text
            assert sample.type == SystemExit
            assert sample.value.code == errno.ENOEXEC
        Path(tmp_path).unlink(missing_ok=True)
