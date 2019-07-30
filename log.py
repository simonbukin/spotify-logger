import requests, webbrowser, urllib, json, os, os.path, time, csv
from auth import client_secret, client_id, redirect_uri
from datetime import datetime

auth_url = 'https://accounts.spotify.com/authorize/?'
token_url = 'https://accounts.spotify.com/api/token/?'

# attempt to refresh a token
def refresh_token():
    if not(os.path.isfile(os.getcwd() + '/token.json')):
        authorize_token()
    else:
        rf_token = None
        with open('refresh_token.json', 'r') as token:
            rf_token = json.load(token)

        print(rf_token)

        grant_type = 'refresh_token'

        post_payload = {'refresh_token': rf_token['refresh_token'],
                        'grant_type': grant_type}

        response = requests.post(token_url, data=post_payload, auth=(client_id, client_secret), timeout=20)
        with open('token.json', 'w') as write_token:
            write_token.write(response.text)

        print('token refreshed!')
        # refresh_tok = response.json()['refresh_token']

# authorize a token for the first time
def authorize_token():
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

        response = requests.post(token_url, data=post_payload, auth=(client_id, client_secret), timeout=60)

        # print(response.text)

        with open('token.json', 'w') as write_token:
            write_token.write(response.text)

        refresh = {'refresh_token': response.json()['refresh_token']}
        print(refresh)
        with open('refresh_token.json', 'w') as write_refresh:
            json.dump(refresh, write_refresh)
    else:
        print('auth successfull!')

def pretty_print_ms(ms):
    s = str(int((ms / 1000) % 60))
    if len(s) == 1:
        s = '0' + s
    m = str(int((ms / (1000 * 60)) % 60))
    return '{}:{}'.format(m, s)

def current_playing(token):
    playback_url = 'https://api.spotify.com/v1/me/player'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    r = None
    try:
        r = requests.get(playback_url, headers=headers, timeout=60)
    except:
        print('Network connection error')
        time.sleep(30)
        pass
    if r:    
        if r.status_code == 200:
            artists = ' '.join([artist['name'] for artist in r.json()['item']['artists']])
            name = r.json()['item']['name']
            time = pretty_print_ms(r.json()['progress_ms'])
            playing = r.json()['is_playing']
            pretty_playing = ''
            if playing:
                pretty_playing = '▶'
            else:
                pretty_playing = '❚❚'
            perc = str(r.json()['progress_ms'] / r.json()['item']['duration_ms'] * 100)[0:4]
            t = datetime.now()
            print('{} --- {} [{} /// {}] - {} - {}'.format(t.strftime('%m/%d/%Y %H:%M:%S'), pretty_playing, time, perc + '%', name, artists))
            return r.json()
        elif r.status_code == 401: # need to refresh
            print(r.text)
            refresh_token()
        elif r.status_code == 204:
            print('No track playing or private session')
            return None
        else:
            print('Error in call: {}'.format(r.status_code))
            print(r.text)
            return None

def main():
    authorize_token()

    while True:
        tok = None
        with open('token.json', 'r') as json_file:
            tok = json.load(json_file)
        token = tok['access_token']

        # all_songs = None
        # with open('history.json') as read:
        #     all_songs = json.load(read)
        # song_info = current_playing(token)
        # all_songs.append(song_info)
        # with open('history.json', 'w') as writefile:
        #     json.dump(all_songs, writefile, indent=4)

        info = current_playing(token)

        if info is not None:
            try:
                to_append = [
                    info['device']['name'],
                    info['device']['type'],
                    info['device']['volume_percent'],
                    info['shuffle_state'],
                    info['repeat_state'],
                    info['timestamp'],
                    info['context']['href'],
                    info['context']['type'],
                    info['progress_ms'],
                    info['item']['album']['href'],
                    info['item']['album']['name'],
                    info['item']['album']['release_date'],
                    info['item']['artists'],
                    info['item']['duration_ms'],
                    info['item']['explicit'],
                    info['item']['href'],
                    info['item']['name'],
                    info['item']['popularity'],
                    info['item']['track_number'],
                    info['item']['type'],
                    info['currently_playing_type'],
                    info['is_playing']
                ]
            except TypeError:
                print('TypeError within non Nonetype info')
                pass

            with open('history.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(to_append)

        time.sleep(5)

main()
