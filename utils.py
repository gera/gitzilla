
"""
utils module for gitzilla

"""

import os
import sys
import subprocess


sNoCommitRev = "0000000000000000000000000000000000000000"

def execute(asCommand, bSplitLines=False, bIgnoreErrors=False):
  """
  Utility function to execute a command and return the output.
  """
  p = subprocess.Popen(asCommand,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       shell=False,
                       close_fds=True,
                       universal_newlines=True,
                       env=None)
  if bSplitLines:
    data = p.stdout.readlines()
  else:
    data = p.stdout.read()
  iRetCode = p.wait()
  if iRetCode and not bIgnoreErrors:
    print('Failed to execute command: %s\n%s' % (asCommand, data), file=sys.stderr)
    sys.exit(-1)

  return data


def get_changes(sOldRev, sNewRev, sFormatSpec, sSeparator, bIncludeDiffStat, sRefName, sRefPrefix):
  """
  returns an array of chronological changes, between sOldRev and sNewRev,
  according to the format spec sFormatSpec.

  Gets changes which are only on the specified ref, excluding changes
  also present on other refs starting with sRefPrefix.
  """
  if sOldRev == sNoCommitRev:
    sCommitRange = sNewRev
  elif sNewRev == sNoCommitRev:
    sCommitRange = sOldRev
  else:
    sCommitRange = "%s..%s" % (sOldRev, sNewRev)

  sFormatSpec = sFormatSpec.strip("\n").replace("\n", "%n")

  if bIncludeDiffStat:
    sCommand = "whatchanged"
  else:
    sCommand = "log"

  asCommand = ['git', sCommand,
               "--format=format:%s%s" % (sSeparator, sFormatSpec)]

  # exclude all changes which are also found on other refs
  # and hence have already been processed.
  if sRefName is not None:
    asAllRefs = execute(
        ['git', 'for-each-ref', '--format=%(refname)', sRefPrefix],
        bSplitLines=True)
    asAllRefs = [x.strip() for x in asAllRefs]
    asOtherRefs = [x for x in asAllRefs if x != sRefName]
    asNotOtherRefs = execute(
        ['git', 'rev-parse', '--not'] + asOtherRefs,
        bSplitLines=True)
    asNotOtherRefs = [x.strip() for x in asNotOtherRefs]
    asCommand += asNotOtherRefs

  asCommand.append(sCommitRange)
  sChangeLog = execute(asCommand)
  asChangeLogs = sChangeLog.split(sSeparator)
  asChangeLogs.reverse()

  return asChangeLogs[:-1]



def notify_and_exit(sMsg):
  """
  notifies the error and exits.
  """
  print("""

======================================================================
Cannot accept commit.

%s

======================================================================

""" % (sMsg,))
  sys.exit(1)

