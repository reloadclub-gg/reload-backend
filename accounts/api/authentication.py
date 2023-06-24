from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

from .controller import handle_login

User = get_user_model()


class VerifiedRequiredAuth(HttpBearer):
    def authenticate(self, request, token: str):
        """
        This is middleware to authenticate users is verified. Is called everytime the client
        makes a new request. All logic goes into the `controller.login` method.

        :params request Request: The request object.
        :return: The login method result (Auth model or None).
        """
        return handle_login(request, token)


class VerifiedExemptAuth(HttpBearer):
    """
    This is middleware to authenticate users isn't verified. Is called everytime the client
    makes a new request. All logic goes into the `controller.login` method.

    :params request Request: The request object.
    :return: The login method result (Auth model or None).
    """

    def authenticate(self, request, token: str):
        request.verified_exempt = True

        return handle_login(request, token)
