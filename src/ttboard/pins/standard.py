'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.util.platform import IsRP2
from ttboard.pins.upython import Pin

if IsRP2:
    import machine

import ttboard.log as logging
log = logging.getLogger(__name__)

class StandardPin:
    '''
        Augmented machine.Pin
        Holds the raw machine.Pin object, provides a callable interface
          obj() # to read
          obj(1) # to write 
        and maintains/allows setting pull, mode and drive attributes
        
        # read/write attribs
        p.mode = Pin.OUT # direction
        p.pull = Pin.PULL_UP # pu
        print(p.drive) # may not be avail on any pins here, I dunno
    
    '''
    def __init__(self, name:str, gpio:int, mode:int=Pin.IN, pull:int=-1, drive:int=0):
        self._name = name
        self._mode = mode
        self._pull = pull 
        self._drive = drive 
        self._gpio_num = None
        self._pwm = None
        if isinstance(gpio, StandardPin):   
            self.raw_pin = gpio.raw_pin
            self._gpio_num = gpio.gpio_num
            self.mode = mode
        elif type(gpio) != int:
            self.raw_pin = gpio 
        else:
            self.raw_pin = Pin(gpio, mode=mode, pull=pull)
            self._gpio_num = gpio
    
    @property 
    def name(self):
        return self._name
    
    @property 
    def is_input(self):
        return self._mode == Pin.IN
    
    @property 
    def mode(self):
        return self._mode 
    
    @mode.setter 
    def mode(self, setMode:int):
        self._mode = setMode 
        log.debug(f'Setting pin {self.name} to {self.mode_str}')
        self.raw_pin.init(setMode, pull=self._pull)
        
    @property 
    def mode_str(self):
        modestr = 'OUT'
        if self.is_input:
            modestr = 'IN'
        return modestr
    @property 
    def pull(self):
        return self._pull 
    
    @pull.setter 
    def pull(self, setPull:int):
        self._pull = setPull 
        self.raw_pin.init(pull=setPull)
        
    @property 
    def drive(self):
        return self._drive 
    
    @drive.setter 
    def drive(self, setDrive:int):
        self._drive = setDrive 
        self.raw_pin.init(drive=setDrive)
        
    @property 
    def gpio_num(self):
        return self._gpio_num
    
    def pwm(self, freq:int=None, duty_u16:int=0xffff/2):
        if self.is_input:
            log.error(f'Trying to twiddle PWM on pin {self.name} that is an input')
            return 
        
        if freq is not None and freq < 1:
            log.info(f'Disabling pwm on {self.name}')
            if self._pwm is not None:
                self._pwm.deinit()
                self._pwm = None
            self.mode = Pin.OUT
            return None
        
        log.debug(f"Setting PWM on {self.name} to {freq}Hz")
        
        if IsRP2:
            self._pwm = machine.PWM(self.raw_pin)
        else:
            log.warn('Not on RP2040--no PWM')
            return None
    
        if freq is not None and freq > 0:
                self._pwm.freq(int(freq))
            
        if duty_u16 is not None and duty_u16 >= 0:
            self._pwm.duty_u16(int(duty_u16))
            
        return self._pwm
        
    
    def __call__(self, value:int=None):
        if value is not None:
            return self.raw_pin.value(value)
        return self.raw_pin.value()
    
    def __getattr__(self, name):
        if hasattr(self.raw_pin, name):
            return getattr(self.raw_pin, name)
        raise AttributeError(f'no attr {name}')
    
    def __repr__(self):
        outval = ''
        if not self.is_input:
            outval = f' {self.raw_pin.value()}'
        return f'<StandardPin {self.name} GP{self.gpio_num} {self.mode_str}{outval}>'
        
    
    def __str__(self):
        outval = ''
        if not self.is_input:
            outval = f' {self.raw_pin.value()}'
        return f'Standard pin {self.name} (GPIO {self.gpio_num}), configured as {self.mode_str}{outval}'
    
