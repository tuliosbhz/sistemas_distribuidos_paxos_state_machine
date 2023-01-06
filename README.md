# sistemas_distribuidos_paxos_state_machine

This project intend to implement a State machine replication based on the paxos algorithm in EV charge points perspective

The simulation of the EVs behaviour will occurr in a 10 minutes span of time. With the following steps:

- System BootUp, the CPs talks to each other
- Minute 1: EV1 connects
- Minute 2: EV2 connects
- Minute 4: EV3 connects
- Minute 8: EV1 stops charging
- Minute 9: EV2 e EV3 stops charging

## Software Arquitecture

### EV behaviour emulator

Can be a class called charge point that have some states atributed to them, like:

- ev.not_connected
- ev.connected_not_charging
- ev.sendNeeds
- ev.receiveScheduling
- ev.charging_with_profile
- ev.charging_without_profile

### EVSE behaviour emulator

Can be a class called charge point that have some states atributed to them, like:

- ChargingPoint.waitingEV
- ChargingPoint.beginSession
- ChargingPoint.authentication
- CharginPoint.energyNegotiation
- ChargingPoint.charging
- ChargingPoint.endSession
- ChargingPoint.restartingsession
- ChargingPoint.failure

### Paxos algorithm

OCPP (Open Charge Point Protocol) is a communication protocol that is used to manage electric vehicle charging stations. It is based on a client-server architecture, where the charging stations are the clients and the central system is the server.

Here is an example of how Paxos might be used to implement a distributed system using OCPP, with a central system acting as the proposer and the charging stations acting as the acceptors:

A client sends a request to the central system, asking it to reserve a charging station for a specific time period.

The central system sends a "prepare" message to the charging stations, proposing a reservation for a specific charging station at a specific time.

The charging stations respond with a "promise" message, indicating that they will not accept any more reservation proposals until they receive a message from the central system.

The central system sends an "accept" message to the charging stations, proposing a reservation for a specific charging station at a specific time.

The charging stations respond with an "acknowledge" message, indicating that they have accepted the proposed reservation.

Once a majority of the charging stations have acknowledged the proposed reservation, the central system has reached consensus and the reservation is accepted.

The client is notified of the agreed-upon reservation, and the system is ready to handle new requests.

This is just a high-level overview of how Paxos might be used with OCPP. There are many details and variations that are beyond the scope of this answer. If you would like more information about OCPP, I recommend visiting the OCPP website:
