Notes on pytest v4.0 (customized for Pelican)

# Simple Test Case
Each test is broken down into four steps:

1. Arrange
2. Act
3. Assert
4. Cleanup

A blank line to separate each grouping of the 4 test steps is a helpful for easier reading.

## Scope Ordering
Basic scope ordering starts with the biggest inclusion scope to smallest:

* **Session** (`scope=session`); pytest, across multiple Python test files.
* **Module** (`scope=module`); within single Python test file.
* **Class** (`scope=class`); within its Python class
* **Function** (`scope=function`); lone focus on one function

Pytest scoping depth is alot simpler than `unittest`.

## Class naming convention under pytest

Pytest test filename shall be in snake_case naming convention and shall begin with `test_`.Add the Pelican source
filename as a suffix to `test_` (i.e. `test_settings.py`, `test_utils.py`)  If a pytest file gets too big
(around +1000 lines), such file
should be divided using additional suffixes (`test_settings_syntax.py`, `test_settings_module.py`)

Class name shall begin with 'Test' and in CamelCase notation. Examples are:
`TestSettings`, `TestServer`, as those are required when using
`pytest`.

Test function name shall begin with '`test_`' and in snake_case notation.  Use its function name that is
being tested as the suffix toward '`test_`'.  Suffixes no longer needs to refer to its Pelican source filename.
Examples are `test_load_source_`, `test_configure_settings`, `test_read_config`.

Organized test functions shall fall into their respective class by its functional characteristic.

## Setup and Teardowns, Scoping ##

As opposite to `unittest`, pytest does allow an assert within the concept of `setUp()`/`tearDown()`.

Downside is that pytest forces one to devise its own `setUp()`/`tearDown()`.  The TREMENDOUSLY better upside
is that once the custom setup/teardown have been finished and polished, many more function tests becomes
easier and shorter to write.

The command to make easier visualizing the setup/teardown is to execute:

    pytest -n0 --setup-plan   [ <file|class|function-name> ]

## Fixtures, the Building Procedural Block ##

The order of `def` fixtures declarations within a source file
does not matter, all `def`s can be in forward-reference order or
backward-referencable.  Only way to reorder a fixture is by including that
fixture's name into the argument list of another fixture's declaration.

NOTE: The execution ordering of function test cases are in sequential order as listed within a module (Python test file).


### Using Fixture ###

Weird thing about putting fixture(s) inside a function/procedure argument list
is that the ordering of its argument DOES NOT matter: this is a block programming
thing, not like most procedural programming languages.

# Fixture Building Blocks #

Supposed that function 'temporary directory path' needs
the support of 'locale' because its filename needs to su

Fixtures that do not get referenced in body of code will not be    #
evaluated, much less get executed; just a lone listing of its      #
fixture in the argument list alone does not make it executable;    #
must use that fixture (fixture_module_get_tests_dir_abs_path) in   #
the body of code as well (a two-fer).                              #

## Fixture Dependencies ##

If a fixture A is in the fixture B's argument list, then fixture B does not
even start to execute until fixture A gets completely executed
(up to any optional `yield` statement found in fixture A).
That "programming" concept alone is useful for making complex conditional
pathways of test blocks simply by referencing the name of its test block.

### Fixture By All, Fixture For All ###

An alternative way to have all test functions use a fixture is not to include its fixture into a function argument list
, is to use the `@pytest.fixture(autouse=True)`.

## Output ##
To check the `STDOUT` (or `STDERR`) console output for a certain phrase/word/number,

```Python
@pytest.fixture(autouse=True)
# If no `scope=`, defaults to `scope=function` ... always.
# `autouse=True` means evoke it no matter if function listed `inject_fixtures` in
# its argument-list or not.
def inject_fixtures(self, caplog):
    self._caplog = caplog
```

Above fixture makes `STDOUT` available on every functions.

### Checking Output ###
To clear the `STDOUT` before using it:

```Python
    with _caplog.at_level(logging.DEBUG):
        _caplog.clear()  # a file-wide global variable

        # <code under test>

    assert " not found" in _caplog.text
```
But more frequently used within a class as:
```Python
    with self.caplog.at_level(logging.DEBUG):
        self._caplog.clear()  # a class-specific variable

        # <code under test>

    assert " not found" in self._caplog.text
```

## CWD: Where Am I? ##
Fastest way to get a bearing of your test data file against a drastically different current working
directory bearing within your test function is to obtain the absolute path of the module (Python test file)
that it resides by using this `__file__.parent` snippet:

This `__file__.parent` ensures a fixed point within the Pelican package and allows `pytest` to be executed from anywhere in the
file system and have its module use itself as its fixed reference point for unit testing.

NOTICE: Yes, pytest must be able to execute from any current working directory and still pass its tests.

The code snippet below provides the absolute path to `tests/` directory which ends
with `tests/` subdirectory; this fixture will always return the same `/<a-pathway-to>/pelican/pelican/tests` value
regardless of the current working directory is at pytest execution time.
```python
from pathlib import Path
import pytest
class TestMyTestEnv:
    @pytest.module(scope="module")
    def fixture_module_get_tests_dir_abs_path(self) -> Path:
        abs_tests_dirpath: Path = Path(__file__).parent  # secret sauce
        return abs_tests_dirpath
```
With the `tests` as our anchor-point for testing, test writing gets easier.

