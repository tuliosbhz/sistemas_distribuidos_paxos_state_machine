import pp1314classes as classes
import sys
import time 


def main(argv):
    server = classes.Server(host='localhost',port=int(argv[1]))
    while True:
        try:
            client_socket = server.accept_client()
            while True:
                print("Waiting  to receive from clients")
                client_socket.recv(1024)
                print("Sending message from request")
                client_socket.send(str.encode(argv[2]))
                time.sleep(2)
        except BrokenPipeError:
            print("Client disconnected")
            client_socket.close()
            pass

if __name__ == "__main__":
   main(sys.argv)