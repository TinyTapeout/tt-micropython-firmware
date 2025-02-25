'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard, Pins
import ttboard.util.platform as plat
import microcotb.dut
from microcotb.testcase import TestCase
from microcotb.dut import NoopSignal
from microcotb.dut import Wire
import ttboard.log as logging


class PinWrapper(microcotb.dut.PinWrapper):
    def __init__(self, name:str, pin):
        super().__init__(name, pin)
        
    @property 
    def value(self):
        return self._pin.value()
    
    @value.setter 
    def value(self, set_to:int):
        if self._pin.mode != Pins.OUT:
            self._pin.mode = Pins.OUT
        self._pin.value(set_to)
        
class ClockPin(microcotb.dut.PinWrapper):
    '''
        clock pin is use *a lot*, needs
        to be optimized a little by 
        calling the low level platform func
    '''
    
    def __init__(self, name:str, pin):
        super().__init__(name, pin)
        
    @property 
    def value(self):
        return plat.read_clock()
    
    @value.setter 
    def value(self, set_to:int):
        plat.write_clock(set_to)
    
            

class DUT(microcotb.dut.DUT):
    TTIOPortNames = ['uo_out', 'ui_in', 'uio_in', 
                     'uio_out', 'uio_oe_pico']
    
    def __init__(self, name:str='DUT'):
        super().__init__(name)
        tt:DemoBoard = DemoBoard.get()
        self.tt = tt # give ourselves access to demoboard object
        
        # wrap the bare clock pin
        self.clk = ClockPin('clk', self.tt.pins.rp_projclk)
        self.rst_n = PinWrapper('rst_n', self.tt.rst_n)
        
        
        # provide the I/O ports from DemoBoard 
        # as attribs here, so we have dut.ui_in.value etc.
        
        for p in self.TTIOPortNames:
            setattr(self, p, getattr(self.tt, p))
        self._log = logging.getLogger(name)
        
        # ena may be used in existing tests, does nothing
        self.ena = NoopSignal('ena', 1)
        
    
    def testing_will_begin(self):
        self._log.debug('About to start a test run')
        # you should absolutely do this if you override:
        if self.tt.is_auto_clocking:
            self._log.info('autoclocking... will stop it.')
            self.tt.clock_project_stop()
        
        # and this: make sure is an output
        self.tt.pins.rp_projclk.mode = Pins.OUT
        
    def testing_unit_start(self, test:TestCase):
        # override if desired
        self._log.debug(f'Test {test.name} about to start')


    def testing_unit_done(self, test:TestCase):
        # override if desired
        
        if test.failed:
            self._log.debug(f'{test.name} failed because: {test.failed_msg}')
        else:
            self._log.debug(f'{test.name} passed!')
        
    
    def testing_done(self):
        # override if desired, but good idea to reset clock pin mode
        # or just call super().testing_unit_done(test) to get it done
        # make sure is an input
        self.tt.pins.rp_projclk.mode = Pins.IN
        
        self._log.debug('All testing done')
        
        
    def __setattr__(self, name:str, value):
        if hasattr(self, name) and name in self.TTIOPortNames:
            port = getattr(self, name)
            port.value = value 
            return
        super().__setattr__(name, value)
        
        
    
        
        