'''
Created on Mar 20, 2024

POST -- Power On Self Test

Place to keep regular boot-up sequence related functions.

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.pins.upython import Pin
import ttboard.util.time as time
from ttboard.boot.first import FirstBoot
import ttboard.pins.gpio_map as gp
from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode

import ttboard.log as logging
log = logging.getLogger(__name__)



class PowerOnSelfTest:
    '''
        The POST class is meant to inspect and 
        act on system at startup.
        It has some class methods for raw pin read access
        and can run various tests on system.
    '''
    
    @classmethod 
    def read_all_pins(self) -> dict:
        '''
            reads all the defined gpio and
            returns a dictionary of pin name (as per GPIOMap)
            to read value.
        '''
        pin_states = dict()
        for name, io in gp.GPIOMap.all().items():
            p = Pin(io, Pin.IN)
            pin_states[name] = p() 
            
        return pin_states

    @classmethod 
    def read_pin(cls, pin:str) -> int:
        '''
            read a specific pin, by (GPIOMap) name or number.
            
            creates a Pin, setting up as an input, and reads it.
            
            @param pin: name (str) or RP2040 number
            @return: the value read
        '''
        
        p = gp.GPIOMap.get_raw_pin(pin, Pin.IN)
        if p is None:
            raise KeyError(f'No pin named {pin} found')
        return p()
    
    @classmethod 
    def write_pin(cls, pin:str, value:int):
        p = gp.GPIOMap.get_raw_pin(pin, Pin.OUT)
        if p is None:
            raise KeyError(f'No pin named {pin} found')
        p(value)
        
    
    
    @classmethod 
    def dotest_buttons_held(cls):
        mux_selectpin = gp.GPIOMap.get_raw_pin('hk_csb', Pin.OUT)
        if mux_selectpin is not None:
            mux_selectpin(1) # have mux, make sure it's is pointed right way
        if cls.read_pin(gp.GPIOMap.project_clock()) and not cls.read_pin(gp.GPIOMap.project_reset()):
            log.info('POST "do test" buttons held')
            return True 
        
        return False
    
    @classmethod 
    def first_boot(cls):
        return FirstBoot.is_first_boot()
    @classmethod 
    def first_boot_log(cls):
        return FirstBoot.first_boot_log()
    
    @classmethod
    def handle_first_boot(cls):
        return FirstBoot.initialize()
        
    def __init__(self, ttdemoboard:DemoBoard):
        '''
            POST instance constructor, expects an instantiated DemoBoard object
        '''
        self._tt = ttdemoboard
        
        
    @property 
    def tt(self) -> DemoBoard:
        '''
            The DemoBoard instance
        '''
        return self._tt
        
    def test_bidirs(self) -> bool:
        '''
            Loads tt_um_test and checks that anything put onto 
            bidir pins is mapped out to output pins.
            @return: False on any failure, True otherwise
        '''
        # select the project from the shuttle
        update_delay_ms = 2
        auto_clock_freq = 1e3
        self.tt.mode = RPMode.ASIC_RP_CONTROL # make sure we're controlling everything
        
        self.tt.shuttle.factory_test.enable()
        curMode = self.tt.mode 
        self.tt.mode = RPMode.ASIC_RP_CONTROL # make sure we're controlling everything
        self.tt.reset_project(False)
        self.tt.in0(0) # want this low
        self.tt.clock_project_PWM(auto_clock_freq) # clock it real good
        
        log.info('POST: starting bidirection pins tests')
        self.tt.bidir_mode = [Pin.OUT] * 8
        for bp in self.tt.bidirs:
            bp(0) # start low
        
        errCount = 0
        for i in range(0xff):
            self.tt.bidir_byte = i 
            time.sleep_ms(update_delay_ms)
            outbyte = self.tt.output_byte
            if outbyte !=  i:
                log.warn(f'MISMATCH between bidir val {i} and output {outbyte}')
                errCount += 1
        
        # reset everything
        self.tt.bidir_mode = [Pin.IN] * 8
            
        self.tt.clock_project_stop()
        self.tt.mode = curMode
        
        if errCount:
            log.error(f'{errCount} ERRORS encountered')
            return False 
        
        log.info('Bi-directional pins acting pretty nicely as inputs!')
        return True
