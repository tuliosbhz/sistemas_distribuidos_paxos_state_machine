import socket

# Constants
NUM_NODES = 5
PROPOSER_ID = 0

# Node class
class Node:
  def __init__(self, node_id):
    self.node_id = node_id
    self.accepted_value = None
    self.promised = False
    self.highest_proposal_num = 0

  def on_prepare(self, proposal_num):
    if proposal_num > self.highest_proposal_num:
      self.highest_proposal_num = proposal_num
      self.promised = True
      return ("promise", self.accepted_value)
    else:
      return ("reject",)

  def on_accept(self, proposal_num, value):
    if self.promised and proposal_num >= self.highest_proposal_num:
      self.accepted_value = value
      self.promised = False
      self.highest_proposal_num = 0
      return ("acknowledge",)
    else:
      return ("reject",)

# Proposer class
class Proposer:
  def __init__(self, node_id):
    self.node_id = node_id
    self.proposal_num = 0

  def propose(self, value):
    self.proposal_num += 1

    # Send prepare message to all nodes
    responses = []
    for node_id in range(NUM_NODES):
      if node_id == self.node_id:
        continue
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(("localhost", node_id))
      s.sendall(("prepare", self.proposal_num))
      response = s.recv(1024)
      s.close()
      responses.append(response)

    # Check for majority of promise responses
    num_promises = sum(response[0] == "promise" for response in responses)
    if num_promises > NUM_NODES / 2:
      # Send accept message to all nodes
      for node_id in range(NUM_NODES):
        if node_id == self.node_id:
          continue
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", node_id))
        s.sendall(("accept", self.proposal_num, value))
        s.close()

      # Wait for majority of acknowledge responses
      num_acknowledgments = 0
      for response in responses:
        if response[0] == "acknowledge":
          num_acknowledgments += 1
      if num_acknowledgments > NUM_NODES / 2:
        # Consensus reached
        return True
    return False

# Acceptor class
class Acceptor:
  def __init__(self, node_id):
    self.node_id = node_id
    self.node = Node(node_id)

  def run(self):
    # Create socket and bind to port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", self.node_id))
    s.listen()

    # Wait for incoming connections
    while True:
      conn, addr = s.accept()
      data = conn.recv(1024)
      if not data:
        break

      # Process request
      request_type = data[0]
      if request_type == "prepare":
        response = self.node.on_prepare(data[1])
      elif request_type == "accept":
        response = self.node.on_accept(data[1], data[2])
      else:
        response = ("error",)

      # Send response
      conn.sendall(response)

      conn.close()

node0 = Proposer(0)
node1 = Acceptor(1)
node2 = Acceptor(2)
node3 = Acceptor(3)
node4 = Acceptor(4)
node4 = Acceptor(5)


