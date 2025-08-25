

****************
django CMS Alias
****************

|PyPiVersion| |Coverage| |DjVersion| |CmsVersion|

django CMS Alias replicates and extends the alias function of django CMS version 3 for
django CMS version 4 and later.

An alias is a collection of plugins that is managed centrally. A reference can be added to
any placeholder using the Alias plugin. Since the Alias plugin creates a reference any changes
to the alias are immediately reflected at all places it is used.

Aliases are created and edited independently of their usage through their own dedicated editing
endpoints, i.e. outside of django CMS pages. This allows content managers to maintain alias
content without needing to navigate to a page where the alias is used.

When editing a page that contains static aliases, these aliases are shown in the structure board,
providing visibility into the alias' content while maintaining the separation between alias management
and page editing. If the static alias can be changed, it is fully accessible through the structure board.

Static aliases cannot be changed in the structure board on views that have no editing interface.

django CMS Alias supports versioning aliases by django CMS Versioning.

.. warning::

    django CMS Alias 3 and later require django CMS 5.0 or later.

    Use ``djangocms-alias>=2,<3`` for django CMS 4.1.


============
Installation
============

Requirements
============

django CMS Alias requires that you have a django CMS 4 (or higher) project already running and set up.


To install
==========

Run::

    pip install djangocms-alias

Add ``djangocms_alias`` and ``parler`` to your project's ``INSTALLED_APPS``.

Run::

    python manage.py migrate djangocms_alias

to perform the application's database migrations.


=====
Usage
=====

Static aliases
==============

Static aliases appear in templates and replace static placeholders which were part of django CMS up to version 3.x.

Example::

    {% load djangocms_alias_tags %}
    ...
    <footer>
      {% static_alias 'footer' %}
    </footer>

Alias plugin
============

Alternatively, aliases can be used with the Alias plugin. It allows to select which alias content is shown at the
exact position the alias plugin is placed.

Side notes
==========
For the plugin to work out of the box ``{% block content %}`` is expected to exist in your main ``base.html`` file.

.. |PyPiVersion| image:: https://img.shields.io/pypi/v/djangocms-alias.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-alias
    :alt: Latest PyPI version
.. |Coverage| image:: https://codecov.io/gh/django-cms/djangocms-alias/graph/badge.svg?token=UUkVjsHGcA
 :target: https://codecov.io/gh/django-cms/djangocms-alias

.. |PyVersion| image:: https://img.shields.io/pypi/pyversions/djangocms-alias.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-alias
    :alt: Python versions

.. |DjVersion| image:: https://img.shields.io/pypi/frameworkversions/django/djangocms-alias.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-alias
    :alt: Django versions

.. |CmsVersion| image:: https://img.shields.io/pypi/frameworkversions/django-cms/djangocms-alias.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-alias
    :alt: django CMS versions