#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import random
import time
import json
import hashlib
import binascii
from datetime import datetime


SITE1 = 'http://j01.best'
SITE2 = 'https://j04.space'
SITES = [SITE2, SITE1]

# should be same as the cron schedule time in the workflow
RUN_TIME_RANGE_START = 0
RUN_TIME_RANGE_END = 15

CONFIG_DB = 'db.json'
# {
#   'username1': {
#       'checked': False,
#       'last_time_checked': '2020-02-20 20:20:20'
#   },
#   ...
# }

URL_HOME   = '{}'
URL_LOGIN   = '{}/auth/register'
URL_USER1   = '{}/user'
URL_SIGNIN  = '{}/signin?c={}' # http://j01.best/signin?c=0.8043126313168425
URL_CHECKIN = '{}/user/checkin?c={}' # http://j01.best/user/checkin?c=0.01422644502656678
URL_USER2   = '{}/xiaoma/get_user?c={}' # http://j01.best/xiaoma/get_user?c=0.2444034705646254

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Content-Type': 'application/json;charset=UTF-8',
    #'Origin': 'http://j01.best',
    #'Referer': 'http://j01.best/signin',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def rand():
    return str(random.random())[:18]

def main(args, site):
    now = time.time()
    s = requests.Session()

    r = s.get(URL_HOME.format(site), headers=HEADERS)
    if r.status_code != 200:
        print('Error: login: error')
        return 1

    HEADERS['Origin'] = site
    r = s.get(URL_LOGIN.format(site), headers=HEADERS)
    if r.status_code != 200:
        print('Error: login: error')
        return 1

    HEADERS['Referer'] = HEADERS['Origin'] + '/signin'
    r = s.post(URL_SIGNIN.format(site, rand()),
                      json={
                          'email': args.username,
                          'passwd': args.password
                      },
                      headers=HEADERS)
    if r.status_code != 200:
        print('Error: signin: error')
        return 1

    r = s.get(URL_USER1.format(site), headers=HEADERS)
    if r.status_code != 200:
        print('Error: user1: error')
        return 1

    HEADERS['Referer'] = URL_USER1.format(site) + '?ran={}'.format(rand())
    r = s.post(URL_CHECKIN.format(site, rand()), headers=HEADERS)
    if r.status_code != 200:
        print('Error: checkin: error')
        return 1

    r = s.get(URL_USER2.format(site, rand()), headers=HEADERS)
    if r.status_code != 200:
        print('Error: user2: error')
        return 1

    print(f'time used: {time.time() -  now}')
    return 0

def load_config(args, username_hash):
    config = {
        username_hash: {
            'checked': False,
        }
    }
    while True:
        if not os.path.exists(CONFIG_DB):
            break
        with open(CONFIG_DB) as f:
            data = f.read()
            if not data.strip():
                break
            config = json.loads(data)
        break

    if username_hash not in config:
        config[username_hash] = {
            'checked': False
        }

    return config

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('password')
    parser.add_argument('-i', '--index', default=0, help='site index in: {}'.format(SITES))
    args = parser.parse_args()
    if args.index is None:
        args.index = 0
    if int(args.index) > len(SITES):
        print('Error: invalid option, index is out of range')
        sys.exit(1)

    sha256 = hashlib.sha256()
    sha256.update(args.username.encode())
    username_hash = binascii.hexlify(sha256.digest()).decode()

    config = load_config(args, username_hash)
    today = datetime.today()
    ret = 0

    for i in range(1):
        # reset the mark in the first time running of the day
        if today.hour == RUN_TIME_RANGE_START:
            config[username_hash]['checked'] = False
        elif today.hour > RUN_TIME_RANGE_END or today.hour < RUN_TIME_RANGE_START:
            print(f'Error: mismatched scheduling, now is hour {today.hour}, expected to between {RUN_TIME_RANGE_START} and {RUN_TIME_RANGE_END}')
            ret = 1
            break
        elif config[username_hash]['checked']:
            print(f'{username_hash} Has been checked today')
            break

        rnd = random.randint(today.hour, RUN_TIME_RANGE_END)
        if rnd == RUN_TIME_RANGE_END:
            config[username_hash]['checked'] = True
            config[username_hash]['last_time_checked'] = today.isoformat()
        else:
            print(f'Skip the running, {rnd} in [{today.hour}, {RUN_TIME_RANGE_END}]')
            break
    else:
        s = random.randint(0, 145)
        print(f'sleep {s}s before running')
        time.sleep(s)

        ret = main(args, SITES[args.index])

    with open(CONFIG_DB, 'w') as f:
        f.write(json.dumps(config, indent=4))

    sys.exit(ret)
