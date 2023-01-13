import json
import socket
import threading
import logging as log
import time

# Script settings
CHARGING_STATIONS_COUNT = 3
BASE_PORT = 18500

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
    self.charging_stations_ids = [x for x in range(CHARGING_STATIONS_COUNT)]

  def reserve_charging_station(self, station_id, start_time, end_time):
    self.proposal_num += 1

    # Send prepare message to all charging stations
    responses = []
    for station_id in self.charging_stations_ids:
      print(f"Going to connect to {station_id}")
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        s.connect(("localhost", BASE_PORT + station_id))
        s.sendall(json.dumps(("prepare", self.proposal_num)).encode())
        response = json.loads(s.recv(1024).decode())
        s.close()
        responses.append(response)
        print("Receveid response from prepare:", responses)
      except:
        print("Error trying to connect")
    # else:
    #   print("Station ID does not exist")

    # Check for majority of promise responses
    num_promises = sum(response[0] == "promise" for response in responses)
    if num_promises > CHARGING_STATIONS_COUNT / 2:
      # Send accept message to all charging stations
      reservation = (station_id, start_time, end_time)
      for station_id in self.charging_stations_ids:
        print(f"Sending to {station_id} the accept")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
          s.connect(("localhost", BASE_PORT + station_id))
          s.sendall(json.dumps(("accept", self.proposal_num, reservation)).encode())
          s.close()
        except:
          print("Error trying to connect")

      # Wait for majority of acknowledge responses
      num_acknowledgments = 0
      for response in responses:
        if response[0] == "acknowledge":
          num_acknowledgments += 1
      if num_acknowledgments > CHARGING_STATIONS_COUNT / 2:
        # Consensus reached
        return True
    return False

# Charging station server class
class ChargingStationServer:
  def __init__(self, station_id):
    self.station_id = station_id
    self.charging_station = ChargingStation(station_id)

  def run(self):
    # Create socket and bind to BASE_port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    #s.settimeout(50)
    s.bind(("localhost", BASE_PORT + self.station_id))
    s.listen()
    time.sleep(1)
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
          print(f"Node{self.station_id} receveid prepare message")
          response = self.charging_station.on_prepare(request[1])
        elif request_type == "accept":
          print(f"Node{self.station_id} receveid accept message")
          response = self.charging_station.on_accept(request[1], request[2])
        else:
          response = ("error",)
        # Send response
        conn.sendall(json.dumps(response).encode())
        conn.close()
      except TimeoutError:
        print("Timeout")
        conn.close()
      time.sleep(0.5)

nodeCentral = CentralSystem()
task_central = threading.Thread(target=nodeCentral.reserve_charging_station, args=(0,0,3,))

nodes = []
tasks = []

for i in range(CHARGING_STATIONS_COUNT):
  nodes.append(ChargingStationServer(i))
  tasks.append(threading.Thread(target=nodes[i].run))
  tasks[i].start()

time.sleep(2)

task_central.start()

# while True:
#   try:
#     nodeCentral.reserve_charging_station(station_id=0, start_time=0, end_time=3)
#   except ConnectionRefusedError:
#     print("Connection refused")
#     continue
#   time.sleep(1)
