'''
Created on Nov 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import gc 
gc.collect()
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
        time_secs = t*cls.scale(units)
        return round(time_secs / clock.period_s)
    
    @classmethod 
    def rescale(cls,t:int, units:str, to_units:str):
        return t*(cls.scale(units)/cls.scale(to_units))
    
class TimeValue:
    def __init__(self, time:int, units:str):
        self.time = time 
        self._units = units
        self.scale = TimeConverter.scale(units)
    
    @property 
    def units(self):
        return self._units 
    @units.setter 
    def units(self, set_to:str):
        self._units = set_to 
        self.scale = TimeConverter.scale(set_to)
    def __float__(self):
        return self.time*self.scale
    
    def __gt__(self, other):
        if isinstance(other, (TimeValue, float)):
            return float(self) > float(other)
        raise ValueError
    
    def __le__(self, other):
        return not (self > other)
    
    def __eq__(self, other):
        return float(self) == float(other)
    
    def __iadd__(self, other):
        if isinstance(other, TimeValue):
            self.time += TimeConverter.rescale(other.time, other.units, self.units)
            return self
        raise ValueError
    
    def __add__(self, other):
        if isinstance(other, TimeValue):
            new_time = self.time + TimeConverter.rescale(other.time, other.units, self.units)
            return TimeValue(new_time, self.units)
        raise ValueError
    
    def __repr__(self):
        return f'<TimeValue {round(self.time)} {self.units}>'
    
    def __truediv__(self, other):
        if isinstance(other, TimeValue):
            other_conv = TimeConverter.rescale(other.time, other.units, self.units)
            return self.time / other_conv
        raise ValueError
    
    def __mult__(self, other:int):
        return TimeValue(self.time*other, self.units)
        

class SystemTime:
    _global_time = TimeValue(0, 'ns')
    
    @classmethod 
    def reset(cls):
        cls._global_time = TimeValue(0, 'ns')
        
    @classmethod 
    def current(cls):
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
        
        