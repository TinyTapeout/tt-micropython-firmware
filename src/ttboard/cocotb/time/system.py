'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.cocotb.time.value import TimeValue
from ttboard.cocotb.clock import Clock

class SystemTime:
    _global_time = TimeValue(0, 'ns')
    
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
            cls._global_time += time_or_timevalue
        elif isinstance(time_or_timevalue, int) and units is not None:
            cls._global_time += TimeValue(time_or_timevalue, units)
        else:
            raise ValueError
        
        for clk in Clock.all():
            clk.time_is_now(cls._global_time)
            