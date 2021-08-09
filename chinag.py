#!/usr/bin/env python3
import os, sys
import argparse
import requests
import random
import time
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials


SITE1 = 'http://j01.best'
SITE2 = 'https://j04.space'
SITES = [SITE2, SITE1]

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
    'Origin': '{}',
    #'Referer': 'http://j01.best/signin',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def rand():
    return str(random.random())[:18]

def main(args, site):
    now = time.time()
    s = requests.Session()
    HEADERS['Origin'] = HEADERS['Origin'].format(site)

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

    HEADERS['Referer'] = URL_USER1 + '?ran={}'.format(rand())
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

    cred = credentials.Certificate(os.path.expanduser("~/service-account-file.json"))
    default_app = firebase_admin.initialize_app(cred)

    s = random.randint(0, 145)
    print(f'sleep {s}s before running')
    #time.sleep(s)

    db = firestore.client(default_app)
    doc = db.collection('checked').document('DUZA2gGVjdSflSOHKvW1')
    print(doc.get())
    print(doc.get(['checked']))

    #sys.exit(main(args, SITES[args.index]))
