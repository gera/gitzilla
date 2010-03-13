
"""
utilscripts - utility scripts for gitzilla.

"""

import os
import sys
import bugz.bugzilla
import getpass

def generate_cookiefile():
  """
  asks the user for Bugzilla credentials and generates a cookiefile.
  """
  if len(sys.argv) < 2:
    print """Usage:
    %s <bugzilla_base_url>
""" % sys.argv[0]
    sys.exit(1)

  sBZUrl = sys.argv[1]
  sLogin = os.getlogin()
  sUsername = raw_input("username [%s]: " % (sLogin,))
  sPassword = getpass.getpass("password: ")

  if sUsername == "":
    sUsername = sLogin

  oBZ = bugz.bugzilla.Bugz(sBZUrl, user=sUsername, password=sPassword)
  oBZ.auth()



