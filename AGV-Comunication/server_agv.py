import socket
import sys, os
import threading

from home import checkIPHouse, recvData
from check_ping import check_ping, check_port
from datetime import datetime

# SERVER = '192.168.0.200'
SERVER = '0.0.0.0'
PORT = 10001
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def setup_socket():
      try:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((SERVER, PORT))
      except socket.error as e:
            print(str(e)) 
      server.listen()      
      
def handle_client(conn, addr):

      now = datetime.now()
      current_time = now.strftime("%H:%M:%S")
      print(f"[NEW CONNECTION] Client => {addr[0]} Port=> {addr[1]} connected. {current_time}")

      # 1. check ip where house [return class {one-to-many}]
      HW, HW_name = checkIPHouse(addr[0])

      # 2. add connection
      HW.addConnnection(addr[0], {addr[0]:conn})

      # 3. check ip of phone or AGV
      PhoneOrAGV = HW.IsPhoneOrAGV(addr[0])

      # 4. receive data from client {one-to-one}  call to class home.recvData()
      recvdata = recvData()

      # receive from phone
      if PhoneOrAGV == 'phone':   # task, address
            # ทำงานที่ฟังก์ชัน recvDatafromPhone จนกว่าจะ disconnection
            recvdata.recvDatafromPhone(conn, addr, HW)
      # receive from agv
      else:
            # ทำงานที่ฟังก์ชัน recvDatafromAGV จนกว่าจะ disconnection
            recvdata.recvDatafromAGV(conn, addr, HW, HW_name)

      # xxx. remove connection
      HW.removeConnection(addr[0], conn)
      

# start main app
if __name__ == "__main__":
      # Create socket on port
      # Start listening on socket
      setup_socket()
      
      # check ping connecttion
      check_ping()
      # check_port()
      
      print(f"[LISTENING] Server is listening on {SERVER}")
      print("[STARTING] server is starting...")
      try:
            while True:
                  # Wait for client
                  conn, addr = server.accept()
                  t = threading.Thread(target=handle_client, args=(conn, addr))
                  t.daemon = True
                  t.start()
                  print("[ACTIVE CONNECTIONS] " + str(threading.activeCount() - 1))
      except KeyboardInterrupt:
            conn.close()
            #print(exit)
            sys.exit("Exit by use interrupt")
      except:
            conn.close()


