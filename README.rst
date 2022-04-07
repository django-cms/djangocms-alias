****************
django CMS Alias
****************

============
Installation
============

Requirements
============

django CMS Alias requires that you have a django CMS 3.5 (or higher) project already running and set up.


To install
==========

Run::

    pip install djangocms-alias

Add ``djangocms_alias`` to your project's ``INSTALLED_APPS``.

Run::

    python manage.py migrate djangocms_alias

to perform the application's database migrations.


To contribute
=============

The project makes use of pre-commit hooks in git to help maintain coding standards.
To utilise this during development, need to make sure this is installed.

Run::

    pip install pre-commit
    pre-commit install
