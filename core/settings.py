import os
import sys

import sentry_sdk
from decouple import config
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = config('SECRET_KEY', default='UNSAFE_SECRET_KEY')

PRODUCTION = 'production'
STAGING = 'staging'
LOCAL = 'local'
TARGETS = [PRODUCTION, STAGING, LOCAL]

ENVIRONMENT = config('ENVIRONMENT', default=LOCAL)
assert ENVIRONMENT in TARGETS
DEBUG = config('DEBUG', default=False, cast=bool) or ENVIRONMENT == LOCAL
TEST_MODE = sys.argv[1:2] == ['test']

ADMINS = [('Gabriel Gularte', 'ggularte@3c.gg')]
FRONT_END_URL = config('FRONT_END_URL', default='http://localhost:3000')
HOST_URL = config('HOST_URL', default='localhost')
ALLOWED_HOSTS_DEFAULTS = 'localhost,api,ws,nginx,locust_master'
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=ALLOWED_HOSTS_DEFAULTS).split(',')
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default=FRONT_END_URL).split(',')

HTTPS = config('HTTPS', default=False, cast=bool)
SECURE_SSL_REDIRECT = HTTPS
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SECURE = HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https' if HTTPS else 'http')

SITE_URL_PREFIX = 'https://' if HTTPS else 'http://'
SITE_URL_PORT = config('HOST_PORT', default=8000 if ENVIRONMENT == LOCAL else None)
SITE_URL_SUFFIX = f':{SITE_URL_PORT}' if SITE_URL_PORT else ''
SITE_URL = SITE_URL_PREFIX + HOST_URL + SITE_URL_SUFFIX
DOCKER_SITE_URL = SITE_URL_PREFIX + 'api' + SITE_URL_SUFFIX

CSRF_TRUSTED_ORIGINS = [SITE_URL, FRONT_END_URL]

SILK_ENABLED = config('SILK_ENABLED', default=False, cast=bool)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'social_django',
    'ninja',
    'corsheaders',
    'channels',
    'storages',
    'django_object_actions',
    'accounts.apps.AccountsConfig',
    'pre_matches.apps.PreMatchesConfig',
    'appsettings.apps.AppSettingsConfig',
    'matches.apps.MatchesConfig',
    'notifications.apps.NotificationsConfig',
    'websocket.apps.WebsocketConfig',
    'lobbies.apps.LobbiesConfig',
    'store.apps.StoreConfig',
    'friends.apps.FriendsConfig',
]

if ENVIRONMENT == LOCAL:
    INSTALLED_APPS += [
        'rosetta',
    ]

if SILK_ENABLED:
    INSTALLED_APPS += [
        'silk',
    ]

AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MIDDLEWARE = [
    'core.middleware.HealthCheckMiddleware',
    'core.middleware.PortMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if SILK_ENABLED:
    MIDDLEWARE += [
        'silk.middleware.SilkyMiddleware',
    ]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME', default='test_db' if TEST_MODE else 'postgres'),
        'USER': config('DATABASE_USER', default='postgres'),
        'PASSWORD': config('DATABASE_PASSWORD', default='postgres'),
        'HOST': config('DATABASE_HOST', default='db'),
        'PORT': config('DATABASE_PORT', default=5432, cast=int),
        'CONN_MAX_AGE': config('DATABASE_CONN_MAX_AGE', default=0, cast=int),
    }
}
if config('DATABASE_SSL', default=False, cast=bool):
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)


# Logging Settings
AVAILABLE_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
LOG_LEVEL = config('LOG_LEVEL', default='WARNING').upper()
assert LOG_LEVEL in AVAILABLE_LOG_LEVELS
LOGGING = {
    'version': 1,
    'disable_existing_loggers': TEST_MODE,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'core', 'static')]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', None)
