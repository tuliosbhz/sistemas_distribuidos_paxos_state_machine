import asyncio
import logging
from datetime import datetime
import array
from tracemalloc import start

import uuid

# #Bibliotecas to acess database
# import mysql.connector
# from mysql.connector import errorcode

import database

#Bibliotecas to change color
from colorama import init
init()
from colorama import Fore,Back,Style

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)


from ocpp.routing import on
from ocpp.routing import after
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from ocpp.v201 import call


logging.basicConfig(level=logging.INFO)

def is_valid_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

status=''

class ChargePoint(cp):

    energy_amount = None
    ev_max_current = None
    ev_min_current = None
    ev_max_voltage = None
    evse_max_voltage : int = 250
    last_meter_values: dict = None
    
#################################################################################################### BootNotification response #################################################################

    @on('BootNotification')
    def on_boot_notification(self,charging_station, reason,*args, **kwargs):
            self._model = charging_station['model']
            # print(Back.BLACK + 'The Charging Station from',charging_station['model'],'with model',charging_station['vendor_name'], 'wants to be added, Accepted,Rejected or Pending??'+ Style.RESET_ALL)
            # status=input()
            # database.database_bootnotification(charging_station['model'],charging_station['vendor_name'],1)
            return call_result.BootNotificationPayload(current_time=datetime.utcnow().isoformat(), interval=10, status='Accepted')

#################################################################################################### Heartbeat response ##########################################################################

    @on('Heartbeat')
    def on_heartbeat(self): 
        print('Got a Heartbeat!')
        return call_result.HeartbeatPayload(current_time=datetime.utcnow().strftime('%Y-%m-%d T %H:%M:%S ') + "Z")

    @after('Heartbeat')
    async def after_heartbeat(self):
        global power_setchargingprofile
        global action

        #action, checkAction = database.database_datatransfer(self._model)
        #print(action)
        #if checkAction == 'changed':
        #    await self.send_datatransfer()
        # if action=='stop' or action=='start':
        #     await self.send_datatransfer()

        #power_setchargingprofile=database.database_setchargingprofile(self._model)
        #print(power_setchargingprofile)
        #if power_setchargingprofile>0:
        #    await self.send_setchargingprofile()


#################################################################################################### StatusNotification response #################################################################

    @on('StatusNotification')
    def on_status_notification(self, timestamp, connector_status, evse_id, connector_id, **kwargs):
        print(Back.BLACK + 'The Conector',connector_id, 'in evseid:',evse_id,'is', connector_status + Style.RESET_ALL)
        #database.database_statusnotification(self._model,connector_status)
        # database_chargeevent(self._model,'EVDetected')
        return call_result.StatusNotificationPayload()

#################################################################################################### TransactionEvent response #################################################################

    @on('TransactionEvent')
    async def on_transaction_event(self,event_type,timestamp,trigger_reason,seq_no,transaction_info,**kwargs):
        print(Back.BLACK + 'According to transaction',transaction_info['transaction_id'],',the EVSE is',trigger_reason + Style.RESET_ALL)
        #database.database_transactionevent(self._model,transaction_info['charging_state'])
        return call_result.TransactionEventPayload()

    # @after('TransactionEvent')
    # async def after_transaction_event(self,offline, *args, **kwargs):
    #     if offline==True:


#################################################################################################### NotifyReport response ######################################################################

    @on('NotifyReport')
    def on_notify_report(self,request_id,generated_at,seq_no,**kwargs):
        return call_result.NotifyReportPayloadd()

#################################################################################################### Authorize response #########################################################################
    @on('Authorize')
    async def on_authorize(self,id_token,*args, **kwargs):
        if id_token['type'] != "Central":
            status = "Accepted"
        else:
            print("IDTOKEN receveid of wrong type. 'Central' type Obtained")
            status = "Blocked"
        return call_result.AuthorizePayload(id_token_info={'status':status})

    #@after('Authorize')
    #async def after_authorize(self, *args, **kwargs):
        #await self.send_setchargingprofile()
        

