from distutils.version import LooseVersion

from django import get_version


DJANGO_VERSION = get_version()
DJANGO_4_0 = LooseVersion(DJANGO_VERSION) < LooseVersion('4.1')
