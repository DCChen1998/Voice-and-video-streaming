import sys
import time
import argparse
from voice import Audio_Server, Audio_Client

parser = argparse.ArgumentParser()

parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=9998)

args = parser.parse_args()

IP = args.host
PORT = args.port

if __name__ == "__main__":
    aserver = Audio_Server(PORT)
    aclient = Audio_Client(IP, PORT)
    aclient.start()

    time.sleep(1)

    aserver.start()

    while True:
        time.sleep(1)
        if not aserver.isAlive() or not aclient.isAlive():
            print("Audio connection lost")
            sys.exit(0)