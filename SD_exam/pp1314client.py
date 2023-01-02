import pp1314classes as classes
import sys 
import time


def main(argv):
    counter = 0
    client = classes.Client(host=argv[1], port=int(argv[2]))
    while True:
        message = str(counter)
        print(f"Message sended: {message}")
        client.send_message(message)
        response = client.receive_message()
        print(f"Response from server {response}")
        counter += 1
        time.sleep(5)

if __name__ == "__main__":
    main(sys.argv)