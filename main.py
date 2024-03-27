import requests
import os
import sys

DELUGE_SERVER_IP_ADDRESS = '192.168.1.10'
DELUGE_SERVER_PORT = 32774
DELUGE_SERVER_URL = f'http://{DELUGE_SERVER_IP_ADDRESS}:{DELUGE_SERVER_PORT}/'
DELUGE_PASSWORD = os.environ.get('DELUGE_PASSWORD', 'deluge')
REQUEST_ID = 0


def send_request(session, method, params=None):
    global REQUEST_ID
    REQUEST_ID += 1

    try:
        response = session.post(
            f'{DELUGE_SERVER_URL}/json',
            json={'id': REQUEST_ID, 'method': method, 'params': params or []})

    except requests.exceptions.ConnectionError:
        raise Exception('WebUI seems to be unavailable. Run deluge-web or enable WebUI plugin using other thin client.')

    data = response.json()
    error = data.get('error')
    if error:
        msg = error['message']
        if msg == 'Unknown method':
            msg += f'. Check WebAPI is enabled ({method}).'

        raise Exception('API response: %s' % msg)

    return response, data['result']


def main():
    file_path = sys.argv[-1]

    if not os.path.isfile(file_path):
        raise Exception(f'Invalid file "{file_path}"')

    session = requests.session()
    session.headers['Referer'] = DELUGE_SERVER_URL

    r, data = send_request(session, 'auth.login', [DELUGE_PASSWORD])
    session_id = r.cookies['_session_id']
    session.headers['Cookie'] = f'_session_id={session_id}'

    with open(file_path, 'rb') as f:
        files = {'file': f}
        r = session.post(f'{DELUGE_SERVER_URL}/upload', files=files)

    r.raise_for_status()
    data = r.json()
    uploaded_file_path = data['files'][0]
    send_request(session, 'web.get_torrent_info', [uploaded_file_path])
    send_request(session, 'web.add_torrents', [[{"path": uploaded_file_path, "options": {"file_priorities": [1, 1], "add_paused": False, "compact_allocation": False, "download_location": "/downloads", "move_completed": False, "move_completed_path": "/root/Downloads", "max_connections": -1, "max_download_speed": -1, "max_upload_slots": -1, "max_upload_speed": -1, "prioritize_first_last_pieces": False}}]])


main()
