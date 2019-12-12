import logging
from _sha1 import sha1


class Block:
    MISSING = 0
    DOWNLOADING = 1
    COMPLETED = 2

    def __init__(self, piece_index: int, offset: int, length: int):
        self.piece_index = piece_index
        self.offset = offset
        self.length = length
        self.status = Block.MISSING
        self.data = None


class Piece:
    def __init__(self, index: int, blocks: [], hash_value):
        self.index = index
        self.blocks = blocks
        self.hash_value = hash_value

    def is_complete(self):
        return all(b.status == Block.COMPLETED for b in self.blocks)

    def reset(self):
        for b in self.blocks:
            b.status = Block.MISSING

    def get_next_block(self):
        for b in self.blocks:
            if b.status == Block.MISSING:
                return b

    def concat_blocks(self):
        if not self.is_complete():
            return None

        sorted_blocks = sorted(self.blocks, key=lambda b: b.offset)
        blocks_data = [b.data for b in sorted_blocks]
        return b''.join(blocks_data)

    def is_hash_matching(self):
        piece_hash = sha1(self.concat_blocks()).digest()
        return self.hash_value == piece_hash


    # def received(self, offset: int, data: bytes):
    #     exist = 0
    #     for block in self.blocks:
    #         if block.offset == offset:
    #             block.status = Block.Completed
    #             block.data = data
    #             exist = 1
    #     if exist == 0:
    #         logging.warning('Trying to complete a non-existing block {offset}'.format(offset=offset))





