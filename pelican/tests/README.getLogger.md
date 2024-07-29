
## getLogger()

First to call getLogger in Pelican are:

  ```
  __main__/segment.py
      log = getLogger("rich")
  __main__/filter.py
      logger = logging.getLogger('watchfiles.watcher')
  __main__/main.py/watchfile-package
      logger = logging.getLogger('watchfiles.main')
  __main__/run.py/watchfile-package
      logger = logging.getLogger('watchfiles.main')
  __main__/utils.py
      logger = logging.getLogger(__name__)
  __main__/cache.py
      logger = logging.getLogger(__name__)
  __main__/settings.py
      logger = logging.getLogger(__name__)
  __main__/urlwrappers.py
      logger = logging.getLogger(__name__)
  __main__/\_utils.h/plugins
      logger = logging.getLogger(__name__)
  __main__/blockprocessors.py
      logger = logging.getLogger("MARKDOWN")
  __main__/core.py
      logger = logging.getLogger("MARKDOWN")
  __main__/readers.py
      logger = logging.getLogger(__name__)
  __main__/generators.py
      logger = logging.getLogger(__name__)
  __main__/server.py
      logger = logging.getLogger(__name__)
  __main__/paginator.py
      logger = logging.getLogger(__name__)
  __main__/writers.py
      logger = logging.getLogger(__name__)
  __main__/__init__.py
      logger = logging.getLogger(__name__)

  init()/log.py:151
      log_warnings()/logging/__init__.py
          tests/__init__.py
              log\_warnings()
                pelican.log()  (aka log\_warnings() alias)
```


#   Devil is in the Details:

