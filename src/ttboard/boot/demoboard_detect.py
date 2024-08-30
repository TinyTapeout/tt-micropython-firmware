'''
Created on Aug 30, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.pins.upython import Pin
import ttboard.pins.gpio_map
from ttboard.pins.gpio_map import GPIOMapTT04, GPIOMapTT06

import ttboard.logging as logging
log = logging.getLogger(__name__)

class DemoboardVersion:
    '''
        Simple wrapper for an 'enum' type deal with db versions.
        Supported are TT04/TT05 and TT06+
    '''
    UNKNOWN = 0
    TT04 = 1
    TT06 = 2
    
    @classmethod 
    def to_string(cls, v:int):
        asStr = {
            cls.UNKNOWN: 'UNKNOWN',
            cls.TT04: 'TT04/TT05',
            cls.TT06: 'TT06+'
        }
        if v in asStr:
            return asStr[v]
        return 'N/A'

class DemoboardDetect:
    PCB = DemoboardVersion.UNKNOWN
    CarrierPresent = None 
    CarrierVersion = None 
    
    
    @classmethod 
    def PCB_str(cls):
        return DemoboardVersion.to_string(cls.PCB)
    
    @classmethod 
    def probe_pullups(cls):
        cena_pin = GPIOMapTT06.get_raw_pin(GPIOMapTT06.ctrl_enable(), Pin.IN)
        # cinc_pin = GPIOMapTT06.get_raw_pin(GPIOMapTT06.ctrl_increment(), Pin.IN)
        crst_pin = GPIOMapTT06.get_raw_pin(GPIOMapTT06.ctrl_reset(), Pin.IN)
        
        crst = crst_pin()
        cena = cena_pin()
        
        
        if (not crst) and (not cena):
            log.debug("ctrl mux lines pulled to indicate TT06+ carrier present--tt06+ db")
            log.info("TT06+ demoboard with carrier present")
            cls.PCB = DemoboardVersion.TT06
            cls.CarrierPresent = True
            return True
        
        if crst and cena:
            log.info("probing ctrl mux lines gives no info, unable to determine db version")
            log.warn("TT04 demoboard OR TT06 No carrier present")
            cls.PCB = DemoboardVersion.UNKNOWN
            cls.CarrierPresent = None
        
        return False
        
    @classmethod 
    def probe_tt04mux(cls):
        mux_pin = GPIOMapTT04.get_raw_pin(GPIOMapTT04.mux_select(), Pin.OUT)
        cena_pin = GPIOMapTT04.get_raw_pin(GPIOMapTT04.ctrl_enable(), Pin.IN)
        cinc_pin = GPIOMapTT04.get_raw_pin(GPIOMapTT04.ctrl_increment(), Pin.IN)
        crst_pin = GPIOMapTT04.get_raw_pin(GPIOMapTT04.ctrl_reset(), Pin.IN)
        
        mux_pin(0)
        mux_0 = [cena_pin(), cinc_pin(), crst_pin()]
        
        mux_pin(1)
        mux_1 = [cena_pin(), cinc_pin(), crst_pin()]
        if mux_1 != mux_0:
            log.info("DB seems to have on-board MUX: TT04+")
            cls.PCB = DemoboardVersion.TT04
            return True
        
        log.debug("Mux twiddle has no effect, probably not TT04 db")
        return False
    
    @classmethod 
    def probe(cls):
        if cls.probe_tt04mux():
            cls._configure_gpiomap()
            return True 
        if cls.probe_pullups():
            cls._configure_gpiomap()
            return True 
        
        log.debug("Neither pullup nor tt04mux tests conclusive, assuming TT06+ board")
        cls.PCB = DemoboardVersion.TT06
        cls._configure_gpiomap()
        return False
    
    @classmethod
    def force_detection(cls, dbversion:int):
        cls.PCB = dbversion 
        cls._configure_gpiomap()
            
    @classmethod 
    def _configure_gpiomap(cls):
        mapToUse = {
            
            DemoboardVersion.TT04: GPIOMapTT04,
            DemoboardVersion.TT06: GPIOMapTT06
            
            }
        if cls.PCB in mapToUse:
            ttboard.pins.gpio_map.GPIOMap = mapToUse[cls.PCB]
        else:
            raise RuntimeError('Cannot set GPIO map')
            
        
    