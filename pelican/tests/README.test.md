Notes on pytest v4.0 (customized for Pelican)

## Class naming convention under pytest

Class name shall begin with 'Test' and in camelcase notation. Examples are:
`TestSettings`, `TestServer`.

(Unit) Test name shall begin with 'test_' and in snake case notation.  Examples
are:  `test_settings`, `test_settings_config`, `test_settings_module`.

## Setup and Teardowns, Scoping ##

Cannot do any `assert` of any kind within `setUp()`/`tearDown()`
and `setup_method()`/`teardown_method()` functions; (well, you can, but
you'd be subjected to frequent breakage in future pyTest.)

Overview on scoping of test preparation:
* `setUp()` - on a per-unittest basis
* `setup_method()` - on a per-class/per-method basis; setup any state tied to the
execution of the given function. Invoked for every test function in the
module; It is possible for `setup_method`/`teardown_method` pairs to be
invoked multiple times per testing process.
* `teardown_method()` - on a per-class/per-method basis; teardown any
state that was previously setup with a setup_function call.;
NOT called if a test got skipped/assert-FAILED;
It is possible for `setup_method`/`teardown_method` pairs to be invoked multiple times per testing process.
* `tearDown()` - on a per-unittest basis

Cannot put cleanup handler interacting with the `sys.modules` inside the
`setUp()`/`tearDown()` or its fixture due to Python scoping, retention of
module's name across each test functions; in doing so will fail under
parallelism of unit tests.

## Temporary Directory ##

* Use the `tmp_path` fixture which will provide a temporary directory unique
to each test function.
* Use the `tmp_path_factory`, a session-scoped fixture which can be used to
create arbitrary temporary directories from any other fixture or test.
* `mktemp`, et al. MUST BE performed within each `test_` non-fixture
  procedure until then, we cannot parallel-test this entire file, only
  1-process test (FIXED)


## STDOUT/STDERR ##
Outputs of Pelican can be had by using `--show-capture=[no/log/all/stderr/stdout]` to the pytest CLI.

The `capsys`, `capsysbinary`, `capfd`, and `capfdbinary` fixtures allow access
to `STDOUT`/`STDERR` output created during test execution.

Using `caplog.clear()` impacts ALL `STDOUT` capture across
all parallelized pytest unit tests.  Use sparingly (until fixed by Python)

A simple method is:
```Python
def test_myoutput(capsys):  # or use "capfd" for fd-level
    print("hello")
    sys.stderr.write("world\n")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == "world\n"
    print("next")
    captured = capsys.readouterr()
    assert captured.out == "next\n"
```
Robust (IMHO, preferred) method is:

```Python
import unittest
import capsys

@pytest.fixture(autouse=True)
def inject_fixtures(self, caplog):
    """add support for performing assert in `caplog.text` output"""
    self._caplog = caplog
    self._capsys = capsys


class TestMyStuff(unittest.TestCase):
    def test_my_unit_test(self):
        # Pelican has hijacked unittest, so we must insert _capsys/_caplog
        captured = self._capsys.readouterr()
        with self._caplog.at_level(logging.DEBUG):
            # do something output'y.
            with self._capsys.disable():
            # do something with capture output suppressed
            # do something with capture output resumed
            assert captured.out == "output'y"
```

## Dynamic Module
On handling dynamic Python modules used for Pelican configuration settings file:

There are three levels of entanglement as determined by `sys.getrefcount(my_module)`,
the reference count that other modules make dependencies upon actually
determines how one can remove an intricate, deeply-entrenched module.

Last-always test to ensure no user-supplied modules are left behind as
installed (DONE in `tearDown()` function).  Calling `configure_settings()` in
pytest often requires a corresponding cleanup by calling

```Python
    del sys.modules[DEFAULT_MODULE_NAME]
```

To avoid all that Pelican module-"entanglement", we chose a different
"top-level" module name thereby bypassing the module name `pelican`.
Ideally, we probably should be choosing `pelicancont` over `default_conf`,
simply because Python may take over `default_conf` as part of their future
reloadable Python configuration settings module and that Pelican is by
design doing so much circular dependencies.

To reduce this excessive module reference count, a major rework on Pelican
toward a singular but NON-CIRCULAR `import` would be required but this is not
needed ... yet but may get broke in future `importlib`.

Do a test that built-in modules remains left as untouched (DONE, `tearDown()`)

## Multi-Process `pytest`
Tests will crap out in N-processes if using `mktemp`, et al.; within `setUp()`.

# References
* [tmp_path](https://docs.pytest.org/en/latest/how-to/tmp_path.html)
* [Capture STDOUT/STDERR](https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html)
