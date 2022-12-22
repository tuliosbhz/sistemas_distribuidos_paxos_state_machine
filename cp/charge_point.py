#Insert arguments
import sys
from datetime import datetime

import logging as log
open(file="/home/pi/inesc-ocpp2.0.1/logs/cp_log_debug.txt", mode="a+")
log.basicConfig(filename="/home/pi/inesc-ocpp2.0.1/logs/cp_log_debug.txt", level=log.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filemode="a+")
#log.FileHandler("/home/pi/inesc-ocpp2.0.1/logs/cp_log.txt","a+")
#search the websockets library, if not, print to install it
try:
    import websockets
except ModuleNotFoundError:
    log.info("This example relies on the 'websockets' package")
    log.info("Please install it by running: ")
    log.info(" $ pip install websockets")
    #import sys
    sys.exit(1)

from ocpp.routing import on
from ocpp.routing import after
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from ocpp.v201 import call

import asyncio

#To create the token ID of session
import uuid

import requests #HTTP POST AND PUT
import db_ocpp_methods as ocppdb

from fsm import State
from fsm import stateBoot

import random

class ChargePoint(cp):

    heartbeatInterval: int = None
    sessionId: str = None
    newSessionId: bool = False
    sessionStatus: str = None
    powerUpStatus :bool = None
    evseId: int = None
    tx_start_point: str = None
    tx_stop_point: str = None
    remoteStartId: int = None
    id_token : str = None
    id_token_type: str = None
    id_token_info: str = None
    transaction_id: str = None
    chargingProfile: dict = None
    chargingProfileID: int = None
    # EventTypetype: "enum": ["Ended", "Started", "Updated"]
    eventType: str = None
    # TriggerReasonType: "Authorized","CablePluggedIn","ChargingRateChanged","ChargingStateChanged","Deauthorized","EnergyLimitReached","EVCommunicationLost","EVConnectTimeout","MeterValueClock",
	# "MeterValuePeriodic","TimeLimitReached","Trigger","UnlockCommand","StopAuthorized","EVDeparted","EVDetected","RemoteStop","RemoteStart","AbnormalCondition","SignedDataReceived","ResetCommand"
    triggerReason: str = None
    # ConnectorStatusType: "Available", "Occupied", "Reserved", "Unavailable", "Faulted"
    connectorStatus: str = None
    # ChargingStateType: "Charging", "EVConnected","SuspendedEV","SuspendedEVSE","Idle"
    chargingState: str = None
    energyAmount: int = None #Total energy value that must be transfered to charge the EV
    EVSENominalVoltage: str = None
    EVSENominalPower: str = None
    meterValues: dict = None
    meterValuesPeriod: float = None
    acChargingParameters: dict = None
    chargingInterval: int = None
    scheduleInterval = []
    relayStatus: int = None
    llc_state: str = None
