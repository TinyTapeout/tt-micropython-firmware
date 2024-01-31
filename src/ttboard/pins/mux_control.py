'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.pins.standard import StandardPin
from ttboard.pins.upython import Pin


import ttboard.logging as logging 
log = logging.getLogger(__name__)

class MuxControl:
    '''
        The MUX is a 4-Bit 1-of-2, so has 4 pairs of 
        GPIO that are selected in unison by a single
        signal.
        
        The circuit is organized such that either:
         * all the outputs tied to the mux are selected; or
         * all the control signals are selected
         
        and this selector is actually the HK SPI nCS line.
        
        These facts are included here for reference, the 
        MuxControl object is actually unaware of the 
        specifics and this stuff happens either transparently
        or at higher levels
    
    '''
    def __init__(self, name:str, gpioIdx, defValue:int=1):
        self.ctrlpin = StandardPin(name, gpioIdx, Pin.OUT)
        self.ctrlpin(defValue)
        self.currentValue = defValue
        self._muxedPins = []
        
    def mode_project_IO(self):
        self.select_high()
    def mode_admin(self):
        self.select_low()
        
    def add_muxed(self, muxd):
        self._muxedPins.append(muxd)
        
    def select(self, value:int):
        if value == self.currentValue:
            return 
        
        # set the control pin according to 
        # value.  Note that we need to make 
        # sure we switch ALL muxed pins over
        # otherwise we might end up with contention
        # as two sides think they're outputs
        # safety
        for mp in self._muxedPins:
            mp.current_dir = Pin.IN
            
        if value:
            log.debug('Mux CTRL selecting HIGH set (proj IO)')
            self.ctrlpin(1)
            for mp in self._muxedPins:
                pDeets = mp.high_pin
                mp.current_dir = pDeets.dir
        else:
            log.debug('Mux CTRL selecting LOW set (admin)')
            self.ctrlpin(0)
            for mp in self._muxedPins:
                pDeets = mp.low_pin
                mp.current_dir = pDeets.dir
            
        self.currentValue = value
        
    def select_high(self):
        self.select(1)
        
    def select_low(self):
        self.select(0)
        
