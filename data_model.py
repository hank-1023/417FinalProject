import logging
from _sha1 import sha1


class Block:
    Missing = 0
    Downloading = 1
    Completed = 2

    def __init__(self, piece: int, offset: int, length: int):
        self.piece = piece
        self.offset = offset
        self.length = length
        self.status = Block.Missing
        self.data = None


class Piece:
    def __init__(self, index: int, blocks: [], hash_value):
        self.index = index
        self.blocks = blocks
        self.hash = hash_value

    def is_complete(self):
        for b in self.blocks:
            if b.status != Block.Completed:
                return False

    def reset(self):
        for b in self.blocks:
            b.status = Block.Missing

    def get_next_block(self):
        for b in self.blocks:
            if b.status == Block.Missing:
                return b

    def concat_blocks(self):
        if not self.is_complete():
            return None

        sorted_blocks = sorted(self.blocks, key=lambda b: b.offset)
        result = b''
        blocks_data = [b.data for b in sorted_blocks]
        return result.join(blocks_data)

    def is_hash_matching(self):
        piece_hash = sha1(self.concat_blocks()).digest()
        return self.hash == piece_hash

    def next(self):
        for block in self.blocks:
            if block.status == Block.Missing:
                block.status = Block.Downloading
                return block
        return None

    # def received(self, offset: int, data: bytes):
    #     exist = 0
    #     for block in self.blocks:
    #         if block.offset == offset:
    #             block.status = Block.Completed
    #             block.data = data
    #             exist = 1
    #     if exist == 0:
    #         logging.warning('Trying to complete a non-existing block {offset}'.format(offset=offset))





