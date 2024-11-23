'''
    DFFRAM class and test for tt_um_urish_dffram

'''

import random

from ttboard.pins import Pins
from ttboard.demoboard import DemoBoard
import ttboard.util.time as time
class DFFRAM:
    
    def __init__(self, pins:Pins):
        self.p = pins 
        self._data_in_write = 0
        
        for p in self.p.bidirs:
            p.mode = Pins.OUT 
            
        self.p.ui_in.value = 0
        self.p.uio_in.value = 0
        
    @property 
    def we(self):
        return self.p.in7()
    
    @we.setter 
    def we(self, v:int):
        if v:
            self.p.ui_in[7] = 1
        else:
            self.p.ui_in[7] = 0 
            
    @property 
    def addr(self):
        return  self.p.ui_in.value & 0x7f
    
    @addr.setter 
    def addr(self, v:int):
        self.p.ui_in.value = (self.p.ui_in.value & ~0x7f) | (v & 0x7f)
        
    @property 
    def data_out(self):
        return  self.p.uo_out.value
    
    @property 
    def data_in(self):
        return  self.p.uio_in.value
    
    @data_in.setter
    def data_in(self, v:int):
        self.p.uio_in.value = v        
    
        
        
def setup():
    tt = DemoBoard()
    
    tt.shuttle.tt_um_urish_dffram.enable()

    dffram = DFFRAM(tt.pins)
    
    tt.reset_project(True)
    tt.clock_project_PWM(1e4)
    time.sleep_ms(1)
    
    tt.reset_project(False)
    time.sleep_ms(1)
    return tt, dffram

def test():
    tt, dffram = setup()
    
    tt.clock_project_stop()
    
    # Outputs only valid when clock is low, so start clock low
    tt.clk.off()
    
    print("Writing RAM")
    for i in range(0,128):
        dffram.addr = i
        
        dffram.data_in = i
        dffram.we = 1
        tt.clock_project_once()
        
        # Not sure why but writes need a cycle with we = 0 to take?
        dffram.we = 0
        tt.clock_project_once()
                
    print('Reading RAM')
    dffram.we = 0
    for i in range(0,128):
        dffram.addr = i 
        
        tt.clock_project_once()
        #print(f'Read addr {i} as {dffram.data_out}')
        if dffram.data_out != i:
            print(f"Error at {i}: {dffram.data_out} != {i}")
        
    print('Verify random reads and writes')
    ram = [i for i in range(128)]
    for i in range(1000):
        addr = random.randint(0, 63)
        dffram.addr = addr

        if random.randint(0, 1) == 1:
            data = random.randint(0, 255)
            ram[addr] = data
            dffram.data_in = data
            dffram.we = 1
            tt.clock_project_once()
            dffram.we = 0
            tt.clock_project_once()
        else:
            tt.clock_project_once()
            if dffram.data_out != ram[addr]:
                print(f"Error at {addr}: {dffram.data_out} != {ram[addr]}")
        
    print('Verify RAM contents')
    for i in range(0,128):
        dffram.addr = i
        tt.clock_project_once()
        if dffram.data_out != ram[i]:
            print(f"Error at {i}: {dffram.data_out} != {ram[i]}")
        
    print("Test done")
    return tt, dffram
    
        
        