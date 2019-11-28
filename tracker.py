import random
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
            print(data)

        await client_session.close()


if __name__ == '__main__':
    t = Tracker('torrents/shared.torrent')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(t.connect())
