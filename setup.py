from setuptools import (
    find_packages,
    setup,
)

import djangocms_alias


CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Framework :: Django',
    'Framework :: Django :: 1.11',
    # 'Framework :: Django :: 2.0',
]

INSTALL_REQUIREMENTS = [
    'Django>=1.11,<2.0',  # django cms 3.5 dont support django 2.0 yet
    'django-cms>=3.5<3.7',
    'django-parler>=1.4',
    'djangocms-text-ckeditor',
]

setup(
    name='djangocms-alias',
    author='Divio AG',
    author_email='info@divio.ch',
    url='http://github.com/divio/djangocms-alias',
    license='BSD',
    version=djangocms_alias.__version__,
    description=djangocms_alias.__doc__,
    long_description=open('README.rst').read(),
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIREMENTS,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='test_settings.run',
)
