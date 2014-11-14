# Setup system for EnergyLens Server

# TODO
# 1. Install the pre-requisite libraries - Run install.sh
# 2. Run the config file

"""
Add description
Sample below
"""

"""initd: module for simplifying creation of initd daemons.
This module provides functionality for starting, stopping and
restarting daemons.  It also provides a simple utility for reading the
command line arguments and determining which action to perform from
them.
"""

from setuptools import setup

doclines = __doc__.splitlines()

setup(
    name='energylensplus',
    version='1.0',
    # py_modules=['initd', 'daemon_command'],
    platforms=['Linux'],

    install_requires=['django>=1.6'],

    author='Manaswi Saha',
    author_email='manaswis@iiitd.ac.in',

    description=doclines[0],
    long_description='\n'.join(doclines[2:]),

    license='http://www.gnu.org/licenses/gpl.html',
    url='https://github.com/manaswis/energylensplus',
    # test_suite='test.test_initd.suite',

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Boot :: Init',
    ],
)
