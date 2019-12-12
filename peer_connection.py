import asyncio
import logging
import struct
from asyncio import StreamReader

import bitstring as bitstring


class Peer:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.state = PeerState()
        self.has_pieces = []


class PeerState:
    def __init__(self):
        self.am_choking = True  # client is choking this peer
        self.am_interested = False  # client is interested in this peer
        self.peer_chocking = True  # peer is choking this client
        self.peer_interested = False  # peer is interested in this client


class PeerConnection:

    def __init__(self, ip: str, port: int, info_hash,
                 peer_id, piece_manager):
        self.peer = Peer(ip, port)
        self.state = PeerState()
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.writer = None
        self.reader = None
        self.request_sent = False
        self.piece_manager = piece_manager

    async def start(self):
        ip, port = self.peer.ip, self.peer.port
        print('PeerConnection Got assigned peer with: {ip}'.format(ip=ip))

        self.reader, self.writer = await asyncio.open_connection(ip, port)
        buffer = await self.initiate_handshake()

        await self.send_interested()
        self.state.peer_interested = True

        async for peer_message in PeerDataIterator(self.reader, buffer):
            message_len = peer_message.message_len
            message_id = peer_message.message_id
            print("Received message: " + str(message_id))

            payload = peer_message.payload

            if message_id == 0:
                continue
            elif message_id == 1:  # peer unchock
                self.state.peer_chocking = False
            elif message_id == 2:  # peer interested
                self.state.peer_interested = True
            elif message_id == 3:  # peer not interested
                self.state.peer_interested = False
            elif message_id == 4:  # Have
                have_index = struct.unpack('>I', payload)[0]
                self.peer.has_pieces.append(have_index)
            elif message_id == 5:  # bitfield
                bitfield = struct.unpack('>' + str(message_len - 1) + 's', payload)[0]
                b = bitstring.BitArray(bytes=bitfield)
            elif message_id == 6:
                pass
            elif message_id == 7:  # piece
                data = struct.unpack('>II' + str(message_len - 9) + 's', payload[:message_len + 4])
                index = data[0]
                offset = data[1]
                block = data[2]

                # Can send the next request now
                self.request_sent = False
                # Call to piece manager to process block
                self.piece_manager.event_block_received(index, offset, block)

            elif message_id == 8:  # cancel
                pass

            if self.piece_manager.is_download_completed():
                break
            if not self.state.peer_chocking and not self.request_sent:
                await self.send_request()

    def parse_message(self, message):
        return

    async def initiate_handshake(self):
        packed_bytes = struct.pack(
            '>B19s8x20s20s',  # >: Big Endian, B: single byte, 19s: 19 bytes string,
            # 8x: padded 8 bytes, 20s: 20 bytes string
            19,
            b'BitTorrent protocol',
            self.info_hash,
            self.peer_id.encode('utf-8'))
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

    async def send_interested(self):
        message = struct.pack('>Ib',
                              1,  # Message length
                              2  # interested id
                              )
        self.state.am_interested = True
        self.writer.write(message)
        await self.writer.drain()

    async def send_request(self):
        next_block = self.piece_manager.get_next_block()

        message = struct.pack('>IbIII',
                              13,
                              6,
                              next_block.piece_index,
                              next_block.offset,
                              next_block.length)
        self.writer.write(message)
        await self.writer.drain()


class ProtocolError(BaseException):
    pass


class PeerMessage:
    def __init__(self, message_len: int, message_id: int, payload: bytes = None):
        self.message_len = message_len
        self.message_id = message_id
        self.payload = payload


class PeerDataIterator:
    HEADER_LENGTH = 4

    def __init__(self, reader: StreamReader, buffer):
        self.reader = reader
        self.buffer = buffer

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            try:
                data = await self.reader.read(5)
                message_length = struct.unpack('>I', data[0:4])[0]
                data += await self.reader.read(message_length - 1)
                if data:
                    self.buffer += data
                    message = self.parse_buffer()
                    if message:
                        return message
            except Exception:
                raise StopAsyncIteration()

    def consume_buffer(self, length):
        self.buffer = self.buffer[self.HEADER_LENGTH + length:]

    def parse_buffer(self):
        if len(self.buffer) < self.HEADER_LENGTH:
            return None
        else:
            message_length = struct.unpack('>I', self.buffer[0:4])[0]

            if message_length == 0:
                return PeerMessage(message_length, 0)
            elif len(self.buffer) > message_length:
                message_id = struct.unpack('>b', self.buffer[4:5])[0]
                payload = self.buffer[5: 5 + message_length - 1]
                self.consume_buffer(message_length)
                return PeerMessage(message_length, message_id, payload)
