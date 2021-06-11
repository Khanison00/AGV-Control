'''
1. check ip where house
2. add connection
    - add connection to dict
    - update connection to database (ON)
3. check ip of phone or AGV
4. receive data
    - phone or AGV
    - update Info AGV to database
    - update NEXT ROUTE
    - update LAST ROUTE
5. check AGV status wait
    - wait warning
    - no warning
6. Send data to AGV
    - เรียกใช้ class DataToAGV
        - init GET_ALLPOINT_NUMBER
        - init [wait_point, ipAGV]
    - DataToAGV().check_road  | เรียกใช้โดย  recvData()
        - AGV-1 get_pointNumber == แปลงจาก task, address => point numner 1
        - check_wait_case
            - False is not wait case  => return
            - True is wait case
                - get ip-agv other
                - get position for ip-agv other form database
                - แปลงจาก task2, address2 => point numner 2
                - check point-2 อยู่ในเส้นทางของ point-1 หรือไม่
                    - True => ชน    => return
                    - False => ไม่ชน
                        - กรณีอยู่ระหว่างทาง จุด start[2,3] - 4
                            - True => ชน => return
                            - Flase => ไม่ชน => return
    - True => ไม่ส่งคำสั่งไปหา AGV
    - False => 
        - waitCase == True => ส่งคำสั่ง
        - waitCase == False => ไม่ส่งคำสั้ง


xxx. remove connection
    - remove connection from dict
    - update connection to database (OFF)
    - close connection

'''

from check_route import DataToAGV
from database import Database, SQL
import time, config
from threading import Thread
from createDummy import send
from datetime import datetime
from time import sleep

class HOME:
    def __init__(self, ipAGV, ipPhone):
        self.ipAGV = ipAGV
        self.ipPhone = ipPhone
        self.connection = {}

    def addConnnection(self, addr, conn):
        # add to dict
        if addr not in self.connection.keys():
            self.connection.update(conn)
        else:
            del self.connection[addr]
            self.connection.update(conn)
        # update to database (ON)
        try: 
            con = SQL().connection()
            db = Database(con)
            db.UPDATE_CONNECTION(addr)
        except: pass

    def removeConnection(self, addr, conn):
        # remove from dict
        if addr in self.connection.keys():
            del self.connection[addr]
        # update to database (OFF)
        con = SQL().connection()
        db = Database(con)
        db.UPDATE_DISCONNECTION(addr)
        # close connection
        conn.close()

    def getConnection(self):
        return self.connection

    def IsPhoneOrAGV(self, ip):
        if ip in self.ipPhone:
            # ip phone from CU
            return 'phone'
        else:   # self.ipAGV
            # ip AGV from CU
            return 'agv'


class updateLocation:
    def __init__(self):
        # get all point number
        con = SQL().connection()
        db = Database(con)
        self.All_Point = db.GET_POINT_NUMBER_addWH()
        # get all supply
        con = SQL().connection()
        db = Database(con)
        self.All_Supply = db.GET_ALL_SUPPLY()

    def get_supply(self, Home, Task):
        '''
        supply = {
            wh: {
                task: SI
            }
        }
        '''
        if Home == config.ROOM_KWH:
            return 'PBA'
        else:
            try: return self.All_Supply[Home][str(Task)]
            except: return self.All_Supply[Home][Task]

    def get_pointNumber(self, HW_name, TASK, ADDRESS):
        '''
        point_number = {
            WH1: {
                TASK-1(int): [list-point(int)],
                TASK-2(int): [list-point(int)]
            },
        }
        '''
        point_number = self.All_Point[HW_name][TASK][ADDRESS-1]
        # print(f"\npoint_number => {point_number}\n")
        return point_number

    def update_location(self, AGV_NO, TASK, ADDRESS, ERROR_CODE, BATTERY_VOLTAGE, STATUS, HW_name):
        # update NEXT ROUTE
        if ADDRESS == 4:
            NEXT_ROUTE = self.get_supply(HW_name.upper(), TASK)
            print('NEXT_ROUTE: ' + NEXT_ROUTE)
            con = SQL().connection()
            db = Database(con)
            db.UPDATE_NEXT_ROUTE(AGV_NO, NEXT_ROUTE)
        # # update LAST ROUTE
        if ADDRESS == 1:
            con = SQL().connection()
            db = Database(con)
            LAST_ROUTE = db.GET_NEXT_ROUTE(AGV_NO)
            if LAST_ROUTE.strip() != 'NULL':
                print('LAST_ROUTE => ' + LAST_ROUTE)
                con = SQL().connection()
                db = Database(con)
                db.UPDATE_LAST_ROUTE(AGV_NO, LAST_ROUTE)
                con = SQL().connection()
                db = Database(con)
                db.UPDATE_NEXT_ROUTE(AGV_NO, 'NULL')

        # get point number
        POINT_NUMBER = self.get_pointNumber(HW_name, TASK, ADDRESS)
        con = SQL().connection()
        db = Database(con)
        db.UPDATE_LOCATION(AGV_NO, TASK, ADDRESS, ERROR_CODE, BATTERY_VOLTAGE, STATUS, POINT_NUMBER)
        db.INSERT_LOCATION(AGV_NO, TASK, ADDRESS, ERROR_CODE, BATTERY_VOLTAGE, STATUS, POINT_NUMBER)

        # post to app
        import postTo
        try: postTo.postToApp(AGV_NO, TASK, ADDRESS, POINT_NUMBER, STATUS, ERROR_CODE)
        except: pass
        
        # post to web
        try: postTo.postToServHTTP(AGV_NO, POINT_NUMBER)
        except: pass
        

