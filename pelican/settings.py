import copy
import errno
import importlib.util
import inspect
import locale
import logging
import os
import re
import sys
from os.path import isabs
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional

from pelican.log import LimitFilter

DEFAULT_MODULE_NAME: str = "pelicanconf"

logger = logging.getLogger(__name__)

Settings = Dict[str, Any]

DEFAULT_THEME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "themes", "notmyidea"
)
DEFAULT_CONFIG = {
    "PATH": os.curdir,
    "ARTICLE_PATHS": [""],
    "ARTICLE_EXCLUDES": [],
    "PAGE_PATHS": ["pages"],
    "PAGE_EXCLUDES": [],
    "THEME": DEFAULT_THEME,
    "OUTPUT_PATH": "output",
    "READERS": {},
    "STATIC_PATHS": ["images"],
    "STATIC_EXCLUDES": [],
    "STATIC_EXCLUDE_SOURCES": True,
    "THEME_STATIC_DIR": "theme",
    "THEME_STATIC_PATHS": [
        "static",
    ],
    "FEED_ALL_ATOM": "feeds/all.atom.xml",
    "CATEGORY_FEED_ATOM": "feeds/{slug}.atom.xml",
    "AUTHOR_FEED_ATOM": "feeds/{slug}.atom.xml",
    "AUTHOR_FEED_RSS": "feeds/{slug}.rss.xml",
    "TRANSLATION_FEED_ATOM": "feeds/all-{lang}.atom.xml",
    "FEED_MAX_ITEMS": 100,
    "RSS_FEED_SUMMARY_ONLY": True,
    "FEED_APPEND_REF": False,
    "SITEURL": "",
    "SITENAME": "A Pelican Blog",
    "DISPLAY_PAGES_ON_MENU": True,
    "DISPLAY_CATEGORIES_ON_MENU": True,
    "DOCUTILS_SETTINGS": {},
    "OUTPUT_SOURCES": False,
    "OUTPUT_SOURCES_EXTENSION": ".text",
    "USE_FOLDER_AS_CATEGORY": True,
    "DEFAULT_CATEGORY": "misc",
    "WITH_FUTURE_DATES": True,
    "CSS_FILE": "main.css",
    "NEWEST_FIRST_ARCHIVES": True,
    "REVERSE_CATEGORY_ORDER": False,
    "DELETE_OUTPUT_DIRECTORY": False,
    "OUTPUT_RETENTION": [],
    "INDEX_SAVE_AS": "index.html",
    "ARTICLE_URL": "{slug}.html",
    "ARTICLE_SAVE_AS": "{slug}.html",
    "ARTICLE_ORDER_BY": "reversed-date",
    "ARTICLE_LANG_URL": "{slug}-{lang}.html",
    "ARTICLE_LANG_SAVE_AS": "{slug}-{lang}.html",
    "DRAFT_URL": "drafts/{slug}.html",
    "DRAFT_SAVE_AS": "drafts/{slug}.html",
    "DRAFT_LANG_URL": "drafts/{slug}-{lang}.html",
    "DRAFT_LANG_SAVE_AS": "drafts/{slug}-{lang}.html",
    "PAGE_URL": "pages/{slug}.html",
    "PAGE_SAVE_AS": "pages/{slug}.html",
    "PAGE_ORDER_BY": "basename",
    "PAGE_LANG_URL": "pages/{slug}-{lang}.html",
    "PAGE_LANG_SAVE_AS": "pages/{slug}-{lang}.html",
    "DRAFT_PAGE_URL": "drafts/pages/{slug}.html",
    "DRAFT_PAGE_SAVE_AS": "drafts/pages/{slug}.html",
    "DRAFT_PAGE_LANG_URL": "drafts/pages/{slug}-{lang}.html",
    "DRAFT_PAGE_LANG_SAVE_AS": "drafts/pages/{slug}-{lang}.html",
    "STATIC_URL": "{path}",
    "STATIC_SAVE_AS": "{path}",
    "STATIC_CREATE_LINKS": False,
    "STATIC_CHECK_IF_MODIFIED": False,
    "CATEGORY_URL": "category/{slug}.html",
    "CATEGORY_SAVE_AS": "category/{slug}.html",
    "TAG_URL": "tag/{slug}.html",
    "TAG_SAVE_AS": "tag/{slug}.html",
    "AUTHOR_URL": "author/{slug}.html",
    "AUTHOR_SAVE_AS": "author/{slug}.html",
    "PAGINATION_PATTERNS": [
        (1, "{name}{extension}", "{name}{extension}"),
        (2, "{name}{number}{extension}", "{name}{number}{extension}"),
    ],
    "YEAR_ARCHIVE_URL": "",
    "YEAR_ARCHIVE_SAVE_AS": "",
    "MONTH_ARCHIVE_URL": "",
    "MONTH_ARCHIVE_SAVE_AS": "",
    "DAY_ARCHIVE_URL": "",
    "DAY_ARCHIVE_SAVE_AS": "",
    "RELATIVE_URLS": False,
    "DEFAULT_LANG": "en",
    "ARTICLE_TRANSLATION_ID": "slug",
    "PAGE_TRANSLATION_ID": "slug",
    "DIRECT_TEMPLATES": ["index", "tags", "categories", "authors", "archives"],
    "THEME_TEMPLATES_OVERRIDES": [],
    "PAGINATED_TEMPLATES": {
        "index": None,
        "tag": None,
        "category": None,
        "author": None,
    },
    "PELICAN_CLASS": "pelican.Pelican",
    "DEFAULT_DATE_FORMAT": "%a %d %B %Y",
    "DATE_FORMATS": {},
    "MARKDOWN": {
        "extension_configs": {
            "markdown.extensions.codehilite": {"css_class": "highlight"},
            "markdown.extensions.extra": {},
            "markdown.extensions.meta": {},
        },
        "output_format": "html5",
    },
    "JINJA_FILTERS": {},
    "JINJA_GLOBALS": {},
    "JINJA_TESTS": {},
    "JINJA_ENVIRONMENT": {
        "trim_blocks": True,
        "lstrip_blocks": True,
        "extensions": [],
    },
    "LOG_FILTER": [],
    "LOCALE": [""],  # defaults to user locale
    "DEFAULT_PAGINATION": False,
    "DEFAULT_ORPHANS": 0,
    "DEFAULT_METADATA": {},
    "FILENAME_METADATA": r"(?P<date>\d{4}-\d{2}-\d{2}).*",
    "PATH_METADATA": "",
    "EXTRA_PATH_METADATA": {},
    "ARTICLE_PERMALINK_STRUCTURE": "",
    "TYPOGRIFY": False,
    "TYPOGRIFY_IGNORE_TAGS": [],
    "TYPOGRIFY_DASHES": "default",
    "SUMMARY_END_SUFFIX": "…",
    "SUMMARY_MAX_LENGTH": 50,
    "PLUGIN_PATHS": [],
    "PLUGINS": None,
    "PYGMENTS_RST_OPTIONS": {},
    "TEMPLATE_PAGES": {},
    "TEMPLATE_EXTENSIONS": [".html"],
    "IGNORE_FILES": [".#*"],
    "SLUG_REGEX_SUBSTITUTIONS": [
        (r"[^\w\s-]", ""),  # remove non-alphabetical/whitespace/'-' chars
        (r"(?u)\A\s*", ""),  # strip leading whitespace
        (r"(?u)\s*\Z", ""),  # strip trailing whitespace
        (r"[-\s]+", "-"),  # reduce multiple whitespace or '-' to single '-'
    ],
    "INTRASITE_LINK_REGEX": "[{|](?P<what>.*?)[|}]",
    "SLUGIFY_SOURCE": "title",
    "SLUGIFY_USE_UNICODE": False,
    "SLUGIFY_PRESERVE_CASE": False,
    "CACHE_CONTENT": False,
    "CONTENT_CACHING_LAYER": "reader",
    "CACHE_PATH": "cache",
    "GZIP_CACHE": True,
    "CHECK_MODIFIED_METHOD": "mtime",
    "LOAD_CONTENT_CACHE": False,
    "FORMATTED_FIELDS": ["summary"],
    "PORT": 8000,
    "BIND": "127.0.0.1",
}

