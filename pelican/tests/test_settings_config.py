import copy
import shutil
import tempfile
from pathlib import Path

import pytest

TMP_DIRNAME_SUFFIX = "pelican"


class TestSettingsConfig:
    """Exercise the configure_settings()/settings.py"""

    @pytest.fixture(scope="module")
    def get_absolute_tests_dirpath(self) -> Path:
        """Get the absolute directory path of `tests` subdirectory

        This pytest module-wide fixture will provide the full directory
        path of this `test_settings_config.py`.

        Note: used to assist in placing the `settings` directory underneath it.
        :return: Returns the Path of the tests directory
        :rtype: pathlib.Path"""
        print("get_absolute_tests_dirpath: started")  # NOQA
        abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce
        return abs_tests_dirpath

    @pytest.fixture(scope="class")
    def get_settings_dirpath(self, get_absolute_tests_dirpath) -> Path:
        """Get the absolute directory path of `tests/settings` subdirectory

        This pytest class-wide fixture will provide the full directory
        path of the `settings` subdirectory containing all the pelicanconf.py files.

        :return: Returns the Path of the tests directory
        :rtype: pathlib.Path"""
        print("get_settings_dirpath: started")  # NOQA
        settings_dirpath: Path = get_absolute_tests_dirpath / "settings"
        return settings_dirpath

    @pytest.fixture(scope="function")
    def template_temp_directory(self, get_settings_dirpath) -> Path:
        """Template the temporary directory

        This pytest function-wide fixture will provide the template name of
        the temporary directory.

        :return: Returns the Path of the temporary directory
        :rtype: pathlib.Path"""
        print("template_temp_directory: started")  # NOQA
        temporary_dirpath = tempfile.mkdtemp(
            dir=get_settings_dirpath, suffix=TMP_DIRNAME_SUFFIX
        )
        return temporary_dirpath

    @pytest.fixture(scope="function")
    def create_temp_directory(self, get_settings_dirpath, template_temp_directory):
        print("create_temp_directory: started")  # NOQA
        temporary_dirpath = template_temp_directory
        # Make a copy of the string, pass that copy;
        # keep original for directory cleanup
        passing_dirpath = copy.deepcopy(temporary_dirpath)
        # Create a `pelican/pelican/tests/settings/tmpXXXXpelican` subdirectory.
        print("create_temp_directory: before yield")  # NOQA
        yield passing_dirpath
        print("create_temp_directory: after yield")  # NOQA
        # There is a danger of __pycache__ being overlooked here only if this fails
        # while not a showstopper nor alteration of a test result, this __pycache__
        # would just merely clutter the directory.
        shutil.rmtree(temporary_dirpath)
        print("create_temp_directory: end")  # NOQA

    def test_cs_blanks(
        self,
        get_absolute_tests_dirpath,
        get_settings_dirpath,
        template_temp_directory,
        create_temp_directory,
    ):
        """test a premise

        :param self: this TestSettingsConfig class instantiation
        :type self: TestSettingsConfig class
        :param create_temp_directory: a fixture that provides a temporary directory
                        for testing.
        :type create_temp_directory: object"""
        print("test_cs_blanks: started")  # NOQA
        print(  # NOQA
            f"test_cs_blanks: get_absolute_tests_dirpath: {get_absolute_tests_dirpath}"
        )
        print(f"test_cs_blanks: get_settings_dirpath: {get_settings_dirpath}")  # NOQA
        print(f"test_cs_blanks: template_temp_directory: {template_temp_directory}")  # NOQA
        print(f"test_cs_blanks: create_temp_directory: {create_temp_directory}")  # NOQA
        assert True


if __name__ == "__main__":
    pytest.main()
