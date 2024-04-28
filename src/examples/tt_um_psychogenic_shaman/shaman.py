'''
Created on Apr 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.demoboard import DemoBoard
from examples.tt_um_psychogenic_shaman.util import wait_clocks

import ttboard.logging as logging
log = logging.getLogger(__name__)

class Shaman:
    '''
        A little wrapper to use the TT pins in a way 
        that makes sense with this project
    
    '''
    def __init__(self, tt:DemoBoard):
        self.tt = tt 
    
    @property 
    def data(self):
        return self.tt.input_byte 
    
    @data.setter 
    def data(self, set_to:int):
        self.tt.input_byte = set_to 
        
        
        
    @property 
    def result(self):
        return self.tt.output_byte 
    
    
    @property 
    def result_ready(self):
        # bidir bit 0
        return self.tt.uio0()
    
    @property 
    def begin_processing(self):
        # bidir bit 1
        return self.tt.uio1()
    
    @property 
    def parallel_load(self):
        return self.uio2()
    
    @parallel_load.setter 
    def parallel_load(self, set_to:int):
        self.tt.uio2(set_to)
        
    @property 
    def result_next(self):
        return self.tt.uio3()
    
    @result_next.setter 
    def result_next(self, set_to:int):
        self.tt.uio3(set_to)
        
    @property
    def busy(self):
        return self.tt.uio4()
    
    @property 
    def processing(self):
        return self.tt.uio5()
    
    @property 
    def start(self):
        return self.tt.uio6()
    
    @start.setter 
    def start(self, set_to:int):
        self.tt.uio6(set_to)
        
    @property 
    def data_clock(self):
        return self.tt.uio7()
    
    @data_clock.setter 
    def data_clock(self, set_to:int):
        self.tt.uio7(set_to)
        
    def clock_in_data(self, data_byte:int):
        self.data = data_byte 
        self.data_clock = 1
        wait_clocks(1)
        self.data_clock = 0
        wait_clocks(1)
        

    