#   error_state = -1, // [V2G-537]
#   wait_supportedAppProtocolReq = 0,
#   process_supportedAppProtocolReq = 1,
#   wait_SessionSetupReq = 2,
#   process_SessionSetupReq = 3,
#   wait_ServiceDiscoveryReq = 4,
#   process_ServiceDiscoveryReq = 5,
#   wait_ServicePaymentSelectionReqORServiceDetailReq = 6,
#   process_ServicePaymentSelectionReqORServiceDetailReq = 7,
#   wait_PaymentDetailsReq = 8,
#   process_PaymentDetailsReq = 9,
#   wait_AuthorizationReq = 10,
#   process_AuthorizationReq = 11,
#   wait_ChargeParameterDiscoveryReq = 12,
#   process_ChargeParameterDiscoveryReq = 13,
#   wait_PowerDeliveryReq = 14,
#   process_PowerDeliveryReq = 15,
#   wait_ChargingStatusReq = 16,
#   process_ChargingStatusReq = 17,
#   wait_MeteringReceiptReq = 18,
#   process_MeteringReceiptReq = 19,
#   wait_SessionStopReq = 20,
#   process_SessionStopReq = 21,
    hlc_state: int = 0
    max_schedule_tuples: int = None
    curr_schedule_index: int = None
    
    #StateVariables
    previousState: State = None
    changedState: bool = None

    #Flags for message received
    on_getvariables: bool = None
    on_onsetchargingprofile: bool = None
    on_getbasereport: bool = None
    on_reset: bool = None
    on_requeststarttransaction: bool = None
    on_requeststoptransaction: bool = None
    on_sendmetervalues: bool = None

    def initialization_meter_values(self, energy = 0, voltage=0,frequency=0,current=0,power=0):
        self.meterValues = [
                {'timestamp':datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S '), 
                'sampled_value':[
                {'value': float(energy),'unitOfMeasure':{'unit':'Wh','multiplier':0}}, #Energy
                {'value': float(voltage),'unitOfMeasure':{'unit':'V','multiplier':0}},  #Voltage
                {'value': float(frequency),'unitOfMeasure':{'unit':'Hz','multiplier':0}}, #Frequency
                {'value': float(current),'unitOfMeasure':{'unit':'A','multiplier':0}},  #Current
                {'value': float(power),'unitOfMeasure':{'unit':'W','multiplier':0}}]}]#Power
        return

    async def charge_point_post(self):
        # defining the api-endpoint
        API_ENDPOINT = "http://vcpes14.inesctec.pt:3003/api/measurements"

        energy, voltage, current, power = ocppdb.read_metervalues()
        self.sessionId, sessionStatus, statuscheck =ocppdb.read_lastsessionid(self.sessionId)

        # data to be sent to api
        data_json = '{"SessionID": "%s", "hlcState": %d, "ChargingState": "%s","Voltage": %d,"Current": %d,"Power": %d,"Energy": %d}'%( self.sessionId,self.hlc_state, self.chargingState, voltage, current, power, energy)
        #data = '{"hlcState": self.hlc_state,"ChargingState": self.chargingState,"Voltage": voltage,"Current": current,"Power": power,"Energy": energy,"SessionId": {sessionID}}'
        header = {"Content-Type": "application/json"}
        log.info(data_json)
        # sending post request and saving response as response object
        r = requests.post(url = API_ENDPOINT, data = data_json, headers=header)

        # extracting response text
        status_code = r.status_code
        pastebin_url = r.text
        log.info("PUT: Error in text:%s and STATUS_CODE: %d"%(pastebin_url, status_code))

    async def charge_point_put(self):
        while True:
            try:
                # defining the api-endpoint
                API_ENDPOINT = "http://vcpes14.inesctec.pt:3003/api/measurements"

                energy, voltage, current, power = ocppdb.read_metervalues()
                self.sessionId, sessionStatus, statuscheck = ocppdb.read_lastsessionid(self.sessionId)

                # data to be sent to api
                data_json = '{"SessionID": "%s","hlcState": %d, "ChargingState": "%s","Voltage": %d,"Current": %d,"Power": %d,"Energy": %d}'%(self.sessionId,self.hlc_state, self.chargingState, voltage, current, power, energy)

                header = {"Content-Type": "application/json"}
                # sending post request and saving response as response object
                r = requests.put(url = API_ENDPOINT, data = data_json, headers=header)

                # extracting response text
                status_code = r.status_code
                pastebin_url = r.text
                log.info("PUT: Error in text:%s and STATUS_CODE: %d"%(pastebin_url, status_code))
            except Exception:
                log.error("")
                await asyncio.sleep(10)
                continue
            await asyncio.sleep(5)
                


#################################################################################################### Interface to FSM ################################################################################################

    #Variable that points to instantiation of state
    _state = None

    # method to change the state of the object
    def setStateCP(self, state: State):
        self.previousState = self._state
        self._state = state
        self._state.charge_point = self
        if self.previousState != state: 
            self.changedState = True

    def presentState(self):
        log.info(f"ChargePoint State is in {type(self._state).__name__}")
        return type(self._state).__name__

    async def send_message_to_CSMS(self):    # the methods for executing the elevator functionality. These depends on the current state of the object.
        await self._state.send_message_to_CSMS()

    async def stateTransition(self):
        log.info("Inside transition function inside ChargePoint")
        await self._state.transition()

####################################################################################################### OCPP MESSAGES ##################################################################################################            
########################################################################################################################################################################################################################
#################################################################################################### Hearthbeat request ################################################################################################        
    async def send_heartbeat(self, interval):
        global cont #Descobriremos
        request = call.HeartbeatPayload()
        while True:
            #log.info("Heartbeat")
            await self.call(request)
            await asyncio.sleep(interval)
                
