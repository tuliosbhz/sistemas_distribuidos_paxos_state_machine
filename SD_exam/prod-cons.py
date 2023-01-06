import socket
import struct
import threading
import time

GROUP = "227.5.6.87"
PORT = 5555

def producer(values):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    
    for value in values:
        result = sock.sendto(str(value).encode(), (GROUP, PORT))
        print(f"Sended multicast message: {value} and result: {result}")
        time.sleep(1)

def consumer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((GROUP,PORT))
    mreq = struct.pack("4sl", socket.inet_aton(GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, addr = sock.recvfrom(1024)
        if data:
            print(f"Received from {addr} the data: {data.decode()}")
        else:
            print("Nothing received")

prod_param = [5, 4, 3, 2, 1, "BOOM"]
prod = threading.Thread(target=producer, args=(prod_param,))
cons = threading.Thread(target=consumer)
cons.start()
prod.start()

