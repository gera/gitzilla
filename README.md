
# GitZilla

**NOTE** : This project is no longer actively maintained.

GitZilla is Python magic to support Git-Bugzilla integration. There are
various ways of using GitZilla.

Note that GitZilla must be installed on the machine receiving commits from
everyone - home to the the "official" or the "central" repository.

There's a mailing list for GitZilla now, at gitzilla-talk@googlegroups.com


## Summary of features

GitZilla might be the right tool if you want to::

  - Automatically add commits to bugs referenced in the commit messages
    whenever changes are pushed to a central git repository.

  - Reject commits without a bug reference.

  - Only allow commits referring to active bugs (reject commits referring to
    CLOSED, RESOLVED or any other specific bug states).

  - (contributed, untested): Usable with Gerrit.

  - Some combination or all of the above.


With the above capabilities, GitZilla allows for::

  - Per-user, or system-wide authentication for Bugzilla.
  - Configurable bug comment formats and content.
  - Optional diffstat as part of the bug comments.
  - Configurable regexes for matching bug IDs in commit messages.


## Usage

### Simple ready scripts

To quickly start using GitZilla:

  * Install GitZilla. You may choose the .deb for easy installation on
    Debian/Ubuntu systems. Otherwise, just unpack the source and install in
    the usual setuptools way::

        sudo python3 ./setup.py install

  * Switch to the hooks directory 
    (/path/to/central/repository/Example.git/hooks) 
    and delete the ``post-receive`` and ``update`` hooks.

  * Link (or copy) the gitzilla provided hooks::

        ln -s $(which gitzilla-post-receive) post-receive
        ln -s $(which gitzilla-update) update

  * Read and edit the config file at /etc/gitzillarc. A simple (and sufficient
    for most cases) configuration is something like::

        [/path/to/repository/Example.git]
        bugzilla_url: https://repo.example.com/bugzilla/xmlrpc.cgi
        bugzilla_user: foo@example.com
        bugzilla_password: blahblah
        allowed_bug_states: NEW, ASSIGNED, REOPENED

    (and even the last item is optional!)

  * Commit away!


### Custom GitZilla

If you need the hooks to do other stuff apart from just the Bugzilla
integration, you could write your hook as a Python script and leave the
Bugzilla stuff to functions from ``gitzilla.hookscripts`` or
``gitzilla.hooks``.

In fact with the defaults, are equivalent to the following:

post-receive::

    #!/usr/bin/python
    from gitzilla.hookscripts import post_receive
    post_receive()


update::

    #!/usr/bin/python
    from gitzilla.hookscripts import update
    update()

The functions from ``gitzilla.hookscripts`` parse and pick up values from the
configuration files. If you want to taylor more use the functions from
``gitzilla.hooks``.

post-receive::

    #!/usr/bin/python
    from gitzilla.hooks import post_receive
    post_receive("https://repo.example.com/bugzilla", "username", "password")

update::

    #!/usr/bin/python
    from gitzilla.hooks import update
    update("https://repo.example.com/bugzilla", "username", "password")

You could pass a custom bug id extraction regex and your own logging.Logger
instance. The update hook function also accepts an array of allowed bug status
strings.

Look at the module help for gitzilla.hooks for more information.



## Configuration

GitZilla uses a global configuration file (at /etc/gitzillarc) as well as
per-user configuration files (at ~/.gitzillarc). All the configuration options
are picked up from the global config file, and the user specific config is
allowed to override **only** the ``bugzilla_user`` and ``bugzilla_password``
parameters.

