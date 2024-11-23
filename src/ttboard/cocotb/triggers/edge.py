'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.cocotb.triggers.awaitable import Awaitable
from ttboard.cocotb.clock import Clock
from ttboard.cocotb.time import SystemTime, TimeValue

class Edge(Awaitable):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self._fastest_clock = None 
        self.initial_state = None
        self.primed = False
        
    
    def prepare_for_wait(self):
        return 
    def conditions_met(self):
        print("OVERRIDE ME")
        return False
    
    @property 
    def fastest_clock(self) -> Clock:
        if self._fastest_clock is None:
            self._fastest_clock = Clock.get_fastest()
            
        return self._fastest_clock
    
    @property 
    def time_increment(self) -> TimeValue:
        return self.fastest_clock.half_period
    
    def wait_for_conditions(self):
        while not self.conditions_met():
            SystemTime.advance(self.time_increment)
            
        return
    
    
    def __iter__(self):
        self._fastest_clock = None 
        self.prepare_for_wait()
        return self
    
    def __next__(self):
        self.wait_for_conditions()
        raise StopIteration
    
    
    def __await__(self):
        self._fastest_clock = None 
        self.prepare_for_wait()
        self.wait_for_conditions()
        yield
        return self
    

class RisingEdge(Edge):
    def __init__(self, signal):
        super().__init__(signal)
            
    def prepare_for_wait(self):
        self.initial_state = int(self.signal)
        self.primed = False if self.initial_state else True
        return 
    
    def conditions_met(self):
        if not self.primed:
            if int(self.signal) == 0:
                self.primed = True 
        else:
            if int(self.signal):
                return True
            
        

class FallingEdge(Edge):
    def __init__(self, signal):
        super().__init__(signal)
            
    def prepare_for_wait(self):
        self.initial_state = int(self.signal)
        self.primed = True if self.initial_state else False
        return 
    
    def conditions_met(self):
        if not self.primed:
            if int(self.signal):
                self.primed = True 
        else:
            if int(self.signal) == 0:
                return True
            
        
        
        
        
        
        
        