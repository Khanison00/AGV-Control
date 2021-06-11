import requests

def postToApp(agv, task, addr, point, des, error):
    obj = {
        "AGV_NO": agv,
        "TASK_NO": task,
        "ADDRESS_NO": addr,
        "POINT_NUMBER": point,
        "DESCRIPTION": des,
        "ERROR_CODE": error
    }

    r = requests.post('http://192.168.0.250:8080', json=obj)
    # print(r.status_code)
    
def postToServHTTP(agv, point):
    obj = [agv, point]
    r = requests.post('http://43.72.228.122:5000/AGVDetails', json=obj)
    # print(r.status_code)



# postToApp(5, 100, 3000, 1800, 19, 3)
# postToServHTTP(1, 1)