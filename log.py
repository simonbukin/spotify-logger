from datetime import datetime

import requests
import webbrowser
import urllib
import json
import os
import os.path
import csv
import time

from auth import client_secret, client_id, redirect_uri

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
    """Return and print the currently playing track."""
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
    """Return attribute in dict given a path."""
    for item in path:
        d = d.get(item, {})
        if d is None or d == {}:
            print('{} ::: {} is considered None'.format(path, d))
            return None
    return d


def parse_json(info):
    """Given json from Spotify, convert into array for appending to CSV."""
    if info:
        print(info)
        return {
                'device_name': dict_get(info, ['device', 'name']),
                'device_type': dict_get(info, ['device', 'type']),
                'device_volume': dict_get(info, ['device', 'volume_percent']),
                'shuffle_state': dict_get(info, ['shuffle_state']),
                'repeat_state': dict_get(info, ['repeat_state']),
                'timestamp': dict_get(info, ['timestamp']),
                'context_href': dict_get(info, ['context', 'href']),
                'context_type': dict_get(info, ['context', 'type']),
                'progress_ms': dict_get(info, ['progress_ms']),
                'album_href': dict_get(info, ['item', 'album', 'href']),
                'album_name': dict_get(info, ['item', 'album', 'name']),
                'album_release': (dict_get(info,
                                           ['item', 'album', 'release_date'])),
                'artists': dict_get(info, ['item', 'artists']),
                'duration_ms': dict_get(info, ['item', 'duration_ms']),
                'explicit': dict_get(info, ['item', 'explicit']),
                'href': dict_get(info, ['item', 'href']),
                'name': dict_get(info, ['item', 'name']),
                'popularity': dict_get(info, ['item', 'popularity']),
                'track_number': dict_get(info, ['item', 'track_number']),
                'type': dict_get(info, ['item', 'type']),
                'current_playing_type': (dict_get(info,
                                                  ['currently_playing_type'])),
                'playing': dict_get(info, ['is_playing'])
                }
    else:
        return None


if __name__ == '__main__':
    authorize_token()

    while True:
        with open('token.json', 'r') as json_file:
            tok = json.load(json_file)
        token = tok['access_token']

        if not(os.path.isfile(os.getcwd() + '/history.csv')):
            with open('history.csv', 'w') as f:
                writer = csv.writer(f)
                header = ['device_name',
                          'device_type',
                          'device_volume',
                          'shuffle_state',
                          'repeat_state',
                          'timestamp',
                          'context_href',
                          'context_type',
                          'progress_ms',
                          'album_href',
                          'album_name',
                          'album_release',
                          'artists',
                          'duration_ms',
                          'explicit',
                          'href',
                          'name',
                          'popularity',
                          'track_number',
                          'type',
                          'current_playing_type',
                          'playing']
                writer.writerow(header)

        info = current_playing(token)

        if info:
            to_append = parse_json(info)
            print(to_append)
            print('{} - {}'.format(datetime.now(), to_append['name']))
            with open('history.csv', 'a') as f:
                writer = csv.writer(f)
                attributes = list(to_append.values())
                writer.writerow(attributes)
        time.sleep(5)
