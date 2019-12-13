import asyncio
import logging
import time
from threading import Thread
from asyncio import Queue, CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from multiprocessing import Process

from async_timeout import timeout

from pieces_manager import *
from bencoding import Decoder
from peer_connection import *
from tracker import Tracker
from torrent import Torrent

REQUEST_LENGTH = 2 ** 14
MAX_PEER_CONNECTIONS = 40


class TorrentClient:

    def __init__(self, parse_torrent):
        self.torrent = Torrent(parse_torrent)
        self.tracker = Tracker(self.torrent)
        self.pieces_manager = PiecesManager(Torrent(parse_torrent))
        self.available_peers = Queue()
        self.peers = []
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
            tracker_response = await self.tracker.connect(self.pieces_manager.bytes_uploaded(),
                                                          self.pieces_manager.bytes_downloaded(),
                                                          True)

            if tracker_response:
                self.peers = tracker_response.peers
            print(self.peers)
            for peer in self.peers:
                if peer[0] != '128.8.126.63':
                    continue
                try:
                    pc = PeerConnection(ip=peer[0], port=peer[1], info_hash=self.torrent.info_hash,
                                             peer_id=self.tracker.peer_id.encode('utf-8'),
                                             pieces_manager=self.pieces_manager, )
                    await pc.start()
                    if self.pieces_manager.completed():
                        break
                except TimeoutError:
                    pass
                except ConnectionRefusedError:
                    pass

    def _empty_queue(self):
        while not self.available_peers.empty():
            self.available_peers.get_nowait()


if __name__ == '__main__':
    loop_client = asyncio.get_event_loop()
    client = TorrentClient('torrents/deb-10.1.0-amd64-netinst.iso.torrent')
    task = loop_client.create_task(client.start())
    try:
        loop_client.run_until_complete(task)
        pass
    except CancelledError:
        pass
