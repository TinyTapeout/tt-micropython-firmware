'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard, Pins
import microcotb.dut
from microcotb.dut import NoopSignal
from microcotb.dut import Wire
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
    TTIOPortNames = ['uo_out', 'ui_in', 'uio_in', 
                 'uio_out', 'uio_oe_pico']
    
    def __init__(self, name:str='DUT'):
        self.tt = DemoBoard.get()
        # wrap the bare clock pin
        self.clk = PinWrapper(self.tt.pins.rp_projclk)
        self.rst_n = PinWrapper(self.tt.rst_n)
        
        # provide the I/O ports from DemoBoard 
        # as attribs here
        
        for p in self.TTIOPortNames:
            setattr(self, p, getattr(self.tt, p))
        self._log = logging.getLogger(name)
        self.ena = NoopSignal(1)
        
    
    def testing_will_begin(self):
        self.tt.clock_project_stop()
        
        
    def __setattr__(self, name:str, value):
        if hasattr(self, name) and name in self.TTIOPortNames:
            port = getattr(self, name)
            port.value = value 
            return
        super().__setattr__(name, value)
        
        
class DUT(DUTWrapper):
    
    def __init__(self, name:str='DUT'):
        super().__init__(name)
        
        
    
        
        