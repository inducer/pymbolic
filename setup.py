#!/usr/bin/env python
# -*- coding: latin-1 -*-

from setuptools import setup, find_packages

ver_dic = {}
version_file = open("pymbolic/version.py")
try:
    version_file_contents = version_file.read()
finally:
    version_file.close()

exec(compile(version_file_contents, "pymbolic/version.py", 'exec'), ver_dic)

setup(name="pymbolic",
      version=ver_dic["VERSION_TEXT"],
      description="A package for symbolic computation",
      long_description=open("README.rst").read(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Other Audience',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 2.5',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Mathematics',
          'Topic :: Software Development :: Libraries',
          'Topic :: Utilities',
          ],
      author="Andreas Kloeckner",
      author_email="inform@tiker.net",
      license="MIT",
      url="http://mathema.tician.de/software/pymbolic",

      packages=find_packages(),
      install_requires=[
          "pytools>=2",
          "pytest>=2.3",
          "six",
          ])
