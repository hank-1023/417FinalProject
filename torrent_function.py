from contrib.encoding import Decoder
from contrib.encoding import Encoder
from hashlib import sha1
from collections import namedtuple

SingleTorrent = namedtuple('SingleTorrent', ['name', 'length'])
FileList = namedtuple('FileList', ['length', 'path'])
MultiTorrent = namedtuple('MultiTorrent', ['name', 'FileList'])

class Torrent:

    def __init__(self, file):
        self.file = file
        self.files = []

        torrent = open(self.file, 'rb').read()
        self.meta_info = Decoder(torrent).decode()
        self.info_hash = sha1(Encoder(self.meta_info[b'info']).encode()).digest()
        newlist = []
        if self.multi:
            for a in self.meta_info[b'info'][b'files']:
                newlist.append(FileList(a[b'length'], a[b'path']))

            self.files.append(MultiTorrent(self.meta_info[b'info'][b'name'].decode('utf-8'), newlist))
        else:
            self.files.append(
                SingleTorrent(self.meta_info[b'info'][b'name'].decode('utf-8'), self.meta_info[b'info'][b'length']))

    def announce(self) -> str:
        return self.meta_info[b'announce'].decode('utf-8')

    def multi(self) -> bool:
        return b'files' in self.meta_info[b'info']

    def total_size(self) -> int:
        r = 0
        result = 0
        if self.multi:
            while r < len(self.files[0].FileList):
                result += self.files[0].FileList[r].length
                r += 1
            return result

        return self.files[0].length

    def piece_length(self) -> int:
        return self.meta_info[b'info'][b'piece length']

    def pieces(self):
        data = self.meta_info[b'info'][b'pieces']
        piece = []
        count = 0
        while count < len(data):
            piece.append(data[count:count+20])
            count += 20

        return piece




