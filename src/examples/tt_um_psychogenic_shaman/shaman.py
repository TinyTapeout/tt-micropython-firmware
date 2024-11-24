'''
Created on Apr 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard
from examples.tt_um_psychogenic_shaman.util import wait_clocks

import ttboard.log as logging
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
        return  self.tt.ui_in.value 
    
    @data.setter 
    def data(self, set_to:int):
        self.tt.ui_in.value = set_to 
        
        
        
    @property 
    def result(self):
        return  self.tt.uo_out.value 
    
    
    @property 
    def result_ready(self):
        # bidir bit 0
        return self.tt.uio_out[0]
    
    @property 
    def begin_processing(self):
        # bidir bit 1
        return self.tt.uio_out[1]
    
    @property 
    def parallel_load(self):
        return self.uio_in[2]
    
    @parallel_load.setter 
    def parallel_load(self, set_to:int):
        self.tt.uio_in[2] = set_to
        
    @property 
    def result_next(self):
        return self.tt.uio_in[3]
    
    @result_next.setter 
    def result_next(self, set_to:int):
        self.tt.uio_in[3] = set_to
        
    @property
    def busy(self):
        return self.tt.uio_out[4]
    
    @property 
    def processing(self):
        return self.tt.uio_out[5]
    
    @property 
    def start(self):
        return self.tt.uio_in[6]
    
    @start.setter 
    def start(self, set_to:int):
        self.tt.uio_in[6] = set_to
        
    @property 
    def data_clock(self):
        return self.tt.uio_in[7]
    
    @data_clock.setter 
    def data_clock(self, set_to:int):
        self.tt.uio_in[7] = set_to
        
    def clock_in_data(self, data_byte:int):
        self.data = data_byte 
        self.data_clock = 1
        wait_clocks(1)
        self.data_clock = 0
        wait_clocks(1)
        

    