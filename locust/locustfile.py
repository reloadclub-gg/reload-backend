import itertools

from locust import FastHttpUser, between, task

user_ids = []


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
            self._verify(self.token)
            self.user = self._auth(self.token)
        else:
            self.user = self._auth(self.token)
            if not self.user.get('account').get('is_verified'):
                self._verify(self.token)

        if not self.user.get('id') in user_ids:
            user_ids.append(self.user.get('id'))

    @task
    def usage(self):
        self._prepare()
        self._auth(self.token)

        lobby_id = self.user.get('lobby_id')
        with self.client.get(
            f'/api/lobbies/{lobby_id}/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/detail/",
        ):
            pass

        with self.client.get(
            '/api/friends/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="friends/list/",
        ):
            pass

        with self.client.get(
            '/api/lobbies/invites/?received=true',
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/invites/",
        ):
            pass

        with self.client.get(
            '/api/notifications/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="notifications/list/",
        ):
            pass

        lobby_payload = (
            {'cancel_queue': True} if self.queued_lobby else {'start_queue': True}
        )
        with self.client.patch(
            f'/api/lobbies/{lobby_id}/',
            json=lobby_payload,
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/update/",
        ):
            self.queued_lobby = not self.queued_lobby
