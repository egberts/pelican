This document details the usage, development, and maintenance of unit testings
of Pelican and its content in the `pelican/pelican/tests` directory.

## Installation ##
Check the `pelican/requirements/test.pip` for all Python packages needed
to conduct a unit test in Pelican. To bring your test environment up to current, execute:

```shell
cd <your-pelican-root-package-directory>
pip install -r requirements/test.pip
```

## Usage Guide ##

To exercise all unit testings of Pelican pacakge, execute:
```shell
cd <your-Pelican-root-package-directory>
pytest
```


Three ways to exercise a specific Python test script file:

1. by explicit path to a specific test file,
2. by an entire single directory of test files, and
3. by search pattern(s).

### Specific Test File ###

To exercise a specific test file, like `test_settings.py` from
the root directory of Pelican package, execute:

```shell
pytest pelican/tests/test_settings.py
```
output looks like:
```console
$ pytest pelican/tests/test_settings.py
Test session starts (platform: linux, Python 3.11.2, pytest 8.2.2, pytest-sugar 1.0.0)
rootdir: /home/wolfe/admin/websites/egbert.net/pelican-lost-stuff
configfile: tox.ini
plugins: cov-5.0.0, xdist-3.6.1, anyio-4.4.0, sugar-1.0.0
6 workers [20 items]    collecting ...

 pelican/tests/test_settings.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓             100% ██████████

Results (0.86s):
      20 passed
```

For bare minimum test output, execute:
```shell
pytest -q --no-header --no-summary pelican/tests/test_settings.py
```
and its output looks like:
```console
bringing up nodes...

 pelican/tests/test_settings.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓             100% ██████████

Results (0.83s):
      20 passed
```

### Directory of Test Files ###

To exercise an entire directory of test files, from the root
directory of Pelican package, execute:

```shell
pytest pelican/tests
```
output looks like:
```console
bringing up nodes...

 pelican/tests/test_contents.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓ 13% █▍
 pelican/tests/build_test/test_build_files.py ssssss               7% ▊
 pelican/tests/test_generators.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓ 28% ██▉
 pelican/tests/test_contents.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓                   36% ███▋
 pelican/tests/test_cache.py ✓✓✓✓                                 32% ███▎
 pelican/tests/test_importer.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓                40% ████
 pelican/tests/test_generators.py ✓✓✓✓✓✓✓                         39% ███▉
 pelican/tests/test_cli.py ✓✓✓✓✓✓✓                                35% ███▌
 pelican/tests/test_log.py ⨯                                      40% ████
 pelican/tests/test_paginator.py ✓✓✓                              41% ████▎
 pelican/tests/test_importer.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓                  99% █████████▉
 pelican/tests/test_generators.py ✓✓✓✓✓✓✓✓✓✓✓✓✓                  100% ██████████
 pelican/tests/test_pelican.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓                     96% █████████▋
 pelican/tests/test_cache.py ✓✓✓✓                                 56% █████▋
 pelican/tests/test_readers.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓ 62% ██████▎
                               ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓             98% █████████▊
 pelican/tests/test_rstdirectives.py ✓✓✓                          68% ██████▉
 pelican/tests/test_server.py ✓                                   69% ██████▉
 pelican/tests/test_settings.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓              75% ███████▌
 pelican/tests/test_settings_syntax.py ✓✓✓✓✓✓✓✓                   78% ███████▊
 pelican/tests/test_testsuite.py ✓                                78% ███████▉
 pelican/tests/test_urlwrappers.py ✓✓✓✓                           80% ███████▉
 pelican/tests/test_utils.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓     92% █████████▎
 pelican/tests/test_plugins.py ✓✓✓✓✓✓                             97% █████████▋

Results (3.53s):
     296 passed
       1 failed
         - ../pelican/pelican/tests/test_log.py:35 TestLog.test_log_filter
       6 skipped
```

