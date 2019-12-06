import random
import socket
import struct
from asyncio import Queue
import bencoding
from connection_proto import *
from torrent import *
import aiohttp
import asyncio
from urllib.parse import urlencode


class TrackerResponse:

    def __init__(self):
        self.peers = []
        self.complete = 0
        self.incomplete = 0
        self.interval = 0


class Tracker:
    def __init__(self, torrent_file):
        self.torrent = Torrent(torrent_file)
        peer_id = '-PC0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])
        self.params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': peer_id,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.torrent.total_length,
            # port should be between 6881-6889
            'port': 6889,
            'compact': 1
        }

    async def connect(self) -> TrackerResponse:
        full_url = self.torrent.base_url + '?' + urlencode(self.params)
        client_session = aiohttp.ClientSession()

        async with client_session.get(full_url) as raw_response:
            if not raw_response.status == 200:
                raise ConnectionError('Unable to connect to tracker: status code {}'.format(raw_response.status))
            data = await raw_response.read()
            self.check_response_error(data)

        await client_session.close()

        return self.parse_response(data)

    @staticmethod
    def check_response_error(response):
        try:
            message = response.decode("utf-8")
            if "failure" in message:
                raise ConnectionError('Unable to connect to tracker: {}'.format(message))
        except UnicodeDecodeError:
            pass

    @staticmethod
    def parse_response(response) -> TrackerResponse:
        result = TrackerResponse()

        decoded = bencoding.Decoder(response).decode()

        peers = decoded[b'peers']
        peers = [peers[i:i + 6] for i in range(0, len(peers), 6)]
        for p in peers:
            decoded_port = struct.unpack(">H", p[4:])[0]
            result.peers.append((socket.inet_ntoa(p[:4]), decoded_port))

        result.complete = decoded.get(b'complete', 0)
        result.incomplete = decoded.get(b'incomplete', 0)
        result.interval = decoded.get(b'interval', 0)

        return result


if __name__ == '__main__':
    t = Tracker('torrents/deb-10.1.0-amd64-netinst.iso.torrent')
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(t.connect())

    q = Queue()
    # Putting one address for testing
    print(response.peers[0])
    q.put_nowait(response.peers[0])

    pc = PeerConnection(q, t.params['info_hash'], t.params['peer_id'].encode('utf-8'))
    loop.run_until_complete(pc.start())
