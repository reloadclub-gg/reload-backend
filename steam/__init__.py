import requests
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class SteamClient:
    """
    This class should contain all methods that fetch external data from Steam.
    """

    PLAYER_API_URL = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
    FRIENDS_API_URL = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?relationship=friend'

    @staticmethod
    def get_player_data(steamid: str) -> dict:
        """
        Fetch user data from SteamAPI given a user steamid.
        """
        base_url = SteamClient.PLAYER_API_URL
        api_key = settings.STEAM_API_KEY
        url = f'{base_url}?key={api_key}&steamids={steamid}'
        r = requests.get(url)
        return r.json().get('response').get('players')[0]


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