## Test By Search Pattern ##
To cover certain name of class/function test(s) by its keyword, supply a
search pattern to the pytest `-k` option:
```shell
pytest -rpfs -k custom
```
and all `test_*` function and class names having the subword `custom` will
be included in the `pytest` session:
```console

 pelican/tests/test_paginator.py ✓✓                               33% ███▍
 pelican/tests/test_generators.py ✓                               22% ██▎
 pelican/tests/test_importer.py ✓✓✓✓                              78% ███████▊
 pelican/tests/test_pelican.py ✓✓                                100% ██████████
=========================== short test summary info ============================
PASSED pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_custom_posts_put_in_own_dir_and_catagory_sub_dir
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_unless_custom_post_all_items_should_be_pages_or_posts
PASSED pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern
PASSED pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_custom_posts_put_in_own_dir
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_recognise_custom_post_type
PASSED pelican/tests/test_generators.py::TestGenerator::test_custom_jinja_environment
PASSED pelican/tests/test_generators.py::TestGenerator::test_custom_jinja_environment
PASSED pelican/tests/test_generators.py::TestGenerator::test_custom_jinja_environment
PASSED pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern_last_page
PASSED pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern_last_page
PASSED pelican/tests/test_paginator.py::TestPage::test_custom_pagination_pattern_last_page
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_unless_custom_post_all_items_should_be_pages_or_posts
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_unless_custom_post_all_items_should_be_pages_or_posts
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_recognise_custom_post_type
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_recognise_custom_post_type
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_custom_posts_put_in_own_dir
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_custom_posts_put_in_own_dir
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_custom_posts_put_in_own_dir_and_catagory_sub_dir
PASSED pelican/tests/test_pelican.py::TestPelican::test_custom_generation_works
PASSED pelican/tests/test_importer.py::TestWordpressXmlImporter::test_custom_posts_put_in_own_dir_and_catagory_sub_dir
PASSED pelican/tests/test_pelican.py::TestPelican::test_custom_locale_generation_works
PASSED pelican/tests/test_pelican.py::TestPelican::test_custom_generation_works
PASSED pelican/tests/test_pelican.py::TestPelican::test_custom_generation_works
PASSED pelican/tests/test_pelican.py::TestPelican::test_custom_locale_generation_works
PASSED pelican/tests/test_pelican.py::TestPelican::test_custom_locale_generation_works

Results (1.70s):
       9 passed
```

**TIPS**: Testers and developers may find that search pattern easier to
use than file/directory: the biggest confusion of using `pytest` with
a filespec (path to a file/directory), is what exactly is this current
working directory (`CWD`) is it currently in ...  now.

An example of executing the test script file but within different
directory throughout the Pelican package.
```shell
cd <your-Pelican-root-package-directory>
pytest pelican/tests/test_settings.py
cd pelican
pytest tests/test_settings.py
cd tests
pytest test_settings.py
cd ../../docs
pytest ../pelican/tests/test_settings.py
```

An example of executing the same directory of test script files but
within different directory throughout the Pelican package.
```shell
cd <your-Pelican-root-package-directory>
pytest pelican/tests
cd pelican
pytest tests/
cd tests
pytest
cd ../../docs
pytest ../pelican/tests
```

**IMPORTANT**: the `CWD` becomes an important part of any unit test
dealing with file-related and/or directory-related functionality.

**WARNING**: Sadly, many unit tests have been known to fail with the
above sequence of commands that navigates around the Pelican package
directory tree because this unit test function did not cleanly restore
the original `$CWD` after performing its unit test; also have been
known to fail when not having establish the proper `CWD` before
performing its file-related or directory-related unit test.

# `conftest.py`, a Directory-Wide Module #

`conftest.py` is a `pytest` script file.

`conftest.py` currently resides only within the `pelican/pelican/tests`
directory.

`conftest.py` provides fixtures and functions for use by other
test script files ONLY within that directory.

Much like Pelican's  `support.py` for `unittest`, `conftest.py` provides
common support of fixtures and functions needed by other `test_*`
script files ... within its subdirectory.

**INSIGHT**: `pytest` and `conftest.py` does not transcend across
subdirectories like Python modules can do with `import`.

**CRITICAL**: `conftest.py` also provides supports to pre-existing
`unittest` script files as well.


**NOTICE:** Introducing `conftest.py` into a subdirectory containing
`unittest` script file(s) WILL cause `pytest` to hijack the
Python standard logger from `unittest` used so be careful when
mixing both test packages: the scariest thing?  An empty `conftest.py` will do all that too.

**WARNING:** pytest will register additional custom handlers to
the root logger to be able to capture log records emitted in your code, so you can test whether your program logging behaviour is correct.
