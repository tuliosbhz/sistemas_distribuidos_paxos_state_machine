from __future__ import annotations
# /etc/init.d/charge_point.py
### BEGIN INIT INFO
# Provides:          charge_point.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO
##Imports for the State machine OO
from abc import ABC, abstractmethod
#from gzip import _OpenTextMode
import inspect
from stat import filemode

import charge_point as cp
import asyncio
import random
import datetime
import sys
import logging as log
open(file="/home/pi/inesc-ocpp2.0.1/logs/fsm_logs_info.txt", mode="a+")
log.basicConfig(filename="/home/pi/inesc-ocpp2.0.1/logs/fsm_logs_info.txt", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = log.getLogger()
logger.addHandler(log.StreamHandler(sys.stdout))
logger.setLevel(log.INFO)
import db_ocpp_methods as ocppdb

# The common state interface for all the states
class State(ABC):

    def __new__(cls, *arg, **kwargs):
        # get all coros of A
        parent_coros = inspect.getmembers(State, predicate=inspect.iscoroutinefunction)

        # check if parent's coros are still coros in a child
        for coro in parent_coros:
            child_method = getattr(cls, coro[0])
            if not inspect.iscoroutinefunction(child_method):
                raise RuntimeError('The method %s must be a coroutine' % (child_method,))

        return super(State, cls).__new__(cls, *arg, **kwargs)
    
    @property
    def charge_point(self) -> cp.ChargePoint:
        return self._chargepoint

    @charge_point.setter
    def charge_point(self, chargepoint: cp.ChargePoint) -> None:
        self._chargepoint = chargepoint

    @abstractmethod
    async def send_message_to_CSMS(self) :
        pass

    @abstractmethod
    async def transition(self):
        pass

# Initial state to start the cold boot
class stateBoot(State):

    status = None

    async def send_message_to_CSMS(self):
        log.info("STATE: Boot")
        log.info("Boot notification message sended")
        await self.transition()
    
    async def transition(self):
        if self.charge_point.powerUpStatus == True:
            #self.response = await self.charge_point.send_status_notification()
            self.charge_point.setStateCP(stateWaitCar())

class stateWaitCar(State):

    response: str
    newSessionCheck: bool = False

    async def send_message_to_CSMS(self) :
        if self.charge_point.changedState == True:
            log.info("Wait for EV to be plugged in")
        await self.transition()

    async def transition(self):
        if self.charge_point.connectorStatus == "Occupied":
            self.charge_point.triggerReason = "CablePluggedIn"
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Updated', trigger_reason=self.charge_point.triggerReason)
            self.charge_point.setStateCP(stateWaitSession())

class stateWaitSession(State):

    response: str
    change_mode: bool = False
    charge_mode: str = "not_selected"
    new_charge_mode: bool = None

    async def send_message_to_CSMS(self):
        if self.charge_point.changedState == True:
            log.info("Waiting for HLC STATE")
        self.charge_mode, self.new_charge_mode = ocppdb.read_chargemode(self.charge_point.sessionId, self.charge_mode)
        print("self.charge_mode:", self.charge_mode)
        await self.transition()

    async def transition(self):
        if self.charge_point.connectorStatus == "Faulted":
            self.charge_point.setStateCP(stateError())
        elif self.charge_point.connectorStatus == "Charging":
            if await self.check_mode():
                self.charge_point.setStateCP(stateEnergyDelivery())
        elif self.charge_point.connectorStatus == "Available":
            self.charge_point.triggerReason = "ChargingStateChanged"
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Updated', trigger_reason=self.charge_point.triggerReason)
            self.charge_point.setStateCP(stateWaitCar())
        elif self.charge_point.connectorStatus == "Occupied":
            result = self.check_mode()
            if result == True:
                self.triggerReason = "EVDetected"        
                await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Updated', trigger_reason=self.charge_point.triggerReason)
                self.charge_point.setStateCP(stateSetup())
            elif result == False:
                self.charge_point.setStateCP(stateBasicCharging())
    
    def check_mode(self):
        if self.new_charge_mode == True:
            if self.charge_mode == "llc_only":
                return False
            elif self.charge_mode == "hlc_only" or self.charge_mode == "hlc_c":
                return True
        else:
            return -1

        

class stateBasicCharging(State):
    response: str
    charge_mode: str = "not_selected"
    new_charge_mode: bool = None

    async def send_message_to_CSMS(self) :
        self.charge_mode, self.new_charge_mode = ocppdb.read_chargemode(self.charge_point.sessionId)
        await self.transition()

    async def transition(self):
        if self.charge_point.connectorStatus == "Faulted":
            self.charge_point.setStateCP(stateError())
        elif self.charge_point.connectorStatus == "Available":
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Updated', trigger_reason=self.charge_point.triggerReason)
            self.charge_point.setStateCP(stateWaitCar())
        elif self.charge_mode == "hlc_only" or self.charge_mode == "hlc_c":
            self.charge_point.setStateCP(stateSetup())
        elif self.charge_point.connectorStatus == "Occupied":
            iec_simple_coroutine = asyncio.create_task(self.charge_point.simple_routine())
            await iec_simple_coroutine
            #self.charge_point.setStateCP(stateWaitSession()) #TODO: Implement in the database the paramenters of session to be updated even in basic charging mode
        return

class stateSetup(State):

    response: str

    async def send_message_to_CSMS(self):
        self.charge_point.sessionId,  self.charge_point.sessionStatus, newSessionId = ocppdb.read_lastsessionid(self.charge_point.sessionId)
        self.charge_point.id_token_info, info_check = ocppdb.read_authorize(lastsessionid=self.charge_point.sessionId) #Check if
        if info_check == False or newSessionId == True : #If a new sessionID have been identified, info_check is True if already have been writen in this session
            ocppdb.write_authorize_token(idTokenInfo= "Rejected", lastsessionid=self.charge_point.sessionId)
        await self.transition()
 
    async def transition(self):
        if self.charge_point.hlc_state >= 10: #wait_AuthorizationReq
            self.charge_point.setStateCP(stateAuthorization())

class stateAuthorization(State):
    
    response: str

    async def send_message_to_CSMS(self):
        if self.charge_point.id_token_type != "Central":
            self.response = await self.charge_point.send_authorize()
        else:
            #await asyncio.sleep(2)
            log.info("ChargePoint: Waiting for Authorization from CSMS")
        await self.transition()

    async def transition(self):
        if self.charge_point.on_requeststarttransaction == True:
            self.charge_point.setStateCP(stateRemoteRequestStart())
            self.charge_point.on_requeststarttransaction = False
        elif self.charge_point.connectorStatus == "Available": #EV PLUGGED OUT
            self.charge_point.triggerReason = "ChargingStateChanged"
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Updated', trigger_reason=self.charge_point.triggerReason)
            self.charge_point.setStateCP(stateWaitCar())
        elif self.charge_point.triggerReason == "Authorized": #hlc_state == 11(process_AuthorizationReq)
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Updated', trigger_reason=self.charge_point.triggerReason)
            self.charge_point.setStateCP(stateNotifyEvNeeds())
#Sends the EV needs to the CSMS. In case of success go to stateWaitProfile() 
class stateNotifyEvNeeds(State):
    
    response: dict = None
    ev_notify_needs_sended: bool = False

    async def send_message_to_CSMS(self) :
        requestedEnergyTransfer, eAmount, evMinCurrent, evMaxCurrent, evMaxVoltage, departureTime = ocppdb.read_evchargingneeds(self.charge_point.sessionId)
        if (eAmount != 0) and (self.charge_point.sessionStatus == "EvNeedsStarted"):
            self.response = await self.charge_point.send_notifyevchargingneeds()
            self.ev_notify_needs_sended = True
        elif eAmount == 0:
            log.info("Energy Amount is 0: EV do not request any energy")
            
        await self.transition()

    async def transition(self):
        if self.ev_notify_needs_sended == True:
            if self.response.status == "Accepted": 
                self.charge_point.setStateCP(stateWaitProfile())
        # elif self.charge_point.hlc_state < 11:
        #     self.charge_point.setStateCP(stateNotifyEvNeeds())
        elif self.charge_point.sessionStatus == "Finished" or self.charge_point.sessionStatus == "NotInitialized":
            self.charge_point.setStateCP(stateEndTransaction())
        elif self.charge_point.connectorStatus == "Available":
            log.info("Car Not Connected")
            self.charge_point.setStateCP(stateWaitCar())
        elif self.charge_point.hlc_state == 17 or self.charge_point.hlc_state == 19:
            #Update variables about charging profile that is already started
            ocppdb.read_chargingprofile(self.charge_point.chargingProfile,1,self.charge_point.sessionId)
            if self.charge_point.chargingProfile['charging_schedule'][0]['charging_schedule_period'][0]['start_period'] != None:
                self.charge_point.meterValuesPeriod = 1 # Initialize value
                self.charge_point.setStateCP(stateEnergyDelivery())


# State that waits for the Charging Profile from the CSMS
class stateWaitProfile(State):
    response: str

    async def send_message_to_CSMS(self) :
        await self.transition()

    async def transition(self):
        #Condition to go to the next state
        # if self.charge_point.on_requeststarttransaction == True:
        #     self.charge_point.setStateCP(stateRemoteRequestStart())
        #     self.charge_point.on_requeststarttransaction = False
        if self.charge_point.connectorStatus == "Available":
            log.info("Car Not Connected")
            self.charge_point.setStateCP(stateWaitCar())
        elif self.charge_point.sessionStatus == "Finished" or self.charge_point.sessionStatus == "NotInitialized" or self.charge_point.hlc_state < 10:
            self.charge_point.setStateCP(stateEndTransaction())
        elif self.charge_point.on_setchargingprofile == True:
            ocppdb.update_chargingprofile(self.charge_point.sessionId, self.charge_point.chargingProfileID)
            if self.charge_point.chargingState == "Charging":
                self.charge_point.on_setchargingprofile = False
                self.charge_point.triggerReason = "ChargingStateChanged"
                await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Started', trigger_reason=self.charge_point.triggerReason)
                log.info("Transition to Energy Delivery")
                self.charge_point.meterValuesPeriod = 1 # Initialize value
                self.charge_point.setStateCP(stateEnergyDelivery())
            else:
                log.info("CSMS sended chargingProfile but not Charging Yeat")

            #elif self.charge_point.chargingState == "EvNeedsStarted":
        #elif self.charge_point.sessionStatus == "NotInitialized":
        #    self.charge_point.setStateCP(stateOne())
        # else:
        #     log.info("Waiting for charging profile from CSMS")
        #     await asyncio.sleep(0.5)
        #     self.charge_point.setStateCP(stateWaitProfile())
        

        #if self.charge_point.chargingState == "Charging":
            
#Charging state
class stateEnergyDelivery(State):
    
    response: str
    charging_counter: int = 0
    meter_values = [
                {'timestamp':datetime.datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S '), 
                'sampled_value':[
                {'value': float(0),'unitOfMeasure':{'unit':'Wh','multiplier':0}}, #Energy
                {'value': float(0),'unitOfMeasure':{'unit':'V','multiplier':0}},  #Voltage
                {'value': float(0),'unitOfMeasure':{'unit':'Hz','multiplier':0}}, #Frequency
                {'value': float(0),'unitOfMeasure':{'unit':'A','multiplier':0}},  #Current
                {'value': float(0),'unitOfMeasure':{'unit':'W','multiplier':0}}]}]#Power

    async def send_message_to_CSMS(self):
        if self.charge_point.changedState == True:
            log.info("ChargingStatus", self.charge_point.chargingState)
            ocppdb.write_requeststopcharging(self.charge_point.chargingProfileID, timesupstatus=0)
            await self.process_charging_profile()
        #for i in range(0,10):
        if self.charging_counter >= 9:
            self.charge_point.triggerReason = "EnergyLimitReached"
        else:
            self.charging_counter += 1
        await self.transition()
        #await asyncio.sleep(self.charge_point.meterValuesPeriod) #Not a good practice if changes happen
        
    # if up button is pushed nothing should happen
    async def transition(self):
        if (self.charge_point.triggerReason == "EnergyLimitReached") or (self.charge_point.hlc_state <= 15) or (self.charge_point.hlc_state > 19):
            self.charge_point.on_sendmetervalues = False
            ocppdb.write_requeststopcharging(self.charge_point.chargingProfileID, timesupstatus=1)
            self.charge_point.setStateCP(stateEndTransaction())
        elif self.charge_point.chargingState != "Charging":
            self.charge_point.triggerReason = "ChargingStateChanged"
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Ended', trigger_reason=self.charge_point.triggerReason)
            self.charge_point.setStateCP(stateEndTransaction())
        elif self.charge_point.on_sendmetervalues == True:
            energy, voltage, current, power = ocppdb.read_metervalues()
            self.charge_point.meterValues=[
                {'timestamp':datetime.datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S '), 
                'sampled_value':[
                {'value': float(energy),'unitOfMeasure':{'unit':'Wh','multiplier':0}},
                {'value': float(voltage),'unitOfMeasure':{'unit':'V','multiplier':0}},
                {'value': float(random.randint(49,51)),'unitOfMeasure':{'unit':'Hz','multiplier':0}},
                {'value': float(current),'unitOfMeasure':{'unit':'A','multiplier':0}},
                {'value': float(power),'unitOfMeasure':{'unit':'W','multiplier':0}}]}]
            await self.charge_point.send_meter_values()
        elif self.charge_point.sessionStatus == "Finished" or self.charge_point.sessionStatus == "NotInitialized":
            self.charge_point.setStateCP(stateEndTransaction())
    
    async def process_charging_profile(self):
        #self.triggerReason = "ChargingStateChanged"
        energy = 0
        self.charge_point.chargingInterval = 0
        #Follow here the charging profile defined in transaction
        #self.chargingProfile['schedule']
        log.info("Charging Schedule received, starting scheduled charging")
        len_schedule = len(self.charge_point.chargingProfile['charging_schedule'])
        #self.charge_point.scheduleInterval = range(len_schedule)
        log.info("Quantidade de Schedules recebidos: %d",len_schedule)
        #self.chargingProfile['charging_schedule'][schedule_index]['charging_rate_unit']

        
        #Following the schedule based on time
        for schedule_index in range(len_schedule):
            
            startTime = self.charge_point.chargingProfile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['start_period']
            
            if schedule_index + 1 < len_schedule:
                stopTime = self.charge_point.chargingProfile['charging_schedule'][schedule_index + 1]['charging_schedule_period'][0]['start_period']
            else: 
                stopTime = self.charge_point.chargingProfile['charging_schedule'][0]['duration']
            
            self.charge_point.curr_schedule_index = schedule_index
            self.charge_point.scheduleInterval.append(int(stopTime - startTime)) #Tempo de duração do Schedule atual
            self.charge_point.chargingInterval += self.charge_point.scheduleInterval[schedule_index] #Tempo total de duração do carregamento
            
            log.info("Schedule atual tem o inicio em: %d | Fim em: %d |  Duração de: %d s", startTime, stopTime, self.charge_point.scheduleInterval[schedule_index])
            
            #---------------------------------------- Generating Meter Values based on Charging Profile -------------------------------------------------------#
            self.charge_point.meterValuesPeriod = self.charge_point.scheduleInterval[schedule_index] / 10
            #frequency = random.randint(49,51)
            energy += energy
            # voltage = random.randint(225,250)
            # len_schedule = len(self.charge_point.chargingProfile['charging_schedule'])
            # if self.charge_point.chargingProfile['charging_schedule'][schedule_index]['charging_rate_unit'] == 'A':
            #     current = self.charge_point.chargingProfile['charging_schedule'][self.charge_point.curr_schedule_index]['charging_schedule_period'][0]['limit'] + random.randint(-2,1)
            #     power = current * voltage
            # elif self.charge_point.chargingProfile['charging_schedule'][schedule_index]['charging_rate_unit'] == 'W':
            #     power = self.charge_point.chargingProfile['charging_schedule'][self.charge_point.curr_schedule_index]['charging_schedule_period'][0]['limit']
            #     voltage = 230
            #     current = power / voltage
            
        #await asyncio.sleep(stopTime - startTime)
        
        #self.charge_point.triggerReason = "EnergyLimitReached" #trigger to end the transaction


class stateEndTransaction(State):
    response: str

    async def send_message_to_CSMS(self) :
        if self.charge_point.connectorStatus == "Available": #Plug of car disconected after the transaction ended
            self.charge_point.eventType = "Ended"
            self.charge_point.chargingState = "SuspendedEV"
            self.charge_point.connectorStatus = "Unavailable"
            self.charge_point.triggerReason = "EVDeparted"
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type=self.charge_point.eventType, trigger_reason='ChargingStateChanged')
        else:
            log.info("Car still connected after the transaction is over: Waiting disconnection")
            await asyncio.sleep(2)
        await self.transition()
    # if up buttINFO:ocpp:CP_0ransition to STATE SEVEN")
    async def transition(self):
        #Condition to go to the next state
        if self.charge_point.eventType == "Ended":
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Ended', trigger_reason='ChargingStateChanged')
            await asyncio.sleep(20)
            self.charge_point.setStateCP(stateWaitCar())
        elif (self.charge_point.sessionStatus == "NotInitialized") or (self.charge_point.sessionStatus == "Finished"):
            await asyncio.sleep(20)
            self.charge_point.setStateCP(stateWaitCar())
            #self.charge_point.setStateCP(stateOne())
        # else: 
        #      self.charge_point.setStateCP(stateEndTransaction())

class stateIdle(State):
    response: str

    async def send_message_to_CSMS(self) :
        log.info("Charging Point: Idle mode")
        self.charge_point.chargingState = "Idle"
        await asyncio.sleep(2)
        
        await self.transition()
    # if up button is pushed nothing should happen
    async def transition(self):
        log.info("Transition from Idle State to any")
        #Condition to go to the next state
        if self.charge_point.connectorStatus == "Unavailable" or "Available":
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Ended', trigger_reason='ChargingStateChanged')
            self.charge_point.setStateCP(stateWaitCar())

class stateError(State):
    response: str

    async def send_message_to_CSMS(self) :
        log.info("Charging Point: Error mode")
        await asyncio.sleep(2)
        await self.transition()
    # if up button is pushed nothing should happen
    async def transition(self):
        #Condition to go to the next state
        if self.charge_point.chargingState != "SuspendedEVSE":
            await self.charge_point.send_transaction_event(charging_state = self.charge_point.chargingState, event_type='Ended', trigger_reason='ChargingStateChanged')
            self.charge_point.setStateCP(stateWaitCar())