PYGMENTS_RST_OPTIONS = None


def canonicalize_module_name(module_name: str) -> str:
    """Canonicalize the module name"""
    # Squash module_name into PyPA canonical form
    # PyPA specification:
    #    A valid name consists only of ASCII letters and numbers, period,
    #    underscore and hyphen. It must start and end with a letter or number
    # Also Python squashes hyphen and period into underscore for Python module name.
    canonical_module_name: str = module_name.lower()
    canonical_module_name = canonical_module_name.replace(".", "_")
    canonical_module_name = canonical_module_name.replace("-", "_")
    canonical_module_name = canonical_module_name.replace("__", "_")
    canonical_module_name = canonical_module_name.replace("__", "_")
    canonical_module_name = canonical_module_name.replace("__", "_")
    return canonical_module_name


def validate_module_name(module_name: str) -> bool:
    if not module_name[0].isalpha():
        logger.error(
            f"Module {module_name} name must begins with " "an alpha character."
        )
        return False
    if not module_name[-1].isalpha():
        logger.error(f"Module {module_name} name must ends with " "an alpha character.")
        return False
    if not module_name.isidentifier():
        logger.error(
            f"Module {module_name} name must contain alphanumeric "
            "or underscore ('_')."
        )
        return False
    return True


def load_source(name: str, path: str | Path | None) -> ModuleType | None:
    """
    Loads the Python-syntax file as a module for immediate variable access and
    application execution.

    No search path is used here; implied or not: `path` provides actual
    non-searchable file location.  Using module name alone implies to "search"
    only in the current working directory.

    If module name is not supplied as an argument, then its module name
    shall be extracted from given `path` argument but without any directory
    nor its file extension (just the basic pathLib.Path(path).stem part).

    This function substitutes Python built-in `importlib` but with one distinctive
    but different feature:  No attempts are made to leverage the `PYTHONPATH` as an
    alternative multi-directory search of a specified module name;
    only singular-directory lookup/search is supported here.

    WARNING to DEVELOPER: If you programmatically used the "from" reserved
        Python keyword as in this "from pelicanconf import ..." statement, then you
        will not be able to free up the pelicanconf module, much
        less use 'reload module' features.  (Not a likely scenario, but still usable)

    :param name: Python module name to be loaded into `sys.modules[]`.

                 PyPA Canonicalization is applied toward module name:
                 replace any and all dash symbols with underscore,
                 replace any and all period symbols with underscore,
                 replace all contiguous underscores with a single underscore.

                 Module name follows a naming convention for a valid Python module:
                 no uppercase character,
                 no dash symbol,
                 no directory separator,
                 first character shall be an alpha character,
                 last character shall be an alpha character,
                 rest of character shall be alphnum character or underscore.

                 Also, no period symbol (a Pelican-specific requirement).
    :type name: str

    :param path: optional filespec of the Python script file to load as Python module.
                 If the module name is explicitly given, then the `path` parameter may
                 be a:
                 a directory path which a module is searched for,
                 or a relative file path of the module file,
                 or an absolute file to the module file.
                 If the module name is left blank, then its module name is extracted
                 and canonicalized from its file's filename (without file extension).

                 Argument path can also be blank, which is treated equally a current
                 working directory (`.`).
    :type path: str | pathlib.Path
    :return: the ModuleType of the loaded Python module file.  Will be
            accessible in a form of "pelican.<module_name>".
    :rtype: ModuleType | None
    :raises TypeError: invalid argument passed to this function
    :raises SystemError: file extension is not supported by Python `importlib`
    :raises FileNotFoundError: file is not found
    :raises IsADirectoryError: was expecting a file, got something else
    :raises PermissionError: file has no read access
    :raises ValueError: incorrect value or invalid character in a string given
    :raises ModuleNotFound: module not found in sys.modules[]
    :raises ImportError: Python importlib error
    :raises SyntaxError: given file has Python syntax error
    :raises IndentationError: given file has Python indentation error
    """

    # If module_name remains blank, it is a fatal condition.
    module_name: str = ""
    file_path: Path = Path(
        "."
    )  # os.getcwd() gets us an absolute path, we want relative

    if name is None and (path is None or path == ""):
        err_str = "At least one argument is required"
        logger.fatal(err_str)
        raise SyntaxError(err_str)

    # Lots of interdependencies between name and path, try and get both values
    # before making any further logic on it.
    # name_arg_present = False
    # guess_my_module_name = False

    # Secure the module name
    if name is None:
        possible_module_name = ""
        guess_my_module_name = True
        # module_name is already an empty string here
        #  Check if path can carry the water
    # Enforce strong typing of argument; str type for module name
    elif not isinstance(name, str):
        err_msg = f"argument {name.__str__()} is not a str str type."
        logger.fatal(err_msg)
        raise TypeError(err_msg)
    # Pelican constraint for module name is not to allow 'period' symbol
    # due to lack of module nesting support.
    # This is a given Pelican design issue to support pelicanconf reloadability.
    elif "." in name:
        err_msg = (
            f"In Pelican only, module {name} name is not allow to "
            "have a period symbol as nested module is not designed here."
        )
        logger.fatal(err_msg)
        raise ValueError(err_msg)
    elif name == "":
        # Do we want to see if empty name= can be "autofilled"?
        # Check if the `path=` is a valid file, later
        guess_my_module_name = True
        possible_module_name = ""
    else:
        # module name given is explicit, go with that.
        guess_my_module_name = False
        possible_module_name = name

    # Treat "", "." or None as the same as absolute form of current working directory
    file_or_directory_flag = False

    # Now check for path
    if path is None:
        file_or_directory_flag = False
        # path_name is already an empty string here
        #  Check if module name can carry the brunt
    # Enforce strong typing of argument; str type or Path type for path name
    elif not isinstance(path, str) and not isinstance(path, Path):
        err_msg = f"argument {path.__str__()} is not a str or pathlib.Path type."
        logger.fatal(err_msg)
        raise TypeError(err_msg)
    else:
        # It might be a directory, or it might be a file but not determined here.
        # Don't check path any further, go down to mixed-argument logic block
        file_or_directory_flag = True
        file_path = Path(path)

    # Now we got values of both the name and the path ready for validation
    # Of course, if both are inferred, we cannot do anything so SyntaxError that too
    if not guess_my_module_name and not file_or_directory_flag:
        err_msg = "Must supply at least one argument."
        logger.error(err_msg)
        raise SyntaxError(err_msg)

    # Treat "", "." or None as the same as absolute form of current working directory

    abs_file_path = file_path.absolute()
    # file_path is already a get current working directory
    logger.debug("file_path is inferred as CWD")
    if not file_path.exists():
        err_msg = f"File '{abs_file_path!s}' not found."
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)
    elif not os.access(str(abs_file_path), os.R_OK):
        err_msg = f"'{abs_file_path}' file is not readable."
        logger.error(err_msg)
        raise PermissionError(err_msg)

    if file_path.is_dir():
        # path being a directory is only supported if module name is explicit
        if guess_my_module_name:
            raise IsADirectoryError(
                "Supply missing argument; can only extract module name from a "
                f"file path; not from an implied '{file_path}' directory."
            )
        logger.debug(f"Inferred path is: {abs_file_path}")
        # valid directory in file_path
    elif file_path.is_file():
        # Valid file type and valid file_path
        if guess_my_module_name:
            possible_module_name = file_path.stem
    else:  # path is neither a file nor a directory
        err_msg = f"File {file_path} is neither a file nor a directory."
        logger.error(err_msg)
        raise OSError(err_msg)

    absolute_filespec = file_path.absolute()
    resolved_absolute_filespec = file_path.resolve()

    # We got a valid module name with a valid directory or file path, or
    # we got a valid explicit file path to a module (but no module name)

    # At this point, we have enough to go and call our own `importlib` module

    logger.debug(f"Possible module name: '{possible_module_name}'.")
    if possible_module_name == "":
        raise AssertionError("We screwed up; go fix the code")

    # Got a valid module name at this point (explicit or extracted from filename)
    module_name = canonicalize_module_name(possible_module_name)
    if name != module_name:
        logger.warning(
            f"Canonical module name is now {module_name}; "
            f"given argument value is: '{name}'; update the code."
        )

    if not validate_module_name(module_name):
        err_msg = f"Error in validating module '{module_name}' name."
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Check that the module name is not in sys.module (like site or calendar!!!)
    if module_name in sys.modules:
        err_str = (
            f"Given '{name}' module name is already taken by a Python "
            f"system '{module_name}' module; it may be an "
            "user-defined or a built-in."
        )
        # following logger.fatal is used as-is by test_settings_module.py unit test
        logger.fatal(err_str)
        raise SystemError(err_str)
    # module_name is valid at this point

    try:
        # Using Python importlib, find the module using a full file path
        # specification and its filename and return this Module instance
        module_spec = importlib.util.spec_from_file_location(module_name, file_path)
        logger.debug(f"ModuleSpec '{module_name}' obtained from {absolute_filespec}.")

    except ImportError:
        logger.error(
            f"Location {resolved_absolute_filespec} may be missing a "
            f"module `get_filename` attribute value."
        )
        raise ModuleNotFoundError from ImportError
    except OSError:
        logger.error(
            f"Python module loader for configuration settings file "
            f"cannot determine absolute directory path from {absolute_filespec}."
        )
        raise FileNotFoundError from OSError
    # pass all the other excepts out

    try:
        # With the ModuleSpec object, we can get the
        module_type = importlib.util.module_from_spec(module_spec)
    except ImportError:
        logger.fatal(
            "Loader that defines exec_module() must also define create_module()"
        )
        raise ImportError from ImportError

    # module_type also has all the loaded Python values/objects from
    # the Pelican configuration settings file, but it is not
    # yet readable for all...

    # if you have use "from pelicanconf import ...", then you will not
    # be able to free up the module

    # store the module into the sys.modules
    sys.modules[module_name] = module_type

    try:
        # finally, execute any codes in the Pelican configuration settings file.
        module_spec.loader.exec_module(module_type)
        # Below logger.debug is used as-is by test_settings_module.py unit-test
        logger.debug(
            f"Loaded module '{module_name}' from {resolved_absolute_filespec} file"
        )
        return module_type
    except SyntaxError as e:
        # IndentationError, TabError are also subclass of SyntaxError
        # Other non-runtime exceptions that are not handled herre are:
        # SystemError and MemoryError.
        # Show where in the pelicanconf.py the offending syntax error is at via {e}.
        logger.error(
            f"{e}.\nHINT: "
            f"Try executing `python {resolved_absolute_filespec}` "
            f"for better syntax troubleshooting."
        )
        # Trying something new, reraise the exception up
        raise SyntaxError(
            f"Invalid syntax error at line number {e.end_lineno}"
            f" column offset {e.end_offset}",
            {
                "filename": resolved_absolute_filespec,
                "lineno": int(e.lineno),
                "offset": int(e.offset),
                "text": e.text,
                # "end_lineno": int(e.end_lineno),  # Python 3.10
                # "end_offset": int(e.end_offset),  # Python 3.10
            },
        ) from e
    except Any as e:
        logger.critical(
            f"'Python system module loader for {resolved_absolute_filespec}'"
            f" module failed: {e}."
        )
        sys.exit(errno.ENOEXEC)


