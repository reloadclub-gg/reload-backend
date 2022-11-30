import secrets

from pydantic import BaseModel

from core.redis import RedisClient

cache = RedisClient()


class AuthConfig:
    """
    Config class for the Auth model. Rather this configs to be here instead of
    in Django settings because those settings are specific to the Auth model.
    """
    TOKEN_SIZE: int = 128
    CACHE_TTL_TOKEN: int = 3600 * 24 * 3
    CACHE_TTL_SESSIONS: int = 10
    CACHE_PREFIX_TOKEN: str = '__auth:token:'
    CACHE_PREFIX_SESSIONS: str = '__auth:sessions:'


class Auth(BaseModel):
    """
    This class is meant to be the core authentication middleware to the Redis cache db.
    Every method that touches Redis, and is related to auth (sessions, tokens, login, etc)
    should be here.

    The Redis db keys from this model are described below:

    [key] __auth:token:[token] <user_id>
    Unique user token. Each user that logs in using Steam have one.

    [key] __auth:sessions:[user_id] <int>
    User sessions count. If there isn't a session for a user, it means an offline user.
    When this counter reaches 0, it got a TTL defined by the model config.
    """
    user_id: int
    token: str = None
    token_cache_key: str = None
    sessions_cache_key: str = None
    force_token_create: bool = False

    def __init__(self, **data):
        """
        Tries to fetch an existent token given a user_id. If it fails on that,
        we create a new token for that user but we don't auto save it to Redis.
        To save the token on Redis, one have to explicit call the `create_token`
        method or instantiate this class with `force_token_create` as `True`.
        """
        super().__init__(**data)
        self.__init_sessions()

        if not self.token:
            self.__init_token()

        self.token_cache_key = f'{AuthConfig.CACHE_PREFIX_TOKEN}{self.token}'

        if self.force_token_create:
            self.create_token()

    def __init_token(self):
        """
        Set a token to `self.token` either if find one for `self.user_id` on Redis
        or  generating a new one.
        """
        self.token = self.get_token()
        if not self.token:
            self.token = secrets.token_urlsafe(AuthConfig.TOKEN_SIZE)

    def __init_sessions(self):
        """
        Save the sessions counter key on Redis.
        """
        self.sessions_cache_key = f'{AuthConfig.CACHE_PREFIX_SESSIONS}{self.user_id}'

    def create_token(self):
        """
        Save the token key on Redis.
        """
        cache.set(self.token_cache_key, self.user_id, AuthConfig.CACHE_TTL_TOKEN)

    def get_token(self) -> str:
        """
        Searchs for `user_id` value in all token keys on Redis.
        """
        entries = cache.keys(f'{AuthConfig.CACHE_PREFIX_TOKEN}*')
        for entry in entries:
            if int(cache.get(entry)) == self.user_id:
                return entry.split(':')[-1:][0]

    def refresh_token(self):
        """
        Set a expiration time for the token on Redis.
        """
        cache.expire(self.token_cache_key, AuthConfig.CACHE_TTL_TOKEN)

    def add_session(self):
        """
        Increment the sessions counter key on Redis.
        """
        cache.incr(self.sessions_cache_key)

    def remove_session(self):
        """
        Decrement the sessions counter key on Redis.
        """
        cache.decr(self.sessions_cache_key)

    def expire_session(self, seconds: int = AuthConfig.CACHE_TTL_SESSIONS):
        """
        Set a expiration time for the sessions counter on Redis.
        """
        cache.expire(self.sessions_cache_key, seconds)

    def persist_session(self):
        """
        Remove any expiration time from the sessions counter on Redis.
        """
        cache.persist(self.sessions_cache_key)

    @property
    def sessions_ttl(self):
        """
        Retrieve the TTL (time to live) from the sessions counter on Redis.
        """
        return cache.ttl(self.sessions_cache_key)

    @property
    def sessions(self):
        """
        Retrieve how many sessions are left at the sessions counter on Redis.
        """
        count = cache.get(self.sessions_cache_key)
        if count is not None:
            return int(count)

        return None

    @staticmethod
    def load(token: str):
        """
        Search for a token key on Redis given a token value.

        :return: Auth model.
        """
        # TODO change to getex() when a new release (4.0) of redis-py comes out
        user_id = cache.get(f'{AuthConfig.CACHE_PREFIX_TOKEN}{token}')
        if user_id:
            auth = Auth(user_id=user_id, token=token)
            auth.refresh_token()
            return auth

        return None
