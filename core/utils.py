import logging
import random
import string
from datetime import datetime
from typing import Union
from urllib import parse

import redis
from django.conf import settings
from django.core import mail
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def generate_random_string(length: int = 6, allowed_chars: str = 'all') -> str:
    """
    Gen a random string based on length and allowed_chars (all, letters or digits).
    """
    if allowed_chars == 'letters':
        chars = string.ascii_letters
    elif allowed_chars == 'digits':
        chars = string.digits
    else:
        chars = string.ascii_letters + string.digits

    return ''.join(random.choice(chars) for _ in range(length))


def redis_client():
    """
    Open a connection with the Redis cache database.

    :return: A connected ready to use Redis client.
    """
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_APP_DB,
        charset='utf-8',
        decode_responses=True,
    )


def get_ip_address(request) -> str:
    """
    Find the IP address of the request and return it.

    :params request Request: The request object.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_url_param(url: Union[str, bytes], param: str) -> str:
    """
    Find the param in a url querystring.
    The qs can be a generic url (http://www.url.com/?param=value) or
    a `param=value` bytes type (b'param=value').
    """
    if isinstance(url, bytes):
        url = url.decode('utf-8')

    parsed_url = parse.urlparse(url)
    # check if url is querystring already
    if not parsed_url.query:
        values = parse.parse_qs(url).get(param, [])
        if values:
            return values[0]

    return parse.parse_qs(parsed_url.query)[param][0]


def str_to_timezone(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")


def send_mail(mail_to: str, subject: str, content: str):
    mail.send_mail(
        subject,
        strip_tags(content),
        settings.DEFAULT_FROM_EMAIL,
        mail_to,
        html_message=content,
    )


def get_full_file_path(file):
    if hasattr(settings, 'AWS_LOCATION'):
        return file.url

    return settings.SITE_URL + file.url