def reload_source(name: str, path: str | Path) -> ModuleType | None:
    """Reload the configuration settings file"""
    # first line of defense against errant built-in module name
    if name != DEFAULT_MODULE_NAME:
        logger.error(
            f"Module name of {name} cannot be anything other "
            f"than {DEFAULT_MODULE_NAME}"
        )
        return None
    # second line of defense, this function call only works if one firstly
    # called the load_source()
    if name not in sys.modules:
        logger.error(f"Module name of {name} is not loaded, call load_source() firstly")
        return None
    # Now we can do the dangerous step
    del sys.modules[name]
    module_type = load_source(name, path)
    if module_type is None:
        logger.error(f"Module name of {name} is not loaded, call load_source() firstly")
        return None
    return module_type


def read_settings(
    path: Optional[str] = None,
    override: Optional[Settings] = None,
    reload: bool = False,
) -> Settings:
    """reads the setting files into a Python configuration settings module

    Returns the final Settings list of keys/values after reading the file
    and applying an override of settings on top of it.

    :param path: The full filespec path to the Pelican configuration settings file.
    :type path: str | None
    :param path: The override settings to be used to overwrite the ones read in
                 from the Pelican configuration settings file.
    :type override: Settings | None
    :param reload: A boolean value to safely reload the Pelican configuration settings
                   file into a Python module
    :type reload: bool
    :return: The Settings list of configurations after extracting the key/value from
             the path of Pelican configuration settings file and after the override
             settings has been applied over its read settings.
    :rtype: Settings
    """
    settings = override or {}

    if path:
        settings = dict(get_settings_from_file(path, reload), **settings)

    if settings:
        settings = handle_deprecated_settings(settings)

    if path:
        # Make relative paths absolute
        def getabs(maybe_relative, base_path=path):
            if isabs(maybe_relative):
                return maybe_relative
            return os.path.abspath(
                os.path.normpath(
                    os.path.join(os.path.dirname(base_path), maybe_relative)
                )
            )

        for p in ["PATH", "OUTPUT_PATH", "THEME", "CACHE_PATH"]:
            if settings.get(p) is not None:
                absp = getabs(settings[p])
                # THEME may be a name rather than a path
                if p != "THEME" or os.path.exists(absp):
                    settings[p] = absp

        if settings.get("PLUGIN_PATHS") is not None:
            settings["PLUGIN_PATHS"] = [
                getabs(pluginpath) for pluginpath in settings["PLUGIN_PATHS"]
            ]

    settings = dict(copy.deepcopy(DEFAULT_CONFIG), **settings)
    settings = configure_settings(settings, reload)

    # This is because there doesn't seem to be a way to pass extra
    # parameters to docutils directive handlers, so we have to have a
    # variable here that we'll import from within Pygments.run (see
    # rstdirectives.py) to see what the user defaults were.
    global PYGMENTS_RST_OPTIONS  # noqa: PLW0603
    PYGMENTS_RST_OPTIONS = settings.get("PYGMENTS_RST_OPTIONS", None)
    return settings


