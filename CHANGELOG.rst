=========
Changelog
=========

Unreleased
==========
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
