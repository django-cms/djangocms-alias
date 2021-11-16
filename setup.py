from setuptools import find_packages, setup

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
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Framework :: Django',
    'Framework :: Django :: 2.2',
    'Framework :: Django :: 3.0',
    'Framework :: Django :: 3.1',
    'Framework :: Django :: 3.2',
]

INSTALL_REQUIREMENTS = [
    'Django>=1.11,<3.3',
    'django-parler>=1.4',
    'django-cms',
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
    test_suite='test_settings.run',
)
