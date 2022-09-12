

****************
django CMS Alias
****************

|coverage| |python| |django| |djangocms4|

django CMS Alias replicates and extends the alias function of django CMS version 3
for django CMS version 4.


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

.. |coverage| image:: https://codecov.io/gh/django-cms/djangocms-alias/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/django-cms/djangocms-alias

.. |python| image:: https://img.shields.io/badge/python-3.7+-blue.svg
   :target: https://pypi.org/project/djangocms-alias/

.. |django| image:: https://img.shields.io/badge/django-2.2,%203.2-blue.svg
   :target: https://www.djangoproject.com/

.. |djangocms4| image:: https://img.shields.io/badge/django%20CMS-4-blue.svg
   :target: https://www.django-cms.org/
