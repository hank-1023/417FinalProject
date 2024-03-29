import random
import socket
from urllib.parse import urlencode

import aiohttp

import bencoding
from peer_connection import *


class TrackerResponse:

    def __init__(self):
        self.peers = []
        self.complete = 0
        self.incomplete = 0
        self.interval = 0


class Tracker:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = '-PC0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])

    async def connect(self, uploaded: int, downloaded: int, first_connect=False) -> TrackerResponse:
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.total_length,
            # port should be between 6881-6889
            'port': 6889,
            'compact': 1
        }

        if first_connect:
            params['event'] = 'started'

        full_url = self.torrent.base_url + '?' + urlencode(params)
        client_session = aiohttp.ClientSession()

        async with client_session.get(full_url) as raw_response:
            if not raw_response.status == 200:
                raise ConnectionError('Unable to connect to tracker: status code {}'.format(raw_response.status))
            data = await raw_response.read()
            self.check_response_error(data)

        await client_session.close()
        k = data

        return self.parse_response(data)

    @staticmethod
    def check_response_error(raw_response):
        try:
            message = raw_response.decode("utf-8")
            if "failure" in message:
                raise ConnectionError('Unable to connect to tracker: {}'.format(message))
        except UnicodeDecodeError:
            pass

    @staticmethod
    def parse_response(raw_response) -> TrackerResponse:
        result = TrackerResponse()

        decoded = bencoding.Decoder(raw_response).decode()

        peers = decoded[b'peers']
        peers = [peers[i:i + 6] for i in range(0, len(peers), 6)]
        for p in peers:
            decoded_port = struct.unpack(">H", p[4:])[0]
            result.peers.append((socket.inet_ntoa(p[:4]), decoded_port))

        result.complete = decoded.get(b'complete', 0)
        result.incomplete = decoded.get(b'incomplete', 0)
        result.interval = decoded.get(b'interval', 0)

        return result
