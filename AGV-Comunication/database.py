import pyodbc
import config

class SQL:
      def __init__(self):
            self.conn = pyodbc.connect('Driver={SQL Server};'
                            'Server=43.72.228.207;'
                            'Database=SMART_PROGRESS;'
                            'UID=mntuser;'
                            'PWD=mntuser;')
      def connection(self):
            return self.conn


class Database:
      def __init__(self, connection):
            # self.conn = pyodbc.connect('Driver={SQL Server};'
            #                 'Server=43.72.228.207;'
            #                 'Database=SMART_PROGRESS;'
            #                 'UID=mntuser;'
            #                 'PWD=mntuser;')
            self.conn = connection

      # ---------------- Class updateLocation ------------------------------------------
      def UPDATE_LOCATION(self, AGV_NO, TASK_NO, ADDRESS_NO, ERROR_CODE, BATTERY_VOLTAGE, STATUS_NO, POINT_NUMBER):
            sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_LOCATION] \
                  SET TASK_NO = {TASK_NO}, ADDRESS_NO = {ADDRESS_NO}, ERROR_CODE = {ERROR_CODE}, \
                  BATTERY_VOLTAGE = {BATTERY_VOLTAGE}, UPDATE_TIME = CURRENT_TIMESTAMP, \
                        STATUS_NO = {STATUS_NO}, POINT_NUMBER = {POINT_NUMBER}      \
                  WHERE AGV_NO = {AGV_NO};"
            try: self.QUERY_DATABASE(sql)
            except: pass

      def INSERT_LOCATION(self, AGV_NO, TASK_NO, ADDRESS_NO, ERROR_CODE, BATTERY_VOLTAGE, STATUS_NO, POINT_NUMBER):
            sql = f"INSERT INTO [EKANBAN].[dbo].[TBL_AGV_LOCATION_HISTORY] \
                  (TASK_NO,ADDRESS_NO,ERROR_CODE,BATTERY_VOLTAGE,UPDATE_TIME,STATUS_NO,POINT_NUMBER,AGV_NO) \
                  VALUES ({TASK_NO},{ADDRESS_NO},{ERROR_CODE},{BATTERY_VOLTAGE},CURRENT_TIMESTAMP,{STATUS_NO},{POINT_NUMBER},{AGV_NO});"
            try: self.QUERY_DATABASE(sql)
            except: pass      

      def GET_POINT_NUMBER_addWH(self):
            sql = "SELECT [AGV_OF_HW], [TASK], [POINT_NUMBER] \
                  FROM [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER];"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            dict_point, dict_cu, dict_kwh, dict_si = {}, {}, {}, {}
            for row in cursor:
                  if row[0] == config.ROOM_CU:
                        listPoint_cu = [int(x) for x in list(row[2].split(','))]
                        dict_cu.update({row[1]:listPoint_cu})
                  elif row[0] == config.ROOM_KWH:
                        listPoint_kwh = [int(x) for x in list(row[2].split(','))]
                        dict_kwh.update({row[1]:listPoint_kwh})
                  else:       # SIWH
                        listPoint_si = [int(x) for x in list(row[2].split(','))]
                        dict_si.update({row[1]:listPoint_si})
            dict_point[config.ROOM_CU] = dict_cu
            dict_point[config.ROOM_KWH] = dict_kwh
            dict_point[config.ROOM_SI] = dict_si
            return dict_point

      def GET_NEXT_ROUTE(self, agvno):
            sql = f"SELECT [NEXT_ROUTE]  \
                  FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION]   \
                  WHERE AGV_NO = {agvno};"
            row = self.GET_QUERY(sql)
            return row[0]

      def UPDATE_LAST_ROUTE(self, AGV_NO, LAST_ROUTE):
            sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_LOCATION] \
                  SET LAST_ROUTE = '{LAST_ROUTE}'      \
                  WHERE AGV_NO = {AGV_NO};"
            self.QUERY_DATABASE(sql)
      
      # def GET_SUPPLY(self, TASK, HOME):
      #       sql = f"SELECT SUPPLY   \
      #       FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY]  \
      #       WHERE TASK = {TASK} and HOME = '{HOME}';"
      #       supply = self.GET_QUERY(sql)
      #       return supply[0]

      def GET_ALL_SUPPLY(self):
            sql = "SELECT [HOME], [TASK], [SUPPLY]    \
                  FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY];"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            dict_supply, dict_taskcu, dict_taskkwh, dict_tasksi = {}, {}, {}, {}
            for row in cursor:
                  if row[0] == config.ROOM_CU:
                        dict_taskcu.update({row[1]:row[2]})
                  elif row[0] == config.ROOM_KWH:
                        dict_taskkwh.update({row[1]:row[2]})
                  else:       # SIWH
                        dict_tasksi.update({row[1]:row[2]})
            dict_supply[config.ROOM_CU] = dict_taskcu
            dict_supply[config.ROOM_KWH] = dict_taskkwh
            dict_supply[config.ROOM_SI] = dict_tasksi
            return dict_supply

      def UPDATE_NEXT_ROUTE(self, AGV_NO, NEXT_ROUTE):
            sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_LOCATION] \
                  SET NEXT_ROUTE = '{NEXT_ROUTE}'      \
                  WHERE AGV_NO = {AGV_NO};"
            self.QUERY_DATABASE(sql)

      # ---------------- Class HOME -------------------------------------------------------
      def UPDATE_CONNECTION(self, IP):
            sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_CONNECTION]    \
                  SET [STATUS] = 1, CONNECT_TIME = CURRENT_TIMESTAMP    \
                  WHERE [IP_ADDRESS] = '{IP}';"
            self.QUERY_DATABASE(sql)

      def UPDATE_DISCONNECTION(self, IP):
            sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_CONNECTION]    \
                  SET [STATUS] = 0, DIS_TIME = CURRENT_TIMESTAMP  \
                  WHERE [IP_ADDRESS] = '{IP}';"
            self.QUERY_DATABASE(sql)
            
      # ---------------- File config.py -------------------------------------------------------
      def GET_POINTCASE(self, wh):
            sql = f"SELECT POINT, PATH_RANGE FROM [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER_CASE] WHERE AGV_OF_HW = '{wh}'"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            hw_dict = {}
            for row in cursor:
                  listCase = [int(x) for x in list(row[1].split(','))]
                  hw_dict.update({row[0]:listCase})
                  
            return hw_dict

      # ---------------- File point_number.py -------------------------------------------------------
      def INSERT_POINT_NUMBER(self, task, point, room):
            sql = f"INSERT INTO [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER] (TASK, POINT_NUMBER, AGV_OF_HW)    \
                  VALUES ({task}, '{point}', '{room}');"
            self.QUERY_DATABASE(sql)
            
      def INSERT_POINT_NUMBER_CASE(self, point, path, home):
            sql = f"INSERT INTO [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER_CASE] (POINT, PATH_RANGE, AGV_OF_HW)    \
                  VALUES ({point}, '{path}', '{home}');"
            self.QUERY_DATABASE(sql)

      def DELETE_POINT(self, room, task):
            sql = f"DELETE FROM [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER]   \
                  WHERE [AGV_OF_HW] = '{room}' and [TASK] = {task};"
            self.QUERY_DATABASE(sql)

      def INSERT_SUPPLY(self, row):
            # INSERT [supply, line, project, task, home]
            sql = f"INSERT INTO [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY] (SUPPLY, LINE, PROJECT, TASK, HOME)     \
                  VALUES ('{row[0]}', '{row[1]}', '{row[2]}', {row[3]}, '{row[4]}');"
            self.QUERY_DATABASE(sql)
            
      # ---------------- Class DataToAGV ------------------------------------------
      def GET_ALLPOINT_NUMBER_LAST(self, ip):
            sql = f"SELECT [POINT_NUMBER] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE IP_ADDRESS != '{ip}';"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            point_number = []
            for row in cursor:
                  point_number.append(row[0])
            return set(point_number)
      
      def GET_ALLADDRESS_OFWH(self, WH, ip):
            sql = f"SELECT [ADDRESS_NO] ,[STATUS_NO] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE WH = '{WH}' and IP_ADDRESS != '{ip}';"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            allAddrOfHome = []
            for row in cursor:
                  allAddrOfHome.append([row[0], row[1]])
            return allAddrOfHome
            
      def GET_TASK_ADDRESS(self, ip):
            sql = f"SELECT [TASK_NO] ,[ADDRESS_NO] ,[STATUS_NO] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE IP_ADDRESS = '{ip}';"
            row = self.GET_QUERY(sql)
            return row

      def GET_ALLPOINT_NUMBER(self, HW_name):
            sql = f"SELECT [TASK], [POINT_NUMBER] FROM [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER] WHERE AGV_OF_HW = '{HW_name}';"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            dict_point = {}
            for row in cursor:      # row[0] = task, row[1] = path => point number
                  listPoint = [int(x) for x in list(row[1].split(','))]
                  dict_point.update({row[0]:listPoint})
            return dict_point

      # ---------------- Public Function qurey database ------------------------------
      def QUERY_DATABASE(self, sql):
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()

      def GET_QUERY(self, sql):
            cursor = self.conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                  return row
            
      def get_allIP_from_DB(self):
            sql = 'SELECT [IP_ADDRESS], [STATUS] FROM [EKANBAN].[dbo].[TBL_AGV_CONNECTION]'
            cursor = self.conn.cursor()
            cursor.execute(sql)
            allIP = []
            rememberConnectState = {}
            for row in cursor:
                  allIP.append(row[0])
                  rememberConnectState.update({row[0]:row[1]})
            return allIP, rememberConnectState
      
      def insert_point_maping(self):
            for i in range(186, 201):
                  print(i)
                  
                  try:
                        sql = f'INSERT INTO [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER_MAPPING] ([POINT_NUMBER], [LEFT], [TOP])\
                        VALUES ({i}, 0, 0)' 
                        
                        self.QUERY_DATABASE(sql)
                  except:
                        pass
                  
      def get_point_custore(self, ipagv, wh):
            sql = f"SELECT [POINT_NUMBER] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION]   \
                  WHERE WH = '{wh}' and IP_ADDRESS != '{ipagv}'"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            data = []
            for row in cursor:
                  data.append(row[0])
            return data
      
      def INSERT_POINT_MAPPING(self, point, left, top):
            sql = f"INSERT INTO [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER_MAPPING] ([POINT_NUMBER], [LEFT], [TOP])    \
                  VALUES ({point}, {left}, {top})"
            self.QUERY_DATABASE(sql)

      def GET_TASK_Old(self, ip):
            sql = f"SELECT TASK_NO FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION]    \
                  WHERE IP_ADDRESS = '{ip}'"
            cursor = self.conn.cursor()
            cursor.execute(sql)

            for row in cursor:
                  return int(row[0])

      def check_parking_3(self):
            parking_3 = None
            sql = "SELECT AGV_NO FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE WH = 'CU-KITTING' and ADDRESS_NO = 3"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                  parking_3 = row[0]
            return parking_3

      def check_parking_2(self):
            parking_2 = False
            sql = "SELECT [IP_ADDRESS] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE WH = 'CU-KITTING' and ADDRESS_NO = 2"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                  ipAddr = row[0]
                  parking_2 = True
                  return ipAddr, parking_2
            return None, False

      def check_parking_3_SI(self):
            sql = "SELECT AGV_NO FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE WH = 'SIWH' and (ADDRESS_NO = 3 or ADDRESS_NO = 1 or ADDRESS_NO = 4)"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                  return True
            return False

      def check_parking_2_SI(self):
            parking_2 = False
            sql = "SELECT [IP_ADDRESS] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] WHERE WH = 'SIWH' and ADDRESS_NO = 2"
            cursor = self.conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                  ipAddr = row[0]
                  parking_2 = True
                  return ipAddr, parking_2
            return None, False
            


# A = Database().GET_ALLPOINT_NUMBER('CU-KITTING')
# print(A)
# point = Database().GET_ALLPOINT_NUMBER_LAST('192.168.0.202')
# print(point)
# addr = Database().GET_ALLADDRESS_OFWH('CU-KITTING', '192.168.0.202')
# print(addr)

# data = Database().get_point_custore('192.168.0.206')

# conn = SQL().connection()
# ALL_SUP = Database(conn).GET_ALL_SUPPLY()
# print( 
#      ALL_SUP['CU-KITTING']
# )
