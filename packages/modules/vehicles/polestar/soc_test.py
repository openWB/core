"""
Test Polestar openWB SOC module
"""
import sys
import logging
import argparse
sys.path.append('../../../')
from modules.vehicles.polestar import api
from modules.common.component_state import CarState


def main():
    parser = argparse.ArgumentParser(description='Polestar SOC test')
    parser.add_argument('username', type=str, help='Usually owners email. Enclose in single quotes')
    parser.add_argument('password', type=str, help='Password. Enclose in single quotes')
    parser.add_argument('vin', type=str, help='Vehicle Identification Number')
    parser.add_argument('-d', '--debug', type=int, choices=[10, 20, 30, 40], default=40,
                        action='store', help='debug level:10=DEBUG,20=INFO,30=WARNING,40=ERROR')
    if len(sys.argv) < 4:
        parser.print_help()
        print('Example:\npython3 soc_test.py \'ps2@gmail.com\' \'myPassword\' LPS123456789')
        return

    try:
        args = parser.parse_args(sys.argv[1:])
    except argparse.ArgumentError:
        parser.print_help()

    logging.basicConfig(stream=sys.stdout, format='%(asctime)s:%(levelname)s:%(message)s', level=args.debug)

    car_state: CarState
    car_state = api.fetch_soc(args.username, args.password, args.vin, vehicle=1)
    print('soc=', car_state.soc, ', range=', car_state.range, 'km, last update:', car_state.soc_timestamp)


main()
