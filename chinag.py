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
import pytz
from datetime import datetime


SITE1 = 'http://j01.best'
SITE2 = 'https://j04.space'
SITES = [SITE2, SITE1]

# sensible human living daytime
RUN_TIME_RANGE_START = 8
RUN_TIME_RANGE_END = 23

CONFIG_DB = 'db.json'
# {
#   'username1': {
#       'checked': False,
#       'last_time_checked': '2020-02-20 20:20:20'
#   },
#   ...
# }

URL_HOME    = '{}'
URL_LOGIN   = '{}/auth/register'
URL_USER1   = '{}/user'
URL_SIGNIN  = '{}/signin?c={}' # http://j01.best/signin?c=0.8043126313168425
URL_CHECKIN = '{}/user/checkin?c={}' # http://j01.best/user/checkin?c=0.01422644502656678
URL_USER2   = '{}/xiaoma/get_user?c={}' # http://j01.best/xiaoma/get_user?c=0.2444034705646254

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    #'Content-Type': 'application/json;charset=UTF-8',
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
    url_home    = URL_HOME.format(site)
    url_login   = URL_LOGIN.format(site)
    url_user1   = URL_USER1.format(site)
    url_signin  = URL_SIGNIN.format(site, rand())
    url_checkin = URL_CHECKIN.format(site, rand())
    url_user2   = URL_USER2.format(site, rand())

    r = s.get(url_home, headers=HEADERS)
    if r.status_code != 200:
        print(f'Error: {url_home}')
        return 1

    HEADERS['Origin'] = site
    r = s.get(url_login, headers=HEADERS)
    if r.status_code != 200:
        print(f'Error: {url_login}')
        return 1

    HEADERS['Referer'] = f'{site}/signin'
    HEADERS['Content-Type'] = 'application/json;charset=UTF-8'
    r = s.post(url_signin,
               json={
                   'email': args.username,
                   'passwd': args.password
               },
               headers=HEADERS)
    if r.status_code != 200:
        print(f'Error: {url_signin}')
        return 1

    del HEADERS['Content-Type']
    r = s.get(url_user1, headers=HEADERS)
    if r.status_code != 200:
        print(f'Error: {url_user1}')
        return 1

    HEADERS['Referer'] = f'{url_user1}?ran={rand()}')
    r = s.post(url_checkin, headers=HEADERS)
    if r.status_code != 200:
        print(f'Error: {url_checkin}')
        return 1

    r = s.get(url_user2, headers=HEADERS)
    if r.status_code != 200:
        print(f'Error: {url_user2}')
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
    today = datetime.today() # UTC time
    today = today.astimezone(pytz.timezone('Asia/Shanghai'))
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
            print(f'user {username_hash} has checked in today')
            break

        rnd = random.randint(today.hour, RUN_TIME_RANGE_END)
        if rnd == RUN_TIME_RANGE_END:
            print(f'Starting to work on {today.isoformat(" ")}')
        else:
            print(f'Skip the running, {rnd} in [{today.hour}, {RUN_TIME_RANGE_END}]')
            break
    else:
        s = random.randint(0, 145)
        print(f'sleep {s}s before running')
        time.sleep(s)

        ret = main(args, SITES[args.index])
        if ret == 0:
            config[username_hash]['checked'] = True
            config[username_hash]['last_time_checked'] = today.isoformat(' ')

    with open(CONFIG_DB, 'w') as f:
        f.write(json.dumps(config, indent=4))

    sys.exit(ret)
