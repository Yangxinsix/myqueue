import re
from setuptools import setup, find_packages

with open('q2/__init__.py') as fd:
    version = re.search("__version__ = '(.*)'", fd.read()).group(1)

with open('README.rst') as fd:
    long_description = fd.read()

setup(name='q2',
      version=version,
      description='Simple job queue',
      long_description=long_description,
      author='J. J. Mortensen',
      author_email='jjmo@dtu.dk',
      url='https://gitlab.com/jensj/q2',
      packages=find_packages(),
      entry_points={'console_scripts': ['q2 = q2.cli:main']},
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: '
          'GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: Unix',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Text Editors :: Text Processing'])  # ???
