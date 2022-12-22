#Database imports
#from sqlite3 import Timestamp
import sys
from sys import modules
import mysql
import mysql.connector
from mysql.connector import errorcode

import mariadb
#from mariadb.constants import ERR

import logging as log
# open(file="/home/pi/inesc-ocpp2.0.1/logs/db_ocpp_debug.txt", mode="a")
# log.basicConfig(filename="/home/pi/inesc-ocpp2.0.1/logs/cp_log_debug.txt", level=log.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filemode="a+")


#To get Unixtimestamp
import time
from datetime import datetime

from requests import session       

configDB = {
    'user': 'evseuser',
    'password': 'pass',
    'host': 'localhost',
    'database' : 'ocppdb'
    #'port': '3306',
    #'client_flags': [ClientFlag.SSL],
    #'ssl_ca': '/opt/mysql/ssl/ca.pem',
    #'ssl_cert': '/opt/mysql/ssl/client-cert.pem',
    #'ssl_key': '/opt/mysql/ssl/client-key.pem',
}

configGrafanaDB = {
    'user': 'tulio',
    'password': '',
    'host': '10.12.6.15',
    'port': '3306',
    'database' : 'evse',
    'auth_plugin' : 'caching_sha2_password'
    #'client_flags': [ClientFlag.SSL],
    #'ssl_ca': '/opt/mysql/ssl/ca.pem',
    #'ssl_cert': '/opt/mysql/ssl/client-cert.pem',
    #'ssl_key': '/opt/mysql/ssl/client-key.pem',
}

#Try to connect to Data Base

#**em_args = energy, voltage, frequency, current

def ocppdb_connect():
    ocppdb = None
    ocppdbCur = None
    try:
        ocppdb = mariadb.connect(**configDB)
        ocppdbCur = ocppdb.cursor()
        # ocppdb = mysql.connector.connect(**configDB)
        # ocppdbCur = ocppdb.cursor(buffered=False)
    except mariadb.OperationalError as err:
        print(f"Erro na base de dados: {err}")
        # if err.errno == ERR.ER_ACCESS_DENIED_ERROR:
        #     print("Something is wrong with your user name or password")
        # elif err.errno == ERR.ER_BAD_DB_ERROR:
        #     print("Database does not exist")
        # else:
        #     print(err)

    return ocppdb, ocppdbCur

def ocppdb_close(ocppdb, ocppdbCur):
    ocppdbCur.close()
    ocppdb.close()
    return 1

def grafana_connect():
    grafanadb = None
    grafanaCur = None
    try:
        grafanadb = mysql.connector.connect(**configGrafanaDB)
    except mysql.connector.Error as err:
        print(f"Erro na base de dados: {err}")
        return grafanadb, 0
        # if err.errno == ERR.ER_ACCESS_DENIED_ERROR:
        #     print("Grafana DB: Something is wrong with your user name or password")
        # elif err.errno == ERR.ER_BAD_DB_ERROR:
        #     print("Grafana Database does not exist")
        # else:
        #     print(err)
    finally:
        grafanaCur = grafanadb.cursor(buffered=False)
    return grafanadb, grafanaCur

def db_close(db, dbCursor):
    db.close()
    dbCursor.close()
    return 1

def bootstatus(cp_id, connected):
    
    grafanadb, grafanaCur = grafana_connect()
    #date=datetime.now().isoformat()
    date = time.time()
    # add_bootnotification = ("INSERT INTO BootNotification" "(model,vendorName,timestamp,active)" "VALUES (%s, %s, %s,%s)")
    # data_bootnotification = (model,vendor_name,date,1)
    add_bootnotification = "UPDATE BootNotification SET timestamp=FROM_UNIXTIME({date}),connected='{status_str}' WHERE CP_id='{cp_str}'".format(date=date,status_str=connected,cp_str=cp_id)
    #data_bootnotification = (date,connected,cp_id)
    # print(datetime.utcnow().isoformat())
    grafanaCur.execute(add_bootnotification)
    #print(Back.BLACK + 'Write Database BootNotification'+ Style.RESET_ALL)
    grafanadb.commit()
    db_close(grafanadb, grafanaCur)

