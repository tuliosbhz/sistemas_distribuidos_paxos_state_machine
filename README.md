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
