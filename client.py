import asyncio
import logging
import time
from asyncio import Queue, CancelledError
from PiecesManager import *
from bencoding import Decoder
from connection_proto import *
from tracker import Tracker
from torrent import Torrent

REQUEST_LENGTH = 2 ** 14
MAX_PEER_CONNECTIONS = 40


class TorrentClient:

    def __init__(self, parse_torrent):
        self.tracker = Tracker(parse_torrent)
        self.pieces_manager = PiecesManager(Torrent(parse_torrent))
        self.available_peers = Queue()
        self.peers = [PeerConnection(self.available_peers,
                                     self.tracker.torrent.info_hash,
                                     self.tracker.peer_id,
                                     self.on_block_received)
                      for _ in range(MAX_PEER_CONNECTIONS)]
        self.user_canceled = False

    async def start(self):
        previous_time = None
        interval = 1800

        while True:
            if self.user_canceled:
                break
            if self.pieces_manager.completed():
                print("File Download Complete")
                break

            current_time = time.time()

            if not previous_time or previous_time - current_time < interval:
                tracker_response = await self.tracker.connect(self.pieces_manager.bytes_uploaded(),
                                                              self.pieces_manager.bytes_downloaded(),
                                                              previous_time is None)

                if tracker_response:
                    previous_time = current_time
                    interval = tracker_response.interval
                    self._empty_queue()
                    for p in tracker_response.peers:
                        self.available_peers.put_nowait(p)

    def _empty_queue(self):
        while not self.available_peers.empty():
            self.available_peers.get_nowait()

    def on_block_received(self):
        # self.pieces_manager.event_block_received()
        pass


if __name__ == '__main__':
    t = Tracker('torrents/1056.txt.utf-8.torrent')
    print(Torrent('torrents/1056.txt.utf-8.torrent').total_length)
    print(Torrent('torrents/1056.txt.utf-8.torrent').piece_length)
    with open('torrents/deb-10.1.0-amd64-netinst.iso.torrent', 'rb') as f:
        meta_info = f.read()
    torrent = Torrent('torrents/1056.txt.utf-8.torrent')
    torrent.info()
    print(torrent)
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(t.connect(0, 0, None))

    q = Queue()
    # Putting one address for testing
    print(response.peers[-1])
    q.put_nowait(response.peers[-1])

    client = TorrentClient('torrents/1056.txt.utf-8.torrent')
    task = loop.create_task(client.start())
    try:
        loop.run_until_complete(task)
    except CancelledError:
        logging.warning('Event loop was canceled')
