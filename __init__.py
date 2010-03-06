
"""
GitZilla

Git-Bugzilla integration in a Python module.

Requirements
------------

  - Python (tested with 2.6, should work with >= 2.5)
  - pybugz (tested with 0.8.0)

pybugs can be obtained from http://github.com/ColdWind/pybugz/downloads

"""

__version__ = '1.0'
__author__ = 'Devendra Gera <gera@theoldmonk.net>'
__license__ = """Copyright 2010, Devendra Gera <gera@theoldmonk.net>,
All rights reserved.

This is Free Software, released under the terms of the GNU General Public
License, version 3. A copy of the license can be obtained by emailing the
author, or from http://www.gnu.org/licenses/gpl-3.0.html

As noted in the License, this software does not come with any warranty,
explicit or implied, to the extent permissible by law.
This program might, and would be buggy. Use it at your own risk.
"""

sDefaultSeparator = "~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~."

sDefaultFormatSpec = """
commit      %H
parents     %P
Author      %aN (%aE)
Date        %aD
Commit By   %cN (%cE)
Commit Date %cD

%s

%b
""".replace("\n", "%n")

import re

oDefaultBugRegex = re.compile(r"bug\s*(?:#|)\s*(?P<bug>\d+)",
                              re.MULTILINE | re.DOTALL | re.IGNORECASE)

import logging

class NullHandler(logging.Handler):
  def emit(self, record):
    pass

NullLogger = logging.getLogger("gitzilla")
NullLogger.addHandler(NullHandler())

