import time

class Node:
    def __init__(self, id, neighbors):
        self.id = id
        self.neighbors = neighbors
        self.leader = None
        self.received_bully = False

    def start_election(self):
        # Broadcast a "Bully" message to all neighbors
        # Reset the received_bully flag
        self.received_bully = False
        print("Process started")
        for neighbor in self.neighbors:
            neighbor.receive_bully(self)

    def receive_bully(self, sender):
        if sender.id > self.id:
            # Discard the message
            print("Discard the message")
            return
        elif sender.id < self.id:
            # Send an ACK message and start a timer
            print(f"Node {self.id} send ACK for Node {sender.id}")
            sender.receive_ack(self)
            self.start_timer()
        else:
            # We are the leader!
            print(f"Node {self.id} was elected leader")
            self.leader = self
            self.received_bully = True
            self.check_election_complete()

    def receive_ack(self, sender):
        # The sender is the leader
        self.leader = sender
        self.received_bully = True
        self.check_election_complete()

    def start_timer(self):
        self.timer = time.time()

    def stop_timer(self):
        if hasattr(self, 'timer'):
            del self.timer

    def check_timer(self):
        if not hasattr(self, 'timer'):
            print(f"The node {self.id} has no timer")
            return
        if time.time() - self.timer > 1:
            # Timer expired, remove the sender from the list of neighbors
            self.neighbors.remove(self.leader)
            self.leader = None
            # Restart the election process
            print(f"Restarting the election on node {self.id}")
            self.start_election()
        else:
            # Timer not expired, do nothing
            pass
    
    def check_election_complete(self):
        print(f"Check election called at Node {self.id}")
        # Check if all nodes have received the "Bully" message
        if all(node.received_bully for node in self.neighbors):
            print("HERE")
            self.stop_election()
            
    def stop_election(self):
        # Stop the timer and remove the leader
        print(f"Stop election called at Node {self.id}")
        self.stop_timer()
        self.leader = None
   
    def remove(self,node_to_remove):
        for index in self.neighbors:
            if node_to_remove.id == self.neighbors[index]:
                print(f"{self.neighbors[index]} removed")
                self.neighbors.pop(index)


node1 = Node(1, [])
node2 = Node(2, [])
node3 = Node(3, [])
node4 = Node(4, [])

# Add neighbors to each node
node1.neighbors = [node2, node3]
node2.neighbors = [node1, node3]
node3.neighbors = [node1, node2, node4]
node4.neighbors = [node3]

# Start the election process on any node
node1.start_election()
time.sleep(5)
node2.start_election()
node3.start_election()
node4.start_election()

print(f"node1 leader: {node1.leader.id}")
print(f"node2 leader: {node2.leader.id}")
print(f"node3 leader: {node3.leader.id}")
print(f"node4 leader: {node4.leader.id}")

# Wait a few seconds for the election to complete
time.sleep(1)

#Print the leader of each node
# while True:
#     try:
#         print(f"node1 leader: {node1.leader.id}")
#         print(f"node2 leader: {node2.leader.id}")
#         print(f"node3 leader: {node3.leader.id}")
#         print(f"node4 leader: {node4.leader.id}")
#         time.sleep(10)
#     except AttributeError:
#         #print("Leader not elected yet")
#         continue
#     time.sleep(20)