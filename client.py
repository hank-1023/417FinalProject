import asyncio
import logging
from asyncio import CancelledError

from peer_connection import PeerConnection
from pieces_manager import *
from torrent import Torrent
from tracker import Tracker

REQUEST_LENGTH = 2 ** 14
MAX_PEER_CONNECTIONS = 40


class TorrentClient:

    def __init__(self, torrent_file):
        self.torrent = Torrent(torrent_file)
        self.tracker = Tracker(self.torrent)
        self.pieces_manager = PiecesManager(self.torrent)
        self.user_canceled = False

    async def start(self):
        previous_time = None

        tracker_response = await self.tracker.connect(self.pieces_manager.bytes_uploaded(),
                                                      self.pieces_manager.bytes_downloaded(),
                                                      previous_time is None)
        if tracker_response:

            peers = tracker_response.peers
            port = 0
            for p in peers:
                if p[0] == '128.8.126.63':
                    port = p[1]
                    break

            pc = PeerConnection('128.8.126.63',
                                port,
                                self.tracker.torrent.info_hash,
                                self.tracker.peer_id,
                                self.pieces_manager)
            await pc.start()

        else:
            print("Tracker no response")

    # def _empty_queue(self):
    #     while not self.available_peers.empty():
    #         self.available_peers.get_nowait()

    def on_block_received(self, piece_index, block_offset, data):
        self.pieces_manager.event_block_received(piece_index, block_offset, data)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    client = TorrentClient('torrents/1184-0.txt.torrent')
    task = loop.create_task(client.start())
    try:
        loop.run_until_complete(task)
    except CancelledError:
        logging.warning('Event loop was canceled')
