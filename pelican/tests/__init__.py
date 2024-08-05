#
# This pelican/tests/__init__.py is to stay largely empty.
#
# Presence of this __init__.py file is required in the tests directory
# to assist pytest/unittest in locating the Pelican package `basedir` (aka root)
# directory:
# The primary mechanism to identifying this `basedir` directory is the first
# absense of an __init__.py file while traversing up the directory tree.
#
# To make a common function or fixture available to all test script files,
# insert it into the 'conftest.py' (for pytest) or the # 'support.py' (unittest).
#
# Reference:
#  * https://docs.pytest.org/en/latest/explanation/goodpractices.html#test-package-name
#  * https://docs.pytest.org/en/latest/explanation/goodpractices.html#choosing-a-test-layout-import-rules
#  * https://docs.pytest.org/en/6.2.x/pythonpath.html#test-modules-conftest-py-files-inside-packages
#
## import logging
# import warnings
#
# from pelican.log import log_warnings
#
# redirect warnings module to use logging instead
# log_warnings()
#
# setup warnings to log DeprecationWarning's and error on
# warnings in pelican's codebase
# warnings.simplefilter("default", DeprecationWarning)
# warnings.filterwarnings("error", ".*", Warning, "pelican")

# Add a NullHandler to silence warning about no available handlers
# logging.getLogger().addHandler(logging.NullHandler())