#################################################################################################### MeterValues response #####################################################################

    @on('MeterValues')
    async def on_meter_values(self,evse_id,meter_value,*args, **kwargs):
        print(Back.BLACK +'A carregar, com os seguintes valores:'+ Style.RESET_ALL)
        #print('Energia:',meter_value[0]['sampled_value'][0]['value'],meter_value[0]['sampled_value'][0]['unit_of_measure':'unit'])
        print('Energia:',meter_value[0]['sampled_value'][0]['value'])
        print('Tensao:',meter_value[0]['sampled_value'][1]['value'])
        print('Frequencia da Tensão:',meter_value[0]['sampled_value'][2]['value'])
        print('Currente:',meter_value[0]['sampled_value'][3]['value'])
        print('Potencia:',meter_value[0]['sampled_value'][4]['value'])
        print(''+ Style.RESET_ALL)
        #database.database_metervalues(self._model,meter_value[0]['sampled_value'][1]['value'],
        #meter_value[0]['sampled_value'][3]['value'],
        #meter_value[0]['samp1led_value'][4]['value'],
        #meter_value[0]['sampled_value'][0]['value'])

        last_meter_values = None
        energy_transfered = None
        energy_amount = None
        
        print(f'MeterValues >\n'
        f'{evse_id=}\n'
        f'{meter_value=}\n')

        print('Energia:', meter_value[0]['sampled_value'][0]['value'])
        print('Tensao:', meter_value[0]['sampled_value'][1]['value'])
        print('Frequencia da Tensão:', meter_value[0]['sampled_value'][2]['value'])
        print('Currente:', meter_value[0]['sampled_value'][3]['value'])
        print('Potencia:', meter_value[0]['sampled_value'][4]['value'])

        if not self.last_meter_values:
            self.last_meter_values = meter_value
            self.energy_transfered = 0
        else:
            diff_energy = None # diferencial de energia
            for i, sv in enumerate(meter_value[0]['sampled_value']):
                if sv['unit_of_measure']['unit'] == 'Wh':
                    self.last_meter_values[0]['sampled_value'][i]['value'] -= sv['value']
                    diff_energy = abs(self.last_meter_values[0]['sampled_value'][i]['value'])
                    self.energy_transfered += diff_energy

                elif sv['unit_of_measure']['unit'] == 'kWh':
                    self.last_meter_values[0]['sampled_value'][i]['value'] -= sv['value']
                    self.last_meter_values[0]['sampled_value'][i]['value'] = \
                    abs(self.last_meter_values[0]['sampled_value'][i]['value'])
                    self.last_meter_values[0]['sampled_value'][i]['value'] /= 1000
                    diff_energy = self.last_meter_values[0]['sampled_value'][i]['value']
                    self.energy_transfered += diff_energy

        current_soc = self.energy_transfered / self.energy_amount
        print(current_soc) # nivel atual da carga
       
        return call_result.MeterValuesPayload()

    #@after('MeterValues')
    #async def after_meter_values(self,*args, **kwargs):
        #global power_setchargingprofile
        #global action
       
        #action, checkChange =database.database_datatransfer(self._model)
        #print(action)
        
        #if checkChange: 
        #    await self.send_datatransfer()

        #power_setchargingprofile=database.database_setchargingprofile(self._model)
        #print(power_setchargingprofile)

        #if power_setchargingprofile>0:
        #    await self.send_setchargingprofile()


#################################################################################################### Get15118ISO response #######################################################################

    @on('Get15118EVCertificate')
    def on_get15118EVCertificate(self, iso15118_schema_version,action,exi_request):
        print('Version=',iso15118_schema_version)
        print('Action=',action)
        print('exiRequest=',exi_request)
        return call_result.Get15118EVCertificatePayload(status='Accepted',exi_response=exi_request )

#################################################################################################### NotifyEVChargingNeeds response #################################################################

    @on('NotifyEVChargingNeeds')
    def on_notifyevchargingneeds(self, charging_needs: dict, evse_id: int, max_schedule_tuples: int = None):
        self.energy_amount = charging_needs['ac_charging_parameters']['energy_amount']
        self.ev_max_current = charging_needs['ac_charging_parameters']['ev_max_current']
        self.ev_min_current = charging_needs['ac_charging_parameters']['ev_min_current']
        self.ev_max_voltage = charging_needs['ac_charging_parameters']['ev_max_voltage']
        return call_result.NotifyEVChargingNeedsPayload(status='Accepted')
    
    @after('NotifyEVChargingNeeds')
    async def after_notifyevchargingneeds(self, *args, **kwargs):
        
        await self.send_setchargingprofile(self.energy_amount, self.ev_max_current, self.ev_min_current, self.ev_max_voltage, self.evse_max_voltage)
    
#################################################################################################### SetChargingProile response #################################################################

    @on('SetChargingProfile')
    def on_setchargingprofile(self,evse_id,charging_profile):
        return call_result.SetChargingProfilePayload(status='Accepted')

#################################################################################################### SetVariables request #################################################################

    async def send_set_variables(self):
       request = call.SetVariablesPayload(set_variable_data = [{'attributeValue':'Actual' , 'component' : {'name' : 'olacomponent'} ,'variable' : {'name':'olavariable'}}])
       response = await self.call(request)

