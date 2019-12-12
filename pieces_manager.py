import math
import time
from data_model import *
from client import REQUEST_LENGTH
from peer_connection import PeerState

class PiecesManager:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peers = {}
        self.total_pieces_num = len(torrent.pieces)

        self.missing_pieces = self.initiate_all_pieces()
        self.downloading_pieces = {int: Piece}
        self.completed_pieces = {int: Piece}

        # self.downloading_blocks = []

        self.queue = []

    def initiate_all_pieces(self):
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

    def is_download_completed(self):
        return len(self.completed_pieces) == self.total_pieces_num

    @staticmethod
    def bytes_uploaded():
        upload = 0
        return upload == 0

    def bytes_downloaded(self):
        return len(self.completed_pieces) * self.torrent.piece_length

    def event_block_received(self, peer_id, piece_index, block_offset, data):
        if piece_index in self.downloading_pieces.keys():
            piece = self.downloading_pieces[piece_index]
            self.add_block_to_piece(block_offset, data, piece)

            if piece.is_complete():
                if piece.is_hash_matching():
                    # self.write
                    self.downloading_pieces.pop(piece_index)
                    self.completed_pieces[piece_index] = piece
                else:
                    # reset the piece's blocks to all missing
                    piece.reset()
        else:
            raise Exception("Piece not found in downloading")



        # for piece in self.downloading_blocks:
        #     if piece.block[1].index == p_index & piece.block[1].offset == b_offset:
        #         self.downloading_blocks.remove(piece)
        #         break
        #
        # for piece in self.queue:
        #     if piece.index == p_index:
        #         piece.received(b_offset, data)
        #         if piece.is_complete():
        #             if piece.is_hash_matching():
        #                 self.queue.remove(piece)
        #                 self.completed_pieces.append(piece)
        #                 downloaded = self.total_pieces_num - len(self.missing_pieces) - len(self.queue)
        #             else:
        #                 print("wrong piece")
        #                 piece.reset()

    def add_block_to_piece(self, block_offset, block_data, piece):
        block_exist = False
        for block in piece.blocks:
            if block.offset == block_offset:
                block.status = Block.Completed
                block.data = block_data
                block_exist = True
        if not block_exist:
            raise Exception("Write to blocks not existed")

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
        for pieces in self.missing_pieces:
            self.missing_pieces.remove(pieces)
            self.queue.append(pieces)
            return pieces
        return None




