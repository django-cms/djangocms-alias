=========
Changelog
=========

2.0.0rc3 (2023-12-12)
=====================
* fix: avoid generating migrations based on settings.LANGUAGE by @vasekch in https://github.com/django-cms/djangocms-alias/pull/186
* fix: Enable caching for `static_alias` template tag by @vasekch in https://github.com/django-cms/djangocms-alias/pull/200
* fix: `static_alias` unnecessarily creates new content objects when used with versioning by @fsbraun in https://github.com/django-cms/djangocms-alias/pull/202
* feat: Django 5.0 support, fixed test suite by @fsbraun in https://github.com/django-cms/djangocms-alias/pull/203
* fix: Migration dependency on latest django-cms migration.
* fix: Allow using a variable as the identifier in static_alias template tag
* fest: Django 4.0, 4.1, and 4.2 support added
* fest: Django 2.2 support removed
* fest: Python 3.7 support removed
* ci: Changed test setup to run tox from github actions for consistency in testing
* feat: Use django CMS 4.1 GrouperModelAdmin utility (breaking change wrt. django CMS 4.0)
* fix: Admin menu entry show alias change list in the language of the currently shown object
* fix: Automatically create static aliases in the language needed (fixing #162)

1.11.0 (2022-10-14)
===================
* feat: Hiding Aliases entry from admin index menu as aliases are managed through Alias Content
* fix: Removed refs to missing static files (#143)

1.10.0 (2022-09-21)
===================
* feat: Enabled edit button from ExtendedVersionAdminMixin

1.9.0 (2022-09-07)
==================
* feat: Edit alias plugin opens in side-frame

1.8.0 (2022-07-18)
==================
* fix: remove back button from alias preview and associated unused custom views

1.7.2 (2022-07-14)
==================
* fix: Resetting category field in plugin to null instead of using placeholder when site is changed

1.7.1 (2022-06-10)
==================
* fix: AliasContent Category admin_order_field incorrect ordering
* fix: Alias field in plugin should be disabled unless site/category is populated

1.7.0 (2022-05-31)
==================
* feat: Clean out old sass, js and css dist from gulp and package.json
* feat: Create plugin alias filter to use category and or site
* fix: Outdated build scripts from Node 5 to Node 16

1.6.1 (2022-05-13)
==================
* fix: Moved category list filter after site
* fix: Ordering category filter by name

1.6.0 (2022-04-29)
==================
* feat: Add AliasContent admin changelist Category filter

1.5.0 (2022-04-26)
==================
* feat: Add AliasContent admin changelist UnPublished filter
* fix: Add correct icons for Alias Manager actions
* build: Added ``long_description_content_type`` for setuptools.
* ci: Changed test workflow so that the coverage reporting happens after all unittests run
* ci: Updated deprecated isort v4 CLI flags for the v5 double-dashed arguments
* fix: Added parler to the installation instructions as an installed app

1.4.1 (2022-04-13)
==================
* fix: Re-order AliasContent changelist filters as per the spec

1.4.0 (2022-04-12)
==================
* feat: Add AliasContent admin changelist Site filter

1.3.0 (2022-04-12)
==================
* feat: Add site dropdown to create alias wizard and change alias admin

1.2.0 (2022-04-11)
==================
* feat: Changed Site dropdown url for Aliases to point to the admin changelist
* feat: Refactor alias topdown and versioning action menus

1.1.0 (2022-04-06)
==================
* feat: Remove Add cta and hide delete dropdown actions from AliasContent admin ChangeList
* feat: Site field added to plugin

1.0.2 (2022-04-01)
==================
* feat: Add more Alias actions to Alias AliasContent Manager versioning actions

1.0.1 (2022-04-01)
==================
* feat: Close the sideframe when following links to the alias placeholder endpoints

1.0.0 (2022-03-30)
==================
* feat: Add preview link to Alias AliasContent Manager versioning actions
* feat: Add versioning actions to Alias AliasContent Manager
* feat: Github Actions integration
* Python 3.8, 3.9 support added
* Django 3.0, 3.1 and 3.2 support added
* Python 3.5 and 3.6 support removed
* Django 1.11 support removed