def session_initialization(lastsessionID:str, hlc_state: int, chargingProgress:float, meterValues:dict, chargingState:str):
    grafanadb, grafanaCur = grafana_connect()
    if grafanaCur == 0:
        log.error("DB: Grafana not initialized")
        return
    timeStamp=time.time()
    energy = meterValues[0]['sampled_value'][0]['value']
    voltage = meterValues[0]['sampled_value'][1]['value']
    current = meterValues[0]['sampled_value'][3]['value']
    power = meterValues[0]['sampled_value'][4]['value']
    add_bootnotification = """INSERT INTO evse000session (SessionID,Timestamp,State,ChargingState,Charging_progress,Voltage, Current, Power, Energy) VALUES ('{SessionID}',FROM_UNIXTIME({Timestamp}),{State},'{ChargingState}',{ChargingProgress},{Voltage},{Current},{Power},{Energy})""".format(SessionID=lastsessionID,Timestamp=timeStamp,State=hlc_state,ChargingState=chargingState,ChargingProgress=chargingProgress,Voltage=voltage, Current=current, Power=power, Energy=energy)
    #data_bootnotification = (lastsessionID,timeStamp,hlc_state,chargingProgress, voltage, current, power, energy)
    # print(datetime.utcnow().isoformat())
    grafanaCur.execute(add_bootnotification)
    #print(Back.BLACK + 'Write Database BootNotification'+ Style.RESET_ALL)
    grafanadb.commit()
    db_close(grafanadb, grafanaCur)

def session_update(lastsessionID:str, hlc_state: int, chargingProgress:float, meterValues:dict, chargingState:str):
    grafanadb, grafanaCur = grafana_connect()
    
    energy = meterValues[0]['sampled_value'][0]['value']
    voltage = meterValues[0]['sampled_value'][1]['value']
    current = meterValues[0]['sampled_value'][3]['value']
    power = meterValues[0]['sampled_value'][4]['value']
    timeStamp=time.time()
    add_bootnotification = """UPDATE evse000session SET SessionID = '{SessionID}',Timestamp=FROM_UNIXTIME({Timestamp}),hlcState={State},ChargingState='{ChargingState}', Charging_progress={ChargingProgress}, Voltage={Voltage}, Current={Current}, Power={Power}, Energy={Energy} ORDER BY TimeStamp DESC LIMIT 1""".format(SessionID=lastsessionID,Timestamp=timeStamp,State=hlc_state,ChargingProgress=chargingProgress,Voltage=voltage, Current=current, Power=power, Energy=energy, ChargingState=chargingState)
    #data_bootnotification = (lastsessionID,timeStamp,hlc_state,chargingProgress, voltage, current, power, energy)
    grafanaCur.execute(add_bootnotification)
    grafanadb.commit()
    db_close(grafanadb, grafanaCur)


def read_chargemode(lastsessionid:str, charge_mode:int=None):
    old = charge_mode

    ocppdb, ocppdbCur = ocppdb_connect() 
    #Get the State value of the LowLevel charger(EVSE)
    select_query = """SELECT ChargeMode FROM bc_state WHERE SessionID = '{sessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(sessionid_str = lastsessionid)
    ocppdbCur.execute(select_query)
    for info in ocppdbCur.fetchall() :
       charge_mode = info[0]
    ocppdb_close(ocppdb, ocppdbCur)
    if old != charge_mode: # New charge_mode at the EVSE
        if charge_mode == 0: #LLC_ONLY
            return "llc_only", True
        elif charge_mode == 1: #HLC_ONLY
            return "hlc_only", True
        elif charge_mode == 2: #HLC_ONLY
            return "hlc_c", True
        else:
            return "not_selected", True
    else:
        return charge_mode, False


def read_state(state, lastsessionid:str):
    old = state

    ocppdb, ocppdbCur = ocppdb_connect() 
    #Get the State value of the LowLevel charger(EVSE)
    select_query = """SELECT State FROM bc_state WHERE SessionID = '{sessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(sessionid_str = lastsessionid)
    ocppdbCur.execute(select_query)
    for info in ocppdbCur.fetchall() :
       state = info[0]
    ocppdb_close(ocppdb, ocppdbCur)
    if old != state: #To check if the variable changed his value
        return state, True
    else:
        return state, False