#################################################################################################### BootNotification request ###########################################################################################
    async def send_boot_notification(self):
        global requestedEnergyTransfer
        #global max_schedule_tuples_aux
        self.button_start=False
        self.button_stop=False
        self.button=False
        self.button_rep=False
        global boot # Flag to indicate PowerUp with CSMS
        #global sessionid
        self.sessionId, self.sessionStatus, newSessionId = ocppdb.read_lastsessionid(self.sessionId)
        self.lowlevel2ocpp()
        #if newSessionId == True:
        #    ocppdb.write_authorize_token(idTokenInfo= "Rejected", lastsessionid=self.sessionId)
        self.initialization_meter_values()
        log.info("SessionID in BootNotification: %s", self.sessionId)
        log.info("Session Status: %s", self.sessionStatus)
        
        if len(sys.argv) < 3:
            log.warn("SYS_ARG: Argumentos a menos do que o solicitado")
            log.warn("[Opcional] Para correr o script: python3 <nome do programa> EnergyAmount evseID")
            self.energyAmount = random.randint(100,300)
            self.evseId = random.randint(9999,99999)
        else :
            self.energyAmount = int(sys.argv[1])
            self.evseId = int(sys.argv[2])
        
        #select_routine_task = asyncio.create_task(self.select_routine())
        iso_smart_coroutine = asyncio.create_task(self.smart_routine())
        http_put_routine = asyncio.create_task(self.charge_point_put())
        
        request = call.BootNotificationPayload(charging_station={'model':'EVSE4.1-000','vendorName':'INESCEVSE'}, reason="PowerUp")
        response = await self.call(request)

        if response.status == 'Accepted':
            await self.charge_point_post()
            #ocppdb.bootstatus(connected='connected', cp_id='CP_0')
            boot = True # PowerUp successfully with CSMS
            self.powerUpStatus = True
            self.heartbeatInterval = response.interval
            #heartbeat_interval = response.interval
            heartbeat_coroutine = asyncio.create_task(self.send_heartbeat(self.heartbeatInterval))
            #messages_coroutine = asyncio.create_task(self.simple_routine())
            await heartbeat_coroutine
            await http_put_routine
            #await messages_coroutine

        if response.status == 'Pending' or 'Rejected':
            boot = False # PowerUp failled with CSMS
            self.powerUpStatus = False
            if response.status == 'Rejected': log.info("The boot_notification was rejected by CSMS")
            await asyncio.sleep(response.interval)
            await self.send_boot_notification()
        
        #await ev_coroutine
        #await select_routine_task
        await iso_smart_coroutine
        return response.status
  
