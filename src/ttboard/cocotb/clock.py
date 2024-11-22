
'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import gc 
import ttboard.util.time as time
gc.collect()
from ttboard.cocotb.time import TimeValue, SystemTime
gc.collect()

_ClockForSignal = dict()     
class Clock:
    @classmethod 
    def get(cls, signal):
        global _ClockForSignal
        if signal in _ClockForSignal:
            return _ClockForSignal[signal]
        return None
    @classmethod
    def clear_all(cls):
        global _ClockForSignal
        _ClockForSignal = dict()
    @classmethod 
    def all(cls):
        global _ClockForSignal
        return _ClockForSignal.values()
    
    def __init__(self, signal, period, units):
        self.signal = signal
        self.running = False
        
        self.half_period =  TimeValue(period/2, units)
        self.next_toggle = TimeValue(period/2, units)
        self.current_signal_value = 0
        self.sleep_us = 0
        half_per_secs = float(self.half_period)
        if  half_per_secs > 250e-6:
            self.sleep_us = round(half_per_secs*1e-6)
            
        self._toggle_count = 0
        
    
    @property 
    def event_interval(self):
        return self.half_period
    
    def start(self):
        global _ClockForSignal
        _ClockForSignal[self.signal] = self
        
    def num_events_in(self, time_or_timevalue:int, units:str=None):
        if isinstance(time_or_timevalue, TimeValue):
            tv = time_or_timevalue 
        elif units is not None:
            tv = TimeValue(time_or_timevalue, units)
        else:
            raise ValueError
        return tv / self.half_period
    
    def time_has_passed(self):
        while self.next_toggle <= SystemTime.current():
            self.toggle()
            self.next_toggle += self.half_period
    
    def toggle(self):
        # print(f"toggle {self._toggle_count}")
        new_val = 1 if not self.current_signal_value else 0
        self.signal.value = new_val 
        self.current_signal_value = new_val
        if self.sleep_us:
            time.sleep_us(self.sleep_us)
    
    def tick(self):
        # clock will go through whole period, end where it started
        self.toggle()
        self.toggle()
        
    