def read_relay_status(relayStatus, lastsessionid:str):
    old = relayStatus
    #print(old, relayStatus)
    ocppdb, ocppdbCur = ocppdb_connect()
    #Get the State value of the LowLevel charger(EVSE)
    select_query = """SELECT RelayStatus FROM bc_relay_status WHERE SessionID = '{sessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(sessionid_str = lastsessionid)
    ocppdbCur.execute(select_query)
    for info in ocppdbCur.fetchall() :
       relayStatus = info[0]
    ocppdb_close(ocppdb, ocppdbCur)
    #print(old, relayStatus)
    if old != relayStatus: #To check if the variable changed his value
        return relayStatus, True
    else:
        return relayStatus, False

# def write_setchargingprofile(charging_profile):
#     ocppdb, ocppdbCur = ocppdb_connect() 
#     query= "UPDATE SetChargingProfile SET power = {power_value} WHERE id = 1".format(power_value = charging_profile)
#     ocppdbCur.execute(query)
#     ocppdb.commit()
#     ocppdb_close(ocppdb, ocppdbCur)
#     return True

def write_requeststartstop(message_id):
    ocppdb, ocppdbCur = ocppdb_connect() 
    query="UPDATE DataTransfer SET action = '{0}'".format(message_id)
    ocppdbCur.execute(query)
    ocppdb.commit()
    ocppdb_close(ocppdb, ocppdbCur)
    return True

def read_metervalues():
        #MySQL data base Querys to get data
        ocppdb, ocppdbCur = ocppdb_connect() 

        ocppdbCur.execute("SELECT energy FROM MeterValues")
        energy = float(ocppdbCur.fetchone()[0])
        ocppdbCur.execute("SELECT voltage FROM MeterValues")
        voltage = float(ocppdbCur.fetchone()[0])
        #ocppdbCur.execute("SELECT frequence FROM MeterValues")
        #frequencia = float(ocppdbCur.fetchone()[0])
        ocppdbCur.execute("SELECT current FROM MeterValues")
        current = float(ocppdbCur.fetchone()[0])
        ocppdbCur.execute("SELECT power FROM MeterValues")
        power = float(ocppdbCur.fetchone()[0])
        
        ocppdb_close(ocppdb, ocppdbCur)
        return energy, voltage, current, power



def read_lastsessionid(lastsessionid:str):
        sessionid:str
        sessionstatus:str 
        #MySQL data base Querys to get data
        ocppdb, ocppdbCur = ocppdb_connect() 
        ocppdbCur.execute("SELECT LastSessionID, Status FROM session ORDER BY TimeStamp DESC LIMIT 1")
        #sessionid = str(ocppdbCur.fetchone()[0])
        records = ocppdbCur.fetchall()
        sessionid = records[0][0]
        sessionstatus = records[0][1]
        ocppdb_close(ocppdb, ocppdbCur)
        if lastsessionid != sessionid:
            log.info("New SessionID: %s", sessionid)
            log.info("New Session Status: %s", sessionstatus)
            return sessionid, sessionstatus, True
        else:
            return sessionid, sessionstatus, False


def read_hlcstate(lasthlcstate:int ,lastsessionid:str):
        #MySQL data base Querys to get data
        ocppdb, ocppdbCur = ocppdb_connect()
        select_query = """SELECT HlcCurrState FROM hlc_state WHERE SessionID = '{sessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(sessionid_str = lastsessionid)
        ocppdbCur.execute(select_query)
        hlc_state = int(ocppdbCur.fetchone()[0])
        ocppdb_close(ocppdb, ocppdbCur)
        if lasthlcstate != hlc_state:
            log.info("New HLC STATE: %d", hlc_state)
            return hlc_state, True
        else:
            return hlc_state, False
        

