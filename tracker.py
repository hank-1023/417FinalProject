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


class Tracker:
    def __init__(self, torrent_file):
        self.torrent = Torrent(torrent_file)

    async def connect(self):
        peer_id = '-PC0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': peer_id,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.torrent.total_length,
            # port should be between 6881-6889
            'port': 6889,
            'compact': 1
        }

        full_url = self.torrent.base_url + '?' + urlencode(params)
        client_session = aiohttp.ClientSession()

        async with client_session.get(full_url) as response:
            if not response.status == 200:
                raise ConnectionError('Unable to connect to tracker: status code {}'.format(response.status))
            data = await response.read()
            self.check_response_error(data)

            decoded = bencoding.Decoder(data).decode()
            peers = decoded[b'peers']
            peers = [peers[i:i + 6] for i in range(0, len(peers), 6)]

            peers_queue = Queue()
            for p in peers:
                await peers_queue.put((socket.inet_ntoa(p[:4]), _decode_port(p[4:])))

            pc = PeerConnection(peers_queue, self.torrent.info_hash, peer_id.encode('utf-8'))
            await pc.start()

        await client_session.close()

    @staticmethod
    def check_response_error(response):
        try:
            message = response.decode("utf-8")
            if "failure" in message:
                raise ConnectionError('Unable to connect to tracker: {}'.format(message))
        except UnicodeDecodeError:
            pass


def _decode_port(port):
    """
    Converts a 32-bit packed binary port number to int
    """
    # Convert from C style big-endian encoded as unsigned short
    return struct.unpack(">H", port)[0]


if __name__ == '__main__':
    t = Tracker('torrents/1056.txt.utf-8.torrent')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(t.connect())
