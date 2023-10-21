import random
import string

import psycopg2

from locust import FastHttpUser, events, task

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
    user = None
    token = None

    def __generate_random_email(self):
        domain = "@locust.com"
        username_length = random.randint(3, 20)
        username = ''.join(
            random.choice(string.ascii_lowercase) for _ in range(username_length)
        )
        return username + domain

    @task
    def verify(self):
        if not self.user:
            return

        account = self.user.get('account')
        is_verified = account and account.get('is_verified')
        if is_verified:
            return

        # print('VERIFICA', self.user)
        self.token = self.user.get('token')
        verification_token = self.user.get('verification_token')
        verify = self.client.post(
            '/api/accounts/verify/',
            json={'verification_token': verification_token},
            headers={'Authorization': f'Bearer {self.token}'},
            name="accounts/verify/",
        )
        self.user = verify.json()

    @task
    def signup(self):
        if self.user:
            return

        email = self.__generate_random_email()
        fake_signup = self.client.post(
            '/api/accounts/fake-signup/',
            json={'email': email},
            name='accounts/signup',
        )
        self.user = fake_signup.json()

    @task
    def usage(self):
        if not self.user or not self.token:
            return

        account = self.user.get('account')
        is_verified = account and account.get('is_verified')
        if not is_verified:
            return

        # print('NAVEGA', self.user)

        self.client.get(
            '/api/accounts/auth/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="accounts/detail/",
        )

        self.client.get(
            '/api/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="app/maintenance/",
        )

        self.client.get(
            '/api/friends/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="friends/list/",
        )

        self.client.get(
            '/api/lobbies/invites/?received=true',
            headers={'Authorization': f'Bearer {self.token}'},
            name="lobbies/invites/",
        )

        self.client.get(
            '/api/notifications/',
            headers={'Authorization': f'Bearer {self.token}'},
            name="notifications/list/",
        )

    @task
    def get(self):
        self.client.get("/api/", name="get")

    @task
    def post(self):
        self.client.post("/api/", name="post")

    @task
    def put(self):
        self.client.put("/api/", name="put")

    @task
    def patch(self):
        self.client.patch("/api/", name="patch")

    @task
    def delete(self):
        self.client.delete("/api/", name="delete")


events.test_stop.add_listener(on_test_stop)
