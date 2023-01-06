import socket
import time
import threading

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host,self.port))
        self.server_socket.listen()
    def accept_client(self):
        client_socket, client_address = self.server_socket.accept()
        print(f"Connection accepted with client address {client_address}")
        return client_socket

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.client_socket.connect((self.host, self.port))

    def send_request(self, message):
        self.client_socket.sendall(message.encode())
        print("Sended request to server")
        return

    def receive_response(self):
        data = self.client_socket.recv(1024)
        print(f"Receive response from server: {data}")
        return data
    
    def close_connection(self):
        self.client_socket.close()

def server_routine():
    server = Server("localhost",9999)
    while True:
        client_socket = server.accept_client()
        while True:
            try:
                data = client_socket.recv(1024)
                if data:
                    print(f"Received from client: {data}")
                    client_socket.sendall(data)
                else:
                    print("No data received from client")
                    break
            
            except:
                print("Transation with client over")
                client_socket.close()
        client_socket.close()

def client_routine():
    client = Client("localhost", 9999)
    count = 0
    while True:
        message = f"Sending message number{count}"
        client.send_request(message)
        response = client.receive_response()
        if response:
            print(f"Response received from server {response}")
        else:
            print("No response from server")
        time.sleep(1)
        count += 1

server_thrd =threading.Thread(target=server_routine)
client_thrd = threading.Thread(target=client_routine)

server_thrd.start()
client_thrd.start()


