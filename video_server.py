import struct
import socket
import threading
import queue
import signal
import sys
import os
import numpy as np
from enum import Enum

class Mode(num):
    data = 2
    payLoad = 1

class RecvThread:
    def __init__(self):
        self.running = True
    
    def close(self):
        self.running = False

    def recv_image(self,src,count):
        while(self.running):
            try:
                request = src[0].recv(81920)
            except:
                continue
            else:
                r_data[count] += request
                if (mode[count] == Mode.payLoad and len(r_data[count] >= payload_size)):
                    mode[count] = Mode.data
                    packed_msg_size = r_data[count][:payload_size]
                    r_data[count] = r_data[count][payload_size:]
                    msg_size = struct.unpack("L",packed_msg_size)[0]
                
                elif (mode[count] == Mode.data and len(r_data[count] >= msg_size)):
                    mode[count] = Mode.payLoad
                    frame = r_data[count][:msg_size]
                    r_data[count] = r_data[count][msg_size:]
                    if(not frame_queue[count].full()):
                        frame_queue[count].put(frame)
                    else:
                        print("Queue full")

def disconnect(ID):
    available[ID] = True;
    threadlist[ID].close()
    threadlist[ID] = None
    NO_THREAD_RUNNING[ID] = True
    frame_queue[ID] = queue.Queue(1)
    clients[ID] = None
    mode[ID] = Mode.payLoad
    r_data[ID] = b""
    print("DIsconnected",ID)

def get_available_ID():
    for ID, a in enumerate(available):
        if a:
            available[ID] = False
            return ID

def send_Image(des_client,ID,data):
    conn = des_client[0]
    addr = des_client[1]
    conn.setblocking(100)
    try:
        conn.sendall(data)
    except:
        print(ID,addr,"has diconnected")
        disconnect(ID)
    conn.setblocking(0)



mode = [Mode.payLoad] * 4
payload_size = struct.calcsize("L")
r_data = [b""] * 4
frame_queue = []
for i in range(4):
    q = queue.Queue(1)
    frame_queue.append(q)

bind_ip = ""
bind_port = 9998
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server.setblocking(0)
server.bind((bind_ip,bind_port))
server.listen(5)
print ("[*] Listening on %s:%d" % (bind_ip, bind_port))
threadlist = [None] * 4
NO_THREAD_RUNNING = [True] * 4
clients = [None] * 4
NEW_CLIENT = True
available = [True] * 4
while (True):
    try:
        client_conn, addr = server.accept()
    except:
        pass
    else:
        NEW_CLIENT = True
        client_conn.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        ID = get_available_ID()
        clients[ID] = (client_conn, addr)
        print ("[*] Acepted connection from: %s:%d" % (addr[0],addr[1]))
        print (ID,available)
    if NEW_CLIENT:
        for ID,src_client in enumerate(clients):
            if(NO_THREAD_RUNNING[ID]):
                Recv = RecvThread
                threads = threading.Thread(target = Recv.recv_image, args = (src_client,ID))
                threads.start()
                threadlist[ID] = Recv
                NO_THREAD_RUNNING[ID] = False
                print("Start recving thread of",ID,src_client[1])
        NEW_CLIENT = False
    for i, frame_q in enumerate(frame_queue):
        if not frame_q.empty():
            frame = frame_q.get()
            for ID, client in enumerate(clients):
                if available[ID]:
                    continue
                if ID != i:
                    data = struct.pack("B",i) + frame
                    send_Image(client, ID, data)
