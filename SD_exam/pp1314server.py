import pp1314classes as classes
import sys
import time 

#To use multiple connections simultaneously need to use threads or asyncronous method
def main(argv):
    server = classes.Server(host='localhost',port=int(argv[1]))
    while True:
        try:
            client_socket = server.accept_client() #Receives only one client per exchange of messagese, but can handle different clients
            while True:
                print("Waiting  to receive from clients")
                data = client_socket.recv(1024)
                if data:
                    print("Sending message from request")
                    client_socket.send(str.encode(argv[2]))
                    time.sleep(2)
                else:
                    print("No more data from the client")
                    break
            client_socket.close()
        except BrokenPipeError:
            print("Client disconnected")
            client_socket.close()
            pass

if __name__ == "__main__":
   main(sys.argv)