import socket
import struct
import time
import threading

# Multicast group and port
GROUP = "224.3.29.71"
PORT = 8888
ADDRESS = "localhost"

# Producer
def producer(temperatures):
    # Create multicast socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ADDRESS,8000))
    # Send temperatures in multicast
    for temperature in temperatures:
        message = f"Temperature: {temperature}"
        sock.sendto(message.encode(), (ADDRESS, PORT))
        print(f"Sent message: {message}")
        time.sleep(1)

# Consumer
def consumer():
    # Create multicast socket and join group
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ADDRESS, PORT))
    # mreq = struct.pack("4sl", socket.inet_aton(GROUP), socket.INADDR_ANY)
    # sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Receive messages in an endless loop
    while True:
        data, (addr,port) = sock.recvfrom(1024)
        message = data.decode()
        print(f"Received message: {message}")

# Example usagE
parameters = [25.0, 26.5, 28.0]
t_producer = threading.Thread(target=producer, args=(parameters,))
t_producer.start()
t_consumer= threading.Thread(target=consumer)
t_consumer.start()


#producer([25.0, 26.5, 28.0])