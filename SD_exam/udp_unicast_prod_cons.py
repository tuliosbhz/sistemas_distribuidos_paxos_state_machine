import socket

# The producer sends messages to the consumer using UDP packets
def producer():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to a specific address and port
    sock.bind(("localhost", 12345))

    # Send a message to the consumer
    message = b"Hello, consumer!"
    sock.sendto(message, ("localhost", 54321))

# The consumer receives messages from the producer using UDP packets
def consumer():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to a specific address and port
    sock.bind(("localhost", 54321))

    # Receive a message from the producer
    data, (source_address, source_port) = sock.recvfrom(1024)
    print(f"Received message from {source_address}:{source_port}: {data}")

# Run the producer and consumer in separate threads
import threading
threading.Thread(target=producer).start()
threading.Thread(target=consumer).start()
