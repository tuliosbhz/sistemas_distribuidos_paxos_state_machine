import charge_point as cp
import db_ocpp_methods as ocppdb
#Exit in case of exceptions
import sys

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    #import sys
    sys.exit(1)

from ast import And
import asyncio
from datetime import datetime
import sched
import time                         #To get Unixtimestamp
from tkinter import EventType
from tracemalloc import start


#################################################################################################### Main:Communicate with Sever(CSMS) ###########################################################################################
async def main(args):
    count_tries = 0
    #async with websockets.connect('ws://csms-inesctec:8000/CP_0', subprotocols=['ocpp2.0.1']
    #async with websockets.connect('wss://ocpp.evcm.ubiwhere.com',ping_interval=None, ping_timeout=None, close_timeout=None,subprotocols=['ocpp2.0.1']
    #async with websockets.connect('ws://ocpp.evcm.ubiwhere.com/INESC_CP_0', subprotocols=['ocpp2.0.1']
    #async with websockets.connect('ws://ocpptests.ddns.net:9000/INESC_CP_0', subprotocols=['ocpp2.0.1']
    #async with websockets.connect('ws://192.168.1.133:9000/CP_0', subprotocols=['ocpp2.0.1']
    #async with websockets.connect('ws://ocpptests.ddns.net:9000/INESC_CP_0', subprotocols=['ocpp2.0.1']

    while True: 
        try:
            print("Trying connection with Charging Station Managing System...")
            #async with websockets.connect('ws://192.168.40.97:9000/CP_0', subprotocols=['ocpp2.0.1']
            if count_tries <= 3:
                async with websockets.connect('ws://ocpp.evcm.ubiwhere.com:9000/INESC_CP_0', subprotocols=['ocpp2.0.1']
                ) as ws:
                    charge_point = cp.ChargePoint('INESC_CP_0', ws)
                    print(charge_point)
                    await asyncio.gather(charge_point.start(), charge_point.send_boot_notification())
            else:
                await asyncio.sleep(10)
                # async with websockets.connect('ws://192.168.1.156:8000/INESC_CP_0', subprotocols=['ocpp2.0.1']
                # ) as ws:
                #     charge_point = cp.ChargePoint('INESC_CP_0', ws)
                #     print(charge_point)
                #     await asyncio.gather(charge_point.start(), charge_point.send_boot_notification())
        except (ConnectionRefusedError, websockets.exceptions.ConnectionClosedError, OSError):
            print("Connection refused: CSMS not up or wrong address")
            #ocppdb.bootstatus(connected='disconnected', cp_id='CP_0')
            count_tries += count_tries
            await asyncio.sleep(2)
        await asyncio.sleep(5)
            


#################################################################################################### Loop ###########################################################################################

if __name__ == '__main__':
    try:
        # asyncio.run() is used when running this example with Python 3.7 and
        # higher.
        asyncio.run(main(sys.argv))
    except (AttributeError, KeyboardInterrupt):
        # For Python 3.6 a bit more code is required to run the main() task on
        # an event loop.
        #ocppdb.bootstatus(connected='disconnected', cp_id='CP_0')
        loop = asyncio.get_event_loop()
        try:
            asyncio.ensure_future(main(sys.argv))
            #asyncio.ensure_future(charge_point.routine(heartbeat_interval))
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            print("Closing Loop")
            loop.close()

        # #loop = asyncio.get_event_loop()
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(main())
        # loop.close()
