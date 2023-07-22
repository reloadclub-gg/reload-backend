import itertools
import random

from locust import FastHttpUser, between, task

user_ids = []


class AppUser(FastHttpUser):
    wait_time = between(1, 2.5)
    id_auto_number = itertools.count(start=1)
    user = None
    token = None

    def _fake_signup(self):
        email = f'email{next(self.id_auto_number)}@locust.com'

        with self.client.post(
            '/api/accounts/fake-signup/',
            json={
                'email': email,
            },
            name="accounts/signup/",
        ) as response:
            return response.json().get('token')

    def _verify(self, token: str):
        with self.client.post(
            '/api/accounts/verify/',
            json={
                'verification_token': 'debug0',
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

    def _prepare(self):
        if not self.token:
            self.token = self._fake_signup()
            self.user = self._auth(self.token)
            self._verify(self.token)
        else:
            self.user = self._auth(self.token)
            if not self.user.get('account').get('is_verified'):
                self._verify(self.token)

        if not self.user.get('id') in user_ids:
            user_ids.append(self.user.get('id'))

    @task
    def profile(self):
        self._prepare()
        user_id = random.choice(user_ids)
        with self.client.get(
            f'/api/profiles/?user_id={user_id}',
            headers={'Authorization': f'Bearer {self.token}'},
            name="profiles/detail/",
        ):
            pass

    @task
    def lobby(self):
        self._prepare()
        lobby_id = self.user.get('lobby_id')
        if lobby_id:
            with self.client.get(
                f'/api/lobbies/{lobby_id}/',
                headers={'Authorization': f'Bearer {self.token}'},
                name="lobbies/detail/",
            ):
                pass
