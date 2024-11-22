'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.cocotb.clock import Clock, TimeConverter

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
        self.cycle_count = 0
        
    def __iter__(self):
        # print(f"Will tick {self.num_cycles} times ")
        self.cycle_count = self.num_cycles
        return self

    def next(self): 
        clk = Clock.get(self.signal)
        if clk is None:
            print("CLK NO CLK")
        else:
            while self.cycle_count > 0:
                self.cycle_count -= 1
                clk.tick()
        raise StopIteration
    
    def __next__(self):
        return self.next()
    
    def deadbeef(self):
        clk = Clock.get(self.signal)
        if clk is None:
            print("CLK NO CLK")
        else:
            if self.cycle_count > 0:
                self.cycle_count -= 1
                clk.tick()
                yield self.cycle_count
        raise StopIteration
            
    
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
        self.time = time 
        self.units = units 
        self.time_s = time * TimeConverter.scale(units)
        self.cycle_count = 0
        
    
    def countdowns(self):
        all_clocks = Clock.all()
        countdowns = []
        max_ticks = 0
        for clk in all_clocks:
            nt = clk.numticks_in(self.time, self.units)
            if nt > max_ticks:
                max_ticks = nt 
            #print(f'Want {nt} ticks for {clk}')
            countdowns.append([nt, clk])
            
        #print(f"Set cyclecount {max_ticks}")
        self.cycle_count = max_ticks
        
        return countdowns
        
    
    def __iter__(self):
        self._countdowns = self.countdowns()
        return self
    
    def __next__(self): 
        while self.cycle_count > 0:
            self.cycle_count -= 1
            self.tick_all()
        raise StopIteration
    
    def tick_all(self):
        for cidx in range(len(self._countdowns)):
            if self._countdowns[cidx][0] > 0:
                self._countdowns[cidx][1].tick()
                self._countdowns[cidx][0] -= 1
    
    def __await__(self):
        self._countdowns = self.countdowns()
        for _i in range(self.cycle_count):
            self.tick_all()
        yield
        return self
    
    