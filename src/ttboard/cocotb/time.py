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
        tval = TimeValue(t, units)
        return round(tval / clock.period)
    
    @classmethod 
    def rescale(cls,t:int, units:str, to_units:str):
        if units == to_units:
            return t
        return t*(cls.scale(units)/cls.scale(to_units))
    
class TimeValue:
    def __init__(self, time:int, units:str):
        self._time = time 
        self._units = units
        self.scale = TimeConverter.scale(units)
        self._as_float = None
    
    @property 
    def time(self):
        return self._time 
    
    @time.setter 
    def time(self, set_to:int):
        self._time = set_to 
        self._as_float = None
    @property 
    def units(self):
        return self._units 
    @units.setter 
    def units(self, set_to:str):
        self._units = set_to 
        self.scale = TimeConverter.scale(set_to)
        self._as_float = None
    def __float__(self):
        if self._as_float is None:
            self._as_float = self.time*self.scale
        return self._as_float
    
    def __gt__(self, other):
        if isinstance(other, (TimeValue, float)):
            return float(self) > float(other)
        raise ValueError
    
    def __lt__(self, other):
        return float(self) < float(other)
    
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
    
    def __mul__(self, other:int):
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
        
        