def read_authorize(lastsessionid:str):
    id_token_info = ""
    ocppdb, ocppdbCur = ocppdb_connect() 
    select_query = """SELECT * FROM authorize WHERE SessionID = '{sessionid_str}' """.format(sessionid_str = lastsessionid)
    ocppdbCur.execute(select_query)
    for info in ocppdbCur.fetchall():
       id_token_info = info[0]
    ocppdb_close(ocppdb, ocppdbCur)
    if id_token_info == "Rejected" or id_token_info == "Accepted":
        return id_token_info, True
    else:
        return id_token_info, False #Indicates that dont have registered yet in OCPPDB at this session

#Use this function in setChargingProfileResponse after receiving the charging profile from the EVSE
def read_chargingprofile(chargingprofile:dict, maxScheduleTuple, lastsessionid: str):
    ocppdb, ocppdbCur = ocppdb_connect()
    now = time.time()
    #------------------------------------------- Getting the ChargingProfileID extraido do charging_profile ---------------------------------------#
    ocppdbCur.execute("SELECT ChargingProfileID FROM charging_profile ORDER BY TimeStamp DESC LIMIT 1")
    chargingProfileID = int(ocppdbCur.fetchone()[0])
    #------------------------------------------- Inserindo o ChargingProfileID como referência na tabela que possui o SessionID --------------------#
    select_query = """SELECT ChargingRateUnit, TIME_TO_SEC(Duration),  TIME_TO_SEC(StartPeriod), LimitPower, NumberOfPhases FROM charging_schedule WHERE ChargingProfileID = {chargingProfileId} ORDER BY ChargingScheduleID DESC LIMIT 1""".format(
                        chargingProfileId= chargingProfileID)
    ocppdbCur.execute(select_query)
    records = ocppdbCur.fetchall()
    chargingprofile['charging_schedule'][0]['charging_rate_unit'] = records[0][0]
    chargingprofile['charging_schedule'][0]['duration'] = records[0][1]
    chargingprofile['charging_schedule'][0]['charging_schedule_period'][0]['start_period'] = records[0][2]
    chargingprofile['charging_schedule'][0]['charging_schedule_period'][0]['limit'] = records[0][3]
    numberOfPhases = records[0][4]

    ocppdb_close(ocppdb, ocppdbCur)

    return chargingProfileID, numberOfPhases

def write_authorize_token(idTokenInfo, lastsessionid:str):
    
    ocppdb, ocppdbCur = ocppdb_connect()
    now = time.time()
    select_query = """INSERT INTO authorize (TimeStamp, idTokenInfo, SessionID) VALUES (FROM_UNIXTIME({time}),"{idtoken_str}", "{sessionid_str}")""".format(time=now, idtoken_str = idTokenInfo, sessionid_str = lastsessionid)
    ocppdbCur.execute(select_query)
    ocppdb.commit()
    ocppdb_close(ocppdb, ocppdbCur)

def update_authorize(idToken: str, idTokenType:str, idTokenInfo:str, lastsessionid: str):
    ocppdb, ocppdbCur = ocppdb_connect()
    now = time.time()
    print(idToken)
    print(idTokenInfo)
    print(idTokenType)
    update_query = """UPDATE authorize SET TimeStamp = FROM_UNIXTIME({time}), IdToken = '{token}', IdTokenType = '{type}', IdTokenInfo = '{idtoken_inf}' WHERE SessionID = '{sessionid_str}' ORDER BY TimeStamp DESC LIMIT 1;""".format(time=now, token = idToken, type = idTokenType, idtoken_inf = idTokenInfo, sessionid_str = lastsessionid)
    ocppdbCur.execute(update_query)
    ocppdb.commit()
    ocppdb_close(ocppdb, ocppdbCur)

