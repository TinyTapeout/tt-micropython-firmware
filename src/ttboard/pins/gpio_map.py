'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.pins.upython import Pin
from ttboard.mode import RPModeDEVELOPMENT
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
    def demoboard_uses_mux(cls):
        return False
    
    @classmethod 
    def mux_select(cls):
        raise RuntimeError('not implemented')
    
    @classmethod
    def muxed_pairs(cls):
        raise RuntimeError('not implemented')
        
    @classmethod
    def muxed_pinmode_map(cls, rpmode:int):
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
            "in0": cls.IN0,
            "in1": cls.IN1,
            "in2": cls.IN2,
            "in3": cls.IN3,
            "out4": cls.OUT4,
            "out5": cls.OUT5,
            "out6": cls.OUT6,
            "out7": cls.OUT7,
            "in4": cls.IN4,
            "in5": cls.IN5,
            "in6": cls.IN6,
            "in7": cls.IN7,
            "uio0": cls.UIO0,
            "uio1": cls.UIO1,
            "uio2": cls.UIO2,
            "uio3": cls.UIO3,
            "uio4": cls.UIO4,
            "uio5": cls.UIO5,
            "uio6": cls.UIO6,
            "uio7": cls.UIO7,
            "rpio29": cls.RPIO29
        }
        return retDict
        
class GPIOMapTT04(GPIOMapBase):
    '''
        A place to store 
         name -> GPIO #
        along with some class-level utilities, mainly for internal use.
        
        This allows for low-level control, if you wish, e.g.
        
        myrawpin = machine.Pin(GPIOMap.OUT4, machine.Pin.OUT)
        
        The only caveat is that some of these are duplexed through 
        the MUX, and named accordingly (e.g. nCRST_OUT2)
    '''
    RP_PROJCLK = 0
    HK_CSB = 1
    HK_SCK = 2
    SDI_nPROJECT_RST = 3 # SDI_OUT0 = 3
    HK_SDO = 4 #  SDO_OUT1 = 4
    OUT0 = 5 # nPROJECT_RST = 5
    CTRL_ENA_OUT1 = 6 # CTRL_ENA = 6
    nCRST_OUT2 = 7
    CINC_OUT3 = 8
    IN0 = 9
    IN1 = 10
    IN2 = 11
    IN3 = 12
    OUT4 = 13
    OUT5 = 14
    OUT6 = 15 
    OUT7 = 16
    IN4  = 17
    IN5  = 18
    IN6  = 19
    IN7  = 20
    UIO0 = 21
    UIO1 = 22
    UIO2 = 23
    UIO3 = 24
    UIO4 = 25
    UIO5 = 26
    UIO6 = 27
    UIO7 = 28
    RPIO29 = 29
    
    
    @classmethod 
    def project_clock(cls):
        return cls.RP_PROJCLK
    
    @classmethod 
    def project_reset(cls):
        return cls.SDI_nPROJECT_RST
    
    @classmethod 
    def ctrl_increment(cls):
        return cls.CINC_OUT3
    
    @classmethod 
    def ctrl_enable(cls):
        return cls.CTRL_ENA_OUT1
    
    @classmethod 
    def ctrl_reset(cls):
        return cls.nCRST_OUT2
    
    
    @classmethod 
    def demoboard_uses_mux(cls):
        return True
    
    
    @classmethod 
    def mux_select(cls):
        return cls.HK_CSB
    
    
    
    @classmethod 
    def all(cls):
        retDict = cls.all_common()
        retDict.update({
            "hk_csb": cls.HK_CSB,
            "hk_sck": cls.HK_SCK,
            "sdi_nprojectrst": cls.SDI_nPROJECT_RST, # "sdi_out0": cls.SDI_OUT0,
            "hk_sdo": cls.HK_SDO, # "sdo_out1": cls.SDO_OUT1,
            "out0": cls.OUT0,
            "cena_out1": cls.CTRL_ENA_OUT1, # "ctrl_ena": cls.CTRL_ENA,
            "ncrst_out2": cls.nCRST_OUT2,
            "cinc_out3": cls.CINC_OUT3,
        })
        return retDict
    @classmethod
    def muxed_pairs(cls):
        mpairnames = [
            'sdi_nprojectrst',
            'cena_out1',
            'ncrst_out2',
            'cinc_out3'
        ]
        retVals = {}
        for mpair in mpairnames:
            retVals[mpair] = mpair.split('_')
        
        return retVals;
    
    
    @classmethod 
    def muxed_pinmode_map(cls, rpmode:int):
        
        pinModeMap = {
            'nprojectrst': Pin.IN, # "special" pin -- In == pulled-up, NOT reset
            'sdi': Pin.OUT,
            'cena': Pin.OUT, 
            'out1': Pin.IN,
            
            'ncrst': Pin.OUT,
            'out2': Pin.IN,
            
            
            'cinc': Pin.OUT,
            'out3': Pin.IN
            }
        if rpmode == RPModeDEVELOPMENT.STANDALONE:
            for k in pinModeMap.keys():
                if k.startswith('out'):
                    pinModeMap[k] = Pin.OUT
            
        
        return pinModeMap
    


class GPIOMapTT06(GPIOMapBase):
    RP_PROJCLK = 0
    PROJECT_nRST = 1
    CTRL_SEL_nRST = 2
    CTRL_SEL_INC = 3
    CTRL_SEL_ENA = 4
    OUT0 = 5
    OUT1 = 6
    OUT2 = 7
    OUT3 = 8
    IN0 = 9
    IN1 = 10
    IN2 = 11
    IN3 = 12
    OUT4 = 13
    OUT5 = 14
    OUT6 = 15 
    OUT7 = 16
    IN4  = 17
    IN5  = 18
    IN6  = 19
    IN7  = 20
    UIO0 = 21
    UIO1 = 22
    UIO2 = 23
    UIO3 = 24
    UIO4 = 25
    UIO5 = 26
    UIO6 = 27
    UIO7 = 28
    RPIO29 = 29
    
    @classmethod 
    def project_clock(cls):
        return cls.RP_PROJCLK
    
    @classmethod 
    def project_reset(cls):
        return cls.PROJECT_nRST
    
    
    @classmethod 
    def ctrl_increment(cls):
        return cls.CTRL_SEL_INC
    
    @classmethod 
    def ctrl_enable(cls):
        return cls.CTRL_SEL_ENA
    
    @classmethod 
    def ctrl_reset(cls):
        return cls.CTRL_SEL_nRST
    
    @classmethod 
    def all(cls):
        retDict = cls.all_common()
        #retDict = GPIOMapBase.all(cls)
        retDict.update({
            'nprojectrst': cls.PROJECT_nRST,
            'cinc': cls.CTRL_SEL_INC,
            'cena': cls.CTRL_SEL_ENA,
            'ncrst': cls.CTRL_SEL_nRST
        })
        return retDict

GPIOMap = GPIOMapTT04
