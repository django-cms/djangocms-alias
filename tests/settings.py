import os
from distutils.util import strtobool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENABLE_VERSIONING = strtobool(os.environ.get("ENABLE_VERSIONING", "1"))

EXTRA_INSTALLED_APPS = ["djangocms_versioning"] if ENABLE_VERSIONING else []

SECRET_KEY = "test1234"
TIME_ZONE = "Europe/Zurich"

INSTALLED_APPS = [
    "djangocms_alias",
    "djangocms_alias.test_utils",
    "djangocms_alias.test_utils.text",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cms",
    "menus",
    "treebeard",
    "sekizai",
    "parler",
] + EXTRA_INSTALLED_APPS
VERSIONING_ALIAS_MODELS_ENABLED = ENABLE_VERSIONING
MIGRATION_MODULES = {
    "sites": None,
    "contenttypes": None,
    "auth": None,
    "cms": None,
    "menus": None,
    "text": None,
    "djangocms_alias": None,
    "djangocms_versioning": None,
}
CMS_PERMISSION = True

LANGUAGES = (
    ("en", "English"),
    ("de", "German"),
    ("fr", "French"),
    ("it", "Italiano"),
)

CMS_LANGUAGES = {
    1: [
        {"code": "en", "name": "English", "fallbacks": ["de", "fr"]},
        {
            "code": "de",
            "name": "Deutsche",
            "fallbacks": ["en"],  # FOR TESTING DO NOT ADD 'fr' HERE
        },
        {
            "code": "fr",
            "name": "Française",
            "fallbacks": ["en"],  # FOR TESTING DO NOT ADD 'de' HERE
        },
        {
            "code": "it",
            "name": "Italiano",
            "fallbacks": ["fr"],  # FOR TESTING, LEAVE AS ONLY 'fr'
        },
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [os.path.join("tests", "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
                "cms.context_processors.cms_settings",
            ],
        },
    },
]

CMS_TEMPLATES = (
    ("fullwidth.html", "Fullwidth"),
    ("page.html", "Normal page"),
    ("static_alias.html", "Static Alias Template"),
)
PARLER_LANGUAGES = {
    1: [
        {
            "code": "en",
            "fallbacks": ["de", "fr"],
            "hide_untranslated": False,
        },
        {
            "code": "de",
            "fallbacks": ["en"],
            "hide_untranslated": False,
        },
        {
            "code": "fr",
            "fallbacks": ["en"],
            "hide_untranslated": False,
        },
        {
            "code": "it",
            "fallbacks": ["fr"],  # FOR TESTING, LEAVE AS ONLY 'fr'
            "hide_untranslated": False,
        },
    ],
    "default": {
        "code": "en",
        "fallbacks": ["en"],
        "hide_untranslated": False,
    },
}
PARLER_ENABLE_CACHING = False
LANGUAGE_CODE = "en"
DJANGOCMS_ALIAS_TEMPLATES = [
    ("custom_alias_template", "Custom Template Name"),
]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
CMS_CONFIRM_VERSION4 = True

SITE_ID = 1
STATIC_URL = "/static/"

ROOT_URLCONF = "tests.urls"