### DATADIR, where's the beef? ###

Often times, test functions needs to use a sample test file (or two); a directory is needed to hold
these sample test files.

OLD-TIMERS: In `Makefile` (or RedHat RPM) nomenclature, this is the `DATADIR`.

If a `settings` directory is used to store all your test data files, then it would be under
the `pelican/pelican/tests/settings` directory.

With the `tests` absolute path and adding `settings`, private `DATADIR` is provided for `settings`/`test_settings_*`
function tests:

```python
from pathlib import Path
import pytest
class TestMySpecificDataDir:
    @pytest.fixture(scope="class")
    def fixture_cls_get_datadir_dir_abs_path(
        self, fixture_module_get_tests_dir_abs_path
    ) -> Path:

        settings_dirpath: Path = fixture_module_get_tests_dir_abs_path / "settings"
        return settings_dirpath
```

Some might ask why isn't this particular code in the form of a function and not a fixture?  Because of pytest
scoping rules: we do not to provide this function to other sessions or modules (test file(s))
or other classes (within the same test file).

But you could make this a function/not-fixture, if your test setup allows it.


## Temporary Directory ##

A fixture to handle the creation and deletion of temporary directory is:
```python
import copy
from pathlib import Path
import shutil
import tempfile
TMP_DIRNAME_SUFFIX = "myapp"
    def fixture_func_create_tmp_dir_abs_path(
        self, fixture_cls_get_datadir_abs_path,
    ):
        temporary_dir_path: Path = Path(
            tempfile.mkdtemp(
                dir=fixture_cls_get_datadir_abs_path,
                suffix=TMP_DIRNAME_SUFFIX
            )
        )
        original_tmp_dir_path = copy.deepcopy(temporary_dir_path)

        yield temporary_dir_path  # make available its dirname

        shutil.rmtree(original_tmp_dir_path)
```

## Avoiding Parallelization
Sometimes, there is a need for a critical section during testing; `sys.modules[]` is rather sensitive in its
addition/removal of modules to the Python runtime.

A fixture that enforces serialization of function unit test comprise two fixtures:
1. a lock file
2. a wait-loop

A working exaxmple of a lock file fixture is:
```python
import filelock
import contextlib
import os
import pytest

@pytest.fixture(scope="session")
def fixture_session_lock(tmp_path_factory):
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / "serial.lock"
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        os.remove(path=lock_file)
```
The above session-scope fixture will leverage pytest `tmp_path_factory` to create a temporary directory
for its session-wide (single pytest, single `serial.lock`) lock file to be used by all test functions.

Upon an error, the lock file gets deleted.

If different lockfile is desired (on a per-class or per-module basis), simply drop the `scope=` down to `class` and
relocate the code snippet of fixture_func_serial to under its desired class.

The serializaer (wait-loop) then builds on top of the lock file fixture:
```python
import filelock
import contextlib
import os
import pytest
class TestThingsSequentially:
    @pytest.fixture(scope="function")
    def fixture_func_serial(self, fixture_session_lock):
        """mark function test as serial/sequential ordering

        Include `serial` in the function's argument list ensures
        that no other test(s) also having `serial` in its argument list
        shall run."""
        with fixture_session_lock.acquire(poll_interval=0.1):
            yield
```
Then simply add the `fixture_func_serial` to each test function declarator's argument list to
start enforcing 1-process testing:
```python
def test_my_system_access(self, fixture_func_serial):
    # Arrange
    do_sensitive_syscalls()
    # Act
    # Assert
    # Cleanup
    undo_sensitive_syscalls()

def test_other_system_access(self, fixture_func_serial):
    # Arrange
    # Act
    # Assert
    # Cleanup
    do_sensistive_syscalls()
```
Now, both `test_[my|other]_system_access` will never execute in parallel.

## Internationalization ##
```python
import locale
import pytest

@pytest.fixture(scope="session")
def fixture_session_locale_all():
    """Support the locale"""
    # Save original locale
    old_locale = locale.setlocale(locale.LC_ALL)
    locale.setlocale(locale.LC_ALL, "C")

    yield  # execute a unit test

    # Restore original locale
    locale.setlocale(locale.LC_ALL, old_locale)
```
If specific locale is desired, change the `"C"` portion of the
code, rename the function in code snippet above.


# Appendix #

## Appendix A - Windows-centric ##

NOTE: Microsoft Windows prohibits the use of `CON`, `PRN`, `AUX`, `CLOCK$`, `NUL`, `COM1`, `COM2`,
`COM3`, `COM4`, `COM5`, `COM6`, `COM7`, `COM8`, `COM9`, `LPT1`, `LPT2`, `LPT3`, `LPT4`, `LPT5`,
`LPT6`, `LPT7`, `LPT8`, `LPT9` as a filename, so we should be careful not to allow those as a Python module name.
Using most of those typically results in a hard-hang (no Ctrl-C available) within its console.