No matter how hard you try, because any test file resides under the
Pelican source package, this pytest script will ALWAYS pick up and preload
the Pelican `FatalLogger` logging.Logger class (that `pelican/__init.py__`
created from `log.init` (in `log.py`, aka `init_logging()`) before running any
of log-related tests given below in this file.

This test deals ONLY with the installed Pelican package (as opposed to
uninstalled Pelican package).

Some overviews to reiterate here:
*  logging.Logger is a singleton-class;
*  logging.Logger uses same instance throughout the entire package until its
       rootLogger gets swapped out (like our FatalLogger class).
*  logging.root.manager is the same for ALL subclasses of the logging class.
*  Zeroizing the logging.root.manager is tricky to do, it keeps coming back
       by some Python modules.
*  level only is used by its Logger subclass (and do not propagate upward)

# To learn the names of all loggers that exist:

```console
Logger.manager
Logger.manager.loggerDict
# To learn all the facts about one particular logger:
Logger.name
Logger.level
Logger.parent
Logger.propagate
Logger.filters
Logger.handlers
Logger.disabled
# Learning about a Handler in the handlers list:
Handler.level
Handler.filters
Handler.formatter
logging_tree.printout() reports:
<--""
    Level NOTSET so inherits level NOTSET
    Handler <NullHandler (NOTSET)>
    Handler <_LiveLoggingStreamHandler (NOTSET)>
      Formatter <_pytest.logging.ColoredLevelFormatter object at 0x7fecbc15e410>
    Handler <_FileHandler /dev/null (NOTSET)>
      Formatter <_pytest.logging.DatetimeFormatter object at 0x7fecbc15e310>
    Handler <LogCaptureHandler (NOTSET)>
      Formatter <_pytest.logging.ColoredLevelFormatter object at 0x7fecbcc21290>
    Handler <LogCaptureHandler (NOTSET)>
      Formatter <_pytest.logging.ColoredLevelFormatter object at 0x7fecbcc21290>
    |
    o<--"MARKDOWN"
    |   Level NOTSET so inherits level NOTSET
    |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |
    o<--[concurrent]
    |   |
    |   o<--"concurrent.futures"
    |       Level NOTSET so inherits level NOTSET
    |
    o<--"pelican"
    |   Level NOTSET so inherits level NOTSET
    |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.cache"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.contents"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.generators"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.paginator"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--[pelican.plugins]
    |   |   |
    |   |   o<--"pelican.plugins._utils"
    |   |       Level NOTSET so inherits level NOTSET
    |   |       Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.readers"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.server"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.settings"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.urlwrappers"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.utils"
    |   |   Level NOTSET so inherits level NOTSET
    |   |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |   |
    |   o<--"pelican.writers"
    |       Level NOTSET so inherits level NOTSET
    |       Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |
    o<--[py]
    |   |
    |   o<--"py.warnings"
    |       Level DEBUG
    |       Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
    |
    o<--"rich"
    |   Level NOTSET so inherits level NOTSET
    |
    o<--[watchfiles]
        |
        o<--"watchfiles.main"
        |   Level NOTSET so inherits level NOTSET
        |   Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
        |
        o<--"watchfiles.watcher"
            Level NOTSET so inherits level NOTSET
            Filter <pelican.log.LimitFilter object at 0x7fecbc1af0d0>
   To ensure that unit tests are working, preemptively unloading `FatalLogger`
   class is that critical step before most tests within this unit test file.
```
 CLI command to see a list of ALL logging.Logger subclasses:

```shell
python -c "import logging;print(logging.root.manager.loggerDict)"
```

Raw `python` in an isolated non-Python directory and a clean ENVVAR gets
you the following list of handlers:

```console
  []  # empty list
```

Pycharm `python -i` within Pelican package directory gets you ALL of
following list of handlers (including whereas noted below, listed in insertion
order):
```console
<Logger pkg_resources.extern.packaging.tags (WARNING)>,
<FatalLogger pkg_resources.extern.packaging (WARNING)>,
<FatalLogger pkg_resources.extern (WARNING)>,
<FatalLogger pkg_resources (WARNING)>,
<Logger setuptools.extern.packaging.tags (WARNING)>,
<FatalLogger setuptools.extern.packaging (WARNING)>,
<FatalLogger setuptools.extern (WARNING)>,
<FatalLogger setuptools (WARNING)>,
<Logger setuptools.config._apply_pyprojecttoml (WARNING)>,
<FatalLogger setuptools.config (WARNING)>,
<Logger setuptools.config.pyprojecttoml (WARNING)>,
#
# (Starting here, only the `python -i` within Pelican package directory
# gets you the following additional handlers but for PyCharm, it continues below):
<Logger concurrent.futures (WARNING)>,
<FatalLogger concurrent (WARNING)>,
<Logger asyncio (WARNING)>,
<Logger rich (WARNING)>,
<FatalLogger watchfiles.watcher (WARNING)>,
<FatalLogger watchfiles (WARNING)>,
<FatalLogger watchfiles.main (WARNING)>,
<FatalLogger pelican.utils (WARNING)>,
<FatalLogger pelican (WARNING)>,
<FatalLogger pelican.cache (WARNING)>,
<FatalLogger pelican.settings (WARNING)>,
<FatalLogger pelican.urlwrappers (WARNING)>,
<FatalLogger pelican.contents (WARNING)>,
<FatalLogger pelican.plugins._utils (WARNING)>,
<FatalLogger pelican.plugins (WARNING)>,
<FatalLogger MARKDOWN (WARNING)>,
<FatalLogger pelican.readers (WARNING)>,
<FatalLogger pelican.generators (WARNING)>,
<FatalLogger pelican.server (WARNING)>,
<FatalLogger pelican.paginator (WARNING)>,
<FatalLogger pelican.writers (WARNING)>,
<FatalLogger py.warnings (DEBUG)>,
<FatalLogger py (WARNING)>,
<FatalLogger root (WARNING)>
```

So it is apparent that having a stable test environment just for testing our
app-specific logging has become a rather iffy proposition when having to deal with
all the other handlers: hence, we need here this ultra-clean logging setup.

    from pelican.log import init as init_pelican_logger


Always check for `.level` attribute in int type using logging.Logger class

Add a NullHandler to silence warning about no available handlers

    logging.getLogger().addHandler(logging.NullHandler())

# References
Source: https://til.tafkas.net/posts/-resetting-python-logging-before-running-tests/
