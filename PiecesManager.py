import math
import time
from DataModel import *

BLOCK = 2**14


class PiecesManager:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peers = {}
        self.missing_list = self._initial_piece()
        self.sending_list = []
        self.queue = []
        self.have_pieces = []
        self.total_pieces = len(torrent.pieces)

    def _initial_piece(self):
        torrent = self.torrent
        piece = []
        total_pieces = len(torrent.pieces)
        block_num = math.ceil(torrent.piece_length/BLOCK)

        for index, hash in enumerate(torrent.pieces):
            if index < total_pieces:
                #all the pieces except for the last one
                blocks = [Block(index, offset * BLOCK, BLOCK) for offset in range(block_num)]
            else:
                #the last piece which may not be full length
                block_num_last = math.ceil(torrent.total_size() % torrent.piece_length / BLOCK)
                blocks = [Block(index, offset * BLOCK, BLOCK) for offset in range(block_num_last-1)]
                last_length = torrent.piece_length - ((block_num_last-1)*BLOCK)
                blocks.append(Block(index, (block_num_last-1) * BLOCK, last_length))
            piece.append(Piece(index, blocks, hash))
        return piece

    def completed(self):
        return len(self.have_pieces) == self.total_pieces

    @staticmethod
    def bytes_uploaded():
        upload = 0
        return upload == 0

    def bytes_downloaded(self):
        return len(self.have_pieces) * self.torrent.piece_length

    def event_block_received(self, peer_id, index, offset, data):
        for piece in self.sending_list:
            if piece.block[1].index == index & piece.block[1].offset == offset:
                self.sending_list.remove(piece)
                break

        for piece in self.queue:
            if piece.index == index:
                piece.received(offset, data)
                if piece.is_complete():
                    if piece.is_hash_matching():
                        self.queue.remove(piece)
                        self.have_pieces.append(piece)
                        downloaded = self.total_pieces - len(self.missing_list) - len(self.queue)
                    else:
                        print("wrong piece")
                        piece.reset()

    def add_peers(self, peer_id, pieces):
        self.peers[peer_id] = pieces

    def update_peers(self, peer_id, index):
        if peer_id in self.peers:
            self.peers[peer_id][index] = 1

    def next_request(self,peer_id):
        if peer_id not in self.peers:
            return None

        block = self.current_pending(peer_id)
        if not block:
            block = self.push_next(peer_id)
            if not block:
                self.find_next(peer_id).new_request()

        return block

    def current_pending(self, peer_id):
        current = int(round(time.time() * 1000))
        for blocks in self.sending_list:
            if blocks[2] + 300*1000 > current:
                blocks[2] = current
                return blocks[1]
        return None

    def push_next(self, peer_id):
        for pieces in self.queue:
            if self.peers[peer_id][pieces.index] == 1:
                block = pieces.next()
                if block:
                    self.queue.append((block, int(round(time.time() * 1000))))
                    return block

        return None

    def find_next(self, peer_id):
        for pieces in self.missing_list:
            self.missing_list.remove(pieces)
            self.queue.append(pieces)
            return pieces
        return None




