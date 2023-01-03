import socket
import struct
import time
import threading

# Multicast group and port
GROUP = "224.3.29.71"
PORT = 8888

# Producer
def producer(temperatures):
    # Create multicast socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

    # Send temperatures in multicast
    for temperature in temperatures:
        message = f"Temperature: {temperature}"
        sock.sendto(message.encode(), (GROUP, PORT))
        print(f"Sent message: {message}")
        time.sleep(1)

# Consumer
def consumer():
    # Create multicast socket and join group
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((GROUP, PORT))
    mreq = struct.pack("4sl", socket.inet_aton(GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Receive messages in an endless loop
    while True:
        print("here")
        data, addr = sock.recvfrom(1024)
        message = data.decode()
        print(f"Received message: {message}")

# Example usage
t_consumer= threading.Thread(target=consumer)
t_consumer.start()
producer([25.0, 26.5, 28.0])