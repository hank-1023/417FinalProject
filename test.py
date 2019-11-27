import bencode
from torrent_function import Torrent
from contrib.encoding import Decoder
from contrib.encoding import Encoder


torr = Torrent('/Users/yuqinguan/Desktop/FinalProject/417FinalProject/shared.torrent')
print(torr.announce())
print(torr.total_size())
print(torr.piece_length())
print(torr.pieces())
print()

bencode.bdecode('i12e')

