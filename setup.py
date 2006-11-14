#!/usr/bin/env python
# -*- coding: latin-1 -*-

from distutils.core import setup,Extension
import glob
import os
import os.path

setup(name="pymbolic",
      version="0.10",
      description="A package for symbolic computation",
      author=u"Andreas Kloeckner",
      author_email="inform@tiker.net",
      license = "BSD, like Python itself",
      url="http://news.tiker.net/software/pymbolic",
      packages=["pymbolic", "pymbolic.mapper"],
      package_dir={"pymbolic": "src", "pymbolic.mapper":"src/mapper"}
     )
