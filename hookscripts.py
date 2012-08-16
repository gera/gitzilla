
"""
hookscripts - ready to use hook scripts for gitzilla.

These pick up configuration values from the environment.

"""

import os
import re
import sys
import gitzilla.hooks
import logging
import ConfigParser

DEFAULT = 'DEFAULT'

def to_bool(v):
  if isinstance(v, str):
    return v.lower() in ["yes", "true", "t", "1"]
  else:
    return bool(v)

def get_or_default(conf, section, option, default=None):
  if conf.has_option(section, option):
    return conf.get(section, option)
  elif conf.has_option(DEFAULT, option):
    return conf.get(DEFAULT, option)
  return default


def has_option_or_default(conf, section, option):
  return conf.has_option(section, option) or conf.has_option(DEFAULT, option)


def bz_auth_from_config(config, sRepo):
  sBZUser = None
  sBZPasswd = None

  if has_option_or_default(config, sRepo, "bugzilla_user") and has_option_or_default(config, sRepo, "bugzilla_password"):
    sBZUser = get_or_default(config, sRepo, "bugzilla_user")
    sBZPasswd = get_or_default(config, sRepo, "bugzilla_password")

  return (sBZUser, sBZPasswd)



def get_bz_data(siteconfig, userconfig):
  sRepo = os.getcwd()

  sBZUrl = get_or_default(siteconfig, sRepo, "bugzilla_url")
  if sBZUrl is None:
    sBZUrl = get_or_default(userconfig, sRepo, "bugzilla_url")

  sUserOption = get_or_default(siteconfig, sRepo, "user_config", "allow")
  sUserOption = {"deny": "deny", "force": "force"}.get(sUserOption, "allow")

  sBZUser, sBZPasswd = None, None

  # If "force", site config credentials irrelevant because they must not be used.
  if sUserOption != "force":
    (sBZUser, sBZPasswd) = bz_auth_from_config(siteconfig, sRepo)

  # If "deny", user config credentials irrelevant because they must not be used.
  if sUserOption != "deny":
    (uuser, upasswd) = bz_auth_from_config(userconfig, sRepo)
    if (sUserOption == "force"):
      # If "force", user config credentials MUST be used
      sBZUser, sBZPasswd = uuser, upasswd
    elif (sUserOption == "allow") and not (None in (uuser, upasswd)):
      # If "allow", only use user config credentials if there are any.
      sBZUser, sBZPasswd = uuser, upasswd
  elif (None in (sBZUser, sBZPasswd)):
    # User config may not be used, and that includes the cookie jar, if any.
    raise ValueError("No default Bugzilla auth found. Cannot use user-auth because user_config is set to 'deny'")

  if not sBZUrl:
    print "missing/incomplete bugzilla conf (no bugzilla_url)"
    sys.exit(1)

  return (sBZUrl, sBZUser, sBZPasswd)


def get_logger(siteconfig):
  sRepo = os.getcwd()
  logger = None
  if has_option_or_default(siteconfig, sRepo, "logfile"):
    logger = logging.getLogger("gitzilla")
    logger.addHandler(logging.FileHandler(get_or_default(siteconfig, sRepo, "logfile")))
    # default to debug, but switch to info if asked.
    sLogLevel = get_or_default(siteconfig, sRepo, "loglevel", "debug")
    logger.setLevel({"info": logging.INFO}.get(sLogLevel, logging.DEBUG))

  return logger


def get_bug_regex(siteconfig):
  sRepo = os.getcwd()
  oBugRegex = None
  if has_option_or_default(siteconfig, sRepo, "bug_regex"):
    oBugRegex = re.compile(get_or_default(siteconfig, sRepo, "bug_regex"),
                           re.MULTILINE | re.DOTALL | re.IGNORECASE)

  return oBugRegex


def post_receive(aasPushes=None):
  """
  The gitzilla-post-receive hook script.

  The configuration is picked up from /etc/gitzillarc and ~/.gitzillarc

  The user specific configuration is allowed to override the bugzilla
  username and password.

  aasPushes is a list of (sOldRev, sNewRev, sRefName) tuples, for when these
  aren't read from stdin (gerrit integration).
  """
  siteconfig = ConfigParser.RawConfigParser()
  siteconfig.readfp(file("/etc/gitzillarc"))
  sRepo = os.getcwd()

  userconfig = ConfigParser.RawConfigParser()
  userconfig.read(os.path.expanduser("~/.gitzillarc"))

  (sBZUrl, sBZUser, sBZPasswd) = get_bz_data(siteconfig, userconfig)

  logger = get_logger(siteconfig)
  oBugRegex = get_bug_regex(siteconfig)
  sRefPrefix = get_or_default(siteconfig, sRepo, "git_ref_prefix")
  sSeparator = get_or_default(siteconfig, sRepo, "separator")
  sFormatSpec = get_or_default(siteconfig, sRepo, "formatspec")
  bIncludeDiffStat = to_bool(get_or_default(siteconfig, sRepo, "include_diffstat", True))

  gitzilla.hooks.post_receive(sBZUrl, sBZUser, sBZPasswd, sFormatSpec,
                              oBugRegex, sSeparator, logger, None,
                              sRefPrefix, bIncludeDiffStat, aasPushes)



def update():
  """
  The gitzilla-update hook script.

  The configuration is picked up from /etc/gitzillarc and ~/.gitzillarc

  The user specific configuration is allowed to override the bugzilla
  username and password.
  """
  siteconfig = ConfigParser.RawConfigParser()
  siteconfig.readfp(file("/etc/gitzillarc"))
  sRepo = os.getcwd()

  logger = get_logger(siteconfig)
  oBugRegex = get_bug_regex(siteconfig)
  sRefPrefix = get_or_default(siteconfig, sRepo, "git_ref_prefix")
  sSeparator = get_or_default(siteconfig, sRepo, "separator")

  bRequireBugNumber = to_bool(get_or_default(siteconfig, sRepo, "require_bug_ref", True))
  asAllowedStatuses = None
  if has_option_or_default(siteconfig, sRepo, "allowed_bug_states"):
    asAllowedStatuses = map(lambda x: x.strip(),
                get_or_default(siteconfig, sRepo, "allowed_bug_states").split(","))

  # and the bugzilla info.
  userconfig = ConfigParser.RawConfigParser()
  userconfig.read(os.path.expanduser("~/.gitzillarc"))
  (sBZUrl, sBZUser, sBZPasswd) = get_bz_data(siteconfig, userconfig)

  gitzilla.hooks.update(oBugRegex, asAllowedStatuses, sSeparator, sBZUrl,
                        sBZUser, sBZPasswd, logger, None, sRefPrefix,
                        bRequireBugNumber)


