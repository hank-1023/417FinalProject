import asyncio
import logging
import math
import os
import time
from asyncio import Queue
from collections import namedtuple, defaultdict
from hashlib import sha1
from tracker import *
import struct



class TorrentClient:

    def __init__(self, torrent):
        self.tracker = Tracker(torrent)
        self.peers = []
        self.available_peers = Queue()


