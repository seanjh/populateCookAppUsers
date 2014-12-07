import random
import json

import requests

names_file = 'data/names.txt'
domains_file = 'data/domains.txt'
web_hostname = 'http://127.0.0.1:3000'
register = '/register'


class User(object):
    PASSWORD = 'qwerty1234'

    def __init__(self, name, domain):
        self.name = name.rstrip()
        self.domain = domain.rstrip()
        self._id = None
        self.followers = list()
        self.following = list()
        self._v = None
        self._provider = None

    def insert(self, collection):
        pass

    @property
    def user_object(self):
        user = dict()
        user['name'] = '%s' % self.name
        parts = self.name.split()
        first = parts[0]
        last = parts[1]
        user['username'] = '%s%s' % (first.lower()[0], last.lower())
        user['email'] = '%s@%s' % (user['username'], self.domain)
        user['password'] = User.PASSWORD
        user['confirmPassword'] = user['password']
        return user

    @property
    def mongo_id(self):
        if not self._id:
            return None
        else:
            return self._id

    @property
    def version(self):
        return self._v

    @property
    def provider(self):
        return self._provider

    @mongo_id.setter
    def mongo_id(self, id_str):
        self._id = id_str

    def update_from_json(self, json_object):
        if json_object.get('_id'):
            self.mongo_id = json_object.get('_id')
        if json_object.get('followers'):
            self.followers = json_object.get('followers')
        if json_object.get('following'):
            self.followers = json_object.get('following')
        if json_object.get('__v'):
            self._v = json_object.get('__v')
        if json_object.get('provider'):
            self._provider = json_object.get('provider')

    def __str__(self):
        return '%s' % self.user_object


class CookAppSite(object):
    login_endpoint = '/login'
    logout_endpoint = '/logout'
    me_endpoint = '/users/me'
    register_endpoint = '/register'
    following_endpoint = '/following'

    def __init__(self, session, hostname='http://127.0.0.1:3000'):
        self.session = session
        self.hostname = hostname

    def get_endpoint_URI(self, endpoint):
        return '%s%s' % (self.hostname, endpoint)

    def add_user(self, user_object):
        assert user_object.get('name')is not None
        assert user_object.get('username')is not None
        assert user_object.get('email') is not None
        assert user_object.get('password') is not None
        assert user_object.get('confirmPassword') is not None
        assert user_object.get('password') == user_object.get('confirmPassword')

        res = self.session.post(
            '%s%s' % (self.hostname, CookAppSite.register_endpoint),
            data=user_object
        )
        if res.status_code == requests.codes.ok:
            return self.login(user_object)
        else:
            print 'Failed to add %s' % json.dumps(user_object)
            if res.json():
                print '%s: %s' % (res, res.json())
                if 'Username already taken' in res.json()[-1].get('msg'):
                    return
                else:
                    res.raise_for_status()

    def get_user_object(self):
        res = self.session.get(self.get_endpoint_URI(CookAppSite.me_endpoint))
        if not res.status_code == requests.codes.ok:
            res.raise_for_status()
        return res.json()

    def logout(self):
        res = self.session.get(self.get_endpoint_URI(CookAppSite.logout_endpoint))
        if not res.status_code == requests.codes.ok:
            res.raise_for_status()

    def login(self, user_object):
        self.logout()
        login_object = dict()
        login_object['email'] = user_object.get('email')
        login_object['password'] = user_object.get('password')
        res = self.session.post(
            self.get_endpoint_URI(CookAppSite.login_endpoint),
            data=login_object
        )
        if not res.status_code == requests.codes.ok:
            res.raise_for_status()
        if res.json():
            return res.json().get('user')
        else:
            return None

    def is_logged_in(self, username):
        user = self.get_user_object()
        return user is not None and user.get('username') == username

    def follow_users(self, users_to_follow):
        responses = []
        for user_id in users_to_follow:
            req_obj = {"userId": user_id}
            res = self.session.post(
                self.get_endpoint_URI(CookAppSite.following_endpoint),
                data=req_obj
            )
            responses.append(res)
            if res.status_code == requests.codes.ok:
                print 'Successfully followed %s' % user_id
            else:
                res.raise_for_status()
        return self.get_user_object()


def load_names():
    with open(names_file) as infile:
        return infile.readlines()


def load_domains():
    with open(domains_file) as infile:
        return infile.readlines()


def get_random_follows(user, all_users, maximum=20):
    return [all_users[i].mongo_id for i in
            random.sample(range(len(all_users)), random.randrange(maximum))
            if all_users[i].mongo_id
            and all_users[i].mongo_id != user.mongo_id
    ]


def main():
    names = load_names()
    domains = load_domains()
    users = []
    # make users
    for name in names:
        domain = domains[random.randrange(len(domains))]
        user = User(name.decode('utf-8'), domain.decode('utf-8'))
        users.append(user)

    # add users to site
    session = requests.Session()
    ctrl = CookAppSite(session)
    for user in users:
        user_obj = ctrl.add_user(user.user_object)
        if user_obj:
            user.update_from_json(user_obj)
            print 'Updating user %s (id=%s)' % (user.name, user.mongo_id)
        else:
            print 'Could not create user %s' % user.name

    # connect randomly to other users
    for user in users:
        user_obj = ctrl.login(user.user_object)
        if user_obj is None:
            print 'Failed to login %s (id=%s)' % (user.name, user.mongo_id)
            continue
        follow_list = get_random_follows(user, users)
        user_obj = ctrl.follow_users(follow_list)
        if user_obj:
            user.update_from_json(user_obj)
            print 'User %s (id=%s) is following: %s' % (user.name, user.mongo_id, str(user.following))
        else:
            print 'Failed to add followers for User %s (id=%s)' % (user.name, user.mongo_id)

if __name__ == '__main__':
    main()