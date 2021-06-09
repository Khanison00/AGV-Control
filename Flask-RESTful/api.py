from flask_restful import Resource, reqparse
from flask import request, jsonify

from database import Database

'''
    1. Scan Parking
        - insert [plarkid, shopid, qty, flag, ctime, plan_lot] => db.[TBL_AGV_MONITOR_PARKING_DETAILS]
            - get Area, Line, Balance, plan_lot => db.[TBL_LAMA_PART_CALLING]
                - success return 0
                - error return -1
        - update [parkingID, area, line, status] => db.[TBL_AGV_MONITOR_PARKING_STATUS]
    2. Scan OUT
        - Get shoppingList and Quantity & status Next Round order by time => db.[TBL_LAMA_PART_CALLING]
        * Next
            - POST to Update 
                - update FLAG and OUT_TIME => db.[TBL_AGV_MONITOR_PARKING_DETAILS]
                - update STATUS => db.[TBL_AGV_MONITOR_PARKING_STATUS]
            - Get Details from db.[TBL_LAMA_PART_CALLING] join db.[TBL_AGV_TO_SUPPLY]
        * Go
            - send socket to tcp:192.168.2.200:10001
'''

db = Database()

class CheckInternet(Resource):
    def get(self):
        return 200


class ScanParkingCUS(Resource):
    def __init__(self):
        self.home = 'CU-STORE'
        
    # 201  Create 
    # Create new resource Ex. /question
    def post(self):
        json_data = request.get_json(force=True)
        shoppingList = json_data['shoppingList']
        parkingCode = json_data['parkingCode']
        print(shoppingList)
        print(parkingCode)

        # select, insert and update
        for shopID in shoppingList:
            db = Database()
            msg = db.PARKING(shopID, parkingCode, self.home)
            if msg['msg'] != 0:
                break
        print(msg)
        return msg


class ScanOUTCUS(Resource):
    def __init__(self):
        self.home = 'CU-STORE'

    def get(self):
        db = Database()
        parkingCode = db.GET_PARKING()
        # parkingCode = {
        #     "parkingCode": "A01",
        # }

        return parkingCode

    def post(self):
        parkingCode = request.get_json(force=True)['parkingCode']
        print(parkingCode)

        data = {}
        data['Home'] = self.home
        
        try:
            db = Database()
            data['AGVNO'], data['ipAgv'] = db.select_AGV(self.home)
            data['msg'] = 'success'
        except:
            data['msg'] = 'ไม่มีรถ AGV ว่าง'
            return data

        try:
            db = Database()
            data = db.GET_DATA_DETAILS(parkingCode, data)
        except:
            data['msg'] = 'ไม่มี cart ใน parking นี้'
        
        print(data)

        return data


class ScanOUTCUK(Resource):
    def __init__(self):
        self.home = 'CU-KITTING'

    def post(self):
        kittingID = request.get_json(force=True)['kittingID']
        reMark = request.get_json(force=True)['reMark']

        print(kittingID)
        print(reMark)

        db = Database()
        data = db.GET_DATA_CUKITTING(kittingID, reMark, self.home)

        print(data)

        return data

class GetAGVIPCUK(Resource):
    def __init__(self):
        self.home = 'CU-KITTING'
        
    def get(self):
        # get IP AGV
        db = Database()
        data = db.GET_AGV_CUK(self.home)

        print(data)

        return data



class getLineSI(Resource):
    def post(self):
        data = request.get_json(force=True)

        db = Database()
        data = db.get_line_siwh(data['kittingID'])

        return data


class ScanOUTSI(Resource):
    def __init__(self):
        self.home = 'SIWH'

    def post(self):
        kittingID = request.get_json(force=True)['kittingID']
        lineSelect = request.get_json(force=True)['lineSelect']

        print(kittingID, lineSelect)

        db = Database()
        data = db.GET_DATA_SIWH(self.home, kittingID, lineSelect)
        data['line'] = lineSelect

        print(data)

        return data

class getAGVSI(Resource):
    def __init__(self):
        self.home = 'SIWH'

    def get(self):
        db = Database()
        data = db.getAGVSI(self.home)

        return data



class getManualLine(Resource):
    def post(self):
        line = request.get_json(force=True)['line']

        db = Database()
        data = db.getManualLine(line)

        return data


db = Database()
map_mark = db.GET_POINT_NUMBER_MAPPING()
error_mark = db.GET_ERROR_CODE()
data_pack = {}

class PackData:
    def __init__(self):
        self.mapM = map_mark.copy()
        self.error_mark = error_mark.copy()

    def pack_data(self):
        db = Database()
        point_obj = db.GET_AGV_DETAIL()
        for elem in point_obj:
            addPoint = self.mapM[point_obj[elem][0]]
            addPoint.update({'point': point_obj[elem][0]})
            addPoint.update({'agvno': elem})
            # addPoint.update({'error': self.error_mark[point_obj[elem][1]]})
            data_pack.update({str(elem): addPoint})         

# init class PackData
packData = PackData()
packData.pack_data()

class AGVDetails(Resource):
    def __init__(self):
        self.mapM = map_mark.copy()
        self.error_mark = error_mark.copy()
        
    def post(self):
        data = request.get_json(force=True)
        # data[0] -> agv
        # data[1] -> point
        # data[2] -> error
        # get left, top
        new_pack = self.mapM[data[1]].copy()

        # add error
        # new_pack.update({'error': self.error_mark[data[2]]})

        # add agv no.
        new_pack.update({'agvno': data[0]})

        # add point number
        new_pack.update({'point': data[1]})

        if str(data[0]) in data_pack.keys():
            data_pack[str(data[0])] = new_pack
        
        return data_pack
    
    def get(self):
        return data_pack



