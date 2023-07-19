import itertools

from locust import FastHttpUser, between, task


class AppUser(FastHttpUser):
    wait_time = between(1, 2.5)
    id_auto_number = itertools.count(start=1000)
    queued = False
    queue_available = True

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
    def queue(self):
        if not self.queue_available:
            return

        updated_user = self.auth(self.token)

        if updated_user.get('match_id'):
            return

        lobby_id = updated_user.get('lobby_id')

        with self.client.get(
            f'/api/lobbies/{lobby_id}/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/detail/",
        ) as response:
            lobby = response.json()

        restricted = lobby.get('restriction_countdown')

        if not self.queued and not restricted:
            with self.client.patch(
                f'/api/lobbies/{lobby_id}/',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'start_queue': True},
                name="lobbies/start_queue/",
            ) as response:
                self.queued = True
                return response.json()
        else:
            with self.client.patch(
                f'/api/lobbies/{lobby_id}/',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'cancel_queue': True},
                name="lobbies/cancel_queue/",
            ) as response:
                self.queued = False
                return response.json()

    @task
    def lock_in_or_ready(self):
        updated_user = self.auth(self.token)

        if updated_user.get('match_id'):
            return

        if updated_user.get('pre_match_id'):
            self.queue_available = False
            with self.client.get(
                '/api/pre-matches/',
                headers={'Authorization': f'Bearer {self.token}'},
                name="pre_matches/detail/",
            ) as response:
                pre_match = response.json()

            if pre_match and pre_match.get('state') == 'pre_start':
                with self.client.post(
                    '/api/pre-matches/lock-in/',
                    headers={'Authorization': f'Bearer {self.token}'},
                    name="pre_matches/lock-in/",
                ) as response:
                    return response.json()
        else:
            self.queue_available = True
