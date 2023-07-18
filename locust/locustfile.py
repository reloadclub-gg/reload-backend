import itertools

from locust import FastHttpUser, between, events, task


class AppUser(FastHttpUser):
    wait_time = between(1, 2.5)
    id_auto_number = itertools.count(start=1000)
    queued = False

    def on_start(self):
        self.token = self.fake_signup()
        self.verify(self.token)
        self.user = self.auth(self.token)

    def fake_signup(self):
        email = f'email{next(self.id_auto_number)}@locust.com'

        with self.client.post(
            '/api/accounts/fake-signup/',
            json={
                'email': email,
            },
        ) as response:
            return response.json().get('token')

    def verify(self, token: str):
        with self.client.post(
            '/api/accounts/verify/',
            json={
                'verification_token': 'debug0',
            },
            headers={'Authorization': f'Bearer {token}'},
        ) as response:
            return response.json()

    def auth(self, token: str):
        with self.client.get(
            '/api/accounts/auth/',
            headers={'Authorization': f'Bearer {token}'},
        ) as response:
            return response.json()

    @task
    def fetch_profile(self):
        user_id = self.user.get('id')

        with self.client.get(
            f'/api/profiles/?user_id={user_id}',
            headers={'Authorization': f'Bearer {self.token}'},
        ) as response:
            return response.json()

    @task
    def queue(self):
        lobby_id = self.user.get('lobby_id')

        if not self.queued:
            with self.client.patch(
                f'/api/lobbies/{lobby_id}/',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'start_queue': True},
            ) as response:
                self.queued = True
                return response.json()
        else:
            with self.client.patch(
                f'/api/lobbies/{lobby_id}/',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'cancel_queue': True},
            ) as response:
                self.queued = False
                return response.json()
