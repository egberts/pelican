import copy
import os
import shutil
import tempfile
from pathlib import Path

import pytest

DIRDATA_DIRSPEC: Path = Path("settings" + os.sep)
TMP_DIRNAME_SUFFIX = "pelican"


# Note: Unittest test setUp/tearDown got replaced by Pytest and its fixtures.
#
# Pytest provides four levels of fixture scopes:
#
#   * Function (Set up and tear down once for each test function)
#   * Class (Set up and tear down once for each test class)
#   * Module (Set up and tear down once for each test module/file)
#   * Session (Set up and tear down once for each test session i.e comprising
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
class TestSettingsConfig:
    """Exercise the configure_settings()/settings.py"""

    ######################################################################
    #                           FIXTURES, Simple                         #
    # Following fixtures are the lowest test block of the pyramid        #
    # building of test blocks as denoted by a simple `(self)` argument   #
    # list for a class function (or `()` for a classless function).      #
    ######################################################################
    #
    # Any fixture that has a `scope=module` argument avails to this entire file.
    # Any fixture that has a `scope=class` argument stays within this class/module.
    # Any fixture that has a `scope=function` argument under a class stays within this
    # class/module, or before any class avails to the entire file.
    #
    # This fixture is placed firstly here (as a practice, not a rule).
    # This fixture name is optionally suffixed as `fixture_module_`, et al. for
    # block readability and as an easy reference.
    #
    @pytest.fixture(scope="module")
    # Strong typing a return (via `-> Path`) of this fixture is an NOOP.
    def fixture_module_get_tests_dir_abs_path(self):
        """Get the absolute directory path of `tests` subdirectory

        This pytest module-wide fixture will provide a full directory
        path of this `test_settings_config.py`.

        Note: used to assist in locating the `settings` directory underneath it.

        This fixture gets evoked exactly once (file-wide) due to `scope=module`.

        :return: Returns the Path of the tests directory
        :rtype: pathlib.Path"""
        abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce
        # Fixture can return ANY type of object (int, dict, list, combo of types)
        #
        # Return statement, if returning an object, uses the object's implicit type as
        # dictated by its last assignment within this code body and completely ignores
        # the explicit type of its return value found on declaration line of a fixture.
        return abs_tests_dirpath

    ######################################################################
    #                      FIXTURES - Building Blocks                    #
    # Fixtures that do not get referenced in body of code will not be    #
    # evaluated, much less get executed; just a lone listing of its      #
    # fixture in the argument list alone does not make it executable;    #
    # must use that fixture (fixture_module_get_tests_dir_abs_path) in   #
    # the body of code as well (a two-fer).                              #
    ######################################################################
    #
    # if a fixture A is in the fixture B's argument list, then fixture B does not
    # even start to execute until fixture A gets completely executed
    # (up to any optional `yield` statement found in fixture A).
    #
    # That "programming" concept alone is useful for making complex conditional
    # pathways of test blocks simply by referencing the name of its test block.
    @pytest.fixture(scope="class")
    # Strong-typing the argument item in a fixture's argument list is an NOOP.
    def fixture_cls_get_settings_dir_abs_path(
        self, fixture_module_get_tests_dir_abs_path
    ):
        """Get the absolute directory path of `tests/settings` subdirectory

        This pytest class-wide fixture will provide the full directory
        path of the `settings` subdirectory containing all the pelicanconf.py files.

        This fixture gets evoked exactly once within its entire class due
        to `scope=class`.

        :return: Returns the Path of the tests directory
        :rtype: pathlib.Path"""
        settings_dirpath: Path = fixture_module_get_tests_dir_abs_path / "settings"
        return settings_dirpath

    # Before 1st line of code execute, Pytest collects a list of all fixtures that were
    # referenced in other function/fixture's body of code; Unreferenced fixture and
    # its code gets ignored.  Pytest then precomputes the execution dependency order of
    # all collected test blocks/components/fixture then starts executing in that order.
    @pytest.fixture(scope="function")
    # Strong-typing a fixture argument/value is a NOOP, but still
    # applicable within fixture's code body.
    def fixture_func_template_temp_dir_abs_path(
        self, fixture_cls_get_settings_dir_abs_path
    ):
        """Template the temporary directory

        This pytest function-wide fixture will provide the template name of
        the temporary directory.

        This fixture executes exactly once every time a test case function references
        this via `scope=function`.

        :return: Returns the Path of the temporary directory
        :rtype: pathlib.Path"""
        # Precomputed order of other fixtures' execution is:
        #   fixture_cls_get_settings_dir_abs_path: completed here
        temporary_dirpath: Path = Path(
            tempfile.mkdtemp(
                dir=fixture_cls_get_settings_dir_abs_path, suffix=TMP_DIRNAME_SUFFIX
            )
        )
        return temporary_dirpath

    # In order to execute fixture again, it has to be referenced by another function.
    #
    # Repeatedly referencing the fixture name in body of code only get the
    # same precomputed/cached return value (as determined by fixture's scope attribute).
    #
    # The argument list in fixture's declaration statement is only for block-building
    # of test components, and not the customary, one-way value-passing (C/C++/Python,
    # or Pascal's two-way) of variables between callers/callee: that is, argument list
    # is for test block building, not argument passing.
    #
    # Its ordering of the function argument list gets intrinsically computed BEFORE this
    # main function gets its first line of code executed.  Also, a pytest thing.
    #
    # Return value are computed only once and on demand as determined by
    # the precomputed ordering execution of fixtures.
    #
    # No multiple temporary directories done here (unless you evoked fixture
    # from an entirely different test case/test module/fixture).
    @pytest.fixture(scope="function")
    def fixture_func_create_tmp_dir_abs_path(
        self,
        fixture_func_template_temp_dir_abs_path,
        # redundant to specify other dependencies of sub-fixtures here such as:
        #   fixture_cls_get_settings_dir_abs_path
    ) -> Path:
        """Create and cleanup disposable temporary directory

        This fixture executes every time a test case function references this
        via its own `scope=function`.

        This is the part that does the old unittest's both `setUp()` and `tearDown()`
        but with providing a disposable temporary directory here.
        :param fixture_func_template_temp_dir_abs_path: a test block to create a template temporary dir
        :type fixture_func_template_temp_dir_abs_path: object
        :return: the directory path specification of a newly created temporary directory
        :rtype: pathlib.Path
        """
        # Precomputed order of other fixtures' execution is:
        #   fixture_cls_get_settings_dir_abs_path: completed here
        #   fixture_func_template_temp_dir_abs_path: completed here
        temporary_dir_path = fixture_func_template_temp_dir_abs_path
        # Make a hard copy of the temp_dir string, pass that copy;
        # keep original for directory cleanup
        # this is a secured issue, like avoiding a modified 'rm -rf /#oops'
        # this is by a new value pointer (since Python does not have read-only variable)
        #
        # Of course, the id(obj) will remain the identical after a deepcopy() if code
        # does not make its variable mutable.  A nice insurance policy here.
        original_tmp_dir_path = copy.deepcopy(copy.deepcopy(temporary_dir_path))
        # `yield` statement pauses here within this code body and now start
        # executing the code of the function that is referencing this fixture here.
        yield temporary_dir_path
        # Now execute the caller's code to 100% completion before resuming here.

        # There is a danger of __pycache__ being overlooked here only if this fails
        # while not a showstopper nor alteration of a test result, this __pycache__
        # would just merely clutter the directory.
        shutil.rmtree(original_tmp_dir_path)

    ######################################################################
    #                              FUNCTIONS                             #
    #
    # Functions (formerly unittest or test case) do not have scope and   #
    # rely entirely on fixture(s) to get their scoping constructs for    #
    # its applicable test procedures.                                    #
    #                                                                    #
    # SIDENOTE: This makes chaining/splitting of multiple test cases     #
    # possible here (but not done here).                                 #
    #                                                                    #
    # Function starts executing once the all referenced fixtures get     #
    # completely finished or the keyword `yield` is encountered in one   #
    # of those fixtures.                                                 #
    # (`yield` is in fixture_func_create_tmp_dir_abs_path).              #
    ######################################################################
    #
    # Again, in the test_cs_abs_tmpfile() argument list, ordering of these fixtures
    # do not matter (it's like Python import statements).  But it can get and provide
    # object values from those fixtures (like temporary directory path here).
    #
    # Ordering of all fixtures that got references by any body of statement codes gets
    # 100% evaluated before anything gets its start of code execution.
    def test_cs_abs_tmpfile(
        self,
        # fixture_func_template_temp_dir_abs_path,
        # fixture_module_get_tests_dir_abs_path,
        # fixture_cls_get_settings_dir_abs_path,
        fixture_func_create_tmp_dir_abs_path,
    ):
        """test a premise

        A test procedure that leverages fixtures (via its procedure argument list)

        :param self: this TestSettingsConfig class instantiation
        :type self: TestSettingsConfig class
        :param fixture_func_create_tmp_dir_abs_path: a fixture that provides a
                                                     temporary directory for testing.
        :type fixture_func_create_tmp_dir_abs_path: object"""
        # Precomputed order of other fixtures' execution is:
        #   fixture_module_get_tests_dir_abs_path: completed
        #   fixture_cls_get_settings_dir_abs_path: completed
        #   fixture_func_template_temp_dir_abs_path: completed
        #   fixture_func_create_tmp_dir_abs_path: (before `yield`)
        my_tmp_abs_path = fixture_func_create_tmp_dir_abs_path
        print(f"test_cs_abs_tmpfile: my_tmp_abs_path: {my_tmp_abs_path}")  # NOQA
        assert True
        #   fixture_func_create_tmp_dir_abs_path: (after `yield`): completed

    def test_cs_relative_tmpfile(
        self,
        # fixture_func_template_temp_dir_abs_path,
        # fixture_cls_get_settings_dir_abs_path,
        fixture_func_create_tmp_dir_rel_path,
        # fixture_module_get_tests_dir_abs_path,
    ):
        """test a premise

        A test procedure that leverages fixtures (via its procedure argument list)

        :param self: this TestSettingsConfig class instantiation
        :type self: TestSettingsConfig class
        :param fixture_func_create_tmp_dir_rel_path: a fixture that provides a temporary directory
                        for testing.
        :type fixture_func_create_tmp_dir_rel_path: object"""
        # Precomputed order of other fixtures' execution is:
        #   fixture_module_get_tests_dir_rel_path: completed
        #   fixture_cls_get_settings_dir_rel_path: completed
        #   fixture_func_template_temp_dir_rel_path: completed
        #   fixture_func_create_tmp_dir_rel_path: (before `yield`)
        my_tmp_relative_path = fixture_func_create_tmp_dir_rel_path
        print(f"test_cs_relative_tmpfile: my_tmp_abs_path: {my_tmp_relative_path}")  # NOQA
        assert True


if __name__ == "__main__":
    # if executing this file alone, it tests this file alone.
    # Can execute from any current working directory
    pytest.main([__file__])

    # more, complex variants of pytest
    # pytest.main([__file__, "-n0", "-rAw", "--capture=no", "--no-header"])
    # pytest.main([__file__, "-n0"])  # single-process, single-thread
