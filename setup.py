# fix broken behaviour - hardlinks are a FS attribute, not an OS attribute
# without doing this, the builds fail on encfs, AFS, NFS etc.
import os
if hasattr(os, 'link'):
  delattr(os, 'link')

from setuptools import setup
args = dict(
  name='gitzilla',
  description='Git-Bugzilla integration',
  author='Devendra Gera',
  author_email='gera@theoldmonk.net',
  url='http://www.theoldmonk.net/gitzilla/',
  version='1.9.1',
  requires=['pybugz'],
  package_dir={'gitzilla': '.'},
  packages=['gitzilla'],
  package_data={'': ['etc/*']},
  include_package_data=True,
  entry_points={
    'console_scripts': [
      'gitzilla-post-receive = gitzilla.hookscripts:post_receive',
      'gitzilla-update = gitzilla.hookscripts:update',
      'gitzilla-gencookie = gitzilla.utilscripts:generate_cookiefile',
    ],
  }
)

setup(**args)

