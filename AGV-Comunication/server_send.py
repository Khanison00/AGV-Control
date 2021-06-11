import socket
from createDummy import send
import time

SERVER = '0.0.0.0'
PORT = 10001
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server.bind((SERVER, PORT))
except socket.error as e:
    print(str(e))
server.listen(10)

try:
    while True:
            # Wait for client
            conn, addr = server.accept()

            if addr[0] == '192.168.0.204':
                print(f"[NEW CONNECTION] Client => {addr[0]} Port=> {addr[1]} connected.")
                print('ex. start >> 4 | stop >> 8 | charging >> 1')
                cmd = int(input('input command: '))
                task = int(input('input task: '))
                addr = int(input('input address: '))
                print()
                send(conn, task, addr, cmd)
                time.sleep(3)
                conn.close()
            else:
                conn.close()

except KeyboardInterrupt:
    conn.close()