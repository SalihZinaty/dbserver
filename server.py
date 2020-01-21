# [START imports]

# importing the google datastore library and the webapp2 package
from google.appengine.ext import ndb
import webapp2
DEFAULT_ACCOUNT_NAME = 'default_account'
# [END imports]


def account_key(account_name=DEFAULT_ACCOUNT_NAME):
    return ndb.Key('Account', account_name)


class Account(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    value = ndb.StringProperty(indexed=True)
    history = ndb.StringProperty(repeated=True)
    hidx = ndb.IntegerProperty(indexed=True)


class Last(ndb.Model):
    last = ''


class SetHandler(webapp2.RequestHandler):
    # set the variable to the DB
    def get(self):
        nameid = self.request.get('name')
        Last.last = nameid
        valueid = self.request.get('value')
        query = Account.query(Account.name == nameid)
        accountid = query.fetch()

        if not accountid:
            account = Account(parent=account_key(account_name=DEFAULT_ACCOUNT_NAME))
            account.name = nameid
            account.value = valueid
            account.history.append('None')
            account.history.append(valueid)
            account.hidx = 1
            account.put()
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(account.name + ' = ' + account.value)
        else:
            query = Account.query(Account.name == nameid)
            account = query.fetch()
            account[0].value = valueid
            account[0].history = account[0].history[0:account[0].hidx+1]
            account[0].history.append(valueid)
            account[0].hidx = account[0].hidx + 1
            account[0].put()
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(account[0].name + ' = ' + account[0].value)


class GetHandler(webapp2.RequestHandler):
    # get the variable from the DB
    def get(self):
        name = self.request.get('name')
        query = Account.query(Account.name == name)
        account = query.fetch()
        if not account:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('None')
        else:
            # need to connect to the database
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(account[0].value)


class UnsetHandler(webapp2.RequestHandler):
    # unset the variable
    def get(self):
        name = self.request.get('name')
        Last.last = name
        query = Account.query(Account.name == name)
        account = query.fetch()
        account[0].value = 'None'
        account[0].history = account[0].history[0:account[0].hidx + 1]
        account[0].history.append('None')
        account[0].hidx = account[0].hidx + 1
        account[0].put()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(name + ' = ' + account[0].value)


class NumEqualToHandler(webapp2.RequestHandler):
    # print the number of variables that are set to the value the user enters
    def get(self):
        val = self.request.get('value')
        query = Account.query(Account.value == val)
        account = query.fetch()
        len_acc = len(account)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(len_acc)


class UndoHandler(webapp2.RequestHandler):
    # undo the most recent SET/UNSET command
    def get(self):
        name = Last.last
        query = Account.query(Account.name == name)
        account = query.fetch()
        if account[0].hidx > 0:
            account[0].hidx = account[0].hidx - 1
            account[0].value = account[0].history[account[0].hidx]
            account[0].put()
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(name + ' = ' + account[0].value)
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('NO COMMANDS')


class RedoHandler(webapp2.RequestHandler):
    # redo all the commands
    def get(self):
        name = Last.last
        query = Account.query(Account.name == name)
        account = query.fetch()
        if account[0].hidx < len(account[0].history)-1:
            account[0].hidx = account[0].hidx + 1
            account[0].value = account[0].history[account[0].hidx]
            account[0].put()
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(name + ' = ' + account[0].value)
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('NO COMMANDS')


class EndHandler(webapp2.RequestHandler):
    # end the app and remove all the data from it
    # print CLEANED once it done
    def get(self):
        grabname = ndb.query.gql('SELECT name FROM Account')
        names = grabname.fetch()
        for i in range(len(names)):
            names[i].key.delete()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('CLEANED')


# [START app]
app = webapp2.WSGIApplication([
    ('/get', GetHandler),
    ('/set', SetHandler),
    ('/unset', UnsetHandler),
    ('/numequalto', NumEqualToHandler),
    ('/undo', UndoHandler),
    ('/redo', RedoHandler),
    ('/end', EndHandler)
], debug=False)
# [END app]
