# sistemas_distribuidos_paxos_state_machine

This project intend to implement a State machine replication based on the paxos algorithm in EV charge points perspective

## Software Arquitecture

### EVSE behaviour emulator

Can be a class called charge point that have some states atributed to them, like:

ChargingPoint.waitingEV
ChargingPoint.beginsession
ChargingPoint.authentication
CharginPoint.energyNegotiation
ChargingPoint.charging
ChargingPoint.endsession
ChargingPoint.restartingsession
ChargingPoint.failure

### Paxos algorithm
