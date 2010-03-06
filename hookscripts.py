
"""
hookscripts - ready to use hook scripts for gitzilla.

These pick up configuration values from the environment.

"""

import os
import sys
import gitzilla.hooks
import logging
import ConfigParser

def get_or_default(conf, section, option, default=None):
  if conf.has_option(section, option):
    return conf.get(section, option)
  return None


def get_bz_data(siteconfig, userconfig):
  sRepo = os.getcwd()

  try:
    sBZUrl = siteconfig.get(sRepo, "bugzilla_url")
    sBZUser = siteconfig.get(sRepo, "bugzilla_user")
    sBZPasswd = siteconfig.get(sRepo, "bugzilla_password")
  except:
    print "missing/incomplete bugzilla conf"
    sys.exit(1)

  if userconfig.has_section(sRepo):
    if userconfig.has_option(sRepo, "bugzilla_user") and \
        userconfig.has_option(sRepo, "bugzilla_password"):
      sBZUser = userconfig.get(sRepo, "bugzilla_user")
      sBZPasswd = userconfig.get(sRepo, "bugzilla_password")

  return (sBZUrl, sBZUser, sBZPasswd)



def get_logger(siteconfig):
  sRepo = os.getcwd()
  logger = None
  if siteconfig.has_option(sRepo, "logfile"):
    logger = logging.getLogger("gitzilla")
    logger.addHandler(logging.FileHandler(siteconfig.get(sRepo, "logfile")))
    # default to debug, but switch to info if asked.
    sLogLevel = get_or_default(siteconfig, sRepo, "loglevel", "debug")
    logger.setLevel({"info": logging.INFO}.get(sLogLevel, logging.DEBUG))

  return logger


def get_bug_regex(siteconfig):
  sRepo = os.getcwd()
  oBugRegex = None
  if siteconfig.has_option(sRepo, "bug_regex"):
    oBugRegex = re.compile(siteconfig.get(sRepo, "bug_regex"),
                           re.MULTILINE | re.DOTALL | re.IGNORECASE)

  return oBugRegex




def post_receive():
  """
  The gitzilla-post-receive hook script.

  The configuration is picked up from /etc/gitzillarc and ~/.gitzillarc

  The user specific configuration is allowed to override the bugzilla
  username and password.
  """
  siteconfig = ConfigParser.SafeConfigParser()
  siteconfig.readfp(file("/etc/gitzillarc"))
  sRepo = os.getcwd()

  if not siteconfig.has_section(sRepo):
    print "No %s section found in /etc/gitzillarc" % (sRepo,)
    sys.exit(1)

  userconfig = ConfigParser.SafeConfigParser()
  userconfig.read(os.path.expanduser("~/.gitzillarc"))

  (sBZUrl, sBZUser, sBZPasswd) = get_bz_data(siteconfig, userconfig)

  logger = get_logger(siteconfig)
  oBugRegex = get_bug_regex(siteconfig)
  sSeparator = get_or_default(siteconfig, sRepo, "separator")
  sFormatSpec = get_or_default(siteconfig, sRepo, "formatspec")

  gitzilla.hooks.post_receive(sBZUrl, sBZUser, sBZPasswd, sFormatSpec,
                              oBugRegex, sSeparator, logger)



def update():
  """
  The gitzilla-update hook script.

  The configuration is picked up from /etc/gitzillarc and ~/.gitzillarc

  The user specific configuration is allowed to override the bugzilla
  username and password.
  """
  siteconfig = ConfigParser.SafeConfigParser()
  siteconfig.readfp(file("/etc/gitzillarc"))
  sRepo = os.getcwd()

  if not siteconfig.has_section(sRepo):
    print "No %s section found in /etc/gitzillarc" % (sRepo,)
    sys.exit(1)

  logger = get_logger(siteconfig)
  oBugRegex = get_bug_regex(siteconfig)
  sSeparator = get_or_default(siteconfig, sRepo, "separator")
  sFormatSpec = get_or_default(siteconfig, sRepo, "formatspec")
  sBZUrl = None
  sBZUser = None
  sBZPasswd = None

  asAllowedStatuses = None
  if siteconfig.has_option(sRepo, "allowed_bug_states"):
    asAllowedStatuses = map(lambda x: x.strip(),
                siteconfig.get(sRepo, "allowed_bug_states").split(","))

    # and then we need the bugzilla info as well.
    userconfig = ConfigParser.SafeConfigParser()
    userconfig.read(os.path.expanduser("~/.gitzillarc"))
    (sBZUrl, sBZUser, sBZPasswd) = get_bz_data(siteconfig, userconfig)


  gitzilla.hooks.update(oBugRegex, asAllowedStatuses, sSeparator,
                        sBZUrl, sBZUser, sBZPasswd, logger)


