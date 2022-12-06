#!/usr/bin/env python3

from typing import Union
import logging
import datetime
import jwt
from helpermodules.pub import Pub

initialToken = '1.2.3'

log = logging.getLogger("soc."+__name__)


class socUtils:

    def __init__(self):
        pass

    def read_token_file(self, path: str) -> str:
        try:
            self.tf = open(path, "r")           # try to open Token file
            token = self.tf.read()              # read token
            self.tf.close()
        except Exception:
            token = None                # if no old token found set Token_old to dummy value
        return token

    def write_token_file(self, path: str, token: str, config={}):
        try:
            log.debug("store Token in file " + path)
            self.tf = open(path, "w")
            self.tf.write(token)         # write Token file
            self.tf.close()
        except Exception as e:
            log.debug('Token file write exception ' + str(e))

    def write_token_mqtt(self, topic: str, token: str, config={}):
        try:
            config['configuration']['refreshToken'] = token
            # log.debug("write_token.mqtt: " + json.dumps(config, ensure_ascii=False, indent=4))
            Pub().pub(topic, config)
        except Exception as e:
            log.debug('Token mqtt write exception ' + str(e))

    def get_token_expiration(self, token: str, fmt: str) -> Union[int, str]:
        try:
            self.token_dec = jwt.decode(token, 'utf-8', options={"verify_signature": False})
            self.exp = self.token_dec['exp']
            self.exp_dt = datetime.datetime.fromtimestamp(self.exp).strftime(fmt)
        except Exception as e:
            log.debug('get_token_expiration error ' + str(e))
            self.exp = None
            self.exp_dt = None

        return self.exp, self.exp_dt
