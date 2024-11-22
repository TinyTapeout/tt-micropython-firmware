'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard, Pins
from ttboard.ports.io import IO
import ttboard.log as logging

class SliceWrapper:
    def __init__(self, port, idx_or_start:int, slice_end:int=None):
        self._port = port 
        # can't create slice() on uPython...
        self.slice_start = idx_or_start
        self.slice_end = slice_end
        
    @property 
    def value(self):
        if self.slice_end is not None:
            return self._port[self.slice_start:self.slice_end]
        
        return self._port[self.slice_start]
    
    @value.setter 
    def value(self, set_to:int):
        if self.slice_end is not None:
            self._port[self.slice_start:self.slice_end] = set_to
        else:
            self._port[self.slice_start] = set_to
        
    def __repr__(self):
        if self.slice_end is not None:
            return str(self._port[self.slice_start:self.slice_end])
        else:
            return str(self._port[self.slice_start])


class PinWrapper:
    def __init__(self, pin):
        self._pin = pin 
        
    @property 
    def value(self):
        return self._pin.value()
    
    @value.setter 
    def value(self, set_to:int):
        if self._pin.mode != Pins.OUT:
            self._pin.mode = Pins.OUT
        self._pin.value(set_to)
            

class DUTWrapper:
    def __init__(self, name:str='DUT'):
        self.tt = DemoBoard.get()
        self.clk = PinWrapper(self.tt.clk)
        self.rst_n = PinWrapper(self.tt.rst_n)
        self._log = logging.getLogger(name)
        
    @classmethod
    def new_slice_attribute(cls, source:IO, idx_or_start:int, slice_end:int=None):
        return SliceWrapper(source, idx_or_start, slice_end)
    
    def add_slice_attribute(self, source:IO, name:str, idx_or_start:int, slice_end:int=None):
        slc = self.new_slice_attribute(source, idx_or_start, slice_end)
        setattr(self, name, slc)
        
    
        
        