#################################################################################################### GetVariables request ############################################################################

    async def send_get_variables(self):
       request = call.GetVariablesPayload(get_variable_data = [{'component' : {'name' : 'raspEVSE4'} ,'variable' : {'name':'Energy'}}])
       response = await self.call(request)

#################################################################################################### GetBaseReport request ##########################################################################

    async def send_get_base_report(self):
       request = call.GetBaseReportPayload(request_id=2 , report_base = "ConfigurationInventory")
       response = await self.call(request)

#################################################################################################### SendReset request ##############################################################################

    async def send_reset(self):
       request = call.ResetPayload(type = 'Immediate')
       response = await self.call(request)

#################################################################################################### SetChargingProile request ##############################################################################

    async def send_setchargingprofile(self, energy_amount: int, ev_max_current: int, ev_min_current, ev_max_voltage: int, evse_max_voltage: int):
        #charging_profile =
        #Developing schedules based on ac parameters 
        # 1 - Fastest charge (Minimum time)
        limit = ev_max_current * evse_max_voltage
        # 2 - Slowest charge (Maximum time)
        #limit = ev_min_current * evse_max_voltage
        duration = int((energy_amount / limit) * 3600 )  #Hour to seconds
        stackLevel = 0
        chargingProfilePurpose = "TxDefaultProfile"
        chargingProfileKind = "Absolute"
        chargingRateUnit = "W"
        startPeriod = 0
        #duration = 50 # 50 seconds
        #limit = 3680 # 3680 W (~16A)
        request=call.SetChargingProfilePayload(
            evse_id=23,
            charging_profile={'id': 1,
                            'stackLevel': stackLevel,
                            'chargingProfilePurpose':chargingProfilePurpose,
                            'chargingProfileKind': chargingProfileKind,
                            'chargingSchedule':[{'id':1,'chargingRateUnit': chargingRateUnit ,'duration': duration ,'chargingSchedulePeriod':[{'startPeriod': startPeriod ,'limit': limit}]}]
                            })
        await self.call(request)

#################################################################################################### RequestStartTransaction request ##############################################################################
    async def send_requeststarttransaction(self):
        request=call.RequestStartTransactionPayload(id_token={'idtoken':str(uuid.UUID),'type':'Central'}, remote_start_id=1)
        await self.call(request)

#################################################################################################### RequestStopTransaction request ##############################################################################
    async def send_requeststoptransaction(self):
        request=call.RequestStopTransactionPayload(transaction_id='1234')
        await self.call(request)



#################################################################################################### DataTransfer request ##############################################################################
    async def send_datatransfer(self):
        request=call.DataTransferPayload(vendor_id='1234',message_id=action)
        await self.call(request)
        
#################################################################################################### Waiting for Clients connection #################################################################

async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint instance and start listening for messages."""
    try:
        requested_protocols = websocket.request_headers['Sec-WebSocket-Protocol']
    except KeyError:
        logging.info("Client hasn't requested any Subprotocol. " "Closing Connection")
        return await websocket.close()
        logging.error( "Client hasn't requested any Subprotocol. Closing Connection")
        return await websocket.close()
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning('Protocols Mismatched | Expected Subprotocols: %s,' ' but client supports %s | Closing connection', websocket.available_subprotocols, requested_protocols)
        return await websocket.close()

    charge_point_id = path.strip('/')
    charge_point = ChargePoint(charge_point_id, websocket)

    print(f"Charger {charge_point.id} connected")
    #database.database_bootnotification(charge_point.id,'connected')

    try:
        await charge_point.start()
        #database.database_bootnotification(charge_point.id,'connected')
        print(f"Charger {charge_point.id} connected")
    except websockets.exceptions.ConnectionClosedOK or websockets.exceptions.ConnectionClosedError:
        print(f"Charger {charge_point.id} disconnected")
        #database.database_bootnotification(charge_point.id,'disconnected')

        
#################################################################################################### Main Function #################################################################

async def main():
   
    #  deepcode ignore BindToAllNetworkInterfaces: <Example Purposes>
    server = await websockets.serve(on_connect,'0.0.0.0',8000,subprotocols=['ocpp2.0.1'])
    #server = await websockets.serve(on_connect,'csms-inesctec',8000,subprotocols=['ocpp2.0.1'])

    logging.info("Server Started listening to new connections...")

    await server.wait_closed()
    
if __name__ == '__main__':
    try:
        # asyncio.run() is used when running this example with Python 3.7 and
        # higher.
        asyncio.run(main())
    except AttributeError:
        # For Python 3.6 a bit more code is required to run the main() task on
        # an event loop.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
