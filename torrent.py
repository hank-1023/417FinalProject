import torrent_parser as tp
from hashlib import sha1

import bencoding


class DownloadFileInfo:
    def __init__(self, filename, length, path=None):
        self.filename = filename
        self.length = length
        # For multi-file
        self.path = path


class Torrent:
    def __init__(self, torrent_file):
        self.meta_data = tp.parse_torrent_file(torrent_file)
        self.multi_file = 'files' in self.meta_data['info']
        self.files = []
        self.base_url = self.meta_data['announce']
        self.total_length = self.meta_data['info']['length']

        with open(torrent_file, 'rb') as f:
            meta_info = f.read()
            self.raw_meta = bencoding.Decoder(meta_info).decode()
            info = bencoding.Encoder(self.raw_meta[b'info']).encode()
            self.info_hash = sha1(info).digest()

    # def parse_meta(self, meta):
    #     self.base_url = meta['announce']
    #     encoded_info_hash = tp.encode(meta['info'])
    #     self.info_hash = sha1(encoded_info_hash).digest()
    #     # populates self.files array
    #     # self.add_files(meta['info'])

    # def add_files(self, info_dict):
    #     if self.multi_file:
    #         for item in info_dict['files']:
    #             f = DownloadFileInfo(None, item['length'], item['path'])
    #             self.files.append(f)
    #             self.total_length += item['length']
    #     else:
    #         f = DownloadFileInfo(info_dict['name'], info_dict['length'])
    #         self.files.append(f)
    #         self.total_length = info_dict['length']

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

    def output_file(self):
        return self.meta_data['info']['name']



if __name__ == '__main__':
    torrent = Torrent('torrents/1056.txt.utf-8.torrent')
    print(torrent.pieces)