if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', 'sa-east-1')
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_LOCATION = config('AWS_LOCATION')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN')
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': config(
            'AWS_S3_OBJECT_PARAMETERS__CACHE_CONTROL', default='max-age=86400'
        ),
        'ACL': config('AWS_S3_OBJECT_PARAMETERS__ACL', default='public-read'),
    }
    STATICFILES_STORAGE = 'core.cdn.StaticRootS3BotoStorage'
    DEFAULT_FILE_STORAGE = 'core.cdn.MediaRootS3BotoStorage'


# Email Settings
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
if EMAIL_HOST == 'localhost':
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'Equipe Reload Club <equipe@reloadclub.gg>'
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='suporte@reloadclub.freshdesk.com')


# Steam Settings
STEAM_API_KEY = config('STEAM_API_KEY', default=None)


# Auth Settings
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_STEAM_API_KEY = STEAM_API_KEY
SOCIAL_AUTH_STEAM_EXTRA_DATA = ['player']
AUTHENTICATION_BACKENDS = (
    'social_core.backends.steam.SteamOpenId',
    'django.contrib.auth.backends.ModelBackend',
)
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/accounts/auth/finish/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/accounts/auth/finish/'
SOCIAL_AUTH_URL_NAMESPACE = 'accounts:auth'
SOCIAL_AUTH_ALLOW_INACTIVE_USERS_LOGIN = True
FRONT_END_AUTH_URL = FRONT_END_URL + '/api/auth/?token={}'
LOGIN_URL = reverse_lazy('admin:login')


# Cache Settings
REDIS_HOST = config('REDIS_HOST', default='redis')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_USERNAME = config('REDIS_USERNAME', default='default')
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_APP_DB = config('REDIS_APP_DB', default=0, cast=int)
REDIS_TEST_DB = config('REDIS_APP_DB', default=2, cast=int)
REDIS_SSL = config('REDIS_SSL', default=False, cast=bool)
REDIS_CONN_PROTOCOL = 'rediss' if REDIS_SSL else 'redis'


# Sentry Settings
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
        send_default_pii=True,
        environment=ENVIRONMENT,
        attach_stacktrace=True,
        sample_rate=0.25,
    )


# Channels Settings
CHANNEL_REDIS_DB = config('CHANNEL_REDIS_DB', default=10, cast=int)
CHANNEL_REDIS_CONN_STR = '{}://{}:{}@{}:{}/{}'.format(
    REDIS_CONN_PROTOCOL,
    REDIS_USERNAME,
    REDIS_PASSWORD,
    REDIS_HOST,
    REDIS_PORT,
    CHANNEL_REDIS_DB,
)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.pubsub.RedisPubSubChannelLayer',
        'CONFIG': {'hosts': [CHANNEL_REDIS_CONN_STR]},
    },
}


# Celery Settings
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_REDIS_DB = config('CELERY_REDIS_DB', default=11, cast=int)
CELERY_BROKER_URL = '{}://{}:{}@{}:{}/{}'.format(
    REDIS_CONN_PROTOCOL,
    REDIS_USERNAME,
    REDIS_PASSWORD,
    REDIS_HOST,
    REDIS_PORT,
    CELERY_REDIS_DB,
)
CELERY_RESULT_BACKEND = None
CELERY_IGNORE_RESULT = True


# Websocket Application Settings
GROUP_NAME_PREFIX = 'app'


# Team & Match Settings
TEAM_READY_PLAYERS_MIN = (
    5 if TEST_MODE else config('TEAM_READY_PLAYERS_MIN', default=5, cast=int)
)
MATCH_READY_COUNTDOWN = (
    30 if TEST_MODE else config('MATCH_READY_COUNTDOWN', default=30, cast=int)
)
MATCH_READY_COUNTDOWN_GAP = config('MATCH_READY_COUNTDOWN_GAP', default=-4, cast=int)
MATCHES_LIMIT_PER_SERVER = config('MATCHES_LIMIT_PER_SERVER', default=20, cast=int)
MATCHES_LIMIT_PER_SERVER_GAP = config(
    'MATCHES_LIMIT_PER_SERVER_GAP',
    default=5,
    cast=int,
)


