import math
import os

from client import REQUEST_LENGTH
from data_model import Piece, Block


class PiecesManager:
    def __init__(self, torrent):
        self.torrent = torrent
        self.total_pieces_num = len(torrent.pieces)

        self.missing_pieces = self.initiate_all_pieces()
        self.downloading_piece = None
        self.completed_pieces = []

        self.fd = os.open(self.torrent.output_file, os.O_RDWR | os.O_CREAT)

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
        result = len(self.completed_pieces) == self.total_pieces_num
        if result:
            os.close(self.fd)
            print("Download is completed")
        return result

    @staticmethod
    def bytes_uploaded():
        return 0

    def bytes_downloaded(self):
        return len(self.completed_pieces) * self.torrent.piece_length

    def event_block_received(self, piece_index, block_offset, data):
        piece = self.downloading_piece
        if piece:
            self.add_block_to_piece(block_offset, data, piece)
        else:
            raise Exception("Piece not set for downloading")

        if piece.is_complete():
            if piece.is_hash_matching():
                self.downloading_piece = None
                self.completed_pieces.insert(piece_index, piece)
                self.write_piece(piece)

                print("Piece " + str(piece_index) + " Completed")
            else:
                # reset the piece's blocks to all missing
                piece.reset()

    def get_next_block(self) -> Block:
        if not self.downloading_piece:
            self.downloading_piece = self.missing_pieces.pop(0)
        block = self.downloading_piece.get_next_block()
        block.status = Block.DOWNLOADING
        return block

    def add_block_to_piece(self, block_offset, block_data, piece):
        block_exist = False
        for block in piece.blocks:
            if block.offset == block_offset:
                block.status = Block.COMPLETED
                block.data = block_data
                block_exist = True
                break
        if not block_exist:
            raise Exception("Write to blocks not existed")

    def write_piece(self, piece):
        position = piece.index * self.torrent.piece_length
        os.lseek(self.fd, position, os.SEEK_SET)
        os.write(self.fd, piece.concat_blocks())
