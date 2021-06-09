from flask import Flask
from flask_restful import Api

from api import CheckInternet, ScanParkingCUS, ScanOUTCUS,  \
    AGVDetails, ScanOUTCUK, GetAGVIPCUK, ScanOUTSI, getLineSI,  \
    getAGVSI, getManualLine

app = Flask(__name__)
api = Api(app)

api.add_resource(CheckInternet, '/')

# CU-STORE
api.add_resource(ScanParkingCUS, '/parkingCUS')
api.add_resource(ScanOUTCUS, '/ScanOUTCUS')
api.add_resource(AGVDetails, '/AGVDetails')

# CU-Kitting
api.add_resource(ScanOUTCUK, '/ScanOUTCUK')
api.add_resource(GetAGVIPCUK, '/GetAGVIPCUK')

# SI-WH
api.add_resource(getLineSI, '/getLineSI')
api.add_resource(ScanOUTSI, '/ScanOUTSI')
api.add_resource(getAGVSI, '/getAGVSI')
api.add_resource(getManualLine, '/getManualLine')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')