def get_settings_from_module(module: Optional[ModuleType] = None) -> Settings:
    """Clones a dictionary of settings from a module.

    :param module: Attempts to load a module using singular current working directory
                   (`$CWD`) search method then returns a clone-duplicate of its
                   settings found in the module.
                   If no module (`None`) is given, then default module name is used.
    :type module: ModuleType | None
    :return: Returns a dictionary of Settings found in that Python module.
    :rtype: Settings"""
    context = {}
    if module is not None:
        context.update((k, v) for k, v in inspect.getmembers(module) if k.isupper())
    return context


def get_settings_from_file(path: str, reload: bool) -> Settings:
    """Loads module from a file then clones dictionary of settings from that module.

    :param path: Attempts to load a module using a file specification (absolute or
                 relative) then returns a clone-duplicate of its settings found in
                 the module.  If no module (`None`) is given, then default module
                 name is used.
    :param path: A file specification (absolute or relative) that points to the
                 Python script file containing the keyword/value assignment settings.
    :param reload:  A bool value to check if module is already preloaded
                    before doing a reload.
    :return: Returns a dictionary of Settings found in that Python module.
    :rtype: Settings"""
    name = DEFAULT_MODULE_NAME
    # Keep the module name constant for Pelican configuration settings file
    if reload:
        module = reload_source(name, path)
    else:
        module = load_source(name, path)
    return get_settings_from_module(module)


