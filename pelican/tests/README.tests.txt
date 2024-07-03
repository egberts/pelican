To help get your bearings around multiple directories within this 
package and used as a document example, the example of this package 
root directory in here is:

    GITHUB_PELICAN_DIRPATH="~/work/github/pelican"

QUICK TEST LIST
===============

To get a complete list of all test names, execute in any subdirectory
along the `pelican/pelican/tests` path:

    pytest --collect-only -q

Choose your test, then execute for example as:

    # if in pelican/pelican/tests subdirectory
    pytest test_cli.py::TestParseOverrides::test_flags    

    # if in pelican/pelican subdirectory
    pytest tests/test_contents.py::TestPage::test_signal

    # if in top_root of pelican subdirectory
    pytest pelican/tests/test_contents.py::TestPage::test_use_args

Quick HOWTO
===========

To perform unittest of an uninstalled Pelican package, we can
exercise specific tests by using pytest in a number of ways:


    cd $GITHUB_PELICAN_DIRPATH
    pytest pelican/tests/tests_readers.py

    cd ${GITHUB_PELICAN_DIRPATH}/pelican
    pytest tests/test_utils.py
    pytest tests

    cd ${GITHUB_PELICAN_DIRPATH}/pelican/test
    # Execute all unittests
    pytest     # in the current working directory of 'tests'
    # Execute all classes of a test file
    pytest test_content.py
    # Execute a specific class of test
    pytest test_settings.py::TestSettingsConfiguration

It is easiest to perform unit test inside the `pelican/pelican/tests` directory.

WARNING: Be careful of your current (`$CWD`) directory, if it does not have
a `__init__.py` file, your unit test MAY revert to the installed version
of Pelican.

Organization of Pelican unit test are:

    output/    - A directory (always in git repo, never deleted)
                 Never use the '-d' delete output option if your 
                 $CWD or Pelican-PATH is in this tests directory.

    content/   - store all content files for your unit test(s)


Environment of pytest
---------------------
To interested test developers, Pytest will look at the following 
files for environmental settings:

    pelican/tox.ini (via pytest tox plugin)
    pelican/pyproject.toml (via pytest toml plugin)
    /home/wolfe/virtualenvs/pelican/pyvenv.cfg

Your unittest should clear any pre-existing environment variables if 
your unittest case is dependent on this environment variable(s).


REQUIREMENTS
============
Pelican pytest requires the following dependencies:

    $ sudo dpkg-reconfigure locales
      <select ALL checkbox>ENTER
      <reselect your own locale>ENTER
      # wait long time for populating many locales
    $ pip3 -r requirements/test.pip

For non-virtual Python on Debian 12, do:
    
    $ sudo dpkg-reconfigure locales
      <select ALL checkbox>ENTER
      <reselect your own locale>ENTER
      # wait long time for populating many locales
    $ sudo apt install python3-pygments python3-pytest 
    $ sudo apt install python3-pytest-cov python3-pytest-xdist 
    $ sudo apt textualize-markdown python3-bs4 python3-lxml
    $ sudo apt python3-typogrify

NOTE:  No nose, no unittest, just pytest used here.
       Also use python3-markdown (not yet python3-markdown2)

How does pytest get its bearing?
================================
The __init__.py gives the first clue to its bearing
of where the package is and its test files.

'tests' (and 'test') is the standard directory name for pytest to find.

pytest will find pelican/pelican/tests/test_XXX.py and realize it is 
NOT part of a package given that there's no __init__.py file in the 
same folder.  It will then add pelican/pelican/tests to sys.path in 
order to import 'test_XXX.py' as the module 'test_XXX'.

This Pelican Overview
=====================
To see general overview of Pelican as supplied by the Python code docstrings:

    $ cd $GITHUB_PELICAN_DIRPATH
    $ python -c "import pelican;help(pelican)"

