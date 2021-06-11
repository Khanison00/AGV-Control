# --------------------------------- AGV Status ----------------------------------
waiting = 0x07      # 7
waiting2 = 0x15      # 21
traveling = 0x13    # 19
stop = 0x03         # 3
start = 0x04        # 4

# --------------------------------- ip from house ? ---------------------------------
CUAGV = ['192.168.0.211', '192.168.0.213']
CUphone = ['192.168.0.250']

HWKAGV = ['192.168.0.214', '192.168.0.215']
HWKphone = ['192.168.0.251']

SIAGV = ['192.168.0.216', '192.168.0.217']
SIphone = ['192.168.0.252']

# --------------------------------- start address ---------------------------------
start_custore = 2
start_cukitting = 3
start_siwh = 3

# -------------------------------- config ทางเข้าจอด -------------------------
# CU - STORE
cuSelectParking = 12
parkingCU = [1, 4, 6]
task_addressCU = {
    1: [1, 31],      # SI - MAX 33
    4: [21, 35],      # CT - MAX 37
    6: [15, 44]       # CU - MAX 45
}
# --------------------------------- WH Name ---------------------------------
ROOM_CU = 'CU-STORE'
ROOM_KWH = 'CU-KITTING'
ROOM_SI = 'SIWH'
# ------------------------------ End WH Name ---------------------------------

def getStartAddr(wh):
    if wh == ROOM_CU:
        START_Addr = start_custore
    elif wh == ROOM_KWH:
        START_Addr = start_cukitting
    else:   # ROOM_SI
        START_Addr = start_siwh
    return START_Addr

# ------------------------------ Set Task And IPAGV ------------------------------

def set_task_agvip(ROOM):
    if ROOM == ROOM_KWH:
        # agvip_obj = WH_Kitting()
        agvip_obj = HWKAGV
    elif ROOM == ROOM_SI:
        # agvip_obj = SI_HW()
        agvip_obj = SIAGV
    else:   # CU-STORE
        # agvip_obj = CU_STORE()
        agvip_obj = CUAGV
    return agvip_obj

# --------------------------------------------------------------------------------------------