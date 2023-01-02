# Implement a server and respective client using TCP and the language you prefer. 
# The server should support a single operation: Average, which returns the temperatures average value(received from the sensors)
# Executes indefinitely, waiting for rqeusts from clients and answering them.

# Opens TCP connection socket
# Binds with his own address
# Listen to connection from clients
import socket

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
    def accept_client(self):
        client_socket, client_address = self.server_socket.accept()
        print(f"Connected by {client_address}")
        return client_socket

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host,self.port))
    
    def send_message(self, message:str):
        result = self.client_socket.send(str.encode(message))
        print("Message: ", message, "sended with return code: ", result)

    def receive_message(self):
        data = self.client_socket.recv(1024).decode()
        return data
    
    def close(self):
        self.client_socket.close()



