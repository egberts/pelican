Notes on pytest v4.0 (customized for Pelican)

## Simple Test Case
Each test is broken down into four steps:

1. Arrange
2. Act
3. Assert
4. Cleanup

## Scope Ordering
The ordering of test cases are in nested order starting with biggest
inclusion scope to smallest:

* Session (`scope=session`)
* Module (`scope=module`)
* Class (`scope=class`)
* Function (`scope=function`)

This scoping depth is alot simpler than `unittest`.

## Class naming convention under pytest

Pytest filename shall begin with `test_`.  Add the Pelican source filename as a suffix to `test_`.
(i.e. `test_settings.py`, `test_utils.py`)  If a pytest file gets too big (around +1000 lines), such file
should be divided using additional suffixes (`test_settings_syntax.py`, `test_settings_module.py`)

Class name shall begin with 'Test' and in CamelCase notation. Examples are:
`TestSettings`, `TestServer`, as those are required when using
`pytest`.

Test function name shall begin with '`test_`' and in snake_case notation.  Use its function name that is
being tested as the suffix toward '`test_`'.  Suffixes no longer needs to refer to its Pelican source filename.
Examples are `test_load_source_`, `test_configure_settings`, `test_read_config`.


Organized test functions shall fall into their respective class by its functional characteristic.

## Setup and Teardowns, Scoping ##

As opposed to `unittest`, pytest will allow an assert within `setUp()`/`tearDown()`.

Downside is that pytest forces one to devise its own `setUp()`/`tearDown()`.  The TREMENDOUSLY better upside
is that once the custom setup/teardown have been finished and polished, many more function tests becomes
easier and shorter to write.  This command makes it easier to visualize setup/teardown in pytest:

    pytest -n0 --setup-plan   [ <file|class|function-name> ]

## Fixtures, the Building Procedural Block ##

The order of `def` fixtures/functions declarations within a source file
does not matter, all `def`s can be in forward-reference order or
backward-referencable.  Only way to reorder a fixture is by including that
fixture's name into the argument list of another fixture's declaration.

### Using Fixture ###

Weird thing about putting fixture(s) inside a function/procedure argument list
is that the ordering of its argument DOES NOT matter: this is a block programming
thing, not like most procedural programming languages.

#### Fixture Building Blocks ####

Supposed that function 'temporary directory path' needs
the support of 'locale' because its filename needs to su

Fixtures that do not get referenced in body of code will not be    #
evaluated, much less get executed; just a lone listing of its      #
fixture in the argument list alone does not make it executable;    #
must use that fixture (fixture_module_get_tests_dir_abs_path) in   #
the body of code as well (a two-fer).                              #

##### Fixture Dependencies #####

If a fixture A is in the fixture B's argument list, then fixture B does not
even start to execute until fixture A gets completely executed
(up to any optional `yield` statement found in fixture A).
That "programming" concept alone is useful for making complex conditional
pathways of test blocks simply by referencing the name of its test block.

#### Fixture By All, Fixture For All

An alternative way to use fixture is not to include its fixture into a function argument list
, is to use the `@pytest.fixture(autouse=True)`.

#### Output ####
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

#### Checking Output ####
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


## Temporary Directory ##

## Module Name ##

# Appendix #

## Appendix A - Windows-centric ##

NOTE: Microsoft Windows does not allow the use of `CON`, `PRN`, `AUX`, `CLOCK$`, `NUL`, `COM1`, `COM2`,
`COM3`, `COM4`, `COM5`, `COM6`, `COM7`, `COM8`, `COM9`, `LPT1`, `LPT2`, `LPT3`, `LPT4`, `LPT5`,
`LPT6`, `LPT7`, `LPT8`, `LPT9` as a filename, so we should be careful not to allow those as a Python module name.
Using most of those typically results in a hard-hang (no Ctrl-C available) within its console.
