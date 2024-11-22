'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.cocotb.clock import Clock
from ttboard.cocotb.time import TimeValue, SystemTime
class Awaitable:
    def __init__(self, signal=None):
        self.signal = signal
    
    def __iter__(self):
        return self

    def __next__(self): 
        raise StopIteration
    
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
            all_clocks = sorted(Clock.all(), key=lambda x: float(x.half_period))
            fastest_clock = all_clocks[0]
            time_increment = fastest_clock.half_period
            while SystemTime.current() < target_time:
                SystemTime.advance(time_increment)
                for clk in all_clocks:
                    clk.time_has_passed()
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
    
class Timer(Awaitable):
    def __init__(self, time:int, units:str):
        super().__init__()
        self.time = TimeValue(time, units)
        
    
    def run_timer(self):
        all_clocks = sorted(Clock.all(), key=lambda x: float(x.half_period))
        fastest_clock = all_clocks[0]
        time_increment = fastest_clock.half_period
        target_time = SystemTime.current() + self.time
        while SystemTime.current() < target_time:
            SystemTime.advance(time_increment)
            for clk in all_clocks:
                clk.time_has_passed()
                
    def __iter__(self):
        return self
    
    def __next__(self): 
        self.run_timer()
        raise StopIteration
    
    
    def __await__(self):
        self.run_timer()
        yield
        return self
    
    