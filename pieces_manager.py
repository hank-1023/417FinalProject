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
        self.file_list = []
        self.missing_list = self.initiate_blocks()
        self.sending_list = []
        self.queue = []
        self.have_pieces = []
        count = 0;
        self.fd = []
        while count < len(self.torrent.output_file):
            self.fd.append(os.open(self.torrent.output_file[count][0], os.O_RDWR | os.O_CREAT))
            count += 1
        self.is_multi_file = torrent.multi_file

    def initiate_blocks(self):
        pointer = 0
        pieces = []
        count = 1
        ind = 0
        length = self.torrent.total_length[ind]
        while count < self.total_pieces_num:
            if count * self.torrent.piece_length > length:
                self.file_list.append(count)
                ind += 1
                length += self.torrent.total_length[ind]
            count += 1
        self.file_list.append(self.total_pieces_num)
        for index, piece_hash in enumerate(self.torrent.pieces):
            total_length = self.torrent.length_to_download
            if index != math.ceil(total_length/self.torrent.piece_length) - 1:
                blocks = []
                # No. of blocks for each piece except for the last one
                block_num = math.ceil(self.torrent.piece_length / REQUEST_LENGTH)
                for offset in range(block_num):
                    blocks.append(Block(index, offset * REQUEST_LENGTH, REQUEST_LENGTH))
            else:
                # For last piece
                blocks = []
                last_piece_length = total_length % self.torrent.piece_length
                block_num = math.ceil(last_piece_length / REQUEST_LENGTH)
                for offset in range(block_num):
                    blocks.append(Block(index, offset * REQUEST_LENGTH, REQUEST_LENGTH))

            # If the last block in last piece is smaller, change the length of last block
                if last_piece_length % REQUEST_LENGTH > 0:
                    last = blocks[-1]
                    last.length = last_piece_length % REQUEST_LENGTH
                    blocks[-1] = last
            pieces.append(Piece(index, blocks, piece_hash))
            pointer += 1
        return pieces

    def close(self):
        for fd in self.fd:
            if fd:
                os.close(fd)
        print(self.fd)

    def pieces_num(self):
        return self.have_pieces

    def completed(self):
        if len(self.have_pieces) == self.total_pieces_num:
            return True
        else:
            return False

    def peer_completed(self, peer_id):
        exist = False
        count = 0
        pieces_not_complete = 0
        while count < self.total_pieces_num:
            if self.peers[peer_id][count]:
                pieces_not_complete += 1
                for piece in self.have_pieces:
                    if piece.index == count:
                        pieces_not_complete -= 1
            count += 1
        return pieces_not_complete == 0

    @staticmethod
    def bytes_uploaded() -> int:
        upload = 0
        return upload

    def bytes_downloaded(self) -> int:
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

    def current_queue(self):
        piece_downloading = ""
        for block in self.queue:
            if not block:
                return None;
            else:
                for piece in self.queue:
                    piece_downloading += str(piece.index) + " "
        return piece_downloading

    def previous_piece(self, piece):
        for target_piece in self.have_pieces:
            if piece.index == target_piece.index:
                return piece

    def _write(self, piece):
        if not self.torrent.multi_file:
            pos = piece.index * self.torrent.piece_length
            os.lseek(self.fd[0], pos, os.SEEK_SET)
            os.write(self.fd[0], piece.data)
            return
        pos = piece.index * self.torrent.piece_length
        count = piece.index
        ind = 0
        while ind < len(self.file_list):
            count -= self.file_list[ind]-1
            if count == 0:
                os.lseek(self.fd[ind], pos, os.SEEK_SET)
                os.write(self.fd[ind], piece.data[:self.torrent.total_length[ind]-pos])
                if ind < len(self.fd)-1:
                    os.lseek(self.fd[ind+1], 0, os.SEEK_SET)
                    os.write(self.fd[ind+1], piece.data[self.torrent.total_length[ind]-pos:])
                break
            elif count > 0:
                count = piece.index
                pos -= self.torrent.total_length[ind]
                ind += 1
            else:
                os.lseek(self.fd[ind], pos, os.SEEK_SET)
                os.write(self.fd[ind], piece.data)
                break


