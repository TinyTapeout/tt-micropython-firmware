'''
Created on Aug 30, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import ttboard.util.platform as platform
from ttboard.pins.upython import Pin
import ttboard.pins.gpio_map
from ttboard.pins.gpio_map_dbv3 import GPIOMapTTDBv3

import ttboard.log as logging
log = logging.getLogger(__name__)

class DemoboardVersion:
    '''
        Simple wrapper for an 'enum' type deal with db versions.=
    '''
    UNKNOWN = 0
    TT04 = 1
    TT06 = 2
    TTDBv3 = 3
    
    @classmethod 
    def to_string(cls, v:int):
        asStr = {
            cls.UNKNOWN: 'UNKNOWN',
            cls.TT04: 'TT04/TT05',
            cls.TT06: 'TT06+',
            cls.TTDBv3: 'TTDBv3',
        }
        if v in asStr:
            return asStr[v]
        return 'N/A'
    
class DemoboardCarrier:
    UNKNOWN = 0
    TT_CARRIER = 1
    FPGA = 2
    

class DemoboardDetect:
    '''
        DemoboardDetect
        centralizes and implements strategies for detecting
        the version of the demoboard.
        
        Breaking changes in pinouts between demoboard versions
        have been handled here, as required, to detect the current 
        hardware and map pins to functions in a unified manner.
        
        Starting with the release of the DB v3 "ETR", SDK 
        support is now limited to RP2350-based boards and, as 
        of the time of this comment, only one such board exists.
        
        In order to allow for future potentially breaking modifications,
        without disruption to existing code, the functionality remains 
        here, even if in a degenerate form that currently does very little
        in regards to detecting the DB version.
        
        However the probing job is also used to see what is populated atop
        the demoboard, and running the probe will also populate
        
            DemoboardDetect.CarrierPresent (boolean)
        and
            DemoboardDetect.CarrierVersion 
        one of
            DemoboardCarrier.UNKNOWN 
            DemoboardCarrier.TT_CARRIER   # an ASIC
            DemoboardCarrier.FPGA         # FPGA breakout
            

        This class has:
         a probe() method, to encapsulate all the action,
         PCB, CarrierPresent class attribs to hold the results
        
        Recommended start-up for scripts is thus of the form
        
            from ttboard.boot.demoboard_detect import DemoboardDetect
            from ttboard.demoboard import DemoBoard
            
            tt = None # will hold our SDK handle
            if DemoboardDetect.probe():
                print(f' Yay {DemoboardDetect.PCB_str()} db detected')
                tt = DemoBoard.get()
            
            # ...
    '''
    PCB = DemoboardVersion.UNKNOWN
    CarrierPresent = None 
    CarrierVersion = None 
    
    
    @classmethod 
    def PCB_str(cls):
        return DemoboardVersion.to_string(cls.PCB)
    
    @classmethod
    def probe_rp2350(cls):
        if not platform.IsRP2350:
            return False 
        
        # check for FPGA board
        fpga_detect_pin = GPIOMapTTDBv3.get_raw_pin(GPIOMapTTDBv3.MNG07, Pin.IN)
        
        # mng 7 pulled high?
        if fpga_detect_pin():
            cls.CarrierPresent = True
            cls.CarrierVersion = DemoboardCarrier.FPGA
            return True
            
        
        # check for standard carrier
        cena_pin = GPIOMapTTDBv3.get_raw_pin(GPIOMapTTDBv3.ctrl_enable(), Pin.IN)
        crst_pin = GPIOMapTTDBv3.get_raw_pin(GPIOMapTTDBv3.ctrl_reset(), Pin.IN)
        
        crst = crst_pin()
        cena = cena_pin()
        
        if (not crst) and (not cena):
            log.debug("ctrl lines pulled to indicate TT carrier present on board")
            log.info("TTDBv3 demoboard with carrier present")
            cls.CarrierPresent = True
            cls.CarrierVersion = DemoboardCarrier.TT_CARRIER
            return True
        
        
        cls.CarrierVersion = DemoboardCarrier.UNKNOWN
        return False 
    
    
    @classmethod 
    def rp_all_inputs(cls):
        log.debug("Setting all RP GPIO to INPUTS")
        pins = []
        num_io = 30
        if platform.IsRP2350:
            num_io = 41
        for i in range(num_io):
            pins.append(platform.pin_as_input(i, Pin.PULL_DOWN))
            
        return pins
        
    @classmethod 
    def probe(cls):
        result = False
        cls.rp_all_inputs()
        if platform.IsRP2350:
            cls.PCB = DemoboardVersion.TTDBv3
            if cls.probe_rp2350():
                result = True
        else:
            cls.PCB = DemoboardVersion.UNKNOWN
        
        # always configure gpio map to _something_
        cls._configure_gpiomap()
        
        return result
    
    @classmethod
    def force_detection(cls, dbversion:int):
        cls.PCB = dbversion 
        cls._configure_gpiomap()
            
    @classmethod 
    def _configure_gpiomap(cls):
        mapToUse = {
            DemoboardVersion.TTDBv3: GPIOMapTTDBv3,
            DemoboardVersion.UNKNOWN: GPIOMapTTDBv3, # default pin mapping
        }
        if cls.PCB in mapToUse:
            log.debug(f'Setting GPIOMap to {mapToUse[cls.PCB]}')
            ttboard.pins.gpio_map.GPIOMap = mapToUse[cls.PCB]
        else:
            raise RuntimeError(f'Cannot set GPIO map: this SDK is does not support {DemoboardVersion.to_string(cls.PCB)} demoboards')
            
        
    