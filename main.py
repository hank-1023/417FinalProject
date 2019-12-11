import argparse
import asyncio
import signal
import logging
from client import *
from connection_proto import *
from DataModel import *
from tracker import *


def main():
    print("start")
    loop = asyncio.get_event_loop()
    print("start")
    client = TorrentClient(Torrent('torrents/1056.txt.utf-8.torrent'))
    task = loop.create_task(client.start())