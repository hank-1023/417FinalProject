import torrent_parser as tp
from hashlib import sha1

import bencoding


class Torrent:
    def __init__(self, torrent_file):
        self.meta_data = tp.parse_torrent_file(torrent_file)
        self.files = []
        self.base_url = self.meta_data['announce']
        self.total_length = self.meta_data['info']['length']
        self.output_file = self.meta_data['info']['name']

        with open(torrent_file, 'rb') as f:
            meta_info = f.read()
            self.raw_meta = bencoding.Decoder(meta_info).decode()
            info = bencoding.Encoder(self.raw_meta[b'info']).encode()
            self.info_hash = sha1(info).digest()

    @property
    def pieces(self):
        data = self.raw_meta[b'info'][b'pieces']
        pieces = []
        offset = 0
        length = len(data)

        while offset < length:
            pieces.append(data[offset:offset + 20])
            offset += 20
        return pieces

    @property
    def piece_length(self) -> int:
        return self.meta_data['info']['piece length']