#Use this function in setChargingProfileResponse after receiving the charging profile from the EVSE
def write_chargingprofile(chargingprofile:dict, maxScheduleTuple, lastsessionid: str):
    ocppdb, ocppdbCur = ocppdb_connect()
    #------------------------------------------ Insertion of parameters of the charging profile --------------------------------------------------#
    now = time.time()
    insert_query = """INSERT INTO charging_profile(TimeStamp, IsReceived, StackLevel, ChargingProfilePurpose, ChargingProfileKind) VALUES (FROM_UNIXTIME({time}), 1,{stackLevel}, '{chargingProfilePurpose}', '{chargingProfileKind}')""".format(
                    time=now, stackLevel=chargingprofile['stack_level'],chargingProfilePurpose = chargingprofile['charging_profile_purpose'], chargingProfileKind = chargingprofile['charging_profile_kind'])
    ocppdbCur.execute(insert_query)
    ocppdb.commit()
    #------------------------------------------- Getting the ChargingProfileID extraido do charging_profile ---------------------------------------#
    ocppdbCur.execute("SELECT ChargingProfileID FROM charging_profile ORDER BY TimeStamp DESC LIMIT 1")
    chargingProfileID = int(ocppdbCur.fetchone()[0])
    #------------------------------------------- Inserindo o ChargingProfileID como referência na tabela que possui o SessionID --------------------#
    update_query = """UPDATE iso_charge_parameter_discovery SET Timestamp = FROM_UNIXTIME({time}), ChargingProfileID = {chargingProfileId} WHERE SessionID = '{lastsessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(
                            time=now, chargingProfileId= chargingProfileID, lastsessionid_str=lastsessionid)
    ocppdbCur.execute(update_query)
    ocppdb.commit()
    #------------------------------------------- Inserindo o ChargingSchedule baseado no ChargingProfileID ------------------------------------------#
    print("MAX SCHEDULE TUPLE: ", maxScheduleTuple)
    len_schedule = len(chargingprofile['charging_schedule'])
    for schedule_index in range(len_schedule):
        now = time.time()
        insert_query = """INSERT INTO charging_schedule (TimeStamp, ChargingRateUnit, Duration, StartPeriod, LimitPower, NumberOfPhases, ChargingProfileID) 
                        VALUES (FROM_UNIXTIME({time}), "{unit}", SEC_TO_TIME({duration}), SEC_TO_TIME({startPeriod}), {limitPower}, {numberOfPhases}, {chargingProfileID} )""".format( time=now,
                            unit=chargingprofile['charging_schedule'][schedule_index]['charging_rate_unit'], duration= now + chargingprofile['charging_schedule'][schedule_index]['duration'],
                            limitPower = chargingprofile['charging_schedule'][0]['charging_schedule_period'][0]['limit'],
                            startPeriod = now + chargingprofile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['start_period'], 
                            numberOfPhases = 1, chargingProfileID = chargingProfileID
                        )
        #chargingprofile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['number_phases'] #Optional field
        ocppdbCur.execute(insert_query)
        ocppdb.commit()

    ocppdb_close(ocppdb, ocppdbCur)

    return chargingProfileID

#Use this function in setChargingProfileResponse after receiving the charging profile from the EVSE
def grafana_write_chargingprofile(chargingprofile:dict, maxScheduleTuple, lastsessionid: str):
    ocppdb, ocppdbCur = grafana_connect()
    #------------------------------------------ Insertion of parameters of the charging profile --------------------------------------------------#
    now = time.time()
    insert_query = """INSERT INTO charging_profile(TimeStamp, IsReceived, StackLevel, ChargingProfilePurpose, ChargingProfileKind) VALUES (FROM_UNIXTIME({time}), 1,{stackLevel}, '{chargingProfilePurpose}', '{chargingProfileKind}')""".format(
                    time=now, stackLevel=chargingprofile['stack_level'],chargingProfilePurpose = chargingprofile['charging_profile_purpose'], chargingProfileKind = chargingprofile['charging_profile_kind'])
    ocppdbCur.execute(insert_query)
    ocppdb.commit()
    #------------------------------------------- Getting the ChargingProfileID extraido do charging_profile ---------------------------------------#
    ocppdbCur.execute("SELECT ChargingProfileID FROM charging_profile ORDER BY TimeStamp DESC LIMIT 1")
    chargingProfileID = int(ocppdbCur.fetchone()[0])
    # #------------------------------------------- Inserindo o ChargingProfileID como referência na tabela que possui o SessionID --------------------#
    # update_query = """UPDATE iso_charge_parameter_discovery SET Timestamp = FROM_UNIXTIME({time}), ChargingProfileID = {chargingProfileId} WHERE SessionID = '{lastsessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(
    #                         time=now, chargingProfileId= chargingProfileID, lastsessionid_str=lastsessionid)
    # ocppdbCur.execute(update_query)
    # ocppdb.commit()
    #------------------------------------------- Inserindo o ChargingSchedule baseado no ChargingProfileID ------------------------------------------#
    print("MAX SCHEDULE TUPLE: ", maxScheduleTuple)
    len_schedule = len(chargingprofile['charging_schedule'])
    for schedule_index in range(len_schedule):
        now = time.time()
        insert_query = """INSERT INTO charging_schedule (TimeStamp, ChargingRateUnit, Duration, StartPeriod, LimitPower, NumberOfPhases, ChargingProfileID) 
                        VALUES (FROM_UNIXTIME({time}), "{unit}", SEC_TO_TIME({duration}), SEC_TO_TIME({startPeriod}), {limitPower}, {numberOfPhases}, {chargingProfileID} )""".format( time=now,
                            unit=chargingprofile['charging_schedule'][schedule_index]['charging_rate_unit'], duration= chargingprofile['charging_schedule'][schedule_index]['duration'],
                            limitPower = chargingprofile['charging_schedule'][0]['charging_schedule_period'][0]['limit'],
                            startPeriod = chargingprofile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['start_period'], 
                            numberOfPhases = 1, chargingProfileID = chargingProfileID
                        )
        #chargingprofile['charging_schedule'][schedule_index]['charging_schedule_period'][0]['number_phases'] #Optional field
        ocppdbCur.execute(insert_query)
        ocppdb.commit()

    ocppdb_close(ocppdb, ocppdbCur)

    return chargingProfileID

