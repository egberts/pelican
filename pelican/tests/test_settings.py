"""All of Pelican configuration settings come to life here"""

import copy
import locale
import os
import sys
from os.path import abspath, dirname, join

from pelican.settings import (
    DEFAULT_CONFIG,
    DEFAULT_THEME,
    _printf_s_to_format_field,
    configure_settings,
    handle_deprecated_settings,
    load_source,
    read_settings,
)
from pelican.tests.support import unittest


class TestSettingsConfiguration(unittest.TestCase):
    """Provided a file, it should read it, replace the default values,
    append new values to the settings (if any), and apply basic settings
    optimizations.

    :param unittest.TestCase:
    :type unittest.TestCase: type
    :param return: 0 if successful
    :rtype: type
    :raise ExceptionType: description of exception raised
    """

    def setUp(self):
        self.old_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, "C")
        self.PATH = abspath(dirname(__file__))
        default_conf = join(self.PATH, "default_conf.py")
        self.settings = read_settings(default_conf, reload=True)
        self.original_sys_modules = sys.modules

    def tearDown(self):
        locale.setlocale(locale.LC_ALL, self.old_locale)
        self.assertEqual(
            self.original_sys_modules,
            sys.modules,
            "One of the unit test did not clean up sys.modules " "properly.",
        )

    #  NOTE: testSetup() is done once for all unit tests within the same class.
    #  NOTE: Probably want to use test_module(module) or xtest_()
    #        Parallelized test are done in random order, so this FIRSTLY test
    #        will fail ... most of the time.
    #    def test_overwrite_existing_settings(self):
    #        self.assertEqual(self.settings.get("SITENAME"), "Alexis' log")
    #        self.assertEqual(self.settings.get("SITEURL"), "http://blog.notmyidea.org")
    def test_load_source_invalid_abs_path1_fail(self):
        """load_source(), invalid absolute path, no such file, failing mode"""
        name = "pelicanconf-does-not-exist"
        path = "/no-such-directory"  # a directory, not the expected file
        mod = load_source(name, path)
        self.assertEqual(
            mod, None, "absolute '/no-such-directory' directory path is not found."
        )

    def test_load_source_invalid_abs_path2_fail(self):
        """load_source(), invalid absolute path, directory, failing mode"""
        name = "pelicanconf-does-not-exist"
        path = "/tmp"  # a directory, not the expected file
        mod = load_source(name, path)
        self.assertEqual(
            mod, None, "Missing absolute '/tmp/pelican-does-not-exist.py' file"
        )

    def test_load_source_invalid_abs_path3_fail(self):
        """load_source(), invalid absolute unresolved path, directory, failing mode"""
        name = "pelicanconf-does-not-exist"
        path = "/../tmp"  # a directory, not the expected file
        mod = load_source(name, path)
        self.assertEqual(mod, None, "Missing relative pelicanconf.py")

    def test_load_source_missing_relative_fail(self):
        name = "pelicanconf-does-not-exist"  # module_name
        path = "."  # location of module Python file
        mod = load_source(name, path)
        self.assertEqual(mod, None, "Missing relative pelicanconf.py")

    def test_load_source_missing_absolute_fail(self):
        name = "pelicanconf-does-not-exist"
        path = "/tmp/pelicanconf-does-not-exist.py"
        mod = load_source(name, path)
        self.assertEqual(mod, None)

    def test_overwrite_existing_settings(self):
        self.assertEqual(self.settings.get("SITENAME"), "Alexis' log")
        self.assertEqual(self.settings.get("SITEURL"), "http://blog.notmyidea.org")

    def test_keep_default_settings(self):
        # Keep default settings if not defined.
        self.assertEqual(
            self.settings.get("DEFAULT_CATEGORY"), DEFAULT_CONFIG["DEFAULT_CATEGORY"]
        )

    def test_dont_copy_small_keys(self):
        # Do not copy keys not in caps.
        self.assertNotIn("foobar", self.settings)

    def test_read_empty_settings(self):
        # Ensure an empty settings file results in default settings.
        settings = read_settings(None)
        expected = copy.deepcopy(DEFAULT_CONFIG)
        # Added by configure settings
        expected["FEED_DOMAIN"] = ""
        expected["ARTICLE_EXCLUDES"] = ["pages"]
        expected["PAGE_EXCLUDES"] = [""]
        self.maxDiff = None
        self.assertDictEqual(settings, expected)

    def test_settings_return_independent(self):
        # Make sure that the results from one settings call doesn't
        # affect past or future instances.
        self.PATH = abspath(dirname(__file__))
        default_conf = join(self.PATH, "default_conf.py")
        # settings['SITEURL'] should be blank

        # Trap any exception error
        try:
            # why did setUp() call read_settings firstly?  So, we reload here
            settings = read_settings(default_conf, reload=True)
            settings["SITEURL"] = "new-value"
        except any:
            raise any from None

        # clobber settings['SITEURL']
        new_settings = read_settings(default_conf, reload=True)
        # see if pulling up a new set of original settings (into a different variable,
        # via 'new_settings' does not clobber the 'settings' variable
        self.assertNotEqual(new_settings["SITEURL"], settings["SITEURL"])

    def test_defaults_not_overwritten(self):
        # This assumes 'SITENAME': 'A Pelican Blog'
        settings = read_settings(None)
        settings["SITENAME"] = "Not a Pelican Blog"
        self.assertNotEqual(settings["SITENAME"], DEFAULT_CONFIG["SITENAME"])

    def test_static_path_settings_safety(self):
        # Disallow static paths from being strings
        settings = {
            "STATIC_PATHS": "foo/bar",
            "THEME_STATIC_PATHS": "bar/baz",
            # These 4 settings are required to run configure_settings
            "PATH": ".",
            "THEME": DEFAULT_THEME,
            "SITEURL": "http://blog.notmyidea.org/",
            "LOCALE": "",
        }
        configure_settings(settings)
        self.assertEqual(settings["STATIC_PATHS"], DEFAULT_CONFIG["STATIC_PATHS"])
        self.assertEqual(
            settings["THEME_STATIC_PATHS"], DEFAULT_CONFIG["THEME_STATIC_PATHS"]
        )

    def test_configure_settings(self):
        # Manipulations to settings should be applied correctly.
        settings = {
            "SITEURL": "http://blog.notmyidea.org/",
            "LOCALE": "",
            "PATH": os.curdir,
            "THEME": DEFAULT_THEME,
        }
        configure_settings(settings)

        # SITEURL should not have a trailing slash
        self.assertEqual(settings["SITEURL"], "http://blog.notmyidea.org")

        # FEED_DOMAIN, if undefined, should default to SITEURL
        self.assertEqual(settings["FEED_DOMAIN"], "http://blog.notmyidea.org")

        settings["FEED_DOMAIN"] = "http://feeds.example.com"

        configure_settings(settings)
        self.assertEqual(settings["FEED_DOMAIN"], "http://feeds.example.com")

    def test_theme_settings_exceptions(self):
        settings = self.settings

        # Check that theme lookup in "pelican/themes" functions as expected
        settings["THEME"] = os.path.split(settings["THEME"])[1]
        configure_settings(settings)
        self.assertEqual(settings["THEME"], DEFAULT_THEME)

        # Check that non-existent theme raises exception
        settings["THEME"] = "foo"
        self.assertRaises(Exception, configure_settings, settings)

    def test_deprecated_dir_setting(self):
        settings = self.settings

        settings["ARTICLE_DIR"] = "foo"
        settings["PAGE_DIR"] = "bar"

        settings = handle_deprecated_settings(settings)

        self.assertEqual(settings["ARTICLE_PATHS"], ["foo"])
        self.assertEqual(settings["PAGE_PATHS"], ["bar"])

        with self.assertRaises(KeyError):
            settings["ARTICLE_DIR"]
            settings["PAGE_DIR"]

    def test_default_encoding(self):
        # Test that the user locale is set if not specified in settings

        locale.setlocale(locale.LC_ALL, "C")
        # empty string = user system locale
        self.assertEqual(self.settings["LOCALE"], [""])

        configure_settings(self.settings)
        lc_time = locale.getlocale(locale.LC_TIME)  # should be set to user locale

        # explicitly set locale to user pref and test
        locale.setlocale(locale.LC_TIME, "")
        self.assertEqual(lc_time, locale.getlocale(locale.LC_TIME))

    def test_invalid_settings_throw_exception(self):
        # Test that the path name is valid

        # test that 'PATH' is set
        settings = {}

        self.assertRaises(Exception, configure_settings, settings)

        # Test that 'PATH' is valid
        settings["PATH"] = ""
        self.assertRaises(Exception, configure_settings, settings)

        # Test nonexistent THEME
        settings["PATH"] = os.curdir
        settings["THEME"] = "foo"

        self.assertRaises(Exception, configure_settings, settings)

    def test__printf_s_to_format_field(self):
        for s in ("%s", "{%s}", "{%s"):
            option = f"foo/{s}/bar.baz"
            result = _printf_s_to_format_field(option, "slug")
            expected = option % "qux"
            found = result.format(slug="qux")
            self.assertEqual(expected, found)


if __name__ == "__main__":
    unittest.main()
