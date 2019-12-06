import asyncio
import logging
import struct
from tracker import *

from asyncio import Queue


class PeerConnection:
    def __init__(self, queue: Queue, info_hash,
                 peer_id, on_block_cb=None):
        self.my_state = []
        self.peer_state = []
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.writer = None
        self.reader = None
        self.on_block_cb = on_block_cb
        self.future = asyncio.ensure_future(self.start())

    async def start(self):
        ip, port = await self.queue.get()
        logging.info('Got assigned peer with: {ip}'.format(ip=ip))

        self.reader, self.writer = await asyncio.open_connection(ip, port)
        buffer = await self.initiate_handshake()

    async def initiate_handshake(self):
        packed_bytes = struct.pack(
            '>B19s8x20s20s',  # >: Big Endian, B: single byte, 19s: 19 bytes string,
            # 8x: padded 8 bytes, 20s: 20 bytes string
            19,
            b'BitTorrent protocol',
            self.info_hash,
            self.peer_id)
        hand_shake_length = 68

        # send handshake message to peer
        self.writer.write(packed_bytes)
        await self.writer.drain()

        buff = b''
        try_count = 1  # try counter, maximum 10

        if len(buff) < hand_shake_length and try_count < 10:
            try_count += 1
            buff = await self.reader.read(10240)

        # unpack the response into arrays
        # [2] is info_hash, [3] is remote peer_id, should be the same with local
        response = struct.unpack('>B19s8x20s20s', buff[:hand_shake_length])

        if not response:
            raise ProtocolError('handshake response is empty or over sized')
        if response[2] != self.info_hash:
            raise ProtocolError('info_hash mismatch in handshake')

        self.remote_id = response[3]
        logging.info('Handshake successful')

        return buff[hand_shake_length:]


# class HandShake:
#     length = 68
#
#     def __init__(self, info_hash: bytes, peer_id: bytes):
#         self.info_hash = info_hash
#         self.peer_id = peer_id
#
#     def to_bytes(self):
#         struct.pack(
#             '>B19s8x20s20s',  # >: Big Endian, B: single byte, 19s: 19 bytes string,
#             # 8x: padded 8 bytes, 20s: 20 bytes string
#             19,
#             b'BitTorrent protocol',
#             self.info_hash,
#             self.peer_id)
#
#     @classmethod
#     def to_handshake(cls, data: bytes):
#         logging.debug('Decoding Handshake of length: {length}'.format(length=len(data)))
#         if len(data) != 68:
#             logging.debug('Handshake message length != 68, cannot decode')
#             return None
#         s = struct.unpack('>B19s8x20s20s', data)
#         return cls(info_hash=s[2], peer_id=s[3])


class ProtocolError(BaseException):
    pass






