import config
from database import Database, SQL
from createDummy import send
from time import sleep
from threading import Thread, Lock

mutex = Lock()

class DataToAGV:
    def __init__(self, WH_name):
        self.waitCase = False
        self.WH_name = WH_name

        # get all path [TASK, POINT_NUMBER]
        con = SQL().connection()
        db = Database(con)
        self.dict_point = db.GET_ALLPOINT_NUMBER(self.WH_name)
        '''
        dict_point = {
            TASK-1(int): [list-point(int)],
            TASK-2(int): [list-point(int)]
        }
        '''
        # set task-case and ip-agv
        self.agvip_obj = config.set_task_agvip(self.WH_name)
        con = SQL().connection()
        db = Database(con)
        self.task_obj = db.GET_POINTCASE(self.WH_name)
        
    def send_to_agv(self, conn, ipagv, task, addr):
        point_number = self.get_pointNumber(task, addr)

        # ------- MANAGE CU-STORE -----------
        # เปลี่ยนโปรแกรมช่องจอดรถ
        if self.WH_name == config.ROOM_CU and task == 21 and addr == 1:
            send(conn, 15, 1, config.waiting)

        # เช็คช่องจอดรถ
        if self.WH_name == config.ROOM_CU and point_number == config.cuSelectParking:
            print('MANAGE CU-STORE')
            # ช่องจอดรถ  
            self.parkingCU = (config.parkingCU).copy()
            self.task_addressCU = (config.task_addressCU).copy()

            print('--------------- select parking -------------------')
            # ดึงค่า point number ของรถ agv ของ cu-store มาทั้งหมด
            con = SQL().connection()
            db = Database(con)
            get_point = db.get_point_custore(ipagv, self.WH_name)
            # เช็คทีละคัน
            for point in get_point:
                # เช็คว่าคันนี้จอดอยู่ช่องนี้ไหม
                # ไม่ได้จอด
                print(f'point {point} in parking {self.parkingCU} => {point in self.parkingCU}')
                if int(point) in self.parkingCU:    # true == have  [1, 4, 6]
                    print('remove dict => not check continu ..')
                    # remove dict => not check continu ..
                    self.parkingCU.remove(point)
                    self.task_addressCU.pop(point)

            print(f'came in point {point}')
            # เปลี่ยน task, address and go
            task = self.task_addressCU[self.parkingCU[0]][0]
            address = self.task_addressCU[self.parkingCU[0]][1]
            send(conn, task, address, 4)

        # ------- MANAGE CU-KITTING -----------
        elif self.WH_name == config.ROOM_KWH and addr in [1, 2]:
            print('MANAGE CU-KITTING in [1, 2]')

            if addr == 1:
                # Move to addr 2
                print('Move to addr 2')
                sleep(3.5)
                send(conn, task, 1, config.start)
            
            elif addr == 2:
                # check 3-to-null => move to 3
                print('check 3-to-null => move to 3')
                con = SQL().connection()
                db = Database(con)
                parking_3 = db.check_parking_3()
                if parking_3 is None:
                    sleep(1)
                    send(conn, task, 2, config.start)
                    

        # ------- MANAGE SIWH -----------
        elif self.WH_name == config.ROOM_SI and addr in [1, 2]:
            print('MANAGE SIWH in [1, 2]')
            if addr == 1:
                # Move to addr 2
                print('Move to addr 2')
                sleep(3.5)
                send(conn, task, 1, config.start)

            elif addr == 2:
                # check 3-to-null => move to 3
                con = SQL().connection()
                db = Database(con)
                parking_3_SI = db.check_parking_3_SI()
                if parking_3_SI is False:
                    sleep(1)
                    print('check 3-to-null => move to 3')
                    send(conn, task, 2, config.start)

                    

            else : print('can not move to 3')   

        elif self.WH_name == config.ROOM_SI and(point_number == 74):
            print('check street case')
            
            send(conn, task, addr, config.waiting)
        else:
            print('check_road')
            # status is False => ไม่อยู่ใน wait-case
            # status is False => อยู่ใน wait-case แต่ไม่ชน ส่งข้อมูลสั่ง AGV วิ่งได้
            # status is True => ชน
            #send(conn, task, addr, config.waiting)
            status = self.check_road(ipagv, task, addr)
            if status is False and self.waitCase == True:
                print('\nsend data to agv => success !!\n')
                # send(conn, task, addr, 8)       # stop
                send(conn, task, addr, 4)       # start


    def check_road(self, ipagv, task, addr):
        # ------------------------------- เช็คตัวเอง ----------------------------------------
        # แปลงจาก task, address => point numner
        point_number = self.get_pointNumber(task, addr)
    
        print()
        print(f"Point Number 1 => {point_number}\n")

        # ตรวจสอบว่ามีจุดในเส้นทางเสี่ยง(wait-case) ไหม ?
        crash1 = self.check_wait_case(point_number)
        print("crash1 : ", crash1)
        if crash1 is False:
            self.waitCase = False
            # print("waitCase", self.waitCase)
            return False    # ไม่อยู่ใน (wait-case)

        # in WaitCase
        self.waitCase = True
        
        lockQueue = Thread(target = check_agv_other, args = (ipagv, self.task_obj[point_number], self.WH_name))
        lockQueue.start()
        lockQueue.join()
        
        # ไม่ชน
        return False
    
    def get_pointNumber(self, task, addr):
        return self.dict_point[task][addr-1]

    def check_wait_case(self, point):
        if point in self.task_obj.keys():    # มีจุดอยู่ใน dict ไหม (wait-case)
             return True
        else:
            return False

    # ตรวจสอบว่า point-2 อยู่ใน point-2 หรือไม่ ?
    def check_P2_inPathP1(self, p1, p2):
        if p2 in self.task_obj[p1]:
            return True
        else:
            return False
    
            
def check_agv_other(ipagv, point_case, WH_name):
    # ------------------------------- เช็คคันอื่น ทุกคัน ----------------------------------------
    # lock
    mutex.acquire()
    # จนกว่าเส้นทางจะปลอดภัย
    state = True
    sleepTime = 10
    while state:
        # วน loop เช็คทุกคัน
        con = SQL().connection()
        db = Database(con)
        allPointNumber = db.GET_ALLPOINT_NUMBER_LAST(ipagv)
        print()
        for p in allPointNumber:
            if p in point_case:
                crash2 = True
                print(f'crash2-{p}-True')
                sleep(sleepTime)
                break
            else:
                crash2 = False
                print(f'crash2-{p}-False')
        print(f'crash2--False')
              
        if crash2 == False:
            print('... check in my home ...')
            # ------------------------------- เช็คคันอื่น ที่อยู่บ้านตัวเอง ----------------------------------------
            # วน loop เช็คในบ้านตัวเอง
            con = SQL().connection()
            db = Database(con)
            allAddrOfHome = db.GET_ALLADDRESS_OFWH(WH_name, ipagv)
            START_Addr = config.getStartAddr(WH_name)
            print('START_Addr', START_Addr)
            for addr2, status2 in allAddrOfHome:
                print(f"addr2, status2 = {addr2, status2}")
                # กรณีอยู่ระหว่างทาง จุด start[2,3] - 4 
                if  addr2 == START_Addr and status2 == config.traveling:
                    print('อยู่ระหว่างทาง จุด start[2,3] - 4')
                    sleep(sleepTime)
                    state = True
                    break
                else:
                    print('pass')
                    state = False
    # unlock
    mutex.release()