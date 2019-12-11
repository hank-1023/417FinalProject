import asyncio
import logging
from tracker import *
from asyncio import Queue

CHUNK_SIZE = 10240


class PeerConnection:
    def __init__(self, ip: str, port: int, info_hash,
                 peer_id, block_callback=None):
        self.ip = ip
        self.port = port
        self.my_state = []
        self.peer_state = []
        # self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.writer = None
        self.reader = None
        self.on_block_cb = block_callback
        # self.future = asyncio.ensure_future(self.start())

        self.stop_connection = False

    async def start(self):
        ip, port = self.ip, self.port
        logging.info('Got assigned peer with: {ip}'.format(ip=ip))

        self.reader, self.writer = await asyncio.open_connection(ip, port)
        handshake_data = await self.initiate_handshake()

        self.my_state.append("choked")
        await self.send_interested()
        self.peer_state.append("interested")

        while not self.stop_connection:
            recv = await self.reader.read(CHUNK_SIZE)
            new_buff = handshake_data + recv
            print(new_buff)
            try:
                message_length = struct.unpack('>I', recv[:4])[0]
                # Choke
                if message_length == 0:
                    # alive
                    pass
                if message_length > 0:
                    message_id = struct.unpack('>b', recv[4:5])[0]
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
                        pass
                    elif message_id == 6:
                        # request
                        pass
                    elif message_id == 7:
                        parts = struct.unpack('>IbII' + str(message_length - 9) + 's', recv)
                        print(parts)
                        self.my_state.remove('pending_request')
                        pass
                    elif message_id == 8:
                        # cancel
                        pass
                    elif message_id == 9:
                        # port
                        pass
                    if 'choked' not in self.my_state:
                        if 'interested' in self.peer_state:
                            if 'pending_request' not in self.my_state:
                                self.my_state.append('pending_request')
                                await self.send_request()
            except Exception as e:
                logging.exception('An error occurred')
                raise e

    def parse_message(self, message):
        return

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
        message = struct.pack('>IbIII',
                              13,
                              6,
                              0,
                              0,
                              2 ** 14)
        self.writer.write(message)
        await self.writer.drain()



class ProtocolError(BaseException):
    pass

