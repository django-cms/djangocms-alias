from distutils.version import LooseVersion

import cms


# CMS_VERSION = cms.__version__
CMS_VERSION = '4.0'

CMS_36 = LooseVersion(CMS_VERSION) < LooseVersion('3.7')

try:
    from cms.utils.plugins import reorder_plugins
except ImportError:
    reorder_plugins = None
