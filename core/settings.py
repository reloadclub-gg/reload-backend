import os
import sys

import sentry_sdk
from decouple import config
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
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=HOST_URL).split(',')
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default=FRONT_END_URL).split(',')

HTTPS = config('HTTPS', default=False, cast=bool)
SECURE_SSL_REDIRECT = HTTPS
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SECURE = HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https' if HTTPS else 'http')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_extensions',
    'social_django',
    'ninja',
    'corsheaders',
    'channels',
    'storages',
    'accounts.apps.AccountsConfig',
    'matchmaking.apps.MatchmakingConfig',
    'appsettings.apps.AppSettingsConfig',
]

if ENVIRONMENT == LOCAL:
    INSTALLED_APPS += [
        'rosetta',
    ]

AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
        'NAME': config('DATABASE_NAME', default='postgres'),
        'USER': config('DATABASE_USER', default='postgres'),
        'PASSWORD': config('DATABASE_PASSWORD', default='postgres'),
        'HOST': config('DATABASE_HOST', default='db'),
        'PORT': config('DATABASE_PORT', default=5432, cast=int),
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
if ENVIRONMENT != LOCAL:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'SysLog': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'formatter': 'simple',
                'address': (
                    config('PAPERTRAIL_ADDRESS'),
                    config('PAPERTRAIL_PORT', cast=int),
                ),
            },
        },
        'formatters': {
            'simple': {
                'format': f'%(asctime)s {HOST_URL} {ENVIRONMENT}: %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['SysLog'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AWS_LOCATION = config('AWS_LOCATION', default=None)

if AWS_LOCATION:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')
    AWS_S3_OBJECT_PARAMS = {
        'CacheControl': config(
            'AWS_S3_OBJECT_PARAMS__CACHE_CONTROL', default='max-age=86400'
        ),
        'ACL': config('AWS_S3_OBJECT_PARAMS__ACL', default='public-read'),
    }
    DEFAULT_FILE_STORAGE = 'core.cdn.MediaRootS3BotoStorage'
    STATICFILES_STORAGE = 'core.cdn.StaticRootS3BotoStorage'

# Email Settings
EMAIL_HOST = config('EMAIL_HOST', default='smtp.mailtrap.io')
EMAIL_PORT = config('EMAIL_PORT', default=2525, cast=int)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='e31ca571bd0f1b')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='a69be0ba200ecf')
DEFAULT_FROM_EMAIL = 'Equipe GTA MM <equipe@3c.gg>'


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
FRONT_END_AUTH_URL = FRONT_END_URL + '/auth/?token={}'
FRONT_END_INACTIVE_URL = FRONT_END_URL + '/conta-inativa/'
FRONT_END_VERIFY_URL = FRONT_END_URL + '/verificar/'

# Cache Settings
REDIS_HOST = config('REDIS_HOST', default='redis')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_USERNAME = config('REDIS_USERNAME', default='default')
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_APP_DB = config('REDIS_APP_DB', default=0, cast=int)
REDIS_SSL = config('REDIS_SSL', default=False, cast=bool)


# Sentry Settings
if config('SENTRY_DSN', default=None):
    sentry_sdk.init(
        dsn=config('SENTRY_DSN', default=''),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=config('SENTRY_SAMPLE_RATE', default=1.0),
        send_default_pii=True,
        environment=ENVIRONMENT,
        attach_stacktrace=True,
        debug=DEBUG,
    )


# Channels Settings
CHANNEL_REDIS_DB = config('CHANNEL_REDIS_DB', default=10, cast=int)
CHANNEL_REDIS_CONN_PROTOCOL = 'rediss' if REDIS_SSL else 'redis'
CHANNEL_REDIS_CONN_STR = '{}://{}:{}@{}:{}/{}'.format(
    CHANNEL_REDIS_CONN_PROTOCOL,
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
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{CELERY_REDIS_DB}'

# Websocket Application Settings
GROUP_NAME_PREFIX = 'app'

JAZZMIN_SETTINGS = {
    "site_title": "Reload Admin",
    "site_header": "Reload",
    "site_brand": "Reload",
    "login_logo": None,
    "welcome_sign": "Welcome to the Reload Admin",
    "copyright": "3C.gg",
    "show_sidebar": True,
    "order_with_respect_to": ["auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
}
