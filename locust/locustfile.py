import itertools

import psycopg2

from locust import FastHttpUser, between, events, task

user_ids = []


def clear_db():
    conn = psycopg2.connect("dbname=postgres user=postgres password=postgres host=db")
    cur = conn.cursor()

    cur.execute("DELETE FROM accounts_userlogin;")
    cur.execute(
        """DELETE FROM accounts_account
            WHERE user_id IN (
                SELECT id FROM accounts_user WHERE is_staff=FALSE
            );"""
    )
    cur.execute(
        """DELETE FROM social_auth_usersocialauth
            WHERE user_id IN (
                SELECT id FROM accounts_user WHERE is_staff=FALSE
            );"""
    )
    cur.execute("DELETE FROM accounts_user WHERE is_staff=FALSE;")
    conn.commit()

    cur.close()
    conn.close()


def on_test_stop(environment, **kwargs):
    clear_db()


class AppUser(FastHttpUser):
    wait_time = between(1, 2.5)
    id_auto_number = itertools.count(start=1)
    user = None
    token = None
    verification_token = None
    queued_lobby = False

    def _fake_signup(self):
        email = f'email{next(self.id_auto_number)}@locust.com'

        with self.client.post(
            '/api/accounts/fake-signup/',
            json={'email': email},
            name="accounts/signup/",
        ) as response:
            return (
                response.json().get('token'),
                response.json().get('verification_token'),
            )

    def _verify(self, token: str):
        with self.client.post(
            '/api/accounts/verify/',
            json={
                'verification_token': self.verification_token,
            },
            headers={'Authorization': f'Bearer {token}'},
            name="accounts/verify/",
        ) as response:
            return response.json()

    def _auth(self, token: str):
        with self.client.get(
            '/api/accounts/auth/',
            headers={'Authorization': f'Bearer {token}'},
            name="accounts/detail/",
        ) as response:
            return response.json()

    def _logout(self, token: str):
        with self.client.patch(
            '/api/accounts/logout/',
            headers={'Authorization': f'Bearer {token}'},
            name="accounts/logout/",
        ) as response:
            return response.json()

    def _prepare(self):
        if not self.token:
            self.token, self.verification_token = self._fake_signup()
            self.user = self._auth(self.token)

            if not self.user.get('account').get('is_verified'):
                self._verify(self.token)
                self.user = self._auth(self.token)
        else:
            self.user = self._auth(self.token)
            if not self.user.get('account').get('is_verified'):
                self._verify(self.token)

        if not self.user.get('id') in user_ids:
            user_ids.append(self.user.get('id'))

    def _fetch_maintenance(self):
        with self.client.get(
            '/api/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="app/maintenance/",
        ):
            pass

    def _fetch_lobby(self):
        lobby_id = self.user.get('lobby_id')
        with self.client.get(
            f'/api/lobbies/{lobby_id}/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/detail/",
        ):
            pass

    def _fetch_friends(self):
        with self.client.get(
            '/api/friends/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="friends/list/",
        ):
            pass

    def _fetch_invites(self):
        with self.client.get(
            '/api/lobbies/invites/?received=true',
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/invites/",
        ):
            pass

    def _fetch_notifications(self):
        with self.client.get(
            '/api/notifications/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="notifications/list/",
        ):
            pass

    def _fetch_mock(self):
        with self.client.get(
            '/api/list/',
            name="app/mock/",
        ):
            pass

    @task
    def usage(self):
        self._fetch_mock()
        # self._fake_signup()
        # if not self.user or not self.token:
        #     self._prepare()
        # else:
        #     self._fetch_maintenance()
        # self._fetch_lobby()
        # self._fetch_friends()
        # self._fetch_invites()
        # self._fetch_notifications()


events.test_stop.add_listener(on_test_stop)
