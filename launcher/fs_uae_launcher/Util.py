from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys
from .fs import memoize, get_home_dir

def expand_path(path):
    from .Paths import Paths
    return Paths.expand_path(path)

def get_real_case(path):
    from .Paths import Paths
    return Paths.get_real_case(path)
