import datetime

def dec_to_hex(data_int):
        data_byte = hex(data_int)
        data_byte = data_byte[2:].upper()      

        while len(data_byte) != 4:
            data_byte = '0' + data_byte

        return data_byte[:2], data_byte[2:]

def calucalteChecksum(values):
    s = 0
    for i in values:
        s += i

    return s

def convertToHex(v):
    result = str(hex(v))[2:][-2:]
    l = len(result)
    if l == 1:
        return '0' + result
    return result

def createDummy(task, addr, cmd):
    # get datetime
    x = datetime.datetime.now()

    # start byte [0]
    stx = convertToHex(2)
    # communication command [1]
    # print()
    # print('ex. start >> 4 | stop >> 8 | charging >> 1')
    # cmd = int(input('input command: '))
    command = convertToHex(cmd)

    # task No. [2-3]
    # taskNo = '00'
    # taskNo2 = '12'  # 18
    # task = int(input('input task: '))
    taskNo, taskNo2 = dec_to_hex(task)

    # address No. [4-5]
    # address = '00'
    # address2 = '02' # 2
    # addr = int(input('input address: '))
    address, address2 = dec_to_hex(addr)

    # timeSeting [6 - 10]   int to hex[string]
    y = str(x.year)[2:]
    year = convertToHex(int(y))      # 00-99
    month = convertToHex(x.month)    # 1-12
    day = convertToHex(x.day)        # 1-31
    hour = convertToHex(x.hour)      # 0-23
    minute = convertToHex(x.minute)   # 0-59

    # checksum [11]
    checksum = calucalteChecksum(bytearray.fromhex(command + taskNo + taskNo2 + address + address2 + year + month + day + hour + minute))
    checksum = convertToHex(checksum)

    # stop byte [12]
    etx = convertToHex(3)

    # add to array byte
    result = bytearray.fromhex(stx + command + taskNo + taskNo2 + \
                        address + address2 + year + month + day + \
                        hour + minute + checksum + etx)

    return result   # 13 byte
    
def send(conn, task, addr, cmd):
    conn.send(createDummy(task, addr, cmd))
    
    print('-------------------- send --------------------')
    # print()
    