def update_chargingprofile(lastsessionid: str, chargingProfileID:int):
    ocppdb, ocppdbCur = ocppdb_connect()
    now = time.time()
    update_query = """UPDATE iso_charge_parameter_discovery SET Timestamp = FROM_UNIXTIME({time}), ChargingProfileID = {chargingProfileId} WHERE SessionID = '{lastsessionid_str}' ORDER BY TimeStamp DESC LIMIT 1""".format(
                            time=now, chargingProfileId= chargingProfileID, lastsessionid_str=lastsessionid)
    ocppdbCur.execute(update_query)
    ocppdb.commit()
    ocppdb_close(ocppdb, ocppdbCur)
    return

def write_requeststopcharging(chargingProfileID:str, timesupstatus:bool):
    ocppdb, ocppdbCur = ocppdb_connect()
    select_query = """SELECT TimeUp FROM charging_schedule WHERE ChargingProfileID = {chargingProfileId} ORDER BY TimeStamp DESC LIMIT 1""".format(chargingProfileId= chargingProfileID)
    ocppdbCur.execute(select_query)
    timeUp = ocppdbCur.fetchone()[0]
    if timeUp == 1:
        pass
    else:
        now = time.time()
        update_query = """UPDATE charging_schedule SET Timestamp = FROM_UNIXTIME({time}), TimeUp = {scheduletimeup} WHERE ChargingProfileID = {chargingProfileId}  ORDER BY TimeStamp DESC LIMIT 1""".format(
                                time=now, chargingProfileId= chargingProfileID, scheduletimeup=timesupstatus)
        ocppdbCur.execute(update_query)
        ocppdb.commit()
    ocppdb_close(ocppdb, ocppdbCur)
    return
    