def get_jinja_environment(settings: Settings) -> Settings:
    """Sets the environment for Jinja"""

    jinja_env = settings.setdefault(
        "JINJA_ENVIRONMENT", DEFAULT_CONFIG["JINJA_ENVIRONMENT"]
    )

    # Make sure we include the defaults if the user has set env variables
    for key, value in DEFAULT_CONFIG["JINJA_ENVIRONMENT"].items():
        if key not in jinja_env:
            jinja_env[key] = value

    return settings


def _printf_s_to_format_field(printf_string: str, format_field: str) -> str:
    """Tries to replace %s with {format_field} in the provided printf_string.
    Raises ValueError in case of failure.
    """
    TEST_STRING = "PELICAN_PRINTF_S_DEPRECATION"
    expected = printf_string % TEST_STRING

    result = printf_string.replace("{", "{{").replace("}", "}}") % f"{{{format_field}}}"
    if result.format(**{format_field: TEST_STRING}) != expected:
        raise ValueError(f"Failed to safely replace %s with {{{format_field}}}")

    return result


def handle_deprecated_settings(settings: Settings) -> Settings:
    """Converts deprecated settings and issues warnings. Issues an exception
    if both old and new setting is specified.
    """

    # PLUGIN_PATH -> PLUGIN_PATHS
    if "PLUGIN_PATH" in settings:
        logger.warning(
            "PLUGIN_PATH setting has been replaced by "
            "PLUGIN_PATHS, moving it to the new setting name."
        )
        settings["PLUGIN_PATHS"] = settings["PLUGIN_PATH"]
        del settings["PLUGIN_PATH"]

    # PLUGIN_PATHS: str -> [str]
    if isinstance(settings.get("PLUGIN_PATHS"), str):
        logger.warning(
            "Defining PLUGIN_PATHS setting as string "
            "has been deprecated (should be a list)"
        )
        settings["PLUGIN_PATHS"] = [settings["PLUGIN_PATHS"]]

    # JINJA_EXTENSIONS -> JINJA_ENVIRONMENT > extensions
    if "JINJA_EXTENSIONS" in settings:
        logger.warning(
            "JINJA_EXTENSIONS setting has been deprecated, "
            "moving it to JINJA_ENVIRONMENT setting."
        )
        settings["JINJA_ENVIRONMENT"]["extensions"] = settings["JINJA_EXTENSIONS"]
        del settings["JINJA_EXTENSIONS"]

    # {ARTICLE,PAGE}_DIR -> {ARTICLE,PAGE}_PATHS
    for key in ["ARTICLE", "PAGE"]:
        old_key = key + "_DIR"
        new_key = key + "_PATHS"
        if old_key in settings:
            logger.warning(
                "Deprecated setting %s, moving it to %s list", old_key, new_key
            )
            settings[new_key] = [settings[old_key]]  # also make a list
            del settings[old_key]

    # EXTRA_TEMPLATES_PATHS -> THEME_TEMPLATES_OVERRIDES
    if "EXTRA_TEMPLATES_PATHS" in settings:
        logger.warning(
            "EXTRA_TEMPLATES_PATHS is deprecated use "
            "THEME_TEMPLATES_OVERRIDES instead."
        )
        if settings.get("THEME_TEMPLATES_OVERRIDES"):
            raise Exception(
                "Setting both EXTRA_TEMPLATES_PATHS and "
                "THEME_TEMPLATES_OVERRIDES is not permitted. Please move to "
                "only setting THEME_TEMPLATES_OVERRIDES."
            )
        settings["THEME_TEMPLATES_OVERRIDES"] = settings["EXTRA_TEMPLATES_PATHS"]
        del settings["EXTRA_TEMPLATES_PATHS"]

    # MD_EXTENSIONS -> MARKDOWN
    if "MD_EXTENSIONS" in settings:
        logger.warning(
            "MD_EXTENSIONS is deprecated use MARKDOWN "
            "instead. Falling back to the default."
        )
        settings["MARKDOWN"] = DEFAULT_CONFIG["MARKDOWN"]

    # LESS_GENERATOR -> Webassets plugin
    # FILES_TO_COPY -> STATIC_PATHS, EXTRA_PATH_METADATA
    for old, new, doc in [
        ("LESS_GENERATOR", "the Webassets plugin", None),
        (
            "FILES_TO_COPY",
            "STATIC_PATHS and EXTRA_PATH_METADATA",
            "https://github.com/getpelican/pelican/"
            "blob/main/docs/settings.rst#path-metadata",
        ),
    ]:
        if old in settings:
            message = f"The {old} setting has been removed in favor of {new}"
            if doc:
                message += f", see {doc} for details"
            logger.warning(message)

    # PAGINATED_DIRECT_TEMPLATES -> PAGINATED_TEMPLATES
    if "PAGINATED_DIRECT_TEMPLATES" in settings:
        message = "The {} setting has been removed in favor of {}".format(
            "PAGINATED_DIRECT_TEMPLATES", "PAGINATED_TEMPLATES"
        )
        logger.warning(message)

        # set PAGINATED_TEMPLATES
        if "PAGINATED_TEMPLATES" not in settings:
            settings["PAGINATED_TEMPLATES"] = {
                "tag": None,
                "category": None,
                "author": None,
            }

        for t in settings["PAGINATED_DIRECT_TEMPLATES"]:
            if t not in settings["PAGINATED_TEMPLATES"]:
                settings["PAGINATED_TEMPLATES"][t] = None
        del settings["PAGINATED_DIRECT_TEMPLATES"]

    # {SLUG,CATEGORY,TAG,AUTHOR}_SUBSTITUTIONS ->
    # {SLUG,CATEGORY,TAG,AUTHOR}_REGEX_SUBSTITUTIONS
    url_settings_url = "http://docs.getpelican.com/en/latest/settings.html#url-settings"
    flavours = {"SLUG", "CATEGORY", "TAG", "AUTHOR"}
    old_values = {
        f: settings[f + "_SUBSTITUTIONS"]
        for f in flavours
        if f + "_SUBSTITUTIONS" in settings
    }
    new_values = {
        f: settings[f + "_REGEX_SUBSTITUTIONS"]
        for f in flavours
        if f + "_REGEX_SUBSTITUTIONS" in settings
    }
    if old_values and new_values:
        raise Exception(
            "Setting both {new_key} and {old_key} (or variants thereof) is "
            "not permitted. Please move to only setting {new_key}.".format(
                old_key="SLUG_SUBSTITUTIONS", new_key="SLUG_REGEX_SUBSTITUTIONS"
            )
        )
    if old_values:
        message = (
            "{} and variants thereof are deprecated and will be "
            "removed in the future. Please use {} and variants thereof "
            "instead. Check {}.".format(
                "SLUG_SUBSTITUTIONS", "SLUG_REGEX_SUBSTITUTIONS", url_settings_url
            )
        )
        logger.warning(message)
        if old_values.get("SLUG"):
            for f in ("CATEGORY", "TAG"):
                if old_values.get(f):
                    old_values[f] = old_values["SLUG"] + old_values[f]
            old_values["AUTHOR"] = old_values.get("AUTHOR", [])
        for f in flavours:
            if old_values.get(f) is not None:
                regex_subs = []
                # by default will replace non-alphanum characters
                replace = True
                for tpl in old_values[f]:
                    try:
                        src, dst, skip = tpl
                        if skip:
                            replace = False
                    except ValueError:
                        src, dst = tpl
                    regex_subs.append((re.escape(src), dst.replace("\\", r"\\")))

                if replace:
                    regex_subs += [
                        (r"[^\w\s-]", ""),
                        (r"(?u)\A\s*", ""),
                        (r"(?u)\s*\Z", ""),
                        (r"[-\s]+", "-"),
                    ]
                else:
                    regex_subs += [
                        (r"(?u)\A\s*", ""),
                        (r"(?u)\s*\Z", ""),
                    ]
                settings[f + "_REGEX_SUBSTITUTIONS"] = regex_subs
            settings.pop(f + "_SUBSTITUTIONS", None)

    # `%s` -> '{slug}` or `{lang}` in FEED settings
    for key in ["TRANSLATION_FEED_ATOM", "TRANSLATION_FEED_RSS"]:
        if (
            settings.get(key)
            and not isinstance(settings[key], Path)
            and "%s" in settings[key]
        ):
            logger.warning("%%s usage in %s is deprecated, use {lang} instead.", key)
            try:
                settings[key] = _printf_s_to_format_field(settings[key], "lang")
            except ValueError:
                logger.warning(
                    "Failed to convert %%s to {lang} for %s. "
                    "Falling back to default.",
                    key,
                )
                settings[key] = DEFAULT_CONFIG[key]
    for key in [
        "AUTHOR_FEED_ATOM",
        "AUTHOR_FEED_RSS",
        "CATEGORY_FEED_ATOM",
        "CATEGORY_FEED_RSS",
        "TAG_FEED_ATOM",
        "TAG_FEED_RSS",
    ]:
        if (
            settings.get(key)
            and not isinstance(settings[key], Path)
            and "%s" in settings[key]
        ):
            logger.warning("%%s usage in %s is deprecated, use {slug} instead.", key)
            try:
                settings[key] = _printf_s_to_format_field(settings[key], "slug")
            except ValueError:
                logger.warning(
                    "Failed to convert %%s to {slug} for %s. "
                    "Falling back to default.",
                    key,
                )
                settings[key] = DEFAULT_CONFIG[key]

    # CLEAN_URLS
    if settings.get("CLEAN_URLS", False):
        logger.warning(
            "Found deprecated `CLEAN_URLS` in settings."
            " Modifying the following settings for the"
            " same behaviour."
        )

        settings["ARTICLE_URL"] = "{slug}/"
        settings["ARTICLE_LANG_URL"] = "{slug}-{lang}/"
        settings["PAGE_URL"] = "pages/{slug}/"
        settings["PAGE_LANG_URL"] = "pages/{slug}-{lang}/"

        for setting in ("ARTICLE_URL", "ARTICLE_LANG_URL", "PAGE_URL", "PAGE_LANG_URL"):
            logger.warning("%s = '%s'", setting, settings[setting])

    # AUTORELOAD_IGNORE_CACHE -> --ignore-cache
    if settings.get("AUTORELOAD_IGNORE_CACHE"):
        logger.warning(
            "Found deprecated `AUTORELOAD_IGNORE_CACHE` in "
            "settings. Use --ignore-cache instead."
        )
        settings.pop("AUTORELOAD_IGNORE_CACHE")

    # ARTICLE_PERMALINK_STRUCTURE
    if settings.get("ARTICLE_PERMALINK_STRUCTURE", False):
        logger.warning(
            "Found deprecated `ARTICLE_PERMALINK_STRUCTURE` in"
            " settings.  Modifying the following settings for"
            " the same behaviour."
        )

        structure = settings["ARTICLE_PERMALINK_STRUCTURE"]

        # Convert %(variable) into {variable}.
        structure = re.sub(r"%\((\w+)\)s", r"{\g<1>}", structure)

        # Convert %x into {date:%x} for strftime
        structure = re.sub(r"(%[A-z])", r"{date:\g<1>}", structure)

        # Strip a / prefix
        structure = re.sub("^/", "", structure)

        for setting in (
            "ARTICLE_URL",
            "ARTICLE_LANG_URL",
            "PAGE_URL",
            "PAGE_LANG_URL",
            "DRAFT_URL",
            "DRAFT_LANG_URL",
            "ARTICLE_SAVE_AS",
            "ARTICLE_LANG_SAVE_AS",
            "DRAFT_SAVE_AS",
            "DRAFT_LANG_SAVE_AS",
            "PAGE_SAVE_AS",
            "PAGE_LANG_SAVE_AS",
        ):
            settings[setting] = os.path.join(structure, settings[setting])
            logger.warning("%s = '%s'", setting, settings[setting])

    # {,TAG,CATEGORY,TRANSLATION}_FEED -> {,TAG,CATEGORY,TRANSLATION}_FEED_ATOM
    for new, old in [
        ("FEED", "FEED_ATOM"),
        ("TAG_FEED", "TAG_FEED_ATOM"),
        ("CATEGORY_FEED", "CATEGORY_FEED_ATOM"),
        ("TRANSLATION_FEED", "TRANSLATION_FEED_ATOM"),
    ]:
        if settings.get(new, False):
            logger.warning(
                "Found deprecated `%(new)s` in settings. Modify %(new)s "
                "to %(old)s in your settings and theme for the same "
                "behavior. Temporarily setting %(old)s for backwards "
                "compatibility.",
                {"new": new, "old": old},
            )
            settings[old] = settings[new]

    # Warn if removed WRITE_SELECTED is present
    if "WRITE_SELECTED" in settings:
        logger.warning(
            "WRITE_SELECTED is present in settings but this functionality was removed. "
            "It will have no effect."
        )

    return settings