The configuration files themselves are in the ConfigParser format (see
http://docs.python.org/library/configparser.html). A sample configuration
looks like::

    [DEFAULT]
    user_config: deny
    allowed_bug_states: NEW, ASSIGNED, REOPENED

    [/path/to/repository/.git]
    bugzilla_url: https://repo.example.com/bugzilla/xmlrpc.cgi
    bugzilla_user: foo@example.com
    bugzilla_password: blahblah
    logfile: /var/log/gitzilla.log
    loglevel: info


Each git repository on the system MAY have its own section. The global config
MUST specify the ``bugzilla_url`` parameter.

Default values (applied to each repository unless overridden) may be specified 
in a [DEFAULT] section.

The user specific files are entirely optional.

### Mandatory parameters

  - bugzilla_url


### Optional parameters

  - bugzilla_user

        the default username for Bugzilla.

  - bugzilla_password

        the default password for Bugzilla.

  - user_config

        allow/deny user specific bugzilla credentials. The legal values are
        ``allow``, ``deny`` and ``force``. Defaults to ``allow``.

  - require_bug_ref

        if True, the update hook will require that each commit message contains
        a bug number. If False, it will not. Defaults to True (same as historical
        behaviour).

  - allowed_bug_states

        a comma separated set of states that a bug must be in, in order for
        the commit to be allowed by the update hook.

  - formatspec

        appended to ``--pretty=format:`` and passed to ``git whatchanged``.
        See the ``git whatchanged`` manpage for more info. Newlines are
        automatically converted to '%n', which is what the git format spec
        requires.

  - include_diffstat

       include diffstat (a list of changed file with a histogram). If False,
       the diffstat is not included. Defaults to True to be consistent with
       previous behaviour.

  - separator

        a string which would never occur in commit messages. You should not
        need to set this, as it is already at a safe default.

  - bug_regex

        the (Python) regex for capturing bug numbers. MUST capture all the
        digits (and only the digits) of the bug id in a named group called
        ``bug``. This regex is compiled internally with the MULTILINE, DOTALL
        and IGNORECASE options set. The default regex captures from the
        following forms:

          * bug 123
          * Bug # 123
          * BUG123
          * bug# 123
          * Bug #123

  - git_ref_prefix
        
        the string which must start a git reference for its commits to be
        processed. Defaults to 'refs/heads/' so that we don't process 'tags/'
        and run the risk of processing many commits multiple times. You can
        set it to the empty string to process all git references.
  
  - logfile

        the file to log to. MUST be writable by the uid of the git process. In
        case of ssh pushes, tha usually means it should be writable by all.

  - loglevel

        can be ``info`` or ``debug``. Defaults to ``debug``.


### Security note

Note that the global config would be readable by all and may contain a bugzilla
credentials. If you think this is a problem, you may rely on per-user auth.

If the ``user_config`` option is set to ``allow`` or ``force``, then auth
credentials are picked up from the user specific ``~/.gitzillarc`` file.

If the ``user_config`` option is ``force`` and the ``~/.gitzillarc`` does not
contain bugzilla credentials, then the ``~/.bugz_cookie`` file is used for
authentication. To generate a cookie file, a user may use the
``gitzilla-gencookie`` script. The cookie validity will of course be dependent
on your Bugzilla configuration. If neither credentials nor the cookie file are
present (and valid), Bugzilla interactions will fail and the commits will be
rejected.

If the ``user_config`` option is ``allow``, then user specific credentials are
used if available. Only if credentials are unavailable in both the
user-specific as well as the systemwide configs, the cookie file is used. This
configuration is the default because of the closeness of behaviour from version
1.0.


To summarize:

  - To allow (but not force) users to use their own auth/credentials set
    ``user_config``  to ``allow`` and set ``bugzilla_user`` and
    ``bugzilla_password`` in the system wide config.

  - To enforce user credentials, set ``user_config`` to ``force`` and leave the
    Bugzilla credentials out of the system wide config.

  - To use system wide credentials *only*, set ``user_config`` to ``deny``.

  - To enforce Bugzilla integration, use the update hook. The update hook will
    check the validity of the credentials (system or user, depending on the
    config), regardless of the ``allowed_bug_states`` option. This is a change
    in behaviour from version 1.0.

*cookies are no longer used since Bugzilla 4.4.3


## Requirements

To install and run GitZilla, you need:

  - Python 3 (tested with 3.4.0)
  - pybugz >= 0.11.1

This combination has been tested with Bugzilla 4.4.6 & 4.2.11


If you wish to use python 2:
  - Python (tested with 2.6.4, should work with >=2.5)
  - Pybugz (tested with 0.8.0)
  - Gitzilla <= 2.0

This python 2 combination works with Bugzilla 3.0.11, and with pybugz 0.9.3 it may support up to Bugzilla 4.4.2

The excellent pybugz can be obtained from http://github.com/williamh/pybugz
and http://github.com/williamh/pybugz/releases


## Download

GitZilla is hosted at GitHub : http://github.com/gera/gitzilla

You can access the downloads at : http://github.com/gera/gitzilla/downloads

The download page contains a .deb which should work on Debian and Ubuntu
systems.


## Mailing list

The official GitZilla mailing list: gitzilla-talk@googlegroups.com

