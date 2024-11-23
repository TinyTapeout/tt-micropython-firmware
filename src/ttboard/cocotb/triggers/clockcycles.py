'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.cocotb.triggers.awaitable import Awaitable
from ttboard.cocotb.clock import Clock
from ttboard.cocotb.time import SystemTime
    
class ClockCycles(Awaitable):
    def __init__(self, sig, num_cycles:int):
        super().__init__(sig)
        self.num_cycles = num_cycles
        
    def __iter__(self):
        return self

    def next(self): 
        clk = Clock.get(self.signal)
        
        if clk is None:
            print("CLK NO CLK")
        else:
            num_transitions = self.num_cycles * 2
            target_time = SystemTime.current() + (clk.half_period * num_transitions)
            time_increment = Clock.get_shortest_event_interval()
            #print(f"Is now {SystemTime.current()}, running until {target_time}, increment is {time_increment}")
            while SystemTime.current() < target_time:
                #print("Advancing time")
                SystemTime.advance(time_increment)
                
        raise StopIteration
    
    def __next__(self):
        return self.next()
    
    
    def __await__(self):
        clk = Clock.get(self.signal)
        if clk is not None:
            self.cycle_count = 0
            for _i in range(self.num_cycles):
                clk.tick()
        yield
        return self
    