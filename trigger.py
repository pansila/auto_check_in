import os, sys
import hashlib
import pytz
import argparse
import binascii
import random
import json
from datetime import datetime

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--updatedb')
    args = parser.parse_args()

    sha256 = hashlib.sha256()
    sha256.update(args.username.encode())
    username_hash = binascii.hexlify(sha256.digest()).decode()

    config = load_config(args, username_hash)
    today = datetime.today() # UTC time
    today = today.astimezone(pytz.timezone('Asia/Shanghai'))
    ret = 0

    if not args.updatedb:
        # reset the mark in the first time running of the day
        if today.hour == RUN_TIME_RANGE_START:
            config[username_hash]['checked'] = False
        elif today.hour > RUN_TIME_RANGE_END or today.hour < RUN_TIME_RANGE_START:
            print(f'Error: mismatched scheduling, now is hour {today.hour}, expected to between {RUN_TIME_RANGE_START} and {RUN_TIME_RANGE_END}')
            ret = 1
            break
        elif config[username_hash]['checked']:
            print(f'user {username_hash} has checked in today')
            break

        rnd = random.randint(today.hour, RUN_TIME_RANGE_END)
        if rnd == RUN_TIME_RANGE_END:
            print(f'Starting to work on {today.isoformat(" ")}')
        else:
            print(f'Skip the running, {rnd} in [{today.hour}, {RUN_TIME_RANGE_END}]')
            break
    else:
        config[username_hash]['checked'] = True
        config[username_hash]['last_time_checked'] = today.isoformat(' ')

    with open(CONFIG_DB, 'w') as f:
        f.write(json.dumps(config, indent=4))

    sys.exit(ret)
