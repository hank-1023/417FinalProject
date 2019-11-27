import bencode
from torrent_function import Torrent
from contrib.encoding import Decoder
from contrib.encoding import Encoder

print(open('/Users/yuqinguan/Desktop/FinalProject/417FinalProject/shared.torrent', 'rb').read())
meta_info = open('/Users/yuqinguan/Desktop/FinalProject/417FinalProject/shared.torrent', 'rb').read()
L = list(open('/Users/yuqinguan/Desktop/FinalProject/417FinalProject/shared.torrent', 'rb').read())
K = open('/Users/yuqinguan/Desktop/FinalProject/417FinalProject/shared.torrent', 'rb').read()
print(L)
torrent = Decoder(meta_info).decode()
print(torrent)

L = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
print(L[0:20])

torr = Torrent('/Users/yuqinguan/Desktop/FinalProject/417FinalProject/shared.torrent')
print(torr.announce())
print(torr.total_size())
print(torr.piece_length())
print(torr.pieces())


bencode.bdecode('i12e')

