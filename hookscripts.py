
"""
hookscripts - ready to use hook scripts for gitzilla.

These pick up configuration values from the environment.

"""

import os
import sys
import gitzilla.hooks
import logging
import ConfigParser
import bugz

def get_or_default(conf, section, option, default=None):
  if conf.has_option(section, option):
    return conf.get(section, option)
  return None


def bz_auth_from_config(config, sRepo):
  sBZUser = None
  sBZPasswd = None

  if config.has_section(sRepo):
    if config.has_option(sRepo, "bugzilla_user") and config.has_option(sRepo, "bugzilla_password"):
      sBZUser = config.get(sRepo, "bugzilla_user")
      sBZPasswd = config.get(sRepo, "bugzilla_password")

  return (sBZUser, sBZPasswd)



def get_bz_data(siteconfig, userconfig):
  sRepo = os.getcwd()

  bAllowDefaultAuth = False

  try:
    sBZUrl = siteconfig.get(sRepo, "bugzilla_url")
  except:
    print "missing/incomplete bugzilla conf"
    sys.exit(1)

  sUserOption = get_or_default(siteconfig, sRepo, "user_config", "allow")
  sUserOption = {"deny": "deny", "force": "force"}.get(sUserOption, "allow")

  (sBZUser, sBZPasswd) = bz_auth_from_config(userconfig, sRepo)
  
  # ignore auth from site-config if "force"
  if sUserOption == "force":
    bAllowDefaultAuth = False

  # for 'allow', get the auth from user config but allow fallback
  if sUserOption == "allow":
    bAllowDefaultAuth = True

  # ignore auth from user config is "deny"
  if sUserOption == "deny":
    (sBZUser, sBZPasswd) = bz_auth_from_config(siteconfig, sRepo)
    if None in (sBZUser, sBZPasswd):
      raise ValueError("No default Bugzilla auth found. Cannot use user-auth because user_config is set to 'deny'")

  return (sBZUrl, sBZUser, sBZPasswd, bAllowDefaultAuth)



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



def make_bz_init(siteconfig, bAllowDefaultAuth):
  # return a bz_init function which does the right thing.

  def bz_init(sBZUrl, sBZUser, sBZPasswd):
    # if username/passwd are none, then modify the Bugz instance so that
    # Bugz.get_input and getpass.getpass get the username and passwd
    # from the siteconfig.
    if sBZUrl is None:
      raise ValueError("No Bugzilla URL specified")

    sSiteUser = sBZUser
    sSitePasswd = sBZPasswd

    sRepo = os.getcwd()

    if None in (sBZUser, sBZPasswd):
      if bAllowDefaultAuth:
        # get data from siteconfig
        (sSiteUser, sSitePasswd) = bz_auth_from_config(siteconfig, sRepo)

    oBZ = bugz.bugzilla.Bugz(sBZUrl, user=sBZUser, password=sBZPasswd)
    oBZ.get_input = lambda prompt: sSiteUser
    import getpass
    getpass.getpass = lambda: sSitePasswd
    return oBZ

  return bz_init


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

  (sBZUrl, sBZUser, sBZPasswd, bAllowDefaultAuth) = get_bz_data(siteconfig, userconfig)

  logger = get_logger(siteconfig)
  oBugRegex = get_bug_regex(siteconfig)
  sSeparator = get_or_default(siteconfig, sRepo, "separator")
  sFormatSpec = get_or_default(siteconfig, sRepo, "formatspec")

  bz_init = make_bz_init(siteconfig, bAllowDefaultAuth)

  gitzilla.hooks.post_receive(sBZUrl, sBZUser, sBZPasswd, sFormatSpec,
                              oBugRegex, sSeparator, logger, bz_init)



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

  asAllowedStatuses = None
  if siteconfig.has_option(sRepo, "allowed_bug_states"):
    asAllowedStatuses = map(lambda x: x.strip(),
                siteconfig.get(sRepo, "allowed_bug_states").split(","))

  # and the bugzilla info.
  userconfig = ConfigParser.SafeConfigParser()
  userconfig.read(os.path.expanduser("~/.gitzillarc"))
  (sBZUrl, sBZUser, sBZPasswd, bAllowDefaultAuth) = get_bz_data(siteconfig, userconfig)

  bz_init = make_bz_init(siteconfig, bAllowDefaultAuth)

  gitzilla.hooks.update(oBugRegex, asAllowedStatuses, sSeparator,
                        sBZUrl, sBZUser, sBZPasswd, logger, bz_init)


