import pyaudio
import socket
import threading
import struct
import pickle
import time

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 10

class Audio_Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.address = ("", port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.p = pyaudio.PyAudio()
        self.stream = None

    def __del__(self):
        self.socket.close()
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def run(self):
        print("Audio server started")
        self.socket.bind(self.address)
        self.socket.listen(1)
        client, addr = self.socket.accept()
        print("Remote Audio client successfully connected")
        data = "".encode("utf-8")
        payload_size = struct.calcsize("L")
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  output=True,
                                  frames_per_buffer=CHUNK)
        
        while(True):
            while len(data) < payload_size:
                data += client.recv(81920)
            packed_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("L", packed_size)[0]
            while len(data) < msg_size:
                data += client.recv(81920)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frames = pickle.loads(frame_data)
            for frame in frames:
                self.stream.write(frame, CHUNK)

class Audio_Client(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.address = (ip, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p = pyaudio.PyAudio()
        self.stream = None

    def __del__(self):
        self.socket.close()
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def run(self):
        print("Audio client starts")
        while(True):
            try:
                self.socket.connect(self.address)
                break
            except:
                time.sleep(3)
                continue
        print("Audio client connected")
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)
        while self.stream.is_active():
            frames = []
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = self.stream.read(CHUNK)
                frames.append(data)
            send_data = pickle.dumps(frames)
            try:
                self.socket.sendall(struct.pack('L', len(send_data) + send_data))
            except:
                break