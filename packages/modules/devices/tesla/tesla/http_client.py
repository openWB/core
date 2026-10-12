import requests


class PowerwallHttpClient:
    def __init__(self, host: str, session: requests.Session, cookies):
        self.__base_url = "https://" + host
        self.cookies = cookies
        self.__session = session

    def get_json(self, relative_url: str):
        response = self.__session.get(
            self.__base_url + relative_url,
            cookies=self.cookies,
            verify=False,
            timeout=5,
        )
        return response.json()
