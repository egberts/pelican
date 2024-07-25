import locale
from os.path import abspath, dirname, join

from pelican.settings import (
    handle_deprecated_settings,
    read_settings,
)
from pelican.tests.support import unittest


class TestSettingsConfiguration(unittest.TestCase):
    """Provided a file, it should read it, replace the default values,
    append new values to the settings (if any), and apply basic settings
    optimizations.
    """

    def setUp(self):
        self.old_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, "C")
        self.PATH = abspath(dirname(__file__))
        default_conf = join(self.PATH, "default_conf.py")
        self.settings = read_settings(default_conf)

    def tearDown(self):
        locale.setlocale(locale.LC_ALL, self.old_locale)

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

    def test_deprecated_extra_templates_paths(self):
        settings = self.settings
        settings["EXTRA_TEMPLATES_PATHS"] = ["/foo/bar", "/ha"]

        settings = handle_deprecated_settings(settings)

        self.assertEqual(settings["THEME_TEMPLATES_OVERRIDES"], ["/foo/bar", "/ha"])
        self.assertNotIn("EXTRA_TEMPLATES_PATHS", settings)

    def test_deprecated_paginated_direct_templates(self):
        settings = self.settings
        settings["PAGINATED_DIRECT_TEMPLATES"] = ["index", "archives"]
        settings["PAGINATED_TEMPLATES"] = {"index": 10, "category": None}
        settings = handle_deprecated_settings(settings)
        self.assertEqual(
            settings["PAGINATED_TEMPLATES"],
            {"index": 10, "category": None, "archives": None},
        )
        self.assertNotIn("PAGINATED_DIRECT_TEMPLATES", settings)

    def test_deprecated_paginated_direct_templates_from_file(self):
        # This is equivalent to reading a settings file that has
        # PAGINATED_DIRECT_TEMPLATES defined but no PAGINATED_TEMPLATES.
        settings = read_settings(
            None, override={"PAGINATED_DIRECT_TEMPLATES": ["index", "archives"]}
        )
        self.assertEqual(
            settings["PAGINATED_TEMPLATES"],
            {
                "archives": None,
                "author": None,
                "index": None,
                "category": None,
                "tag": None,
            },
        )
        self.assertNotIn("PAGINATED_DIRECT_TEMPLATES", settings)

    def test_theme_and_extra_templates_exception(self):
        settings = self.settings
        settings["EXTRA_TEMPLATES_PATHS"] = ["/ha"]
        settings["THEME_TEMPLATES_OVERRIDES"] = ["/foo/bar"]

        self.assertRaises(Exception, handle_deprecated_settings, settings)

    def test_slug_and_slug_regex_substitutions_exception(self):
        settings = {}
        settings["SLUG_REGEX_SUBSTITUTIONS"] = [("C++", "cpp")]
        settings["TAG_SUBSTITUTIONS"] = [("C#", "csharp")]

        self.assertRaises(Exception, handle_deprecated_settings, settings)

    def test_deprecated_slug_substitutions(self):
        default_slug_regex_subs = self.settings["SLUG_REGEX_SUBSTITUTIONS"]

        # If no deprecated setting is set, don't set new ones
        settings = {}
        settings = handle_deprecated_settings(settings)
        self.assertNotIn("SLUG_REGEX_SUBSTITUTIONS", settings)
        self.assertNotIn("TAG_REGEX_SUBSTITUTIONS", settings)
        self.assertNotIn("CATEGORY_REGEX_SUBSTITUTIONS", settings)
        self.assertNotIn("AUTHOR_REGEX_SUBSTITUTIONS", settings)

        # If SLUG_SUBSTITUTIONS is set, set {SLUG, AUTHOR}_REGEX_SUBSTITUTIONS
        # correctly, don't set {CATEGORY, TAG}_REGEX_SUBSTITUTIONS
        settings = {}
        settings["SLUG_SUBSTITUTIONS"] = [("C++", "cpp")]
        settings = handle_deprecated_settings(settings)
        self.assertEqual(
            settings.get("SLUG_REGEX_SUBSTITUTIONS"),
            [(r"C\+\+", "cpp")] + default_slug_regex_subs,
        )
        self.assertNotIn("TAG_REGEX_SUBSTITUTIONS", settings)
        self.assertNotIn("CATEGORY_REGEX_SUBSTITUTIONS", settings)
        self.assertEqual(
            settings.get("AUTHOR_REGEX_SUBSTITUTIONS"), default_slug_regex_subs
        )

        # If {CATEGORY, TAG, AUTHOR}_SUBSTITUTIONS are set, set
        # {CATEGORY, TAG, AUTHOR}_REGEX_SUBSTITUTIONS correctly, don't set
        # SLUG_REGEX_SUBSTITUTIONS
        settings = {}
        settings["TAG_SUBSTITUTIONS"] = [("C#", "csharp")]
        settings["CATEGORY_SUBSTITUTIONS"] = [("C#", "csharp")]
        settings["AUTHOR_SUBSTITUTIONS"] = [("Alexander Todorov", "atodorov")]
        settings = handle_deprecated_settings(settings)
        self.assertNotIn("SLUG_REGEX_SUBSTITUTIONS", settings)
        self.assertEqual(
            settings["TAG_REGEX_SUBSTITUTIONS"],
            [(r"C\#", "csharp")] + default_slug_regex_subs,
        )
        self.assertEqual(
            settings["CATEGORY_REGEX_SUBSTITUTIONS"],
            [(r"C\#", "csharp")] + default_slug_regex_subs,
        )
        self.assertEqual(
            settings["AUTHOR_REGEX_SUBSTITUTIONS"],
            [(r"Alexander\ Todorov", "atodorov")] + default_slug_regex_subs,
        )

        # If {SLUG, CATEGORY, TAG, AUTHOR}_SUBSTITUTIONS are set, set
        # {SLUG, CATEGORY, TAG, AUTHOR}_REGEX_SUBSTITUTIONS correctly
        settings = {}
        settings["SLUG_SUBSTITUTIONS"] = [("C++", "cpp")]
        settings["TAG_SUBSTITUTIONS"] = [("C#", "csharp")]
        settings["CATEGORY_SUBSTITUTIONS"] = [("C#", "csharp")]
        settings["AUTHOR_SUBSTITUTIONS"] = [("Alexander Todorov", "atodorov")]
        settings = handle_deprecated_settings(settings)
        self.assertEqual(
            settings["TAG_REGEX_SUBSTITUTIONS"],
            [(r"C\+\+", "cpp")] + [(r"C\#", "csharp")] + default_slug_regex_subs,
        )
        self.assertEqual(
            settings["CATEGORY_REGEX_SUBSTITUTIONS"],
            [(r"C\+\+", "cpp")] + [(r"C\#", "csharp")] + default_slug_regex_subs,
        )
        self.assertEqual(
            settings["AUTHOR_REGEX_SUBSTITUTIONS"],
            [(r"Alexander\ Todorov", "atodorov")] + default_slug_regex_subs,
        )

        # Handle old 'skip' flags correctly
        settings = {}
        settings["SLUG_SUBSTITUTIONS"] = [("C++", "cpp", True)]
        settings["AUTHOR_SUBSTITUTIONS"] = [("Alexander Todorov", "atodorov", False)]
        settings = handle_deprecated_settings(settings)
        self.assertEqual(
            settings.get("SLUG_REGEX_SUBSTITUTIONS"),
            [(r"C\+\+", "cpp")] + [(r"(?u)\A\s*", ""), (r"(?u)\s*\Z", "")],
        )
        self.assertEqual(
            settings["AUTHOR_REGEX_SUBSTITUTIONS"],
            [(r"Alexander\ Todorov", "atodorov")] + default_slug_regex_subs,
        )

    def test_deprecated_slug_substitutions_from_file(self):
        # This is equivalent to reading a settings file that has
        # SLUG_SUBSTITUTIONS defined but no SLUG_REGEX_SUBSTITUTIONS.
        settings = read_settings(
            None, override={"SLUG_SUBSTITUTIONS": [("C++", "cpp")]}
        )
        self.assertEqual(
            settings["SLUG_REGEX_SUBSTITUTIONS"],
            [(r"C\+\+", "cpp")] + self.settings["SLUG_REGEX_SUBSTITUTIONS"],
        )
        self.assertNotIn("SLUG_SUBSTITUTIONS", settings)
