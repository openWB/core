from typing import Optional


class MercedesEQSocToken:
    def __init__(self,
                 refresh_token: str = "",
                 access_token: str = "",
                 expires_in: int = 0,
                 id_token: str = "",
                 token_type: str = "") -> None:
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.expires_in = expires_in
        self.id_token = id_token
        self.token_type = token_type


class MercedesEQSocConfiguration:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, vin: Optional[str] = None,
                 token: MercedesEQSocToken = None) -> None:
        self.client_id = client_id          # show in UI
        self.client_secret = client_secret  # show in UI
        self.vin = vin                      # show in UI
        self.token = token or MercedesEQSocToken()
        # Login Link must be built in UI like this example
        # openWB ID of the current vehicle --> VEHICLEID
        # client_id of this configuration --> CLIENT_ID
        # callback_url of this configuration --> CALLBACK_URL
        #     (http://<IPorHOST>/openWB/packages/modules/vehicles/mercedeseq/callback_ev.php)
        # https://ssoalpha.dvb.corpinter.net/v1/auth?response_type=code&state=<VEHICLEID>&client_id=<CLIENT_ID>
        #                 &redirect_uri=<CALLBAC_URL>&scope=mb:vehicle:mbdata:evstatus%20offline_access%20openid


class MercedesEQSoc:
    def __init__(self,
                 name: str = "MercedesEQ",
                 type: str = "mercedeseq",
                 configuration: MercedesEQSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or MercedesEQSocConfiguration()
