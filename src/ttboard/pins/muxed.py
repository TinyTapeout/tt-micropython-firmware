'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.pins.mux_control import MuxControl
from ttboard.pins.standard import StandardPin
from ttboard.pins.upython import Pin

import ttboard.logging as logging 
log = logging.getLogger(__name__)
class MuxedPinInfo:
    '''
        MuxedPinInfo 
        Details about a pin that is behind the 2:1 MUX
    '''
    def __init__(self, name:str, muxSelect:bool, direction):
        self.name = name 
        self.select = muxSelect
        self.dir = direction 
        
        
class MuxedSelection:
    def __init__(self, parent_pin, pInfo:MuxedPinInfo):
        self._parent = parent_pin 
        self.info = pInfo 
    
    @property 
    def name(self):
        return self.info.name
    
    @property 
    def direction(self):
        return self.info.dir
    
    
    @direction.setter 
    def direction(self, set_to:int):
        cur_dir = self.info.dir 
        
        if set_to == Pin.IN or set_to == Pin.OUT:
            self.info.dir = set_to 
        else:
            raise ValueError(f'Invalid direction {set_to}')
        
        if set_to != cur_dir:
            if self._parent.selected == self.info.select:
                # we are selected and have changed direction
                self._parent.current_dir = set_to 
        
    @property
    def info_string(self):
        direction = 'OUT'
        if self.direction == Pin.IN:
            direction = 'IN'
        return f'{self.info.name}[{direction}]'
    
    
    @property 
    def mode(self):
        return self.direction 
    
    @mode.setter 
    def mode(self, setMode:int):
        # we override mode here to use direction
        # such that if you manually tweak this 
        # it will be remembered as we switch 
        # the mux back and forth
        self.direction = setMode 
    
    @property 
    def mode_str(self):
        return self._parent.mode_str 
    
    
    # punting low-level pin things to parent
    # but this is risky-business -- not currently
    # maintained as part of the muxed pin state
    # just happening on the real GPIO, so use 
    # wisely
    @property 
    def pull(self):
        return self._parent.pull 
    
    @pull.setter 
    def pull(self, set_pull:int):
        self._parent.pull = set_pull
        
    @property 
    def drive(self):
        return self._parent.drive 
    
    @drive.setter 
    def drive(self, set_drive:int):
        self._parent.driver = set_drive
        
    @property 
    def gpio_num(self):
        return self._parent.gpio_num 
    
    
    
    
    def __call__(self, value:int=None):
        self._parent.select_pin(self.info)
        return self._parent(value)
       
    def __repr__(self):
        return f'<MuxedSelection {self.info_string} of {self._parent.name}>'
    
class MuxedPin(StandardPin):
    '''
        A GPIO that actually maps to two logical pins,
        through the MUX, e.g. GPIO 8 which goes through
        MUX to either cinc or out3.
        
        The purpose is to allow transparent auto-switching of mux via
        access so they will behave as the other pins in the system.
        
        E.g. reading Pins.out0() will automatically switch the MUX over
        if required before returning the read value.
        
    '''
    def __init__(self, name:str, muxCtrl:MuxControl, 
            gpio:int, pinL:MuxedPinInfo, pinH:MuxedPinInfo):
        super().__init__(name, gpio, pinH.dir)
        self.ctrl = muxCtrl
        self._current_dir = None
        
        #self._muxHighPin = pinH 
        #self._muxLowPin = pinL 
        self._sel_high = MuxedSelection(self, pinH)
        self._sel_low = MuxedSelection(self, pinL)
        setattr(self, self._sel_high.name, self._sel_high)
        #setattr(self, self._muxHighPin.name, 
        #        self._pinFunc(self._muxHighPin))

        
        setattr(self, self._sel_low.name, self._sel_low)
        #setattr(self, self._muxLowPin.name, self._pinFunc(self._muxLowPin))
        
    @property
    def high_pin(self) -> MuxedPinInfo:
        return self._sel_high.info
    
    @property
    def low_pin(self) -> MuxedPinInfo:
        return self._sel_low.info
    
    @property 
    def current_dir(self):
        return self._current_dir
    
    @current_dir.setter 
    def current_dir(self, setTo):
        if self._current_dir == setTo:
            return 
        self._current_dir = setTo 
        self.mode = setTo
        
        log.debug(f'Set dir to {self.mode_str}')
        
    def select_pin(self, pInfo:MuxedPinInfo):
        self.ctrl.select(pInfo.select)
        self.current_dir = pInfo.dir 
        
    @property 
    def selected(self):
        return self.ctrl.selected
    
    @property 
    def selected_str(self):
        sel = self.selected 
        if sel ==  self.high_pin.select:
            return 'HPIN'
        elif sel == self.low_pin.select:
            return 'LPIN'
        else:
            return '???PIN'
    
    def __repr__(self):
        return f'<MuxedPin {self.name} {self.gpio_num} ({self.selected_str} selected, {self.mode_str}) {self._sel_low.info_string}/{self._sel_high.info_string}>'
    
    def __str__(self):
        return f'MuxedPin {self.name} {self.gpio_num} ({self.selected_str} pin selected, now as {self.mode_str}) {self._sel_low.info_string}/{self._sel_high.info_string}'
