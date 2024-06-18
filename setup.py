from setuptools import find_packages, setup

import djangocms_alias

CLASSIFIERS = [
    "Environment :: Web Environment",
    "Framework :: Django",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Framework :: Django",
    "Framework :: Django :: 3.2",
    "Framework :: Django :: 4.0",
    "Framework :: Django :: 4.1",
    "Framework :: Django :: 4.2",
    "Framework :: Django :: 5.0",
    "Framework :: Django CMS :: 4.1",
]

INSTALL_REQUIREMENTS = [
    "Django>=3.2",
    "django-parler>=1.4",
    "django-cms>=4.1",
]

setup(
    name="djangocms-alias",
    author="Divio AG",
    author_email="info@divio.ch",
    maintainer="Django CMS Association and contributors",
    maintainer_email="info@django-cms.org",
    url="https://github.com/django-cms/djangocms-alias",
    license="BSD",
    version=djangocms_alias.__version__,
    description=djangocms_alias.__doc__,
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    platforms=["OS Independent"],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIREMENTS,
    packages=find_packages(),
    include_package_data=True,
    test_suite="test_settings.run",
)