# Player Dodges & Restriction Settings
MATCH_ROUNDS_TO_WIN = config('MATCH_ROUNDS_TO_WIN', default=13, cast=int)
PLAYER_DODGES_EXPIRE_TIME = config(
    'PLAYER_DODGES_EXPIRE_TIME',
    default=60 * 60 * 24 * 7,  # 1 semana (7 dias)
    cast=int,
)
PLAYER_DODGES_MULTIPLIER = config(
    'PLAYER_DODGES_MULTIPLIER',
    default='1,2,5,10,20,40,60,90',
    cast=lambda v: [float(s.strip()) for s in v.split(',')],
)
PLAYER_MAX_DODGES = len(PLAYER_DODGES_MULTIPLIER)
PLAYER_DODGES_MIN_TO_RESTRICT = config(
    'PLAYER_DODGES_MIN_TO_RESTRICT',
    default=3,
    cast=int,
)
PLAYER_MAX_LOSE_LEVEL_POINTS = config(
    'PLAYER_MAX_LOSE_LEVEL_POINTS',
    default=-99,
    cast=int,
)


# Other App Settings
APP_INVITE_REQUIRED = config('APP_INVITE_REQUIRED', default=False, cast=bool)
APP_GLOBAL_FRIENDSHIP = config('APP_GLOBAL_FRIENDSHIP', default=False, cast=bool)
PLAYER_MAX_LEVEL = config('PLAYER_MAX_LEVEL', default=30, cast=int)
PLAYER_MAX_LEVEL_POINTS = config('PLAYER_MAX_LEVEL_POINTS', default=100, cast=int)
MAX_NOTIFICATION_HISTORY_COUNT_PER_PLAYER = config(
    'MAX_NOTIFICATION_HISTORY_COUNT_PER_PLAYER',
    default=10,
    cast=int,
)
RANKING_LIMIT = config('RANKING_LIMIT', default=100, cast=int)


# Ninja Settings
PAGINATION_PER_PAGE = 10


# FiveM Settings
FIVEM_MATCH_MOCKS_ON = config('FIVEM_MATCH_MOCKS_ON', default=False, cast=bool)
FIVEM_MATCH_MOCK_CREATION_SUCCESS = config(
    'FIVEM_MATCH_MOCK_CREATION_SUCCESS',
    default=True,
    cast=bool,
)
FIVEM_MATCH_MOCK_DELAY_START = config(
    'FIVEM_MATCH_MOCK_DELAY_START',
    default=10,
    cast=int,
)
FIVEM_MATCH_MOCK_DELAY_CONFIGURE = config(
    'FIVEM_MATCH_MOCK_DELAY_CONFIGURE',
    default=5,
    cast=int,
)
FIVEM_MATCH_MOCK_START_SUCCESS = config(
    'FIVEM_MATCH_MOCK_START_SUCCESS',
    default=True,
    cast=bool,
)
FIVEM_MATCH_CREATION_MAX_RETRIES = config(
    'FIVEM_MATCH_CREATION_MAX_RETRIES',
    default=3,
    cast=int,
)
FIVEM_MATCH_CREATION_RETRIES_INTERVAL = config(
    'FIVEM_MATCH_CREATION_RETRIES_INTERVAL',
    default=3,
    cast=int,
)
FIVEM_MATCH_CREATION_RETRIES_TIMEOUT = config(
    'FIVEM_MATCH_CREATION_RETRIES_TIMEOUT',
    default=3,
    cast=int,
)


# Store Settings
STORE_LENGTH = 8
STORE_FEATURED_MAX_LENGTH = 3
STORE_ROTATION_DAYS = 7
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default=None)
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default=None)
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default=None)
