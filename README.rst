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


=============
Configuration
=============

django CMS Alias provides several Django settings to control its behavior:

``STATIC_ALIAS_EDITING_ENABLED``
    Default: ``True``

    Controls whether static aliases can be edited directly on frontend editable objects
    (such as pages) that include the ``{% static_alias %}`` template tag. When set to ``False``,
    static aliases will not be visible in the structure board and only editable from the alias
    admin endpoint.

``VERSIONING_ALIAS_MODELS_ENABLED``
    Default: ``True`` (if djangocms-versioning is installed)

    Enables versioning support for alias models when djangocms-versioning is available. When enabled,
    aliases support draft/published workflows, version history, and proper content lifecycle management.
    Set to ``False`` to disable versioning for aliases even if djangocms-versioning is installed. Any changes
    to any alias will then be immediately visible to the world.

``MODERATING_ALIAS_MODELS_ENABLED``
    Default: ``True`` (if djangocms-moderation is installed)

    Enables moderation workflows for alias models when djangocms-moderation is available. When enabled,
    aliases can be subject to approval workflows before publication. Set to ``False`` to disable moderation
    for aliases even if djangocms-moderation is installed.


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

**New in version 3**: Static aliases can now be edited directly on any frontend
editable object (such as pages) that includes the ``{% static_alias %}``
template tag. Static aliases are marked by a pin icon in the structure board to
distinguish them from regular content.

Editing static aliases on the page provides a convenient way to manage alias
content in context. However, when using djangocms-versioning, there are important
considerations:

**Versioning Considerations:**

* **Independent Publishing**: Static aliases must be published independently from
  their edit endpoint. Use the edit entry in the alias's burger menu in the structure
  board to access the full alias editing interface.

* **Published Content Only**: When objects are viewed on the site (not in edit mode),
  only the latest published alias version is displayed. If no published version exists,
  nothing will be shown.

* **Draft Creation Required**: Published aliases cannot be edited - neither in the
  structure menu nor on their dedicated endpoint. You must create a new draft version
  of the alias before editing is possible.

This workflow ensures content consistency and proper version control while providing the flexibility to edit aliases in context when appropriate.

Alias plugin
============

Alternatively, aliases can be used with the Alias plugin. It allows to select which alias content is shown at the
exact position the alias plugin is placed.

=========
Templates
=========
For the plugin to work out of the box ``{% block content %}`` is expected to exist in your main ``base.html`` file.
Here is the template hierarchy for the edit and preview endpoints::

    base.html
        └── djangocms_alias/base.html {% block content %}
              └── djangocms_alias/alias_content_preview.html  {% block alias_content %}

Use Django's template override mechanism to customize these templates as needed. Say, if your base template has
a different name and the content goes into a block called ``main_content``, you would create a template at
``templates/djangocms_alias/base.html`` with the following content::

    {% extends "mybase.html" %}
    {% load i18n %}

    {% block title %}{% translate "Aliases" %}{% endblock %}
    {% block main_content %}
        <div class="aliases my-additional-class">
            {% block aliases_content %}
            {% endblock aliases_content %}
        </div>
    {% endblock main_content %}



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
