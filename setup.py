#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

VERSION = '0.1.0'

import os, textwrap

from setuptools import setup, find_packages

# -----------------------------------------------------------------------------

f = open(os.path.join(os.path.dirname(__file__), 'docs', 'features.txt'))
long_description = f.read()
f.close()

setup(
      name = 'nagare.ide',
      version = VERSION,
      author = 'Alain Poirier',
      author_email = 'alain.poirier at net-ng.com',
      description = 'Nagare Web IDE',
      long_description = textwrap.dedent("""
      Description
      ^^^^^^^^^^^

      %s

      Installation
      ============

      For a standard installation, read the ``docs/README.txt`` document.

      This document also describes how to install the latest development version
      from the `Nagare subversion repository <svn://www.nagare.org/trunk/nagare/ide#egg=nagare.ide-dev>`_
      """) % long_description,
      license = 'BSD',
      keywords = 'web nagare ide bespin ajax comet traceback yui',
      url = 'http://www.nagare.org',
      download_url = 'http://www.nagare.org/download',
      packages = find_packages(),
      include_package_data = True,
      package_data = {'' : ['*.cfg']},
      zip_safe = False,
      install_requires = ('Pygments', 'nagare>=0.3.0'),
      namespace_packages = ('nagare', 'nagare.ide',),
      entry_points = """
      [nagare.applications]
      ide = nagare.ide.app:app

      [nagare.admin]
      sources = nagare.ide.admin:Admin
      """,
      classifiers = (
                  'Development Status :: 4 - Beta',
                  'License :: OSI Approved :: BSD License',
                  'Intended Audience :: Developers',
                  'Programming Language :: Python',
                  'Environment :: Web Environment',
                  'Operating System :: Microsoft :: Windows :: Windows NT/2000',
                  'Operating System :: Unix',
                  'Topic :: Internet :: WWW/HTTP',
                  'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                  'Topic :: Software Development :: Libraries :: Python Modules',
      )
)