# call to class updateLocation
Location = updateLocation()

# class house
custore = HOME(config.CUAGV, config.CUphone)
cukitting = HOME(config.HWKAGV, config.HWKphone)
sihw = HOME(config.SIAGV, config.SIphone)

# Get All point number
con = SQL().connection()
db = Database(con)
All_Point = db.GET_POINT_NUMBER_addWH()


class recvData:
    def __init__(self):
        self.recv = []
        self.task_addr_old = [0, 0]

    def recvDatafromPhone(self, conn, addr, HW):
        while True:
            recv_phone = (conn.recv(1024)).decode('utf-8')

            if not recv_phone:
                print (f"Client {addr} ** Disconnect **")
                break
            else:
                # get ip AGV conn
                connAGV = HW.getConnection()
                import json
                data = json.loads(recv_phone)
                
                # ---------- Manage CU-STORE -------------------------
                if data['Home'] == 'CU-STORE':
                    if data['status'] == 'MOVE':
                        # data['Home']
                        # data['ipAgv']
                        # data['task']
                        print('-------- MOVE ON -------')
                        # send T => ? : addr => 1 : status => start
                        # print(connAGV['192.168.0.208'])
                        # send(connAGV['192.168.0.208'], 1, 28, 4)
                        con = SQL().connection()
                        db = Database(con)
                        task_old = db.GET_TASK_Old(data['ipAgv'])
                        # [conn, addr, task, address]
                        send(connAGV[data['ipAgv']], task_old, 1, config.start)

                    elif data['status'] == 'GO':
                        # data['Home']
                        # data['ipAgv']
                        # data['task']
                        # data['Time']

                        if data['Time'] != '00.00':
                            # Edit ------------------------------------------------------------
                            hour1 = int(data['Time'].split('.')[0])
                            minute1 = float(data['Time'].split('.')[1]) / 100
                            TIME_TO = hour1 + minute1

                            statTimeTo = True
                            while statTimeTo:
                                result = time.localtime()
                                hour2 = int(result.tm_hour)
                                minute2 = float(result.tm_min) / 100
                                TIME = hour2 + minute2
                                # TIME = f"{result.tm_hour}:{result.tm_min}"
                                # ถึงเวลาไปส่งแล้ว
                                if TIME_TO >= TIME:
                                    statTimeTo = False
                                time.sleep(60)
                            # End Edit ------------------------------------------------------------

                        # send T => ? : addr => 2 : status => start
                        print('-------- Go -------')
                        send(connAGV[data['ipAgv']], data['task'], 2, config.start)
                    
                    elif data['status'] == 'GONOW':
                        print('-------- Go Now -------')
                        send(connAGV[data['ipAgv']], data['task'], 2, config.start)

                # ---------- Manage CU-KITTING -------------------------
                elif data['Home'] == config.ROOM_KWH:
                    # go have cart
                    if data['status'] == 'GO':
                        print('--------- Go -------------------')
                        # check and go
                        sendtoagv = DataToAGV(config.ROOM_KWH)
                        # [conn, addr, task, address]
                        # sendtoagv.send_to_agv(connAGV[data['ipAgv']], data['ipAgv'], int(data['task']), config.start_cukitting)
                        send(connAGV[data['ipAgv']], int(data['task']), 3, config.start)
                    
                    # go no cart
                    elif data['status'] == 'GOTOLINE':
                        print('--------- GOTOLINE -------------------')
                        sendtoagv = DataToAGV(config.ROOM_KWH)
                        # [conn, addr, task, address]
                        # sendtoagv.send_to_agv(connAGV[data['ipAgv']], data['ipAgv'], int(data['task']), config.start_cukitting)
                        send(connAGV[data['ipAgv']], int(data['task']), 3, config.start)

                # ---------- Manage SIWH -------------------------
                elif data['Home'] == config.ROOM_SI:
                    if data['status'] == 'GO':
                        print('--------- Go -------------------')
                        sendtoagv = DataToAGV(config.ROOM_SI)
                        addressStartSI = 3
                        send(connAGV[data['ipAgv']], int(data['task']), addressStartSI, config.start)

                    elif data['status'] == 'GOGabage':
                        print('--------- GOGabage -------------------')
                        sendtoagv = DataToAGV(config.ROOM_SI)
                        addressStartSI = 3
                        send(connAGV[data['ipAgv']], int(data['task']), addressStartSI, config.start)

                    print(data)

                else:
                    print('No WHEREHOURE')

        conn.close()

    def recvDatafromAGV(self, conn, addr, HW, HW_name):
        # get ip AGV conn
        connAGV = HW.getConnection()

        # t1, t2 = 0, 0
        while True:
            # Disconnect Error Not normal
            try: data = conn.recv(1)
            except:
                print (f"Client {addr} ** Disconnect **")
                break
            # Disconnect Error Normal
            if not data:
                print (f"Client {addr} ** Disconnect **")
                break
            else:
                my_bytes = bytearray(data)
                # control_frame = my_bytes[0] & 256-1   # 2^8
                control_frame = my_bytes[0].numerator

                self.recv.append(control_frame)
                    
                if len(self.recv) == 14:
                    print(f"From IP: {addr} Receiver: {self.recv}")
                    now = datetime.now()
                    current_time = now.strftime("%H:%M:%S")
                    print(f'time = {current_time}')
                    print(f"From IP: {addr} AGV No.: {self.recv[1]}")
                    print(f"From IP: {addr} Task: {self.recv[4]}")
                    print(f"From IP: {addr} Address: {self.recv[6]}")
                    print(f"From IP: {addr} Status: {self.recv[8]}")
                    print(f'POINT_NUMBER => {All_Point[HW_name][self.recv[4]][self.recv[6]-1]}')
                    print(f'length task {self.recv[4]} => {len(All_Point[HW_name][self.recv[4]])}')
                    print()

                    task = self.recv[4]
                    address = self.recv[6]
                    
                    # update info AGV to database
                    # [agv_no, task, address, error_code, status, battery, HW_name]
                    Thread(target = Location.update_location, args = (self.recv[1], self.recv[4], self.recv[6] \
                            ,self.recv[7], self.recv[11], self.recv[8], HW_name)).start()

                    # 5. check AGV status wait
                    # t2 = time.time()

                    # print(f"T-1 = {t1}")
                    # print(f"T-2 = {t2}")
                    # print(f"T2 - T1 = {t2 - t1}")

                    # if self.recv[8] == config.waiting and t2 - t1 > 4:
                    if self.recv[8] == (config.waiting) :
                        # t1 = time.time()
                        print(f"\nFrom IP: {addr} => waiting")
                        # 6. Send data to AGV [Send, No send]
                        sendtoagv = DataToAGV(HW_name)
                        # [conn, addr, task, address]
                        sendtoagv.send_to_agv(conn, addr[0], task, address)
                        
                    

                    # -------- CU-KITTING MANAGE -------------------
                    if HW_name == config.ROOM_KWH and (address == 5):
                        con = SQL().connection()
                        db = Database(con)
                        ipAddr, parking_3 = db.check_parking_2()
                        if parking_3:
                            print('************* Move 2 to 3 *************KITTING 3 GO *************')
                            # self.recv[4] is task
                            send(connAGV[ipAddr], task, 2, config.start)

                    # -------- SIWH MANAGE -------------------
                    if HW_name == config.ROOM_SI and (address == 5):
                        con = SQL().connection()
                        db = Database(con)
                        ipAddr_SI, parking_3_SI = db.check_parking_2_SI()
                        if parking_3_SI:
                            print('************* Move 2 to 3 *************SIWH 3 GO *************')
                            # self.recv[4] is task
                            send(connAGV[ipAddr_SI], task, 2, config.start)


                    self.recv = []    

                    # check car running on dangerous road
                    
                    self.recv = []

        conn.close()


def checkIPHouse(addr):
    if addr in config.CUphone or addr in config.CUAGV:
        HW = custore
        HW_name = config.ROOM_CU
    elif addr in config.HWKphone or addr in config.HWKAGV:
        HW = cukitting
        HW_name = config.ROOM_KWH
    else:
        HW = sihw
        HW_name = config.ROOM_SI
    
    return HW, HW_name

