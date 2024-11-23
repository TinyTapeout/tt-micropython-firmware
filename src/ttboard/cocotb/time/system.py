'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.cocotb.time.value import TimeValue
from ttboard.cocotb.clock import Clock
import ttboard.util.time as time 

class SystemTime:
    _global_time = TimeValue(0, 'ns')
    _min_sleep_time = TimeValue(10, 'us')
    
    @classmethod 
    def reset(cls):
        cls._global_time = TimeValue(0, 'ns')
        
    @classmethod 
    def current(cls) -> TimeValue:
        return cls._global_time
        
    @classmethod 
    def set_units(cls, units:str):
        cls._global_time = TimeValue(cls._global_time.time, units)
        
    @classmethod 
    def advance(cls, time_or_timevalue, units:str=None):
        if isinstance(time_or_timevalue, TimeValue):
            tstep = time_or_timevalue
        elif isinstance(time_or_timevalue, int) and units is not None:
            tstep = TimeValue(time_or_timevalue, units)
        else:
            raise ValueError
        
        cls._global_time += tstep
        if cls._min_sleep_time < tstep:
            time.sleep_us(tstep.time_in('us'))
                
        
        for clk in Clock.all():
            clk.time_is_now(cls._global_time)
            