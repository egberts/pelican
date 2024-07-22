# Extracted from "--print-settings"

PATH = "/home/wolfe/admin/websites/egbert.net/pelican/content"
ARTICLE_PATHS = [""]
ARTICLE_EXCLUDES = ["pages"]
PAGE_PATHS = ["pages"]
PAGE_EXCLUDES = [""]
THEME = "notmyidea"
OUTPUT_PATH = "output"
READERS = {}
STATIC_PATHS = ["images"]
STATIC_EXCLUDES = []
STATIC_EXCLUDE_SOURCES = True
THEME_STATIC_DIR = "theme"
THEME_STATIC_PATHS = ["static"]
FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"
AUTHOR_FEED_ATOM = "feeds/{slug}.atom.xml"
AUTHOR_FEED_RSS = "feeds/{slug}.rss.xml"
TRANSLATION_FEED_ATOM = "feeds/all-{lang}.atom.xml"
FEED_MAX_ITEMS = 100
RSS_FEED_SUMMARY_ONLY = True
FEED_APPEND_REF = False
SITEURL = ""
SITENAME = "A Pelican Blog"
DISPLAY_PAGES_ON_MENU = True
DISPLAY_CATEGORIES_ON_MENU = True
DOCUTILS_SETTINGS = {}
OUTPUT_SOURCES = False
OUTPUT_SOURCES_EXTENSION = ".text"
USE_FOLDER_AS_CATEGORY = True
DEFAULT_CATEGORY = "misc"
WITH_FUTURE_DATES = True
CSS_FILE = "main.css"
NEWEST_FIRST_ARCHIVES = True
REVERSE_CATEGORY_ORDER = False
DELETE_OUTPUT_DIRECTORY = False
OUTPUT_RETENTION = []
INDEX_SAVE_AS = "index.html"
ARTICLE_URL = "{slug}.html"
ARTICLE_SAVE_AS = "{slug}.html"
ARTICLE_ORDER_BY = "reversed-date"
ARTICLE_LANG_URL = "{slug}-{lang}.html"
ARTICLE_LANG_SAVE_AS = "{slug}-{lang}.html"
DRAFT_URL = "drafts/{slug}.html"
DRAFT_SAVE_AS = "drafts/{slug}.html"
DRAFT_LANG_URL = "drafts/{slug}-{lang}.html"
DRAFT_LANG_SAVE_AS = "drafts/{slug}-{lang}.html"
PAGE_URL = "pages/{slug}.html"
PAGE_SAVE_AS = "pages/{slug}.html"
PAGE_ORDER_BY = "basename"
PAGE_LANG_URL = "pages/{slug}-{lang}.html"
PAGE_LANG_SAVE_AS = "pages/{slug}-{lang}.html"
DRAFT_PAGE_URL = "drafts/pages/{slug}.html"
DRAFT_PAGE_SAVE_AS = "drafts/pages/{slug}.html"
DRAFT_PAGE_LANG_URL = "drafts/pages/{slug}-{lang}.html"
DRAFT_PAGE_LANG_SAVE_AS = "drafts/pages/{slug}-{lang}.html"
STATIC_URL = "{path}"
STATIC_SAVE_AS = "{path}"
STATIC_CREATE_LINKS = False
STATIC_CHECK_IF_MODIFIED = False
CATEGORY_URL = "category/{slug}.html"
CATEGORY_SAVE_AS = "category/{slug}.html"
TAG_URL = "tag/{slug}.html"
TAG_SAVE_AS = "tag/{slug}.html"
AUTHOR_URL = "author/{slug}.html"
AUTHOR_SAVE_AS = "author/{slug}.html"
PAGINATION_PATTERNS = [
    (1, "{name}{extension}", "{name}{extension}"),
    (2, "{name}{number}{extension}", "{name}{number}{extension}"),
]
YEAR_ARCHIVE_URL = ""
YEAR_ARCHIVE_SAVE_AS = ""
MONTH_ARCHIVE_URL = ""
MONTH_ARCHIVE_SAVE_AS = ""
DAY_ARCHIVE_URL = ""
DAY_ARCHIVE_SAVE_AS = ""
RELATIVE_URLS = False
DEFAULT_LANG = "en"
ARTICLE_TRANSLATION_ID = "slug"
PAGE_TRANSLATION_ID = "slug"
DIRECT_TEMPLATES = ["index", "tags", "categories", "authors", "archives"]
THEME_TEMPLATES_OVERRIDES = []
PAGINATED_TEMPLATES = {"index": None, "tag": None, "category": None, "author": None}
PELICAN_CLASS = "pelican.Pelican"
DEFAULT_DATE_FORMAT = "%a %d %B %Y"
DATE_FORMATS = {}
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
    },
    "output_format": "html5",
}
JINJA_FILTERS = {}
JINJA_GLOBALS = {}
JINJA_TESTS = {}
JINJA_ENVIRONMENT = {"trim_blocks": True, "lstrip_blocks": True, "extensions": []}
LOG_FILTER = []
LOCALE = [""]
DEFAULT_PAGINATION = False
DEFAULT_ORPHANS = 0
DEFAULT_METADATA = {}
FILENAME_METADATA = "(?P<date>\\d{4}-\\d{2}-\\d{2}).*"
PATH_METADATA = ""
EXTRA_PATH_METADATA = {}
ARTICLE_PERMALINK_STRUCTURE = ""
TYPOGRIFY = False
TYPOGRIFY_IGNORE_TAGS = []
TYPOGRIFY_DASHES = "default"
SUMMARY_END_SUFFIX = "…"
SUMMARY_MAX_LENGTH = 50
PLUGIN_PATHS = []
PLUGINS = []
PYGMENTS_RST_OPTIONS = {}
TEMPLATE_PAGES = {}
TEMPLATE_EXTENSIONS = [".html"]
IGNORE_FILES = [".#*"]
SLUG_REGEX_SUBSTITUTIONS = [
    ("[^\\w\\s-]", ""),
    ("(?u)\\A\\s*", ""),
    ("(?u)\\s*\\Z", ""),
    ("[-\\s]+", "-"),
]
INTRASITE_LINK_REGEX = "[{|](?P<what>.*?)[|}]"
SLUGIFY_SOURCE = "title"
SLUGIFY_USE_UNICODE = False
SLUGIFY_PRESERVE_CASE = False
CACHE_CONTENT = False
CONTENT_CACHING_LAYER = "reader"
CACHE_PATH = "cache"
GZIP_CACHE = True
CHECK_MODIFIED_METHOD = "mtime"
LOAD_CONTENT_CACHE = False
FORMATTED_FIELDS = ["summary"]
PORT = 8000
BIND = "127.0.0.1"
FEED_DOMAIN = ""

# DEBUG = False
