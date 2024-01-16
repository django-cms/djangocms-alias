

****************
django CMS Alias
****************

|coverage| |python| |django| |djangocms4|

django CMS Alias replicates and extends the alias function of django CMS version 3 for django CMS version 4.

An alias is a collection of plugins that is managed centrally. A reference can be added to any placeholder using the Alias plugin. Since the Alias plugin creates a reference any changes to the alias are immediately reflected at all places it is used.

django CMS Alias supports versioning aliases by django CMS Versioning.

.. warning::

    This is the development branch for django CMS version 4.1 support.

    For django CMS V4.0 support, see `support/django-cms-4.0.x branch <https://github.com/django-cms/djangocms-alias/tree/support/django-cms-4.0.x>`_


============
Installation
============

Requirements
============

django CMS Alias requires that you have a django CMS 4 (or higher) project already running and set up.


To install
==========

Run::

    pip install git+https://github.com/django-cms/djangocms-alias@master#egg=djangocms-alias

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

Alternatively, aliases can be used with the Alias plugin. It allows to select which alias content is shown at the exact position the alias plugin is placed.

.. |coverage| image:: https://codecov.io/gh/django-cms/djangocms-alias/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/django-cms/djangocms-alias

.. |python| image:: https://img.shields.io/badge/python-3.7+-blue.svg
   :target: https://pypi.org/project/djangocms-alias/

.. |django| image:: https://img.shields.io/badge/django-3.2--4.1-blue.svg
   :target: https://www.djangoproject.com/

.. |djangocms4| image:: https://img.shields.io/badge/django%20CMS-4-blue.svg
   :target: https://www.django-cms.org/

Side notes
============
For the plugin to work out of the box ``{% block content %}`` is expected to exist in your main ``base.html`` file.
