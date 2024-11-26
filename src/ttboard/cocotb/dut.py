'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard, Pins
import microcotb.dut
from microcotb.dut import Wire, NoopSignal
import ttboard.log as logging


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
            

class DUTWrapper(microcotb.dut.DUT):
    def __init__(self, name:str='DUT'):
        self.tt = DemoBoard.get()
        # wrap the bare clock pin
        self.clk = PinWrapper(self.tt.pins.rp_projclk)
        self.rst_n = PinWrapper(self.tt.rst_n)
        ports = ['uo_out', 'ui_in', 'uio_in', 'uio_out', 'uio_oe_pico']
        for p in ports:
            setattr(self, p, getattr(self.tt, p))
        self._log = logging.getLogger(name)
        self.ena = NoopSignal(1)
        
    
    def testing_will_begin(self):
        self.tt.clock_project_stop()
        
        
class DUT(DUTWrapper):
    
    def __init__(self, name:str='DUT'):
        super().__init__(name)
        
        
    
        
        