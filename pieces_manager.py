import math
import os
import time
from DataModel import *
from client import REQUEST_LENGTH


class PiecesManager:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peers = {}
        self.total_pieces_num = len(torrent.pieces)
        self.missing_list = self.initiate_blocks()
        self.sending_list = []
        self.queue = []
        self.have_pieces = []
        self.fd = os.open(self.torrent.output_file, os.O_RDWR | os.O_CREAT)

    def initiate_blocks(self):
        pieces = []
        for index, piece_hash in enumerate(self.torrent.pieces):
            if index != self.total_pieces_num - 1:
                blocks = []
                # No. of blocks for each piece except for the last one
                block_num = math.ceil(self.torrent.piece_length / REQUEST_LENGTH)
                for offset in range(block_num):
                    blocks.append(Block(index, offset * REQUEST_LENGTH, REQUEST_LENGTH))
            else:
                # For last piece
                blocks = []
                last_piece_length = self.torrent.total_length % self.torrent.piece_length
                block_num = math.ceil(last_piece_length / REQUEST_LENGTH)
                for offset in range(block_num):
                    blocks.append(Block(index, offset * REQUEST_LENGTH, REQUEST_LENGTH))

                # If the last block in last piece is smaller, change the length of last block
                if last_piece_length % REQUEST_LENGTH > 0:
                    last = blocks[-1]
                    last.length = last_piece_length % REQUEST_LENGTH
                    blocks[-1] = last
            pieces.append(Piece(index, blocks, piece_hash))

        return pieces

    def close(self):
        if self.fd:
            os.close(self.fd)

    def pieces_num(self):
        return self.have_pieces

    def completed(self):
        return len(self.have_pieces) == self.total_pieces_num

    @staticmethod
    def bytes_uploaded():
        upload = 0
        return upload == 0

    def bytes_downloaded(self):
        return len(self.have_pieces) * self.torrent.piece_length

    def event_block_received(self, peer_id, index, offset, data):
        for block in self.sending_list:
            if (block[0].piece_index == index) & (block[0].offset == offset):
                self.sending_list.remove(block)
                break

        for piece in self.queue:
            if piece.index == index:
                piece.received(offset, data)
                if piece.is_complete():
                    if piece.is_hash_matching():
                        self._write(piece)
                        self.have_pieces.append(piece)
                        self.queue.remove(piece)
                        downloaded = self.total_pieces_num - len(self.missing_list) - len(self.queue)
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
                try:
                    block = self.find_next(peer_id).next()
                    return block
                except AttributeError:
                    pass
        return block

    def current_pending(self, peer_id):
        current = int(round(time.time() * 1000))
        for blocks in self.sending_list:
            if blocks[1] + 300*1000 > current:
                block = (blocks[0], current)
                self.sending_list.remove(blocks)
                self.sending_list.append(block)
                return blocks[0]
        return None

    def push_next(self, peer_id):
        for pieces in self.queue:
            if self.peers[peer_id][pieces.index]:
                block = pieces.next()
                if block:
                    self.sending_list.append((block, int(round(time.time() * 1000))))
                    return block

        return None

    def find_next(self, peer_id):
        for pieces in self.missing_list:
            self.missing_list.remove(pieces)
            self.queue.append(pieces)
            return pieces
        return None

    def _write(self, piece):
        """
        Write the given piece to disk
        """
        pos = piece.index * self.torrent.piece_length
        os.lseek(self.fd, pos, os.SEEK_SET)
        os.write(self.fd, piece.data)


