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

        print('token refreshed!')


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
    print('auth successfull!')


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
            # try:
            #     artist_json = r.json()['item']['artists']
            #     artist_array = [artist['name'] for artist in artist_json]
            #     artists = ' '.join(artist_array)
            #     name = r.json()['item']['name']
            #     time = pretty_print_ms(r.json()['progress_ms'])
            #     playing = r.json()['is_playing']
            #     pretty_playing = ''
            #     if playing:
            #         pretty_playing = '▶'
            #     else:
            #         pretty_playing = '❚❚'
            #     length = r.json()['item']['duration_ms']
            #     progress = r.json()['progress_ms']
            #     perc = str(progress / length * 100)[0:4]
            #     t = datetime.now()
            #     time_print = t.strftime('%m/%d/%Y %H:%M:%S')
            #     print('{} --- {} [{} /// {}] - {} - {}'.format(time_print,
            #                                                    pretty_playing,
            #                                                    time,
            #                                                    perc + '%',
            #                                                    name,
            #                                                    artists))
            # except Exception:
            #     print('error printing, but 200 response')
            return r.json()
        elif r.status_code == 401:  # need to refresh
            print(r.text)
            refresh_token()
            return None
        elif r.status_code == 204:
            print('No track playing or private session')
            return None
        else:
            print('Error in call: {}'.format(r.status_code))
            print(r.text)
            return None
    else:
        print('request failed')
        refresh_token()
        time.sleep(30)


def parse_json(info):
    """Given json from Spotify, convert into array for appending to CSV."""
    new_info = [
            info['device'].get('name'),
            info['device'].get('type'),
            info['device'].get('volume_percent'),
            info.get('shuffle_state'),
            info.get('repeat_state'),
            info.get('timestamp'),
            info['context'].get('href'),
            info['context'].get('type'),
            info.get('progress_ms'),
            info['item']['album'].get('href'),
            info['item']['album'].get('name'),
            info['item']['album'].get('release_date'),
            info['item'].get('artists'),
            info['item'].get('duration_ms'),
            info['item'].get('explicit'),
            info['item'].get('href'),
            info['item'].get('name'),
            info['item'].get('popularity'),
            info['item'].get('track_number'),
            info['item'].get('type'),
            info.get('currently_playing_type'),
            info.get('is_playing')
            ]
    return new_info


def main():
    """Refresh tokens and poll Spotify API."""
    authorize_token()

    while True:
        with open('token.json', 'r') as json_file:
            tok = json.load(json_file)
        token = tok['access_token']

        info = current_playing(token)

        if info:
            to_append = parse_json(info)
            print('{} - success! '.format(datetime.now()))
            with open('history.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(to_append)
        time.sleep(5)


main()
