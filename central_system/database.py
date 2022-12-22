#Bibliotecas to acess database
from sys import modules
import mysql.connector
from mysql.connector import errorcode

from datetime import datetime

from colorama import init
init()
from colorama import Fore,Back,Style


def database_bootnotification(cp_id, connected):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cur = cnx.cursor()

    date=datetime.utcnow().isoformat()
    # add_bootnotification = ("INSERT INTO BootNotification" "(model,vendorName,timestamp,active)" "VALUES (%s, %s, %s,%s)")
    # data_bootnotification = (model,vendor_name,date,1)

    add_bootnotification = "UPDATE BootNotification SET connected=%s WHERE CP_id=%s"
    data_bootnotification = (connected,cp_id)

    # print(datetime.utcnow().isoformat())
    cur.execute(add_bootnotification, data_bootnotification)
    print(Back.BLACK + 'Write Database BootNotification'+ Style.RESET_ALL)

    cnx.commit()

    cur.close()
    cnx.close()


def database_statusnotification(model,connectorstatus):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


    cur = cnx.cursor()

    date=datetime.utcnow().isoformat()

    # add_statusnotification = ("INSERT INTO StatusNotification" "(model,connectorstatus,evseid,connectorid,timestamp)" "VALUES (%s, %s, %s,%s,%s)")
    # data_statusnotification = (model,connectorstatus,evseid,connectorid,date)

    add_statusnotification = "UPDATE StatusNotification SET connectorstatus=%s WHERE model=%s"
    data_statusnotification = (connectorstatus,model)

    # print(datetime.utcnow().isoformat())
    cur.execute(add_statusnotification, data_statusnotification)
    print(Back.BLACK + 'Write Database StatusNotification'+ Style.RESET_ALL)

    cnx.commit()

    cur.close()
    cnx.close()
    
def database_transactionevent(model,chargingstate):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


    cur = cnx.cursor()

    date=datetime.utcnow().isoformat()
    add_transactionevent = ("UPDATE TransactionEvent SET chargingstate=%s WHERE model=%s")
    data_transactionevent = (chargingstate,model)

    # print(datetime.utcnow().isoformat())
    cur.execute(add_transactionevent, data_transactionevent)
    print(Back.BLACK + 'Write Database TransactionEvent'+ Style.RESET_ALL)

    cnx.commit()

    cur.close()
    cnx.close()
    
def database_metervalues(model,tensao,corrente,potencia,energia):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


    cur = cnx.cursor()

    date=datetime.utcnow().isoformat()
    # add_metervalues = ("INSERT INTO MeterValues" "(model,tensao,corrente,potencia,energia,timestamp)" "VALUES (%s, %s, %s,%s,%s,%s)")
    # add_metervalues = ("UPDATE MeterValues SET tensao=%s,corrente=%s,potencia=%s,energia=%s,timestamp=%s WHERE model=%s")
    # data_metervalues = (tensao,corrente,potencia,energia,date,model)

    # print(datetime.utcnow().isoformat())
    # cur.execute(add_metervalues, data_metervalues)
    cur.execute("""UPDATE MeterValues SET tensao=%s,corrente=%s,potencia=%s,energia=%s,timestamp=%s WHERE model=%s""",(tensao,corrente,potencia,energia,date,model))
    print(Back.BLACK + 'Write Database MeterValues'+ Style.RESET_ALL)

    cnx.commit()

    cur.close()
    cnx.close()

def database_stoptransaction(model):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cur = cnx.cursor()

    sql_select_query = """SELECT State FROM StopTransaction WHERE model = '%s'""" %(model)
    # sql_select_query =("SELECT State FROM StopTransaction WHERE CP_id = 'CP_1'")

    cur.execute(sql_select_query)
    # cur.execute(sql_select_query)
    ola=cur.fetchone()[0]
    print(ola)
    # print [int(i[0]) for i in cursor.fetchall()]

    cnx.commit()
    cur.close()
    cnx.close()

    return ola

def database_setchargingprofile(model):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cur = cnx.cursor()

    sql_select_query1 = """SELECT potencia FROM SetChargingProfile WHERE model = '%s'""" %(model)
    sql_select_query2 = """SELECT changed FROM SetChargingProfile WHERE model = '%s'""" %(model)
    sql_select_query3 = "UPDATE SetChargingProfile SET changed=%s WHERE model = %s" 
    
    
    cur.execute(sql_select_query2)
    changed=cur.fetchone()[0]
    print("foi mudado?",changed)

    if changed=='no':
        print("Nao mudado")
        
        cnx.commit()

        cur.close()
        cnx.close()
        return 0

    if changed=='yes':
        datasetcharginfprofile = ('no',model)
        cur.execute(sql_select_query3,datasetcharginfprofile)
        # cur.execute("""UPDATE SetChargingProfile SET changed='no' WHERE model = '%s'""" %(model))
        
        cur.execute(sql_select_query1)
        power=cur.fetchone()[0]
        print("Se sim, qual a power?",power)

        cnx.commit()

        cur.close()
        cnx.close()
        return power

    
def database_datatransfer(model):
    try:
        cnx = mysql.connector.connect(user='tulio', password='b6XTMkPqpsLqfMkSVmn4',host='10.12.6.15',port='3306',database='evse')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cur = cnx.cursor()

    sql_select_query1 = """SELECT action FROM DataTransfer WHERE model = '%s'""" %(model)
    sql_select_query2 = """SELECT changed FROM DataTransfer WHERE model = '%s'""" %(model)
    sql_select_query3 = "UPDATE DataTransfer SET changed=%s WHERE model = %s" 
    
    cur.execute(sql_select_query1)
    action=cur.fetchone()[0]
    
    cur.execute(sql_select_query2)
    changed=cur.fetchone()[0]
    print("foi mudado?",changed)

    if changed=='no':
        print("Nao mudado")
        
        cnx.commit()

        cur.close()
        cnx.close()
        return action, 'not changed'

    if changed=='yes':
        valueDataTransfer = ('no',model)

        cur.execute(sql_select_query3,valueDataTransfer)
        # cur.execute("""UPDATE SetChargingProfile SET changed='no' WHERE model = '%s'""" %(model))
        
        cur.execute(sql_select_query1)
        action=cur.fetchone()[0]
        print("Acao atualizada('start', 'stop'):",action)

        cnx.commit()

        cur.close()
        cnx.close()
        return action, 'changed'


  


