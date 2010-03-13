
"""
hooks - git hooks provided by gitzilla.

"""

import re
import sys
from utils import get_changes, init_bugzilla, get_bug_status, notify_and_exit
from gitzilla import sDefaultSeparator, sDefaultFormatSpec, oDefaultBugRegex
from gitzilla import NullLogger
import traceback


def post_receive(sBZUrl, sBZUser=None, sBZPasswd=None, sFormatSpec=None, oBugRegex=None, sSeparator=None, logger=None, bz_init=None):
  """
  a post-recieve hook handler which extracts bug ids and adds the commit
  info to the comment. If multiple bug ids are found, the comment is added
  to each of those bugs.

  sBZUrl is the base URL for the Bugzilla installation. If sBZUser and
  sBZPasswd are None, then it uses the ~/.bugz_cookie cookiejar.

  oBugRegex specifies the regex used to search for the bug id in the commit
  messages. It MUST provide a named group called 'bug' which contains the bug
  id (all digits only). If oBugRegex is None, a default bug regex is used,
  which is:

      r"bug\s*(?:#|)\s*(?P<bug>\d+)"

  This matches forms such as:
    - bug 123
    - bug #123
    - BUG # 123
    - Bug#123
    - bug123

  The format spec is appended to "--format=format:" and passed to
  "git whatchanged". See the git whatchanged manpage for more info on the
  format spec.

  If sFormatSpec is None, a default format spec is used.

  The separator is a string that would never occur in a commit message.
  If sSeparator is None, a default separator is used, which should be
  good enough for everyone.

  If a logger is provided, it would be used for all the logging. If logger
  is None, logging will be disabled. The logger must be a Python
  logging.Logger instance.

  The function bz_init(url, username, password) is invoked to instantiate the
  bugz.bugzilla.Bugz instance. If this is None, the default method is used.
  """
  if sFormatSpec is None:
    sFormatSpec = sDefaultFormatSpec

  if sSeparator is None:
    sSeparator = sDefaultSeparator

  if oBugRegex is None:
    oBugRegex = oDefaultBugRegex

  if logger is None:
    logger = NullLogger

  if bz_init is None:
    bz_init = init_bugzilla

  oBZ = bz_init(sBZUrl, sBZUser, sBZPasswd)

  sPrevRev = None
  for sLine in iter(sys.stdin.readline, ""):
    (sOldRev, sNewRev, sRefName) = sLine.split(" ")
    if sPrevRev is None:
      sPrevRev = sOldRev
    logger.debug("oldrev: '%s', newrev: '%s'" % (sOldRev, sNewRev))
    asChangeLogs = get_changes(sOldRev, sNewRev, sFormatSpec, sSeparator)

    for sMessage in asChangeLogs:
      logger.debug("Considering commit:\n%s" % (sMessage,))
      oMatch = re.search(oBugRegex, sMessage)
      if oMatch is None:
        logger.info("Bug id not found in commit:\n%s" % (sMessage,))
        continue
      for oMatch in re.finditer(oBugRegex, sMessage):
        iBugId = int(oMatch.group("bug"))
        logger.debug("Found bugid %d" % (iBugId,))
        try:
          oBZ.modify(iBugId, comment=sMessage)
        except Exception, e:
          logger.exception("Could not add comment to bug %d" % (iBugId,))



def update(oBugRegex=None, asAllowedStatuses=None, sSeparator=None, sBZUrl=None, sBZUser=None, sBZPasswd=None, logger=None, bz_init=None):
  """
  an update hook handler which rejects commits without a bug reference.
  This looks at the sys.argv array, so make sure you don't modify it before
  calling this function.

  oBugRegex specifies the regex used to search for the bug id in the commit
  messages. It MUST provide a named group called 'bug' which contains the bug
  id (all digits only). If oBugRegex is None, a default bug regex is used,
  which is:

      r"bug\s*(?:#|)\s*(?P<bug>\d+)"

  This matches forms such as:
    - bug 123
    - bug #123
    - BUG # 123
    - Bug#123
    - bug123

  asAllowedStatuses is an array containing allowed statuses for the found
  bugs. If a bug is not in one of these states, the commit will be rejected.
  If asAllowedStatuses is None, status checking is diabled.

  The separator is a string that would never occur in a commit message.
  If sSeparator is None, a default separator is used, which should be
  good enough for everyone.

  sBZUrl specifies the base URL for the Bugzilla installation.  sBZUser and
  sBZPasswd are the bugzilla credentials.

  If a logger is provided, it would be used for all the logging. If logger
  is None, logging will be disabled. The logger must be a Python
  logging.Logger instance.

  The function bz_init(url, username, password) is invoked to instantiate the
  bugz.bugzilla.Bugz instance. If this is None, the default method is used.
  """
  if oBugRegex is None:
    oBugRegex = oDefaultBugRegex

  if sSeparator is None:
    sSeparator = sDefaultSeparator

  if logger is None:
    logger = NullLogger

  if bz_init is None:
    bz_init = init_bugzilla

  sFormatSpec = sDefaultFormatSpec

  if asAllowedStatuses is not None:
    # sanity checking
    if sBZUrl is None:
      raise ValueError("Bugzilla info required for status checks")

  # create and cache bugzilla instance
  oBZ = bz_init(sBZUrl, sBZUser, sBZPasswd)
  # check auth
  try:
    oBZ.auth()
  except:
    logger.error("Could not login to Bugzilla", exc_info=1)
    notify_and_exit("Could not login to Bugzilla. Check your auth details and settings")

  (sOldRev, sNewRev) = sys.argv[2:4]
  logger.debug("oldrev: '%s', newrev: '%s'" % (sOldRev, sNewRev))

  asChangeLogs = get_changes(sOldRev, sNewRev, sFormatSpec, sSeparator)
  
  for sMessage in asChangeLogs:
    logger.debug("Checking for bug refs in commit:\n%s" % (sMessage,))
    oMatch = re.search(oBugRegex, sMessage)
    if oMatch is None:
      logger.error("No bug ref found in commit:\n%s" % (sMessage,))
      notify_and_exit("No bug ref found in commit:\n%s" % (sMessage,))
    else:
      if asAllowedStatuses is not None:
        # check all bug statuses
        for oMatch in re.finditer(oBugRegex, sMessage):
          iBugId = int(oMatch.group("bug"))
          logger.debug("Found bug id %d" % (iBugId,))
          try:
            sStatus = get_bug_status(oBZ, iBugId)
            if sStatus is None:
              notify_and_exit("Bug %d does not exist" % (iBugId,))
          except Exception, e:
            logger.exception("Could not get status for bug %d" % (iBugId,))
            notify_and_exit("Could not get staus for bug %d" % (iBugId,))

          logger.debug("status for bug %d is %s" % (iBugId, sStatus))
          if sStatus not in asAllowedStatuses:
            logger.info("Cannot accept commit for bug %d in state %s" % (iBugId, sStatus))
            notify_and_exit("Bug %d['%s'] is not in %s" % (iBugId, sStatus, asAllowedStatuses))

