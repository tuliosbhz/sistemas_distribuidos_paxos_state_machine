from threading import Thread
import time

class Process:
    def __init__(self, id, rating):
        self.id = id
        self.rating = rating
        self.leader = False

    def run(self):
        while not self.leader:
            # Check if I am the leader
            if self.is_leader():
                self.leader = True
                print(f"Process {self.id} is the leader")
                break

            # Send request message to all processes with higher rating
            for p in processes:
                print(f"Request message sended by {self.id}")
                if p.rating > self.rating:
                    p.receive_request(self.id)

            # Sleep for a while
            time.sleep(1)

    def receive_request(self, sender_id):
        print(f"Request message received by {self.id}")
        # If I have a higher rating, ignore the request
        if self.rating > self.rating:  # fixed error here
            return

        # If I have the same rating, compare IDs
        if self.rating == self.rating:  # fixed error here
            if self.id > sender_id:
                return

        # Send an ack message back to the sender
        self.send_ack(sender_id)

    def send_ack(self, receiver_id):
        print(f"ACK message sended by {self.id}")
        for p in processes:
            if p.id == receiver_id:
                p.receive_ack()
                break

    def receive_ack(self):
        print(f"ACK message received by {self.id}")
        # If I receive an ack message, it means I am not the leader
        self.leader = False

    def is_leader(self):
        # Check if I am the leader by comparing ratings and IDs
        for p in processes:
            if p.rating > self.rating:
                return False
            if p.rating == self.rating and p.id > self.id:
                return False
        return True

# Create a list of processes
processes = [
    Process(1, 10),
    Process(2, 20),
    Process(3, 15),
    Process(4, 5),
]

# Start all the processes
for p in processes:
    t = Thread(target=p.run)
    t.start()
    time.sleep(5)
