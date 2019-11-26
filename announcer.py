import urllib
import urllib3
import threading
import time
import bencode
import requests


http = urllib3.PoolManager()

class announcer(threading.Thread):
    peer_id = None
    info_hash = None
    upload = 0
    download = 0
    left = 0
    current = []
    url_i = 0
    url_l = []
    t_interval = []
    tracker_res = None
    trackerid = []
    port = 0
    announced = []
    event = ''
    finished = 0


    def __init__(self, peer_id, info_hash, upload, download, left, url, port):
        threading.Thread.__init__(self)
        self.peer_id = urllib.quote(peer_id)
        self.info_hash = urllib.quote(info_hash)
        self.upload = upload
        self.download = download
        self.left = left
        self.url_l = url
        self.url_i = 0
        self.announce(self.url_l[0][0], "&event=started")
        self.trackerid = None
        self.port = port
        self.finished = 0


    def announce(self, url='', event=''):
        if not url:
            url = self.url_l[self.url_i][0]
        if self.finished:
            self.event = '&event=completed'

        packet = url + "?info_hash=" + self.info_hash + "&peer_id=" + self.peer_id + "&uploaded=" + str(self.uploaded) + "&downloaded=" + str(self.downloaded) + "&left=" + str(self.left) + "&port=" + str(self.port) + "&compact=1"
        if event:
            packet += event
        if self.trackerid:
            packet = packet + "&trackerid=" + self.trackerid
        try:
            response = http.request('GET', packet, timeout=10)
            if url not in self.announced:
                self.announced.append(url)
                self.current.append(time.time())
        except threading.ThreadError:
            if self.url_i > len(self.url_l):
                raise Exception("tracker error")
            self.url_i += 1
            self.announce(self.url_l[self.url_i][0], event)
            return
        if not response:
            print("announcer error")
            return
        try:
            self.tracker_res = bencode.decode(response.data)
        except:
            print("bencode error")
            return
        tr = self.tracker_res
        if len(self.announced) > len(self.t_interval):
            self.t_interval.append(tr["interval"])
        if "tracker id" in tr:
            self.trackerid.append(tr["tracker id"])


    def run(self):
        while True:
            if self.finished:
                break
            #when to stop?
            curr_time = time.time()
            i = 0
            while i < len(self.announced):
                if self.current[i] + self.t_interval[i] < curr_time:
                    self.announce(self.announced[i])
                    self.current[i] = curr_time
            if i == 0: return

    def test2(selfself):
        return