import requests
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class SteamClient:
    """
    This class should contain all methods that fetch external data from Steam.
    """

    PLAYER_API_URL = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002'
    FRIENDS_API_URL = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?relationship=friend'

    @staticmethod
    def get_friends(steamid: str) -> list:
        """
        Fetch the friendlist from SteamAPI given a user steamid.
        Returns empty if `TEST_MODE` is on or if user doesn't have any friends on Steam.
        """
        if settings.TEST_MODE:
            return []
        base_url = SteamClient.FRIENDS_API_URL
        api_key = settings.STEAM_API_KEY
        url = f'{base_url}&key={api_key}&steamid={steamid}'
        r = requests.get(url)
        return r.json().get('friendslist', {}).get('friends', [])


class Steam:
    """
    This should contain all code related to any Steam proccess.
    """

    AVATARS_URL = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars'
    DEFAULT_AVATAR_URI = f'{AVATARS_URL}/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb'

    @staticmethod
    def build_avatar_url(hash: str = None, size: str = None) -> str:
        """
        Return a valid Steam URL of an avatar (profile picture) given a hash and size.
        """
        if not hash:
            sufix = f'_{size}.jpg' if size else '.jpg'
            return f'{Steam.DEFAULT_AVATAR_URI}{sufix}'

        prefix = Steam.AVATARS_URL
        path = hash[:2]
        sufix = f'_{size}.jpg' if size else '.jpg'
        return f'{prefix}/{path}/{hash}{sufix}'

    @staticmethod
    def get_player_friends(steam_user) -> list:
        """
        Returns a friendlist given a steam_user.
        The `communityvisibilitystate` is the profile visibility of a user on Steam.
        If this value is other then 3, then that user friendlist is private and we can't
        fetch it, so we return an empty list.

        :params steam_user SteamUser: SteamUser model from accounts.models.user
        """
        # If testing or debugging, everyone is friend of everyone
        if settings.TEST_MODE or settings.DEBUG:
            return [
                {'steamid': user.steam_user.steamid}
                for user in User.objects.filter(is_staff=False)
                if hasattr(user, 'account') and user.account.is_verified
            ]

        # communityvisibilitystate = profile visibility on Steam
        # private profiles (!=3) doesn't return friendlist
        if steam_user.communityvisibilitystate == 3:
            return SteamClient.get_friends(steam_user.steamid)

        return []
