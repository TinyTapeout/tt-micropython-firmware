import math
from ttboard.cocotb.time.system import SystemTime

def get_sim_time(units:str):
    current = SystemTime.current()
    return math.ceil(current.time_in(units))