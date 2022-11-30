import os
import sys

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.getenv('SECRET_KEY', 'UNSAFE_SECRET_KEY')

PRODUCTION = 'production'
STAGING = 'staging'
LOCAL = 'local'
TARGETS = [
    PRODUCTION,
    STAGING,
    LOCAL
]

ENVIRONMENT = os.getenv('ENVIRONMENT', LOCAL)
assert ENVIRONMENT in TARGETS
DEBUG = os.getenv('DEBUG', '0') == '1' or ENVIRONMENT == LOCAL
TEST_MODE = sys.argv[1:2] == ['test']

ADMINS = [('Gabriel Gularte', 'ggularte@3c.gg')]
FRONT_END_URL = os.getenv('FRONT_END_URL', 'http://localhost:3000')
HOST_URL = os.getenv('HOST_URL', 'localhost')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', HOST_URL).split(',')
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', FRONT_END_URL).split(',')

SECURE_SSL_REDIRECT = os.getenv('HTTPS', '0') == '1'
SESSION_COOKIE_SECURE = os.getenv('HTTPS', '0') == '1'
CSRF_COOKIE_SECURE = os.getenv('HTTPS', '0') == '1'
SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https' if os.getenv('HTTPS', '0') == '1' else 'http'
)

INSTALLED_APPS = [
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
]

AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'NAME': os.getenv('DATABASE_NAME', 'postgres'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'postgres'),
        'HOST': os.getenv('DATABASE_HOST', 'db'),
        'PORT': os.getenv('DATABASE_PORT', 5432),
    }
}

if not os.getenv('DATABASE_IGNORE_SSL'):
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
                'address': ('logs3.papertrailapp.com', 28882)
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

AWS_LOCATION = os.getenv('AWS_LOCATION')

if AWS_LOCATION:
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
    AWS_S3_OBJECT_PARAMS = {
        'CacheControl': os.getenv('AWS_S3_OBJECT_PARAMS__CACHE_CONTROL', 'max-age=86400'),
        'ACL': os.getenv('AWS_S3_OBJECT_PARAMS__ACL', 'public-read'),
    }
    DEFAULT_FILE_STORAGE = 'core.cdn.MediaRootS3BotoStorage'
    STATICFILES_STORAGE = 'core.cdn.StaticRootS3BotoStorage'

# Email Settings
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.mailtrap.io')
EMAIL_PORT = os.getenv('EMAIL_PORT', 2525)
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', '0') == '1'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'e31ca571bd0f1b')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'a69be0ba200ecf')
DEFAULT_FROM_EMAIL = 'Equipe GTA MM <equipe@3c.gg>'


# Steam Settings
STEAM_API_KEY = os.getenv('STEAM_API_KEY')


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
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_USERNAME = os.getenv('REDIS_USERNAME', 'default')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_APP_DB = os.getenv('REDIS_APP_DB', 0)
REDIS_SSL = os.getenv('REDIS_SSL', '0') == '1'


# Sentry Settings
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=os.getenv('SENTRY_SAMPLE_RATE', 0.1),
        send_default_pii=True
    )


# Channels Settings
CHANNEL_REDIS_DB = 10
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
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [CHANNEL_REDIS_CONN_STR]
        },
    },
}

# Celery Settings
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_REDIS_DB = os.getenv('CELERY_REDIS_DB', 11)
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{CELERY_REDIS_DB}'

# Websocket Application Settings
GROUP_NAME_PREFIX = 'app'
