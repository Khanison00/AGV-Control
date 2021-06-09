import pyodbc
import datetime
import pprint as pprint

class Database:
    def __init__(self):
        self.conn = pyodbc.connect('Driver={SQL Server};'
                            'Server=43.72.228.207;'
                            'Database=SMART_PROGRESS;'
                            'UID=mntuser;'
                            'PWD=mntuser;')

    def PARKING(self, shoppingList, parkingCode, wh):
        # x = datetime.datetime.now()
        # date = str(x).split(" ")[0]

        # get detail from db.[TBL_LAMA_PART_CALLING]
        line = None
        area = None
        task = None
        try: 
            # get all data
            project, plan_lot, qty, v_color, part_no, area, line = self.get_all_data(shoppingList)
            # get task
            task = self.select_taskToSupply(line, project, wh)
        except: 
            return {'msg': 'ไม่มีในฐานข้อมูล'}
        
        if line is None or area is None:
            # Line and Area is null
            return {'msg': 'Line and Area is null'}
        elif task is None:
            # No Program AGV
            return {'msg': f"Project: {project}, Line: {line} \nNo Program AGV"}
        else:
            # insert detail
            self.insert_detail(parkingCode, shoppingList, project, plan_lot, qty, v_color, part_no, area, line, task)
            # update status
            self.update_status(parkingCode, wh, area, line, shoppingList, 1)
            # success
            return {'msg': 0}

    def get_next_round(self):
        sql = f"SELECT TOP (1) B.SHOPPING_ID, TIME_TO \
                FROM (SELECT * FROM EKANBAN.dbo.TBL_PART_TIME_SUPPLY ) A \
                LEFT JOIN (SELECT * \
                    FROM EKANBAN.dbo.TBL_LAMA_PART_CALLING \
                    WHERE PLAN_DATE = CONVERT(VARCHAR(10), GETDATE(), 120) \
                    AND [STATUS] LIKE '%Next Round%') B \
                ON A.PLAN_ID = B.PLAN_ID \
                WHERE B.PLAN_ID IS NOT NULL  \
                ORDER BY TIME_TO ASC"
        data = {}
        cursor = self.conn.cursor()
        cursor.execute(sql)

        for row in cursor:
            return row[0], row[1]

    def GET_PARKING(self):
        try:
            shopID, timeTo = self.get_next_round()
            sql = f"SELECT PARKING_ID   \
                    FROM [EKANBAN].[dbo].[TBL_AGV_MONITOR_PARKING_DETAILS]    \
                    WHERE SHOPPING_ID = '{shopID}' and OUT_TIME IS NULL;"
            parkid = self.get_query(sql)
            return {"parkingCode": parkid[0]}
        except:
            return {"parkingCode": "ไม่มีข้อมูล"}

    def GET_DATA_DETAILS(self, parkid, data):
        sql = f"SELECT TOP(1) PD.PROJECT, PD.PLAN_LOT, PD.ACT_QTY, PD.VCOLOR, PD.PART_NO, PD.AREA, PD.LINE, PD.TASK \
                FROM [EKANBAN].[dbo].[TBL_AGV_MONITOR_PARKING_DETAILS] PD   \
                RIGHT JOIN (    \
                    SELECT Shopping_id FROM [EKANBAN].[dbo].[TBL_AGV_MONITOR_PARKING_STATUS]    \
                    WHERE PARKING_ID = '{parkid}'    \
                ) PS    \
                ON PD.SHOPPING_ID = PS.Shopping_id  \
                WHERE PD.OUT_TIME IS NULL   \
                ORDER BY PD.CREATE_TIME DESC"

        cursor = self.conn.cursor()
        cursor.execute(sql)

        for row in cursor:
            data['Project'] = row[0]
            data['planlot'] = row[1]
            data['qty'] = row[2]
            data['vcolor'] = row[3]
            data['part'] = row[4]
            data['area'] = row[5]
            data['line'] = row[6]
            data['task'] = row[7]
        
        try:
            shopID, data['Time'] = self.get_next_round()
        except:
            data['Time'] = '00.00'

        # reset parking
        self.update_detail(parkid)
        self.update_parking(parkid)

        return data

    def update_detail(self, parkingCode):
        sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_MONITOR_PARKING_DETAILS]    \
                SET OUT_TIME = CURRENT_TIMESTAMP, FLAG = 0  \
                WHERE PARKING_ID = '{parkingCode}' and OUT_TIME IS NULL;"
        self.query_database(sql)

    def update_parking(self, parkid):
        sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_MONITOR_PARKING_STATUS] \
            SET STATUS = 0, AREA = NULL, LINE = NULL, Shopping_id = NULL  \
            WHERE PARKING_ID = '{parkid}';"
        self.query_database(sql)

    def update_status(self, parkingCode, wh, area, line, shoppingList, status):
        sql = f"UPDATE [EKANBAN].[dbo].[TBL_AGV_MONITOR_PARKING_STATUS] \
            SET AREA = '{area}', LINE = '{line}', Shopping_id = '{shoppingList}', STATUS = {status}, UPDATE_TIME = CURRENT_TIMESTAMP \
            WHERE WAREHOUSE = '{wh}' and PARKING_ID = '{parkingCode}'"
        self.query_database(sql)

    def get_all_data(self, shoppingList):
        sql = f"SELECT TOP(1) ISNULL(WMS.PROJECT, '-') AS PROJECT, \
            ISNULL(WMS.PLAN_ORDER, '-') AS PLAN_LOT,  \
            ISNULL(WMS.ACT_QTY, 0) AS QTY, \
            CASE    \
                WHEN SPI.Variant IS NULL AND SPI.Color IS NULL THEN 'COMMON' \
                WHEN SPI.Variant IS NOT NULL AND SPI.Color IS NULL THEN SPI.Variant \
                WHEN SPI.Variant IS NULL AND SPI.Color IS NOT NULL THEN SPI.Color \
                WHEN SPI.Variant IS NOT NULL AND SPI.Color IS NOT NULL THEN CONCAT(SPI.Variant, '_', SPI.Color) \
            END AS V_COLOR, \
            ISNULL(WMS.ITEM_NO, '-') AS PART_NO, \
            ISNULL(WMS.AREA, IIF(SUBSTRING(WMS.Shopping_id, 1, 4) = 'ESHP', 'SI', 'CU')) AS AREA, \
            ISNULL(WMS.LINE, '*') \
        FROM [EKANBAN].[dbo].[TBL_PART_CALLING_WMS] WMS \
        LEFT JOIN [SMART_SPICES].[dbo].[TBL_SPICES_VARIANT_MASTER] SPI \
        ON WMS.ITEM_NO = SPI.CU_PART_NO COLLATE Thai_CI_AS \
        WHERE WMS.Shopping_id = '{shoppingList}'"
        project, plan_lot, qty, v_color, part_no, area, line = self.get_query(sql)

        if line == '*':
            sql = f"SELECT B.WS_CD \
                    FROM [EKANBAN].[dbo].[TBL_PART_CALLING_WMS] A \
                    LEFT JOIN [EKANBAN].[dbo].[VIEW_PLAN_SEQ_BY_JON] B \
                    ON A.PLAN_ORDER = B.PLN_LOT_NO \
                    WHERE Shopping_id = 'BSHP210309124609'"
            line = self.get_query(sql)

        return project, plan_lot, qty, v_color, part_no, area, line

    def get_query(self, sql):
            cursor = self.conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                return row

    def query_database(self, sql):
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
    
    def select_AGV(self, wh):
        sql = f"SELECT TOP(1) [AGV_NO],A.[IP_ADDRESS]  \
            FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] A inner join [EKANBAN].[dbo].[TBL_AGV_CONNECTION] B \
            ON A.IP_ADDRESS = B.IP_ADDRESS  \
            WHERE A.WH = '{wh}' and A.ADDRESS_NO = 1 and A.STATUS_NO = 7    \
            ORDER By A.UPDATE_TIME ASC"
        
        cursor = self.conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            return str(row[0]), row[1]
        
    def select_taskToSupply(self, line, Project, wh):
        sql = f"SELECT [TASK] FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY] \
        WHERE LINE = '{line}' and PROJECT = '{Project}' and HOME = '{wh}'"
        
        cursor = self.conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            return str(row[0])
            

    def GET_ERROR_CODE(self):
        sql = "SELECT [CODE],[NAME] FROM [EKANBAN].[dbo].[TBL_AGV_ERROR_CODE]"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        listPointMap = {}
        for row in cursor:
            listPointMap.update(
                {
                    row[0]: row[1].replace('\r', '')
                }
            )
            
        return listPointMap

    def GET_POINT_NUMBER_MAPPING(self):
        sql = "SELECT [POINT_NUMBER],[LEFT],[TOP] FROM [EKANBAN].[dbo].[TBL_AGV_POINT_NUMBER_MAPPING]"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        listPointMap = {}
        for row in cursor:
            listPointMap.update(
                {
                    row[0]:
                        {
                            'left': row[1],
                            'top': row[2]                            
                        }
                }
            )
            
        return listPointMap    
    
    def GET_AGV_DETAIL(self):
        sql = "SELECT [AGV_NO], [POINT_NUMBER], [ERROR_CODE] FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION]"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        point_obj = {}      # Dictionary
        for row in cursor:
            point_obj.update(
                {
                    int(row[0]): [row[1], row[2]]
                }
            )
        return point_obj

        

    def GET_DATA_CUKITTING(self, kittingID, reMark, home):
        data = {}
        data['reMark'] = reMark
        data['Home'] = home

        sql = f"SELECT TOP(1) ISNULL(A.WS_CD, '*')	AS LINE \
            , ISNULL(SUBSTRING(B.PRODUCT_FAMILY,1,CHARINDEX('_', B.PRODUCT_FAMILY)-1), '*') AS PROJECT \
            , ISNULL(SUBSTRING(B.PRODUCT_FAMILY, CHARINDEX('_', B.PRODUCT_FAMILY)+1, LEN(B.PRODUCT_FAMILY)), '-') AS VARIANT \
            , ISNULL(A.PLN_LOT_NO, '-') AS PLN_LOT_NO \
            , ISNULL(A.JOB_ORDER_NO, '-') AS JOB_ORDER_NO \
            , ISNULL(A.PLAN_QTY, 0) AS QUANTITY \
            , ISNULL(A.SCH_START_DATE, '-') AS SCH_START_DATE \
            , ISNULL(A.SHIFT_CD, '-') AS SHIFT_CD \
            , ISNULL(B.PRODUCT_NUMBER, '-') AS PRODUCT_NUMBER \
            FROM [EKANBAN].[dbo].[VIEW_PLAN_SEQ_BY_JON]	A \
            LEFT JOIN  \
            [EKANBAN].[dbo].[TBL_BIOS_PLAN_STATUS]	B \
            ON A.ORDER_NUMBER = B.ORDER_NUMBER \
            WHERE A.KITTING_ID = '{kittingID}'"

        cursor = self.conn.cursor()
        cursor.execute(sql)

        for row in cursor:
            data['line'] = row[0]
            data['project'] = row[1]
            data['variant'] = row[2]
            data['planlot'] = row[3]
            data['imaps'] = row[4]
            data['quantity'] = str(row[5])
            data['outplan'] = row[6]
            data['shift'] = row[7]
            data['productnumber'] = row[8]
            data['msg'] = 'success'

        # check
        if 'line' not in list(data.keys()):
            data['msg'] = 'ไม่มีในฐานข้อมูล'
            return data

        # check line null
        if data['line'] == '*':
            data['msg'] = 'ไม่มี Line'
            return data
        
        # check project null
        if data['project'] == '*':
            data['msg'] = 'ไม่มี Project'
            return data

        # query program
        sql = f"SELECT [TASK] \
                FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY] \
                WHERE HOME = '{home}' and LINE = '{data['line']}' and PROJECT = '{data['project']}'"

        cursor = self.conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            if reMark == 'Off-Line':
                data['task'] = row[0].split(',')[0]
            else: # Main-Line
                data['task'] = row[0].split(',')[1]

        if 'task' not in list(data.keys()):
            data['msg'] = 'ไม่มี program AGV'

        # AGV_NO     => [1, 2]
        # IP AGV     => [192.168.0.202, 192.168.0.204]
        sql = f"SELECT [AGV_NO], A.[IP_ADDRESS]  \
                FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] A inner join [EKANBAN].[dbo].[TBL_AGV_CONNECTION] B \
                ON A.IP_ADDRESS = B.IP_ADDRESS  \
                WHERE A.WH = '{home}' and A.ADDRESS_NO = 3 and A.STATUS_NO = 7 and B.STATUS = 1\
                ORDER By A.UPDATE_TIME ASC"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            data['AGVNO'] = str(row[0])
            data['ipAgv'] = row[1]

        # # Simulate
        # data['AGVNO'] = '1'
        # data['ipAgv'] = '192.168.0.202'
        
        # check agv select
        if 'AGVNO' not in list(data.keys()):
            data['msg'] = 'ไม่มี AGV ที่พร้อมใช้งาน'

        return data

    def GET_AGV_CUK(self, home):
        sql = f"SELECT [AGV_NO], A.[IP_ADDRESS]  \
                FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] A inner join [EKANBAN].[dbo].[TBL_AGV_CONNECTION] B \
                ON A.IP_ADDRESS = B.IP_ADDRESS  \
                WHERE A.WH = '{home}' and A.ADDRESS_NO = 3 and A.STATUS_NO = 7 and B.STATUS = 1\
                ORDER By A.UPDATE_TIME ASC"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        data = {}

        for row in cursor:
            data['AGVNO'] = str(row[0])
            data['ipAgv'] = row[1]
            data['msg'] = 'success'

        # check agv select
        if 'AGVNO' not in list(data.keys()):
            data['msg'] = 'ไม่มี AGV ที่พร้อมใช้งาน'

        return data

    def GET_DATA_SIWH(self, home, kittingID, lineSelect):
        sql = f"SELECT ISNULL(PLAN_LOT, '-') AS PLAN_LOT,     \
                ISNULL(WC_CD, '*') AS WC_CD,     \
                ISNULL(ACT_WS_CD, '*') AS ACT_WS_CD,     \
                ISNULL(MAIN_LINE, '-') AS MAIN_LINE,    \
                ISNULL(SUPPLY_QTY, '-') AS SUPPLY_QTY,     \
                ISNULL(OFF_LINE, '-') AS OFF_LINE,    \
                ISNULL(OFFLINE_QTY, '-') AS OFFLINE_QTY,     \
                ISNULL(ENTRY_DATE, '-') AS ENTRY_DATE,     \
                ISNULL(ENTRY_TIME, '-') AS ENTRY_TIME,     \
                ISNULL(USER_ID, '-') AS USER_ID    \
                FROM [EKANBAN].[dbo].[VIEW_SUPPLY_EKANBAN]    \
                WHERE KITTING_ID = '{kittingID}'"

        cursor = self.conn.cursor()
        cursor.execute(sql)
        data = {}
        data['msg'] = 'ไม่มีในฐานข้อมูล'
        data['Home'] = 'SIWH'

        for row in cursor:
            data['PLAN_LOT'] = row[0]
            data['WC_CD'] = row[1]
            data['ACT_WS_CD'] = row[2]
            data['MAIN_LINE'] = row[3]
            data['SUPPLY_QTY'] = row[4]
            data['OFF_LINE'] = row[5]
            data['OFFLINE_QTY'] = row[6]
            data['ENTRY_DATE'] = row[7]
            data['ENTRY_TIME'] = row[8]
            data['USER_ID'] = row[9]
            data['msg'] = 'success'

        if data['msg'] == 'ไม่มีในฐานข้อมูล':
            return data

        # check Line is null
        if (data['WC_CD'] == '*') and (data['ACT_WS_CD'] == '*'):
            data['msg'] = 'ไม่มี Line'
            return data

        # query program
        sql = f"SELECT TASK \
                FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY]   \
                WHERE HOME = '{home}' and LINE = '{lineSelect}'"

        cursor = self.conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            data['task'] = row[0]

        if 'task' not in list(data.keys()):
            data['msg'] = 'ไม่มี program AGV'

        sql = f"SELECT [AGV_NO], A.[IP_ADDRESS]  \
                FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] A inner join [EKANBAN].[dbo].[TBL_AGV_CONNECTION] B \
                ON A.IP_ADDRESS = B.IP_ADDRESS  \
                WHERE A.WH = '{home}' and A.ADDRESS_NO = 3 and A.STATUS_NO = 7 and B.STATUS = 1 \
                ORDER By A.UPDATE_TIME ASC"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            data['AGVNO'] = str(row[0])
            data['ipAgv'] = row[1]

        # Simulator
        # data['AGVNO'] = str(0)
        # data['ipAgv'] = '192.168.0.0'

        # check agv select
        if 'AGVNO' not in list(data.keys()):
            data['msg'] = 'ไม่มี AGV ที่พร้อมใช้งาน'

        return data

    def get_line_siwh(self, kittingID):
        sql = f"  SELECT ISNULL(WC_CD, '*') AS WC_CD,   \
                    ISNULL(ACT_WS_CD, '*') AS ACT_WS_CD     \
                    FROM [EKANBAN].[dbo].[VIEW_SUPPLY_EKANBAN]      \
                    WHERE KITTING_ID = '{kittingID}'"   
        cursor = self.conn.cursor()
        cursor.execute(sql)
        data = {}
        data['msg'] = 'ไม่มีข้อมูล'
        for row in cursor:
            data['WC_CD'] = row[0]
            data['ACT_WS_CD'] = row[1]
            data['msg'] = 'success'

        return data

    def getAGVSI(self, home):
        sql = f"SELECT [AGV_NO], A.[IP_ADDRESS]  \
                FROM [EKANBAN].[dbo].[TBL_AGV_LOCATION] A inner join [EKANBAN].[dbo].[TBL_AGV_CONNECTION] B \
                ON A.IP_ADDRESS = B.IP_ADDRESS  \
                WHERE A.WH = '{home}' and A.ADDRESS_NO = 3 and A.STATUS_NO = 7 and B.STATUS = 1 \
                ORDER By A.UPDATE_TIME ASC"
        cursor = self.conn.cursor()
        cursor.execute(sql)

        data = {}
        data['msg'] = 'success'

        for row in cursor:
            data['AGVNO'] = str(row[0])
            data['ipAgv'] = row[1]

        # Simulator
        # data['AGVNO'] = str(0)
        # data['ipAgv'] = '192.168.0.0'

        # check agv select
        if 'AGVNO' not in list(data.keys()):
            data['msg'] = 'ไม่มี AGV ที่พร้อมใช้งาน'

        return data

    def getManualLine(self, line):
        sql = f"SELECT DISTINCT [WC_CD], substring([WC_CD], 3, 4) AS NUMBER \
                FROM [EKANBAN].[dbo].[VIEW_SUPPLY_EKANBAN]	A \
                WHERE LEN(KITTING_ID) = 21 and LEN([ACT_WS_CD]) > 3  and  \
                        LEN([ACT_WS_CD]) < 5  and  \
                        LEN([WC_CD]) != 0 and  \
                        substring([WC_CD], 1, 2) = '{line}' \
                UNION \
                SELECT DISTINCT [ACT_WS_CD], substring([ACT_WS_CD], 3, 4) AS NUMBER \
                FROM [EKANBAN].[dbo].[VIEW_SUPPLY_EKANBAN]	B \
                WHERE LEN(KITTING_ID) = 21 and LEN([ACT_WS_CD]) > 3  and  \
                        LEN([ACT_WS_CD]) < 5  and  \
                        LEN([ACT_WS_CD]) != 0  and  \
                        substring([ACT_WS_CD], 1, 2) = '{line}' \
                ORDER BY [WC_CD]"

        cursor = self.conn.cursor()
        cursor.execute(sql)

        elem = []

        for row in cursor:
            elem.append(row[0])

        return elem


# data = Database().PARKING('ESHP210223085142', 'A03', 'CU-STORE')
# print(data)

# task = Database().select_taskToSupply('FA12', 'PDX203', 'CU-STORE')
# print(task)

#data = Database().GET_DATA_SIWH('CU-KITTING', 'N34792170210309981001')
#print(data)

#data = Database().GET_AGV_DETAIL(1,2,3)
#print(data)