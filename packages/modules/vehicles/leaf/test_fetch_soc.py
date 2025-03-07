#!/usr/bin/env python3

import sys
import logging

from api_wo_CarState import fetch_soc

logging.basicConfig(stream=sys.stdout, level=5, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') #

username    = 'xyz@ab.de'       #replace by your user ID
password    = 'secretPassword'  #replace by your password
chargepoint = 1

print("SoC: " + str(fetch_soc(username, password, chargepoint)))

