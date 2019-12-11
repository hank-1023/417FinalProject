import time
from asyncio import Queue
from PiecesManager import PiecesManager
from connection_proto import PeerConnection
from tracker import Tracker

REQUEST_LENGTH = 2 ** 14
MAX_PEER_CONNECTIONS = 40


class TorrentClient:

    def __init__(self, torrent):
        self.tracker = Tracker(torrent)
        self.pieces_manager = PiecesManager()
        self.available_peers = Queue()
        self.peers = [PeerConnection(self.available_peers,
                                     self.tracker.torrent.info_hash,
                                     self.tracker.peer_id,
                                     self.on_block_received())
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
                response = await self.tracker.connect(self.pieces_manager.bytes_uploaded(),
                                                      self.pieces_manager.bytes_downloaded(),
                                                      previous_time is None)

                if response:
                    previous_time = current_time
                    interval = response.interval

                for p in response.peers:
                    self.available_peers.put_nowait(p)

    def on_block_received(self):
        self.pieces_manager.event_block_received()
