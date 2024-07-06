import errno
import locale
import logging
import pathlib
from os.path import abspath, dirname, join  # TODO remove due to PEP-0451

import pytest

from pelican.settings import (
    #   DEFAULT_CONFIG,
    #    DEFAULT_THEME,
    #    _printf_s_to_format_field,
    #    configure_settings,
    #    handle_deprecated_settings,
    load_source,
)

#   read_settings,
from pelican.tests.support import unittest

CONFIG_UNPYTHON = "settings/pelicanconf-syntax-error.py"
VALID_MODULE_NAME = "pelicanconf"
VALID_PELICANCONF = "settings/pelicanconf-valid.py"

logging.basicConfig(level=0)
log = logging.getLogger(__name__)
logging.root.setLevel(logging.DEBUG)
log.propagate = True

from _pytest.logging import LogCaptureHandler, _remove_ansi_escape_sequences  # NOQA


class TestSettingsPart2(unittest.TestCase):
    """Provided a file, it should read it, replace the default values,
    append new values to the settings (if any), and apply basic settings
    optimizations.
    """

    def setUp(self):
        self.old_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, "C")
        self.PATH = abspath(dirname(__file__))
        self.default_conf = join(self.PATH, "default_conf.py")
        # each unit test will do the reading of settings

    def tearDown(self):
        locale.setlocale(locale.LC_ALL, self.old_locale)

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    # Emptiness
    def test_load_source_arg_missing_fail(self):
        with pytest.raises(TypeError) as sample:
            load_source()
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    def test_load_source_path_str_blank_fail(self):
        module_type = load_source("")
        assert module_type is None

    def test_load_source_path_arg_str_blank_fail(self):
        module_type = load_source(path="")
        assert module_type is None

    def test_load_source_wrong_arg_fail(self):
        with pytest.raises(TypeError) as sample:
            load_source(no_such_arg="reject this")
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    def test_load_source_arg_unexpected_fail(self):
        with pytest.raises(TypeError) as sample:
            load_source(pathway="reject this")
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    # Module Names, Oh My!
    def test_load_source_arg_path_unfilled_fail(self):
        module_list = {}
        with pytest.raises(TypeError) as sample:
            load_source(module_name=module_list)
        assert sample.type == TypeError

    def test_load_source_unexpected_argument_fail(self):
        module_str = ""
        with pytest.raises(TypeError) as sample:
            load_source(module_name=module_str)
        assert sample.type == TypeError
        # assert sample.value.code only exists for SystemExit

    # All About The Paths
    def test_load_source_path_wrong_type_list_fail(self):
        path_list = {}
        with pytest.raises(TypeError) as sample:
            load_source(path=path_list)
        assert sample.type == TypeError

    def test_load_source_path_wrong_type_dict_fail(self):
        path_dict = []
        with pytest.raises(TypeError) as sample:
            load_source(path=path_dict)
        assert sample.type == TypeError

    def test_load_source_path_wrong_type_tuple_fail(self):
        path_tuple = ()
        with pytest.raises(TypeError) as sample:
            load_source(path=path_tuple)
        assert sample.type == TypeError

    def test_load_source_path_valid_pelicanconf_py_pass(self):
        path = "settings/pelicanconf.py"
        module_type = load_source(path)
        assert module_type is not None

    #    @log_function_details
    def test_load_source_path_pelicanconf_syntax_error_fail(self):
        path = "settings/pelicanconf-syntax-error.py"
        with self._caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as sample:
                self._caplog.clear()
                load_source(path)  # ignore return value due to sys.exit()
            assert "invalid syntax" in self._caplog.text
            assert sample.type == SystemExit
            assert sample.value.code == errno.ENOEXEC


###################################################################################
class TestSettingsModuleName(unittest.TestCase):
    """Exercises both the path and module_name arguments"""

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    # Proper combinatorial - Focus on the Path
    def test_load_source_blank_args_fail(self):
        """load_source(), arguments, all blank, failing mode"""
        """Supply blank string to each arguments and fail"""
        module_name = ""
        blank_filespec = pathlib.Path("")
        module_spec = load_source(blank_filespec, module_name)
        assert module_spec is None

    def test_load_source_blank_filespec_fail(self):
        """load_source(), argument path str is blank, failing mode"""
        """ We do not want to let Pelican search all over the place using PYTHONPATH """
        module_spec = load_source(path="", module_name=VALID_MODULE_NAME)
        assert module_spec is None

    def test_load_source_blank_module_pass(self):
        """load_source(); using blank module name, failing mode"""
        """Used to be like this in the old Pelican days"""
        module_name = ""  # Let the load_source determine its module name, error-prone
        file_location = pathlib.Path(VALID_PELICANCONF)
        with self._caplog.at_level(logging.DEBUG):
            self._caplog.clear()
            module_spec = load_source(file_location, module_name)
            # but we have to check for warning
            # message of 'assumed implicit module name'
            assert "Module name is missing" in self._caplog.text
            assert module_spec is not None

    def test_load_source_python_builtin_module_fail(self):
        """load_source(), Python builtin module, failing mode"""
        with pytest.raises(SystemExit) as sample:
            module_name = "calendar"
            file_location = pathlib.Path(VALID_PELICANCONF)
            # ignore return value of load_source
            load_source(file_location, module_name)
            # pytest always assert this SystemExit, does not get here
        assert sample.type == SystemExit
        assert sample.value.code == errno.EPERM

    def test_load_source_invalid_abs_path1_fail(self):
        """load_source(), invalid absolute path, no such file, failing mode"""
        name = "pelicanconf-does-not-exist"
        path = pathlib.Path("/no-such-directory")  # a directory, not the expected file
        mod = load_source(path, name)
        self.assertEqual(
            mod, None, "absolute '/no-such-directory' directory path is not found."
        )

    def test_load_source_invalid_abs_path2_fail(self):
        """load_source(), invalid absolute path, directory, failing mode"""
        name = "pelicanconf-does-not-exist"
        path = pathlib.Path("/tmp")  # a directory, not the expected file
        mod = load_source(path, name)
        self.assertEqual(
            mod, None, "Missing absolute '/tmp/pelican-does-not-exist.py' file"
        )

    def test_load_source_invalid_abs_path3_fail(self):
        """load_source(), invalid absolute unresolved path, directory, failing mode"""
        name = "pelicanconf-does-not-exist"
        path = pathlib.Path("/../tmp")  # a directory, not the expected file
        mod = load_source(path, name)
        self.assertEqual(mod, None, "Missing relative pelicanconf.py")

    def test_load_source_missing_relative_fail(self):
        name = "pelicanconf-does-not-exist"  # module_name
        path = pathlib.Path(".")  # location of module Python file
        mod = load_source(path, name)
        self.assertEqual(mod, None, "Missing relative pelicanconf.py")

    def test_load_source_missing_absolute_fail(self):
        name = "pelicanconf-does-not-exist"
        path = pathlib.Path("/tmp/pelicanconf-does-not-exist.py")
        mod = load_source(path, name)
        self.assertEqual(mod, None)


if __name__ == "__main__":
    unittest.main()
