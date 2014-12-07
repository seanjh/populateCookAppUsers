from pymongo import MongoClient


class Database(object):

    def __init__(self, hostname, port=27017, username=None, password=None, database=None):
        self.hostname = hostname
        self.port = port
        self.username, self.password, self.database = None, None, None
        if username:
            self.username = username
        if password:
            self.password = password
        if database:
            self.database = database
        self._uri = None
        self.client = MongoClient(self.URI)

    @property
    def URI(self):
        if not self._uri:
            self._uri = 'mongodb://'
            if self.username and self.password:
                self._uri.append('%s:%s@' % (self.username, self.password))
            self._uri.append('%s:%s' % (self.hostname, self.port))
            if self.database:
                self._uri.append('/%s' % self.database)
        return self._uri