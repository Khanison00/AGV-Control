# Echo server program
import socket
import random
from random import randint

foo = ['0','1','2','3','4','5','6','7','8','9','a', 'b', 'c', 'd', 'e','f']
def calucalteChecksum(values):
    print(values)
    s = 0
    for i in values:
        s += i

    return s

def convertToString(v):
    result = str(hex(v))[2:][-2:]
    l = len(result)
    if l == 1:
        return '0'+result
    return result



def connect():
    HOST = 'localhost'    # The remote host
    PORT = 10001              # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s

def randomTask():
    return randint(1, 30)

def randomAddress():
    return randint(1, 8)

def randomValue():
    global foo
    a = random.choice(foo)
    b = random.choice(foo)
    return a + b

def createDummy(kcNo):
    
    stx = '02'
    keycartNo = '07' # str(kcNo)
    optComInfo = '00'
    taskNo = '00'
    taskNo2 = '05' # convertToString(randomTask())
    address = '00'
    address2 = '02' # convertToString(randomTask())
    errorCode = '00'
    agvStatus = '07'
    agvCmd = randomValue()#'02'
    battVolt = randomValue()#'00'
    battVolt2 = randomValue()#'ff'
    checksum = calucalteChecksum(bytearray.fromhex(keycartNo+optComInfo+taskNo+taskNo2+address+address2+errorCode+agvStatus+agvCmd+battVolt+battVolt2))
    checksum = convertToString(checksum)
    #checksum = '07'
    #print checksum,checksum[-2:]
    #print type(checksum),checksum,hex(checksum)
    etx = '01'

    #print 

    result = bytearray.fromhex(stx+keycartNo+optComInfo+taskNo+taskNo2+address+address2+errorCode+agvStatus+agvCmd+battVolt+battVolt2+checksum+etx)

    return result

def Test(kcNo):
    s = connect()
    result = createDummy(kcNo)
    s.send(result)
    s.close()

def read():
    global s
    return s.recv(1024)

def send():
    global s
    s.send(createDummy(50))
    from time import sleep 
    sleep(10)
    
def disconnect(s):
    s.close()
    
s = connect()
send()

