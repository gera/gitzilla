"""
Interface to pybugz.

Attempts to abstract away the major shifts that have happened to the
pybugz interface recently so it will work with several versions.
"""

_pybugz_xmlrpc = False

from bugz.bugzilla import BugzillaProxy as BugzillaProxy

class BugzillaWrapper(object):
    """This is a wrapper to ease using the Bugzilla XMLRPC interface
    and to insulate the other code from changes to how that interface
    is presented by pybugz.

    If this is overridden by hook scripts, you will need to
    monkeypatch the bugz module to have your class in place of this
    one."""

    def __init__(self, url, user, password):
        self._url = url
        self._user = user
        self._password = password
        self._bz = BugzillaProxy(url)
        self._authed = False

    def auth(self):
        if not self._authed:
            self._bz.User.login({'login': self._user,
                                'password': self._password})
            self._authed = True

    def bug_status(self, bugid):
        self.auth()
        bugdat = self._bz.Bug.get({'ids': [bugid],
                                  'include_fields': ['status']})
        return bugdat['bugs'][0]['status']

    def add_bug_comment(self, bugid, comment):
        self.auth()
        self._bz.Bug.add_comment({'id': bugid, 'comment': comment})