def read_evchargingneeds(lastsessionid:str):
        #MySQL data base Querys to get data
        ocppdb, ocppdbCur = ocppdb_connect()

        # ocppdbCur.execute("SELECT * FROM ev_charging_needs WHERE SessionID='%s'", lastsessionid)
        # requestedEnergyTransfer = int(ocppdbCur.fetchone()[0])
        # eAmount = int(ocppdbCur.fetchone()[1])
        # evMinCurrent = int(ocppdbCur.fetchone()[2])
        # evMaxCurrent = int(ocppdbCur.fetchone()[3])
        # evMaxVoltage = int(ocppdbCur.fetchone()[4])
        # departureTime = int(ocppdbCur.fetchone()[5])

        select_query = """SELECT RequestedEnergyTransfer, EnergyAmount, EvMinCurrent, EvMaxCurrent, EvMaxVoltage, DepartureTime FROM ev_charging_needs WHERE SessionID = '{sessionid_str}' """.format(sessionid_str = lastsessionid)
        ocppdbCur.execute(select_query)
        records = ocppdbCur.fetchall()
        if records == []:
            print("No EVChargingNeeds yeat")
            requestedEnergyTransfer = ""
            eAmount = 0
            evMinCurrent = 0
            evMaxCurrent = 0
            evMaxVoltage = 0
            departureTime = 0
        else:
            requestedEnergyTransfer = records[0][0]
            eAmount = records[0][1]
            evMinCurrent = records[0][2]
            evMaxCurrent = records[0][3]
            evMaxVoltage = records[0][4]
            departureTime = records[0][5]
            print("RequestedEnergyTransfer: ", requestedEnergyTransfer)
            print("EAmount: ", eAmount)
            print("EvMinCurrent: ", evMinCurrent)
            print("EvMaxCurrent: ", evMaxCurrent)
            print("EvMaxVoltage: ", evMaxVoltage)
            print("DepartureTime: ", departureTime)

        ocppdb_close(ocppdb, ocppdbCur)

        return requestedEnergyTransfer, eAmount, evMinCurrent, evMaxCurrent, evMaxVoltage, departureTime

def write_evchargingneeds(lastsessionid:str):
        #MySQL data base Querys to get data
        ocppdb, ocppdbCur = ocppdb_connect()

        select_query = """SELECT * FROM ev_charging_needs WHERE SessionID={sessionid_str}""".format(sessionid_str = lastsessionid)
        ocppdbCur.execute(select_query)
        records = ocppdbCur.fetchall()
        requestedEnergyTransfer = records[0]
        eAmount = records[1]
        evMinCurrent = records[2]
        evMaxCurrent = records[3]
        evMaxVoltage = records[4]
        departureTime = records[5]
        print("RequestedEnergyTransfer: ", requestedEnergyTransfer)
        print("EAmount: ", eAmount)
        print("EvMinCurrent: ", evMinCurrent)
        print("EvMaxCurrent: ", evMaxCurrent)
        print("EvMaxVoltage: ", evMaxVoltage)
        print("DepartureTime: ", departureTime)

        ocppdb_close(ocppdb, ocppdbCur)

        return requestedEnergyTransfer, eAmount, evMinCurrent, evMaxCurrent, evMaxVoltage, departureTime


def read_chargeprogress(lastsessionid:str):
    
    ocppdb, ocppdbCur = ocppdb_connect()   

    ocppdbCur.execute("SELECT ChargeProgress FROM iso_power_delivery WHERE SessionID={sessionid_str} ORDER BY PowerDeliveryID DESC LIMIT 1".format(sessionid_str = lastsessionid))
    chargeProgress = str(ocppdbCur.fetchone()[0])

    ocppdb_close(ocppdb, ocppdbCur)

    return chargeProgress
