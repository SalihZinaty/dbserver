# [START imports]

# importing the google datastore library and the webapp2 package
from google.appengine.ext import ndb
import webapp2
DEFAULT_ACCOUNT_NAME = 'default_account'
# [END imports]


def account_key(account_name=DEFAULT_ACCOUNT_NAME):
    # this function used to construct datastore key for the account entity
    return ndb.Key('Account', account_name)


class Account(ndb.Model):
    # this is the main class in the server
    # the Account entity has 4 values that are stored in the datastore:
    #   name: this is the name of the entity
    #   value: the value entered by the client
    #   the history: this is a list, (the repeated argument in the datastore indicates for a list.
    #       the history saves all the history of the entered values of a given name.
    #       when a set/unset command fetched, the history until this point saved and the other part dropped
    #   hidx: this is a pointer for the place in the history list
    name = ndb.StringProperty(indexed=True)
    value = ndb.StringProperty(indexed=True)
    history = ndb.StringProperty(repeated=True)
    hidx = ndb.IntegerProperty(indexed=True)


class Last(ndb.Model):
    #   Class used for saving the last entity name
    #   this class used to identify in witch entity the last set/unset command done on
    last = ''


class SetHandler(webapp2.RequestHandler):
    #   Setting the entity value
    #   if the entity doesn't exist, this class creates new entity with value and name as specified by the user
    def get(self):
        nameid = self.request.get('name')  # grabbing the name from the query
        Last.last = nameid  # adding the name to the last class
        valueid = self.request.get('value')  # grabbing the value from the url query
        query = Account.query(Account.name == nameid)  # filtering the accounts by the specific name
        accountid = query.fetch()  # fetching the query

        if not accountid:  # checking of the account is existing, if not, create new Account instance
            account = Account(parent=account_key(account_name=DEFAULT_ACCOUNT_NAME))  # creating new account instance
            account.name = nameid  # changing the name of the instance to the name from the url query
            account.value = valueid  # same thing for the value
            account.history.append('None')  # adding initial value to the instance 'None'
            account.history.append(valueid)  # adding the value to the history list of the instance
            account.hidx = 1  # initiating the history pointer to 1, (the 0 is the 'None')
            account.put()  # pushing the changes to the datastore
            self.response.headers['Content-Type'] = 'text/plain'  # sending the header
            self.response.write(account.name + ' = ' + account.value)  # sending the response
        else:
            # in case the account is exist, make the same thing
            # because the way it works, the account is a list, therefore, must choose the first one.
            query = Account.query(Account.name == nameid)
            account = query.fetch()
            account[0].value = valueid
            account[0].history = account[0].history[0:account[0].hidx+1]
            account[0].history.append(valueid)
            account[0].hidx = account[0].hidx + 1  # increasing the hidx
            account[0].put()
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(account[0].name + ' = ' + account[0].value)


class GetHandler(webapp2.RequestHandler):
    # get the variable from the datastore
    def get(self):
        name = self.request.get('name')
        query = Account.query(Account.name == name)  # filtering the Accounts by name
        account = query.fetch()
        if not account:  # if the account not found, response with 'None'
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
        if not account:  # if the Account doesn't exist, respond with 'None'
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('None')
        else:
            # if the Account exist, change the value to 'None'
            # then, cut the history list until this unset
            # then, add the 'None' value to the history list
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
        query = Account.query(Account.value == val)  # Checking the number of entities with the same value
        account = query.fetch()
        len_acc = len(account)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(len_acc)


class UndoHandler(webapp2.RequestHandler):
    # undo the most recent SET/UNSET command
    # from the Last class, take the entity that you did a set/unset command on it
    # undo the action
    def get(self):
        name = Last.last
        query = Account.query(Account.name == name)
        account = query.fetch()
        if account and account[0].hidx > 0:  # Check if you still in the range of the history inputs
            account[0].hidx = account[0].hidx - 1  # if yes, decrease the history pointer
            account[0].value = account[0].history[account[0].hidx]  # assign the value of the history in the value field
            account[0].put()  # push to the datastore
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(name + ' = ' + account[0].value)
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('NO COMMANDS')


class RedoHandler(webapp2.RequestHandler):
    # redo all the commands
    #  same as the undo command
    def get(self):
        name = Last.last
        query = Account.query(Account.name == name)
        account = query.fetch()
        if account and account[0].hidx < len(account[0].history)-1:
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
    # use the query of the gql supported by google datastore
    # select the name field from all the accounts
    # loop over all the Accounts and delete them
    def get(self):
        grabname = ndb.query.gql('SELECT name FROM Account')
        names = grabname.fetch()
        for i in range(len(names)):
            names[i].key.delete()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('CLEANED')


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Welcome to the data store\n\n'
                            'please use these routes to use the data store:\n\n'
                            '/set: set a new name and value to the data store\n\n'
                            '/get: get a value for a name from the datastore\n\n'
                            '/unset: unset a name value\n\n'
                            '/numequalto: check the number of names that have the same value\n\n'
                            '/undo: undo set/unset action on the last entered name\n\n'
                            '/redo: redo set/unset action on the last entered name\n\n'
                            '/end: delete all the data store\n\n\n'
                            'Powered by Salih Zinaty')


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/get', GetHandler),
    ('/set', SetHandler),
    ('/unset', UnsetHandler),
    ('/numequalto', NumEqualToHandler),
    ('/undo', UndoHandler),
    ('/redo', RedoHandler),
    ('/end', EndHandler)
], debug=False)
# [END app]
