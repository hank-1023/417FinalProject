
BLOCK = 2**14

class PiecesManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.peers = {}
        self.missing_list = self.initial_piece()
        self.sending_list = []
        self.have_pieces = []
        self.total_pieces = len(torrent.pieces)



    def initial_piece(self, torrent):
        torrent = self.torrent
        piece = []
        length = len(torrent.pieces)
        block_num = (torrent.piece_length/BLOCK) + 1

        for index, hash in enumerate(torrent.pieces):
            if index < total_piece - 1:
                #all the pieces except for the last one
                blocks = [Block(index, offset * BLOCK, BLOCK)
                        for offset in range(block_num)]
            else:
                #the last piece which may not be full length
                block_num_last = ((torrent.total_length % torrent.piece_length)/BLOCK) + 1
                blocks = [Block(index, offset * BLOCK, BLOCK)
                          for offset in range(block_num_last-1)]
                last_length = torrent.piece_length - ((block_num_last-1)*BLOCK)
                blocks.append(Block(index, (block_num_last-1) * BLOCK, last_length))
            piece.append(Piece(index, blocks, hash))
        return piece



    def completed(self):
        return len(self.missing_list) == 0 & len(self.ongoing_list == 0) & len(self.have_pieces) == self.total_pieces

    def bytes_uploaded(self):
        return 0

    def bytes_downloaded(self):
        return len(self.have_pieces) * self.torrent.piece_length

    def event_block_received(self):
        return

    def add_peers(self, peer_id, pieces):
        self.peers[peer_id] = pieces

    def update_peers(self, peer_id, index):
        if peer_id in self.peers:
            self.peers[peer_id][index] = 1



