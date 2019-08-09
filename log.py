from datetime import datetime
import webbrowser
import urllib
import json
import os
import os.path
import csv
import time

import requests
import redis

from auth import client_secret, client_id, redirect_uri, redis_host, redis_port

auth_url = 'https://accounts.spotify.com/authorize/?'
token_url = 'https://accounts.spotify.com/api/token/?'


def refresh_token():
    """Attempt to refresh a token using refresh_token.json."""
    # check for token.json
    if not(os.path.isfile(os.getcwd() + '/token.json')):
        authorize_token()
    else:
        with open('refresh_token.json', 'r') as token:
            rf_token = json.load(token)

        grant_type = 'refresh_token'

        post_payload = {'refresh_token': rf_token['refresh_token'],
                        'grant_type': grant_type}

        response = requests.post(token_url,
                                 data=post_payload,
                                 auth=(client_id, client_secret),
                                 timeout=20)

        with open('token.json', 'w') as write_token:
            write_token.write(response.text)

        print('Token Refreshed')


def authorize_token():
    """Authorize a token for the first time."""
    scope = 'streaming user-read-playback-state user-read-recently-played'

    payload = {'client_id': client_id,
               'response_type': 'code',
               'redirect_uri': redirect_uri,
               'scope': scope,
               'show_dialog': False}

    if not(os.path.isfile(os.getcwd() + '/token.json')):
        webbrowser.open(auth_url + urllib.parse.urlencode(payload))

        encoded_url = input('URL that was redirected: ')
        code = encoded_url[encoded_url.index('?code=') + 6:]
        grant_type = 'authorization_code'

        post_payload = {'code': code,
                        'grant_type': grant_type,
                        'redirect_uri': redirect_uri}

        response = requests.post(token_url,
                                 data=post_payload,
                                 auth=(client_id, client_secret),
                                 timeout=60)

        with open('token.json', 'w') as write_token:
            write_token.write(response.text)

        refresh = {'refresh_token': response.json()['refresh_token']}
        print(refresh)
        with open('refresh_token.json', 'w') as write_refresh:
            json.dump(refresh, write_refresh)
    print('Authorize Token successfull')


# TODO: replace with datetime parsing
def pretty_print_ms(ms):
    """Print milliseconds in a human-readable way."""
    s = str(int((ms / 1000) % 60))
    if len(s) == 1:
        s = '0' + s
    m = str(int((ms / (1000 * 60)) % 60))
    return '{}:{}'.format(m, s)


def current_playing(token):
    """Return and print the currently playing track.
    Parameters
    ----------
    token: string
        Authorization token to send a request.
    Returns
    -------
    r: json or None
        Returns JSON from GET request or None if error
    """
    playback_url = 'https://api.spotify.com/v1/me/player'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    r = None
    try:
        r = requests.get(playback_url, headers=headers, timeout=60)
    except requests.exceptions.ConnectionError:
        print('Network connection error')
        pass
    if r:
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:  # need to refresh
            print('[401] - Refreshing token')
            refresh_token()
            return None
        elif r.status_code == 204:
            print('[204] - No track playing or private session')
            return None
        else:
            print('[{}] - Error'.format(r.status_code))
            print(r.text)
            return None
    else:
        print('Network connection error')
        refresh_token()
        time.sleep(10)


def dict_get(d, path):
    """Return attribute in dict given a path.
    Parameters
    ----------
    d: dict
        dict to be traversed.
    path: list
        list of keys to traverese in the dict.
    Returns
    -------
    d: value or None
        value in key/value pair if found or None if not found.
    """
    for item in path:
        d = d.get(item)
        if d is None:
            print('{} ::: {} is considered None'.format(path, d))
            return None
    return d


def parse_json(info):
    """Given json from Spotify, convert into dict.
    Parameters
    ----------
    info: JSON dict
        JSON dict to be filtered.
    Returns
    -------
    d: dict or None
        Return filtered dict or None if info is None.
    """
    if info:
        return {
                'device_name': dict_get(info, ['device', 'name']),
                'device_type': dict_get(info, ['device', 'type']),
                'device_volume': dict_get(info, ['device', 'volume_percent']),
                'shuffle_state': dict_get(info, ['shuffle_state']),
                'repeat_state': dict_get(info, ['repeat_state']),
                'timestamp': dict_get(info, ['timestamp']),
                'id': dict_get(info, ['item', 'id']),
                'progress_ms': dict_get(info, ['progress_ms']),
                'duration_ms': dict_get(info, ['item', 'duration_ms']),
                'explicit': dict_get(info, ['item', 'explicit']),
                'type': dict_get(info, ['item', 'type']),
                'playing': dict_get(info, ['is_playing'])
                }
    else:
        return None


def redis_convert(d):
    """Convert dict into Redis friendly types.
    Parameters
    ----------
    d: dict
        d is the dictionary containing values that may not be Redis friendly.
    Returns
    -------
    d: dict
        d is a converted dict containg Redis friendly values.
    """
    for key, val in d.items():
        if isinstance(val, bool):
            d[key] = 1 if val else 0
    return d


if __name__ == '__main__':
    authorize_token()

    r = redis.StrictRedis(redis_host, db=0)

    while True:
        with open('token.json', 'r') as json_file:
            tok = json.load(json_file)
        token = tok['access_token']

        info = current_playing(token)

        if info:
            master = parse_json(info)
            master = redis_convert(master)
            try:
                utc_time = int(time.time())
                r.hmset('activity:' + str(utc_time), master)
                print('{} --- {}'.format(datetime.now(), master['id']))
            except Exception as e:
                print('Error: {}'.format(e))
        time.sleep(5)
