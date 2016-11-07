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
            response = self._bz.User.login({'login': self._user,
                                            'password': self._password})
            self._authed = True
            if 'token' in response:
              self._bz_token = response['token']

    def bug_status(self, bugid):
        self.auth()
        params = {'ids': [bugid], 'include_fields': ['status']}
        if hasattr(self, '_bz_token'):
          params['Bugzilla_token'] = self._bz_token

        bugdat = self._bz.Bug.get(params)
        return bugdat['bugs'][0]['status']

    def add_bug_comment(self, bugid, comment):
        self.auth()
        params = {'id': bugid, 'comment': comment}
        if hasattr(self, '_bz_token'):
          params['Bugzilla_token'] = self._bz_token

        self._bz.Bug.add_comment(params)
