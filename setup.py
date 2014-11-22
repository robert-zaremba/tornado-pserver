#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Robert Zaremba
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import codecs
from setuptools import setup, Command  #, find_packages
from glob import glob
import os
from os.path import splitext, basename, join as pjoin

try:
    import nose
except ImportError:
    nose = None
try:
    import pytest
except ImportError:
    pytest = None

class TestCommand(Command):
    """Custom distutils command to run the test suite."""

    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()
        try:
            import functional
        except ImportError as e:
            raise ImportError(str(e) + "\nYou need to obtain it from: \n   http://github.com/robert-zaremba/pyfunctional")

    def finalize_options(self):
        pass

    def run_nose(self):
        """Run the test suite with nose."""
        return nose.core.TestProgram(argv=["", '-vv', pjoin(self._dir, 'tests')])

    def run_unittest(self):
        """Finds all the tests modules in zmq/tests/ and runs them."""
        from unittest import TextTestRunner, TestLoader

        testfiles = [ ]
        for t in glob(pjoin(self._dir, 'tests', '*.py')):
            name = splitext(basename(t))[0]
            if name.startswith('test_'):
                testfiles.append('.'.join(
                    ['tests', name])
                )
        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 2)
        t.run(tests)

    def run_pytest(self):
        import subprocess
        errno = subprocess.call(['py.test','-q'])
        raise SystemExit(errno)

    def run(self):
        """Run the test suite, with py.test, nose, or unittest if nose is unavailable"""
        if pytest:
            self.run_pytest()
        elif nose:
            print ("pytest unavailable, trying test with nose. Some tests might not run, and some skipped, xfailed will appear as ERRORs.")
            self.run_nose()
        else:
            print ("pytest and nose unavailable, falling back on unittest. Skipped tests will appear as ERRORs.")
            return self.run_unittest()


setup(
    name='tornado-pserver',
    version='0.1',
    use_2to3 = True,
    cmdclass = {'test': TestCommand},
    description="Asynchronous, super fast, protocol aware server based on tornado.netutil.TCPServer. It's very easy to extend and supply own protocol.",
    long_description=codecs.open('README.md', "r", "utf-8").read(),
    author='Robert Zaremba',
    author_email='robert.marek.zaremba@wp.eu',
    url='https://github.com/robert-zaremba/tornado-pserver',
    download_url="https://github.com/robert-zaremba/tornado-pserver/tarball/master",
    license='Apache License',
    keywords="tornado server asynchronous protocol tcpserver netstring",
    packages=['pserver'],
    install_requires=['tornado < 4.0'],
    zip_safe=True,
    test_suite="nose.collector",
    tests_require=['nose', 'pyfunctional'],
    classifiers=[
        'Development Status :: 4 - Beta',
        # "Development Status :: 3 - Alpha",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License',
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: PyPy',
        'Operating System :: OS Independent',
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Networking",
    ],
)
