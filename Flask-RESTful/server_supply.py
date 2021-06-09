from flask import Flask, render_template, jsonify, request
import pyodbc

class connectSQL:
    def __init__(self):
        self.conn = pyodbc.connect('Driver={SQL Server};'
                    'Server=43.72.228.207;'
                    'Database=SMART_PROGRESS;'
                    'UID=mntuser;'
                    'PWD=mntuser;'
                    'Trustedconnection=yes;'
                    'MARS_Connection=yes;')

    def createConnection(self):
        return self.conn


app = Flask(__name__)

@app.route('/supply', methods=['GET'])
def index():
    sql = f"SELECT [SUPPLY] ,[LINE] ,[PROJECT] ,[TASK] ,[HOME] FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY]"
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    data = []

    for row in cursor:
        data.append([row[0], row[1], row[2], row[3], row[4]])

    return render_template('index.html', data=data)

@app.route('/supply/<jsgetdata>')
def get_javascript_data(jsgetdata):
    path = jsgetdata.split('@')[0]
    supply = jsgetdata.split('@')[1]

    if path == 'getdata':
        return getData(supply)
    elif path == 'getproject':
        if supply == 'PBA':
            supply = 'CU'
        return getProject(supply)
    elif path == 'getline':
        if supply == 'PBA':
            supply = 'CU'
        return getLine(supply)

def getData(supply):
    sql = f"SELECT [SUPPLY] ,[LINE] ,[PROJECT] ,[TASK] ,[HOME] FROM [EKANBAN].[dbo].[TBL_AGV_TO_SUPPLY] WHERE SUPPLY = '{supply}' ORDER BY TASK"
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    data = []

    for row in cursor:
        data.append([row[0], row[1], row[2], row[3], row[4]])

    return jsonify(data)

def getProject(supply):
    sql = f"SELECT DISTINCT([PROJECT]) FROM [EKANBAN].[dbo].[TBL_PART_CALLING_WMS] WHERE PROJECT IS NOT NULL and AREA = '{supply}' ORDER BY PROJECT"
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    data = []

    for row in cursor:
        data.append(row[0])

    return jsonify(data)

def getLine(supply):
    sql = f"SELECT DISTINCT(LINE) FROM [EKANBAN].[dbo].[TBL_PART_CALLING_WMS] WHERE AREA IS NOT NULL and AREA = '{supply}' ORDER BY LINE"
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    data = []

    for row in cursor:
        data.append(row[0])

    return jsonify(data)

@app.route('/supply/add', methods=['POST'])
def addData():
    sql = request.values['sql']
    print(sql)
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.commit()

    return '', 200

@app.route('/supply/delete', methods=['POST'])
def deleteData():
    sql = request.values['sql']
    print(sql)
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.commit()

    return '', 200

@app.route('/supply/update', methods=['POST'])
def updateData():
    sql = request.values['sql']
    print(sql)
    conn = connectSQL().createConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.commit()

    return '', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
    