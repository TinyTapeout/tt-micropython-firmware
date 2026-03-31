'''
Created on Jan 27, 2026

@author: Pat Deegan
@copyright: Copyright (C) 2026 Pat Deegan, https://psychogenic.com
'''
from ttboard.pins.upython import Pin

class GPIOMapBase:
    
    @classmethod 
    def project_clock(cls):
        raise RuntimeError('not implemented')
    
    @classmethod 
    def project_reset(cls):
        raise RuntimeError('not implemented')
    
    @classmethod 
    def ctrl_increment(cls):
        raise RuntimeError('not implemented')
    
    @classmethod 
    def ctrl_enable(cls):
        raise RuntimeError('not implemented')
    
    @classmethod 
    def ctrl_reset(cls):
        raise RuntimeError('not implemented')
    
    @classmethod 
    def always_outputs(cls):
        return [
            # 'nproject_rst',
            # 'rp_projclk', -- don't do this during "safe" operation
            #'ctrl_ena'
        ]
    
    @classmethod
    def default_pull(cls, pin):
        # both of these now go through MUX and 
        # must therefore rely on external/physical
        # pull-ups.  the nProject reset has PU in 
        # switch debounce, cena... may be a problem 
        # (seems it has a pull down on board?)
        #if pin in ["nproject_rst", "ctrl_ena"]:
        #    return Pin.PULL_UP
        return Pin.PULL_DOWN
    
    @classmethod 
    def get_raw_pin(cls, pin:str, direction:int) -> Pin:
        
        pin_ionum = None
        if isinstance(pin, int):
            pin_ionum = pin 
        else:
            pin_name_to_io = cls.all()
            if pin not in pin_name_to_io:
                return None
            pin_ionum = pin_name_to_io[pin]
            
        return Pin(pin_ionum, direction)
    
    
    @classmethod 
    def all_common(cls):
        retDict = {
            "rp_projclk": cls.RP_PROJCLK,
            "ui_in0": cls.UI_IN0,
            "ui_in1": cls.UI_IN1,
            "ui_in2": cls.UI_IN2,
            "ui_in3": cls.UI_IN3,
            "uo_out4": cls.UO_OUT4,
            "uo_out5": cls.UO_OUT5,
            "uo_out6": cls.UO_OUT6,
            "uo_out7": cls.UO_OUT7,
            "ui_in4": cls.UI_IN4,
            "ui_in5": cls.UI_IN5,
            "ui_in6": cls.UI_IN6,
            "ui_in7": cls.UI_IN7,
            "uio0": cls.UIO0,
            "uio1": cls.UIO1,
            "uio2": cls.UIO2,
            "uio3": cls.UIO3,
            "uio4": cls.UIO4,
            "uio5": cls.UIO5,
            "uio6": cls.UIO6,
            "uio7": cls.UIO7,
        }
        return retDict
        