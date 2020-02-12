import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENABLE_VERSIONING = bool(os.environ.get('ENABLE_VERSIONING', True))
EXTRA_INSTALLED_APPS = []
if ENABLE_VERSIONING:
    EXTRA_INSTALLED_APPS.append('djangocms_versioning')

HELPER_SETTINGS = {
    'TIME_ZONE': 'Europe/Zurich',
    'TOP_INSTALLED_APPS': [
        'djangocms_alias',
    ],
    'INSTALLED_APPS': [
        'parler',
        'djangocms_alias.test_utils.text',
    ] + EXTRA_INSTALLED_APPS,
    'VERSIONING_ALIAS_MODELS_ENABLED': ENABLE_VERSIONING,
    'MIGRATION_MODULES': {
        'sites': None,
        'contenttypes': None,
        'auth': None,
        'cms': None,
        'menus': None,
        'text': None,
        'djangocms_alias': None,
        'djangocms_versioning': None,
    },
    'CMS_PERMISSION': True,
    # At present, testing requires bootstrap to be disabled.
    # 'ALDRYN_BOILERPLATE_NAME': 'bootstrap3',
    'LANGUAGES': (
        ('en', 'English'),
        ('de', 'German'),
        ('fr', 'French'),
        ('it', 'Italiano'),
    ),
    'CMS_LANGUAGES': {
        1: [
            {
                'code': 'en',
                'name': 'English',
                'fallbacks': ['de', 'fr']
            },
            {
                'code': 'de',
                'name': 'Deutsche',
                'fallbacks': ['en']  # FOR TESTING DO NOT ADD 'fr' HERE
            },
            {
                'code': 'fr',
                'name': 'Française',
                'fallbacks': ['en']  # FOR TESTING DO NOT ADD 'de' HERE
            },
            {
                'code': 'it',
                'name': 'Italiano',
                'fallbacks': ['fr']  # FOR TESTING, LEAVE AS ONLY 'fr'
            },
        ],
    },
    'TEMPLATE_DIRS': [
        os.path.join('tests', 'templates'),
    ],
    'PARLER_LANGUAGES': {
        1: [
            {
                'code': 'en',
                'fallbacks': ['de', 'fr'],
                'hide_untranslated': False,
            },
            {
                'code': 'de',
                'fallbacks': ['en'],
                'hide_untranslated': False,
            },
            {
                'code': 'fr',
                'fallbacks': ['en'],
                'hide_untranslated': False,
            },
            {
                'code': 'it',
                'fallbacks': ['fr'],  # FOR TESTING, LEAVE AS ONLY 'fr'
                'hide_untranslated': False,
            },
        ],
        'default': {
            'code': 'en',
            'fallbacks': ['en'],
            'hide_untranslated': False,
        }
    },
    'PARLER_ENABLE_CACHING': False,
    'LANGUAGE_CODE': 'en',
    'DJANGOCMS_ALIAS_TEMPLATES': [
        ('custom_alias_template', 'Custom Template Name'),
    ]
}


def run():
    from djangocms_helper import runner
    runner.cms('djangocms_alias', extra_args=[])


if __name__ == "__main__":
    run()
