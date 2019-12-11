import torrent_parser as tp
from hashlib import sha1


class DownloadFileInfo:
    def __init__(self, filename, length, path=None):
        self.filename = filename
        self.length = length
        # For multi-file
        self.path = path


class Torrent:
    def __init__(self, torrent_file):
        self.meta = tp.parse_torrent_file(torrent_file)
        self.multi_file = 'files' in self.meta['info']
        self.files = []
        self.base_url = None
        self.info_hash = None
        self.total_length = 0

        # add more fields while parsing the dictionary
        self.parse_meta(self.meta)

    def parse_meta(self, meta):
        self.base_url = meta['announce']
        encoded_info = tp.encode(meta['info'])
        self.info_hash = sha1(encoded_info).digest()
        # populates self.files array
        self.add_files(meta['info'])

    def add_files(self, info_dict):
        if self.multi_file:
            for item in info_dict['files']:
                f = DownloadFileInfo(None, item['length'], item['path'])
                self.files.append(f)
                self.total_length += item['length']
        else:
            f = DownloadFileInfo(info_dict['name'], info_dict['length'])
            self.files.append(f)
            self.total_length = info_dict['length']

    @property
    def pieces(self):
        piecesha = self.meta['info']['pieces']
        pieces = []
        offset = 0

        while offset < len(piecesha):
            pieces.append(piecesha[offset:offset + 20])
            offset += 20
        return pieces

    @property
    def piece_length(self) -> int:
        return self.meta['info']['piece length']


    def total_size(self) -> int:
        return self.total_length


