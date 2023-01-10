import json
import socket
import threading
import logging as log
import time

log.basicConfig
# Constants
NUM_CHARGING_STATIONS = 3

# Charging station class
class ChargingStation:
  def __init__(self, station_id):
    self.station_id = station_id
    self.accepted_reservation = None
    self.promised = False
    self.highest_proposal_num = 0

  def on_prepare(self, proposal_num):
    if proposal_num > self.highest_proposal_num:
      self.highest_proposal_num = proposal_num
      self.promised = True
      return ("promise", self.accepted_reservation)
    else:
      return ("reject",)

  def on_accept(self, proposal_num, reservation):
    if self.promised and proposal_num >= self.highest_proposal_num:
      self.accepted_reservation = reservation
      self.promised = False
      self.highest_proposal_num = 0
      return ("acknowledge",)
    else:
      return ("reject",)

# Central system class (continued)
class CentralSystem:
  def __init__(self):
    self.proposal_num = 0
    self.charging_stations = [ChargingStation(i) for i in range(NUM_CHARGING_STATIONS)]

  def reserve_charging_station(self, station_id, start_time, end_time):
    self.proposal_num += 1

    # Send prepare message to all charging stations
    responses = []
    for station in self.charging_stations:
      log.info(f"Going to connect to {station.station_id}")
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        s.connect(("localhost", station.station_id))
        s.sendall(json.dumps(("prepare", self.proposal_num)).encode())
        response = json.loads(s.recv(1024).decode())
        s.close()
        responses.append(response)
      except:
        log.info("Error trying to connect")
    else:
      log.info("Station ID does not exist")

    # Check for majority of promise responses
    num_promises = sum(response[0] == "promise" for response in responses)
    if num_promises > NUM_CHARGING_STATIONS / 2:
      # Send accept message to all charging stations
      reservation = (station_id, start_time, end_time)
      for station in self.charging_stations:
        log.info(f"Sending to {station.station_id} the accept")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
          s.connect(("localhost", station.station_id))
          s.sendall(json.dumps(("accept", self.proposal_num, reservation)).encode())
          s.close()
        except:
          log.info("Error trying to connect")

      # Wait for majority of acknowledge responses
      num_acknowledgments = 0
      for response in responses:
        if response[0] == "acknowledge":
          num_acknowledgments += 1
      if num_acknowledgments > NUM_CHARGING_STATIONS / 2:
        # Consensus reached
        return True
    return False

# Charging station server class
class ChargingStationServer:
  def __init__(self, station_id):
    self.station_id = station_id
    self.charging_station = ChargingStation(station_id)

  def run(self):
    # Create socket and bind to port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    #s.settimeout(50)
    s.bind(("localhost", self.station_id))
    s.listen()

    # Wait for incoming connections
    while True:
      try:
        conn, addr = s.accept()
        data = conn.recv(1024)
        if not data:
          continue
        # Process request
        request = json.loads(data.decode())
        request_type = request[0]
        if request_type == "prepare":
          log.info(f"Node{self.station_id} receveid prepare message")
          response = self.charging_station.on_prepare(request[1])
        elif request_type == "accept":
          log.info(f"Node{self.station_id} receveid prepare message")
          response = self.charging_station.on_accept(request[1], request[2])
        else:
          response = ("error",)
        # Send response
        conn.sendall(json.dumps(response).encode())
        conn.close()
      except TimeoutError:
        log.info("Timeout")
        conn.close()
      time.sleep(0.5)

node1 = ChargingStationServer(0)
node2 = ChargingStationServer(1)
node3 = ChargingStationServer(2)

nodeCentral = CentralSystem()

task_node1 = threading.Thread(target=node1.run)
task_node2 = threading.Thread(target=node2.run)
task_node3 = threading.Thread(target=node3.run)
task_central = threading.Thread(target=nodeCentral.reserve_charging_station, args=(0,0,3,))

task_node1.start()
task_node2.start()
task_node3.start()
time.sleep(2)
task_central.start()

# while True:
#   try:
#     nodeCentral.reserve_charging_station(station_id=0, start_time=0, end_time=3)
#   except ConnectionRefusedError:
#     log.info("Connection refused")
#     continue
#   time.sleep(1)
