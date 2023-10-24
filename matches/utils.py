import time

import requests
from django.conf import settings


@staticmethod
def send_request(req: requests.Request, endpoint: str, server):
    if settings.ENVIRONMENT == settings.LOCAL or settings.TEST_MODE:
        status_code = 201 if settings.FIVEM_MATCH_MOCK_CREATION_SUCCESS else 400
        fivem_response = {'status_code': status_code}
        time.sleep(settings.FIVEM_MATCH_MOCK_DELAY_CONFIGURE)
    else:
        prepared = req.prepare()
        prepared.url = f'http://{server.ip}:{server.api_port}{endpoint}'
        with requests.Session() as s:
            fivem_response = s.send(prepared)
            return fivem_response
