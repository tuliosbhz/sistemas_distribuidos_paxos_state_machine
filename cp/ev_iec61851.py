#%%
from datetime import datetime
import time
import random

class EvseBasic:
    def __init__(self):
        self.state = ['A','B','C','D','E']
        self.llc_state = 'A'
        self.hlc_state = -1
        self.prev_llc_state = 'E'
        self.max_current = 32
        self.curr_current= 16
        self.relay_status = 0
        self.meter_values = {'timestamp': datetime.utcnow().date(), 'voltage':230, 'current':16, 'frequency': 50, 'power': 3580}
        self.sessionid = "0000000000000000"
        self.token_info = "Rejected"
        self.chargemode = 0
    
    def routine(self):
        while True:
            plug_ev = input("Plug connected ? ")
            if "yes" in plug_ev:
                self.llc_state = 'B'
            if self.llc_state != self.prev_llc_state:
                new_llc_state = True
                self.prev_llc_state = self.llc_state
            if self.llc_state == 'B' and new_llc_state:
                self.hlc_state += 1
                time.sleep(1)
            
            if self.hlc_state == 3:#process_SessionSetupReq
                sessionid_int = int(self.sessionid)
                sessionid_size = len(str(sessionid_int))
                index = len(self.sessionid) - sessionid_size
                sessionid_int += 1
                self.sessionid = self.sessionid[:index] + str(sessionid_int)
            if self.hlc_state == 10: #wait_AuthorizationReq:
                self.token_info = "Get from CSMS"
                #Create socket here and request the tokeninfo
                if self.token_info == "Accepted":
                    self.hlc_state += 1
                
            
            self.print_variables()
    
    
    def print_variables(self):
        print(f"self.llc_state = {self.llc_state}")
        print(f"self.hlc_state = {self.hlc_state}")
        print(f"self.prev_llc_state = {self.prev_llc_state}")
        print(f"self.max_current = {self.max_current}")
        print(f"self.curr_current= {self.curr_current}")
        print(f"self.relay_status = {self.relay_status}")
        print(f"self.meter_values = {self.meter_values}")
        print(f"self.sessionid = {self.sessionid})")

evse = EvseBasic()
evse.routine()
yes# %%

# %%
