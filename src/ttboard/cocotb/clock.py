'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import ttboard.util.time as time
import ttboard.log as logging
log = logging.getLogger(__name__)
_ClockForSignal = dict()

class TimeConverter:
    @classmethod 
    def scale(cls, units:str):
        vals = {
                'fs': 1e-15,
                'ps': 1e-12,
                'ns': 1e-9,
                'us': 1e-6,
                'ms': 1e-3,
                'sec': 1
            }
        if units not in vals:
            raise ValueError(f"Unknown units {units}")
        return vals[units]
    
    @classmethod 
    def time_to_clockticks(cls, clock, t:int, units:str):
        if clock is None:
            clock = Clock.get()
            
        time_secs = t*cls.scale(units)
        return round(time_secs / clock.period_s)
            
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
        self.period = period 
        self.units = units
        self.scale = TimeConverter.scale(units)
        self.running = False
        self.period_s = self.period * self.scale
        
        self.sleep_us = 0
        sleep_us = (1e6*self.period_s/2.0)
        if sleep_us >= 500:
            self.sleep_us = sleep_us
            
    
    def start(self):
        global _ClockForSignal
        _ClockForSignal[self.signal] = self
        
    def numticks_in(self, t:int, units:str):
        return TimeConverter.time_to_clockticks(self, t, units)
    
    def tick(self):
        self.signal.value = 1
        if self.sleep_us:
            time.sleep_us(self.sleep_us)
            
        self.signal.value = 0
        if self.sleep_us:
            time.sleep_us(self.sleep_us)
        
    