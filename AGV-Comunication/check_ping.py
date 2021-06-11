import os
from database import Database, SQL
from time import sleep
import threading
import socket

def check_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # get all ip AGV from database
    con = SQL().connection()
    db = Database(con)
    allIP, rememberConnectState = db.get_allIP_from_DB()

    for ip in allIP:
       try:
          response = s.connect((ip, int(10001)))
          s.shutdown(2)
          # update disconnect to database
          con = SQL().connection()
          db = Database(con)
          db.UPDATE_DISCONNECTION(ip)
          # upadte disconnect in dict
          rememberConnectState[ip] = 0
          return True
       except:
          # update connect to database
          con = SQL().connection()
          db = Database(con)
          db.UPDATE_CONNECTION(ip)
          # update connect in dict
          rememberConnectState[ip] = 1
          return False
	# start every 180 s
    timer = threading.Timer(20.0, check_port).start()

def check_ping():
    # get all ip AGV from database
    con = SQL().connection()
    db = Database(con)
    allIP, rememberConnectState = db.get_allIP_from_DB()
    
    for ip in allIP:
        response = os.system("ping -n 1 " + ip)
        if response == 0 and rememberConnectState[ip] == 0:
            # update connect to database
            con = SQL().connection()
            db = Database(con)
            db.UPDATE_CONNECTION(ip)
            # update connect in dict
            rememberConnectState[ip] = 1

        elif response != 0 and rememberConnectState[ip] == 1:
            # update disconnect to database
            con = SQL().connection()
            db = Database(con)
            db.UPDATE_DISCONNECTION(ip)
            # upadte disconnect in dict
            rememberConnectState[ip] = 0
            
    # start every 180 s --> 10 sec
    timer = threading.Timer(90.0, check_ping).start()