def configure_settings(settings: Settings, reload: None | bool = False) -> Settings:
    """Provide optimizations, error checking, and warnings for the given
    settings.
    Also, specify the log messages to be ignored.

    :param settings: Contains a dictionary of Pelican keyword/keyvalue
    :type settings: Settings
    :param reload: A flag to reload the same module but maybe with a different file
    :type reload: bool
    :return: An updated dictionary of Pelican's keywords and its keyvalue.
    :rtype: Settings"""
    if "PATH" not in settings or not os.path.isdir(settings["PATH"]):
        raise Exception(
            "You need to specify a path containing the content"
            " (see pelican --help for more information)"
        )

    # specify the log messages to be ignored
    log_filter = settings.get("LOG_FILTER", DEFAULT_CONFIG["LOG_FILTER"])
    LimitFilter._ignore.update(set(log_filter))

    # lookup the theme in "pelican/themes" if the given one doesn't exist
    if not os.path.isdir(settings["THEME"]):
        theme_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "themes", settings["THEME"]
        )
        if os.path.exists(theme_path):
            settings["THEME"] = theme_path
        else:
            raise Exception("Could not find the theme {}".format(settings["THEME"]))

    # standardize strings to lowercase strings
    for key in ["DEFAULT_LANG"]:
        if key in settings:
            settings[key] = settings[key].lower()

    # set defaults for Jinja environment
    settings = get_jinja_environment(settings)

    # standardize strings to lists
    for key in ["LOCALE"]:
        if key in settings and isinstance(settings[key], str):
            settings[key] = [settings[key]]

    # check settings that must be a particular type
    for key, types in [
        ("OUTPUT_SOURCES_EXTENSION", str),
        ("FILENAME_METADATA", str),
    ]:
        if key in settings and not isinstance(settings[key], types):
            value = settings.pop(key)
            logger.warning(
                "Detected misconfigured %s (%s), falling back to the default (%s)",
                key,
                value,
                DEFAULT_CONFIG[key],
            )

    # try to set the different locales, fallback on the default.
    locales = settings.get("LOCALE", DEFAULT_CONFIG["LOCALE"])

    for locale_ in locales:
        try:
            locale.setlocale(locale.LC_ALL, str(locale_))
            break  # break if it is successful
        except locale.Error:
            pass
    else:
        logger.warning(
            "Locale could not be set. Check the LOCALE setting, ensuring it "
            "is valid and available on your system."
        )

    if "SITEURL" in settings:
        # If SITEURL has a trailing slash, remove it and provide a warning
        siteurl = settings["SITEURL"]
        if siteurl.endswith("/"):
            settings["SITEURL"] = siteurl[:-1]
            logger.warning("Removed extraneous trailing slash from SITEURL.")
        # If SITEURL is defined but FEED_DOMAIN isn't,
        # set FEED_DOMAIN to SITEURL
        if "FEED_DOMAIN" not in settings:
            settings["FEED_DOMAIN"] = settings["SITEURL"]

    # check content caching layer and warn of incompatibilities
    if (
        settings.get("CACHE_CONTENT", False)
        and settings.get("CONTENT_CACHING_LAYER", "") == "generator"
        and not settings.get("WITH_FUTURE_DATES", True)
    ):
        logger.warning(
            "WITH_FUTURE_DATES conflicts with CONTENT_CACHING_LAYER "
            "set to 'generator', use 'reader' layer instead"
        )

    # Warn if feeds are generated with both SITEURL & FEED_DOMAIN undefined
    feed_keys = [
        "FEED_ATOM",
        "FEED_RSS",
        "FEED_ALL_ATOM",
        "FEED_ALL_RSS",
        "CATEGORY_FEED_ATOM",
        "CATEGORY_FEED_RSS",
        "AUTHOR_FEED_ATOM",
        "AUTHOR_FEED_RSS",
        "TAG_FEED_ATOM",
        "TAG_FEED_RSS",
        "TRANSLATION_FEED_ATOM",
        "TRANSLATION_FEED_RSS",
    ]

    if any(settings.get(k) for k in feed_keys):
        if not settings.get("SITEURL"):
            logger.warning(
                "Feeds generated without SITEURL set properly may not be valid"
            )

    if "TIMEZONE" not in settings:
        logger.warning(
            "No timezone information specified in the settings. Assuming"
            " your timezone is UTC for feed generation. Check "
            "https://docs.getpelican.com/en/latest/settings.html#TIMEZONE "
            "for more information"
        )

    # fix up pagination rules
    from pelican.paginator import PaginationRule

    pagination_rules = [
        PaginationRule(*r)
        for r in settings.get(
            "PAGINATION_PATTERNS",
            DEFAULT_CONFIG["PAGINATION_PATTERNS"],
        )
    ]
    settings["PAGINATION_PATTERNS"] = sorted(
        pagination_rules,
        key=lambda r: r[0],
    )

    # Save people from accidentally setting a string rather than a list
    path_keys = (
        "ARTICLE_EXCLUDES",
        "DEFAULT_METADATA",
        "DIRECT_TEMPLATES",
        "THEME_TEMPLATES_OVERRIDES",
        "FILES_TO_COPY",
        "IGNORE_FILES",
        "PAGINATED_DIRECT_TEMPLATES",
        "PLUGINS",
        "STATIC_EXCLUDES",
        "STATIC_PATHS",
        "THEME_STATIC_PATHS",
        "ARTICLE_PATHS",
        "PAGE_PATHS",
    )
    for PATH_KEY in filter(lambda k: k in settings, path_keys):
        if isinstance(settings[PATH_KEY], str):
            logger.warning(
                "Detected misconfiguration with %s setting "
                "(must be a list), falling back to the default",
                PATH_KEY,
            )
            settings[PATH_KEY] = DEFAULT_CONFIG[PATH_KEY]

    # Add {PAGE,ARTICLE}_PATHS to {ARTICLE,PAGE}_EXCLUDES
    mutually_exclusive = ("ARTICLE", "PAGE")
    for type_1, type_2 in [mutually_exclusive, mutually_exclusive[::-1]]:
        try:
            includes = settings[type_1 + "_PATHS"]
            excludes = settings[type_2 + "_EXCLUDES"]
            for path in includes:
                if path not in excludes:
                    excludes.append(path)
        except KeyError:
            continue  # setting not specified, nothing to do

    return settings


# minimum Python 3.6 (vermin tool)
# next upgrade, Python 3.10 (vermin tool)
