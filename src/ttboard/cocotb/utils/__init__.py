
from ttboard.cocotb.time import SystemTime

def get_sim_time(units:str):
    current = SystemTime.current()
    return current.time_in(units)