#################################################################################################### StatusNotification request ###########################################################################################
    async def send_status_notification(self):
        #log.info("The connector status", connectorStatus)
        # if self.id_token_type == None: 
        #     self.id_token = str(uuid.uuid4()) #Unique token created to authorization
        #     self.id_token_type = "Local"
        #await asyncio.sleep(1)
        #self.evseId = 23
        request = call.StatusNotificationPayload(timestamp=datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S '), connector_status=self.connectorStatus, evse_id = self.evseId, connector_id = 1)
        response = await self.call(request)

        # ocppdb1, ocppdbCur = ocppdb.ocppdb_connect()
        # now = time.time()
        # insert_query = """INSERT INTO authorize (timestamp, idtoken, type, status) VALUES (FROM_UNIXTIME({timestamp}),{idtoken_str}, {type}, 'Accepted')""".format(timestamp=now, idtoken_str = self.id_token, type = self.id_token_type)
        # ocppdbCur.execute(insert_query)
        # ocppdb.ocppdb_close(ocppdb1, ocppdbCur)

        return response

#################################################################################################### TransactionEvent request ###########################################################################################
    async def send_transaction_event(self, charging_state, event_type, trigger_reason, transaction_id:str = None):
        if self.transaction_id == None:
            self.transaction_id = "LOC123"

        transaction_id = self.transaction_id
        request = call.TransactionEventPayload(event_type= event_type,
        timestamp=datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S'),
        trigger_reason=trigger_reason,
        seq_no=1,
        transaction_info={'transactionId': transaction_id,'chargingState':charging_state},
        evse = {'id':self.evseId}
        )
        
        response = await self.call(request)

        return response

#################################################################################################### NotifyReport request ###########################################################################################
    async def send_notify_report(self):
        request = call.NotifyReportPayload(request_id='fgreg', generated_at='ergr', seq_no=5)
        await self.call(request)

#################################################################################################### MeterValues request ###########################################################################################
    async def send_meter_values(self, *args, **kwargs):
        global energy, voltage, current, power
        #frequence = 50 #TODO: Insert frequency in table energy meter in local database
        #await asyncio.sleep(2)
        energy, voltage, current, power = ocppdb.read_metervalues()
        #energy, voltage, current, power = 8000, 230, 16, 7400
        request = call.MeterValuesPayload( evse_id=self.evseId, meter_value = self.meterValues)
        response = await self.call(request)

        return response 

#################################################################################################### GetISO15118Certificate request ###########################################################################################
    async def send_getISO15118EVCertificate(self):
        request=call.Get15118EVCertificatePayload(iso15118_schema_version='versao1',action='Install',exi_request='do EV')
        response=await self.call(request)
        if response.status=='Accepted':
            log.info('Certificado bem instalado')
            #await self.send_authorize()

#################################################################################################### Authorize request ###########################################################################################
    async def send_authorize(self):
        if self.id_token_type == None: 
            self.id_token = str(uuid.uuid4()) #Unique token created to authorization
            self.id_token_type = "Local"
        request=call.AuthorizePayload(
            id_token={'id_token': self.id_token ,'type':self.id_token_type}
            )
            # iso15118_certificate_hash_data=[{'hashAlgorithm':'SHA256', 'issuerNameHash': 'Hash1','issuerKeyHash':'Keyhas12345','serialNumber':'123456','responderURL':'www.tata.pt'}])
        response = await self.call(request)
        ocppdb.update_authorize(idToken=self.id_token, idTokenType = self.id_token_type, idTokenInfo= response.id_token_info['status'], lastsessionid=self.sessionId)
        if response.id_token_info['status'] == 'Accepted':
            self.triggerReason = "Authorized"
            log.info("AUTHENTICATION FINISHED: TOKEN ACCEPTED")
            # await self.send_meter_values()
        else:
            log.info("AUTHENTICATION FAILED: TOKEN NOT ACCEPTED")
            log.info("Trying again authentication ...")
        # await self.send_notifyevchargingneeds()
        return response

#################################################################################################### NotifyEVcharging request ###########################################################################################
    async def send_notifyevchargingneeds(self):
        global id_EV
        global stackLevel
        global chargingProfilePurpose
        global chargingProfileKind
        global chargingRateUnit
        global startPeriod
        global limit

        #max_schedule_tuples_aux = 6
        self.max_schedule_tuples = 1
        requestedEnergyTransfer, eAmount, evMinCurrent, evMaxCurrent, evMaxVoltage, departureTime = ocppdb.read_evchargingneeds(self.sessionId)
        #DummyData
        #RequestedEnergyTransferType : 'enum': ['DC', 'AC_single_phase', 'AC_two_phase', 'AC_three_phase']
        #requestedEnergyTransfer, eAmount, evMinCurrent, evMaxCurrent, evMaxVoltage, departureTime =  "AC_single_phase", self.energyAmount, 6, 32, 230, str(time.time())
        
        requestedEnergyTransfer = "AC_single_phase"
        departureTime = str(departureTime)
        acChargingParameters={'energyAmount': eAmount, 'evMinCurrent': evMinCurrent, 'evMaxCurrent': evMaxCurrent, 'evMaxVoltage' : evMaxVoltage}
        
        request=call.NotifyEVChargingNeedsPayload(
            charging_needs={'requestedEnergyTransfer': requestedEnergyTransfer, 'acChargingParameters' : acChargingParameters, 'departureTime': departureTime},
            evse_id=self.evseId,
            max_schedule_tuples=int(self.max_schedule_tuples))

        response = await self.call(request)
        #TODO: Insert the status in the database

        #await asyncio.sleep(3)
                
        #if read_flag=='1':
        #     await self.send_setchargingprofile()
        #else:
        #    log.info("Ficheiro de SetChargingProfileRequest nao modificado")

        return response
        
#################################################################################################### SetChargingProile request ###########################################################################################
    async def send_setchargingprofile(self):
        #Read the EAmount enviado pelo EV ao EVSE da base de dados
        #Calcula um charging profile para cumprir a quantidade de energia solicitada com 50% da potência nominal
        
        request=call.SetChargingProfilePayload(
            evse_id=self.evseId,
            charging_profile={'id':int(id_EV),
                            'stackLevel':int(stackLevel),
                            'chargingProfilePurpose':'ChargingStationMaxProfile',
                            'chargingProfileKind':'Absolute',
                            'chargingSchedule':[{'id':int(id_EV),'chargingRateUnit':chargingRateUnit,'chargingSchedulePeriod':[{'startPeriod':int(startPeriod),'limit':int(limit)}]}]
                            })
        response = await self.call(request)

        return response

    def lowlevel2ocpp(self):
        #Read lowlevel state and relay status from ocppdb
        self.llc_state, stateCheck = ocppdb.read_state(self.llc_state, self.sessionId)
        self.relayStatus, relayCheck = ocppdb.read_relay_status(self.relayStatus, self.sessionId)
        if stateCheck:
            log.info("LLC STATE: %s", self.llc_state)
        if relayCheck:
            log.info("RELAY STATUS: %d", self.relayStatus)
        
        if self.relayStatus == 1: #Relay ON
            if self.llc_state == 'A':
                self.connectorStatus = 'Faulted'
                log.error("ERROR: Low level state A and relay ON")
            elif self.llc_state == 'B':                
                self.connectorStatus = 'Faulted'
                log.error("ERROR: Low level state B and relay ON")
            elif (self.llc_state == 'C' or self.llc_state == 'D'):
                self.chargingState = 'Charging'
                self.connectorStatus = 'Occupied'
            elif self.llc_state == 'E':
                self.chargingState = 'SuspendedEVSE'
                self.connectorStatus = 'Faulted'
                log.error("ERROR: Low level state E")
        elif self.relayStatus == 0: #Relay OFF
            #Conditions of low level communication to OCPP status
            if self.llc_state == 'A':
                self.connectorStatus = 'Available'
                self.chargingState = 'Idle'
            elif self.llc_state == 'B':               
                self.connectorStatus = 'Occupied'
                self.chargingState = 'EVConnected'
            elif (self.llc_state == 'C' or self.llc_state == 'D'): #In case State: B and RelayStatus: True
                self.chargingState = 'EVConnected' 
                self.connectorStatus = 'Occupied'
                log.warn("WARNING: Low level state C or D and relay OFF")
            elif self.llc_state == 'E':
                self.connectorStatus = 'Faulted'
                self.chargingState = 'SuspendedEVSE' 
                log.error("ERROR: Low level state E")

        return stateCheck, relayCheck

    # #Method to implement dinamic compliant with IEC61851
    # async def select_routine(self):
    #     # Wait until the charge_mode is selected between the EV and the EVSE
    #     while True:
    #         charge_mode = ocppdb.read_chargemode(self.sessionId)
    #         if charge_mode == "hlc_c" or "hlc_only":
    #             iso_smart_coroutine = asyncio.create_task(self.smart_routine())
    #             await iso_smart_coroutine
    #             break
    #         elif charge_mode == "bc_only":
    #             iec_simple_coroutine = asyncio.create_task(self.simple_routine())
    #             await iec_simple_coroutine
    #             break
    #         await asyncio.sleep(1)
    #     return

    #Method to implement dinamic compliant with IEC61851
    async def simple_routine(self):
        log.info("Low level comm charging routine started")
        #ocppdb.read_hlcstate(sessionid)

        while True:
            energy, voltage,current, power = ocppdb.read_metervalues()
            self.meterValues = [
                {'timestamp':datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S '), 
                'sampled_value':[
                {'value': float(energy),'unitOfMeasure':{'unit':'Wh','multiplier':0}}, #Energy
                {'value': float(voltage),'unitOfMeasure':{'unit':'V','multiplier':0}},  #Voltage
                {'value': float(50),'unitOfMeasure':{'unit':'Hz','multiplier':0}}, #Frequency
                {'value': float(current),'unitOfMeasure':{'unit':'A','multiplier':0}},  #Current
                {'value': float(power),'unitOfMeasure':{'unit':'W','multiplier':0}}]}]#Power
            #ocppdb.session_update(self.sessionId, self.hlc_state,0,self.meterValues,self.chargingState)
            #ocppdb.read_hlcstate(sessionid)
            #Read data from the database ocppdb
            stateCheck, relayCheck = self.lowlevel2ocpp()
            charge_mode, new_charge_mode = ocppdb.read_chargemode(self.sessionId,0)
            if new_charge_mode == True:
                if charge_mode == "hlc_only" or charge_mode == "hlc_c":
                    break
            #Messages sent when happen some change in state or relay
            if stateCheck or relayCheck: #An event
                if self.connectorStatus=='Available': #State A (No estado A finaliza a função)
                    await self.send_status_notification()
                    log.info("Low level comm charging routine ended")
                    break
                else:
                    if self.connectorStatus == 'Occupied':
                        await self.send_status_notification()
                    if self.chargingState =='EVConnected'  and (self.llc_state=='B' or self.llc_state=='A'):
                        await self.send_transaction_event(self.chargingState, 'Updated', 'ChargingStateChanged')
                    if self.chargingState=='EVConnected' and self.llc_state=='C':
                        await self.send_meter_values()
                    if self.chargingState=='Charging':
                        await self.send_transaction_event(self.chargingState, 'Updated', 'ChargingStateChanged')
                await self.send_status_notification()
            else: #No change in the Low level charger identified
                if self.chargingState=='Charging': #This adds a problem in logic : Discover the problem
                    await self.send_meter_values()
                #If no change happens in lowlevel keep sending heartbeats        
                #await self.send_heartbeat(interval)
            await asyncio.sleep(1)
        
        return

    #State machine to implement use case compliant with ISO 15118
    async def smart_routine(self):
        self.setStateCP(stateBoot())
        log.info("SMART ROUTINE CALLED ")
        #ocppdb.read_hlcstate(sessionid)
        #ocppdb.session_initialization(self.sessionId, self.hlc_state,0,self.meterValues, self.chargingState)
        while True:
            #ocppdb.session_update(self.sessionId, self.hlc_state,0,self.meterValues,self.chargingState)
            self.lowlevel2ocpp()
            self.sessionId, self.sessionStatus, self.newSessionId = ocppdb.read_lastsessionid(self.sessionId)
            self.hlc_state, newHlcState = ocppdb.read_hlcstate(self.hlc_state, self.sessionId)
            #log.info("INSIDE LOOP SMART ROUTINE")
            #Read data from the database ocppdb
            #stateCheck, relayCheck, self.connectorStatus, self.chargingState = self.lowlevel2ocpp()
            #Messages sent when happen some change in state or relay
            #if stateCheck or relayCheck: #An event
            await self.send_message_to_CSMS()
            if self.changedState == True:
                self.presentState()
                self.changedState = False
            if type(self._state).__name__ == "stateEnergyDelivery":
                await asyncio.sleep(self.meterValuesPeriod)
            else:
                await asyncio.sleep(1)
    
    @on('SetVariables')
    async def on_set_variables(self, set_variable_data, **kwargs):
        log.info('Set Variables')
        return call_result.SetVariablesPayload(set_variable_result = [{'attributeStatus':'Accepted' , 'component' : {'name' : 'olacomponent'} ,'variable' : {'name':'olavariable'} }])

#################################################################################################### GetVariables response ###########################################################################################

    @on('GetVariables')
    async def on_get_variables(self, get_variable_data, **kwargs):
        log.info('Get Variables')
        return call_result.GetVariablesPayload(get_variable_result = [{'attributeStatus':'Accepted' , 'component' : {'name' : 'INESC_CP_0'} ,'variable' : {'name':'EvseId'} , 'attributeValue': '23' }])
        
    @after('GetVariables')
    async def after_get_variables(self, *args, **kwargs):
        await self.send_meter_values()
#################################################################################################        # loop = asyncio.get_event_loop()
    @on('GetBaseReport')
    async def on_get_base_report(self, request_id,report_base, **kwargs):
        log.info('report recebido')
        return call_result.GetBaseReportPayload(status='Accepted')

#################################################################################################### Reset response ###########################################################################################

    @on('Reset')
    async def on_reset(self, type, **kwargs):
        log.info('Reset efetuado')
        return call_result.ResetPayload(status ='Accepted')
        #self.chargingProfile['schedule']
#################################################################################################### SetChargingProile response ###########################################################################################

    @on('SetChargingProfile')
    async def on_setchargingprofile(self, evse_id, charging_profile, **kwargs):
        self.on_setchargingprofile = True
        log.info('recebido')
        self.chargingProfile = charging_profile

        self.chargingProfileID = ocppdb.write_chargingprofile(chargingprofile= charging_profile, maxScheduleTuple= self.max_schedule_tuples, lastsessionid=self.sessionId)
        ocppdb.grafana_write_chargingprofile(chargingprofile= charging_profile, maxScheduleTuple= self.max_schedule_tuples, lastsessionid=self.sessionId)
        # len_schedule = len(charging_profile['charging_schedule'])
        # for schedule_index in range(len_schedule):
        #     log.info(  "charging_rate_unit:", charging_profile['charging_schedule'][schedule_index]['charging_rate_unit'],
        #         "charging_schedule_period Duration:", charging_profile['charging_schedule'][schedule_index]['duration'],
        #         "charging_schedule_period Start:" ,charging_profile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['start_period']
        #         #,"charging_schedule_period:"
        #         #charging_profile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['number_phases']
        #         )
        
        return call_result.SetChargingProfilePayload(status ='Accepted')

    @after('SetChargingProfile')
    async def after_setchargingprofile(self, *args, **kwargs):
        self.on_sendmetervalues = True

#################################################################################################### Request Start from CSMS response ###########################################################################################
#
    @on('RequestStartTransaction')
    async def on_requeststarttransaction(self, id_token:dict, remote_start_id:int, **kwargs):
        self.on_requeststarttransaction = True
        self.id_token = id_token['id_token']
        self.id_token_type = id_token['type']
        self.remoteStartId = remote_start_id
        self.transaction_id = "REM123"
        #ocppdb, ocppdbCur = ocppdb.ocppdb_connect() 
        #now = time.time()
        #ocppdbCur.execute("INSERT INTO RequestStartStop (timestamp, idtoken, type, status) VALUE (FROM_UNIXTIME(%d),%s, %s, 'Accepted')", (int(now),str(self.id_token), str(self.token_type)))
        #ocppdb.ocppdb_close(ocppdb, ocppdbCur)
        return call_result.RequestStopTransactionPayload(status ='Accepted')

    @after('RequestStartTransaction')
    async def after_requeststarttransaction(self, *args, **kwargs):
        button_press=1
        stateCheck, relayCheck, connectorStatus, chargingState = await self.lowlevel2ocpp()
        await self.send_transaction_event(chargingState, event_type='Started', trigger_reason='RemoteStart', transaction_id=self.transaction_id)
        #await self.send_meter_values()
        self.on_requeststarttransaction = False


#################################################################################################### Request Stop from CSMS response ###########################################################################################

    @on('RequestStopTransaction')
    async def on_requeststoptransaction(self, req_stop_tx_payload: call.RequestStopTransactionPayload, **kwargs):
        self.on_requeststoptransaction = True
        if req_stop_tx_payload.transaction_id == self.transaction_id:
            cur_status = 'Accepted'
        else: 
            cur_status = 'Rejected' #Need to discover the first message to exchange the transaction_id
            #cur_status = 'Accepted'
        #ocppdb, ocppdbCur = ocppdb.ocppdb_connect()
        #now = time.time() #Unixtimestamp
        #ocppdbCur.execute("INSERT INTO RequestStartStop (timestamp, status) VALUE (FROM_UNIXTIME(%d), %s)", (int(now), cur_status))
        #ocppdb.ocppdb_close(ocppdb, ocppdbCur)
        return call_result.RequestStopTransactionPayload(status = cur_status)

    @after('RequestStopTransaction')
    async def after_requeststoptransaction(self, *args, **kwargs):
        button_press=1
        #stateCheck, relayCheck, connectorStatus, chargingState = self.lowlevel2ocpp()
        self.eventType = "Ended"
        await self.send_transaction_event(self.chargingState, event_type='Ended', trigger_reason='RemoteStop')
        #await self.send_meter_values()

#################################################################################################### DataTransfer response #################################################################################################

    @on('DataTransfer')
    async def on_datatransfer(self, vendor_id,message_id, *args, **kwargs):
        #rwfiles.write_datatransfer(message_id)
        #write_datatransfer(message_id)
        #ocppdbCur.execute("UPDATE SetChargingProfile SET power = %s", message_id)
        return call_result.DataTransferPayload(status ='Accepted')

    @after('DataTransfer')
    async def after_datatransfer(self,vendor_id, message_id, *args, **kwargs):
            if message_id=='start':
                self.button_start=True
