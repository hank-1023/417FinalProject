import asyncio
import logging

import bitstring as bitstring
import cls as cls
import pieces_manager

from tracker import *
from asyncio import Queue
import torrent_parser as tp

CHUNK_SIZE = 10240


class PeerConnection:
    def __init__(self, ip: str, port: int, info_hash,
                 peer_id, pieces_manager, block_callback=None):
        self.ip = ip
        self.port = port
        self.my_state = []
        self.peer_state = []
        # self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.piece_manager = pieces_manager
        self.writer = None
        self.reader = None
        self.on_block_cb = block_callback
        # self.future = asyncio.ensure_future(self.start())

        self.stop_connection = False

    async def start(self):
        ip, port = self.ip, self.port
        logging.info('Got assigned peer with: {ip}'.format(ip=ip))

        self.reader, self.writer = await asyncio.open_connection(ip, port)
        handshake = await self.initiate_handshake()
        handshake_reset = handshake

        self.my_state.append("choked")
        await self.send_interested()
        self.peer_state.append("interested")
        count = 0

        while not self.stop_connection:
            recv = await self.reader.read(CHUNK_SIZE)
            message = handshake + recv
            try:
                message_length = struct.unpack('>I', message[:4])[0]
                # Choke
                if message_length == 0:
                    # alive
                    pass
                if message_length > 0:
                    message_id = struct.unpack('>b', message[4:5])[0]
                    if message_id == 0:
                        # chock
                        self.my_state.append("choked")
                    elif message_id == 1:
                        if 'choked' in self.my_state:
                            self.my_state.remove('choked')
                    elif message_id == 2:
                        # interested
                        self.peer_state.append("interested")
                    elif message_id == 3:
                        # not interested
                        if 'interested' in self.peer_state:
                            self.peer_state.remove('interested')
                    elif message_id == 4:
                        # have
                        pass
                    elif message_id == 5:
                        # bitfield
                        parts = struct.unpack('>Ib' + str(message_length - 1) + 's', message)
                        raw_bitfield, = struct.unpack(">{}s".format(parts[0] - 1), parts[2])
                        bitfield = bitstring.BitArray(bytes=bytes(raw_bitfield))
                        self.piece_manager.add_peers(self.remote_id, bitfield)
                    elif message_id == 6:
                        # request
                        pass
                    elif message_id == 7:
                        if len(message) != message_length + 4:
                            handshake += recv
                        else:
                            parts = struct.unpack('>IbII' + str(message_length - 9) + 's', message)
                            print(count)
                            count += 1
                            self.my_state.remove('pending_request')
                            self.piece_manager.event_block_received(self.remote_id, parts[2], parts[3], parts[4])
                        pass
                    elif message_id == 8:
                        # cancel
                        pass
                    elif message_id == 9:
                        # port
                        pass
                    if self.piece_manager.completed():
                        self.stop_connection = True
                        self.piece_manager.close()
                        print(self.piece_manager.have_pieces)
                    else:
                        if message:
                            if 'choked' not in self.my_state:
                                if 'interested' in self.peer_state:
                                    if 'pending_request' not in self.my_state:
                                        self.my_state.append('pending_request')
                                        await self.send_request()
                                        handshake = handshake_reset
            except Exception as e:
                logging.exception('An error occurred')
                raise e
            print(len(self.piece_manager.have_pieces))

    async def parse_message(self, message):
        pass

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

    async def send_interested(self):
        message = struct.pack('>Ib',
                              1,  # Message length
                              2  # interested id
                              )
        self.writer.write(message)
        await self.writer.drain()

    async def send_request(self):
        block = self.piece_manager.next_request(self.remote_id)
        message = struct.pack('>IbIII',
                              13,
                              6,
                              block.get_piece_index(),
                              block.get_offset(),
                              block.get_length())
        self.writer.write(message)
        await self.writer.drain()



class ProtocolError(BaseException):
    pass


