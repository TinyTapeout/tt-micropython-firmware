'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.pins.upython import Pin
from ttboard.mode import RPModeDEVELOPMENT
class GPIOMap:
    '''
        A place to store 
         name -> GPIO #
        along with some class-level utilities, mainly for internal use.
        
        This allows for low-level control, if you wish, e.g.
        
        myrawpin = machine.Pin(GPIOMap.OUT4, machine.Pin.OUT)
        
        The only caveat is that some of these are duplexed through 
        the MUX, and named accordingly (e.g. SDI_OUT0)
    '''
    RP_PROJCLK = 0
    HK_CSB = 1
    HK_SCK = 2
    SDI_OUT0 = 3
    SDO_OUT1 = 4
    nPROJECT_RST = 5
    CTRL_ENA = 6
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
    def muxed_pairs(cls):
        mpairnames = [
            'sdi_out0',
            'sdo_out1',
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
            'out0': Pin.IN,
            'out1': Pin.IN,
            'out2': Pin.IN,
            'out3': Pin.IN,
            'sdi': Pin.OUT,
            'sdo': Pin.IN,
            'ncrst': Pin.OUT,
            'cinc': Pin.OUT,
            }
        if rpmode == RPModeDEVELOPMENT.STANDALONE:
            for k in pinModeMap.keys():
                if k.startswith('out'):
                    pinModeMap[k] = Pin.OUT
            
        
        return pinModeMap
        
    @classmethod 
    def always_outputs(cls):
        return [
            # 'nproject_rst',
            # 'rp_projclk', -- don't do this during "safe" operation
            'ctrl_ena'
        ]
    
    @classmethod
    def default_pull(cls, pin):
        if pin in ["nproject_rst", "ctrl_ena"]:
            return Pin.PULL_UP
        return Pin.PULL_DOWN
    
    @classmethod 
    def all(cls):
        retDict = {
            "rp_projclk": cls.RP_PROJCLK,
            "hk_csb": cls.HK_CSB,
            "hk_sck": cls.HK_SCK,
            "sdi_out0": cls.SDI_OUT0,
            "sdo_out1": cls.SDO_OUT1,
            "nproject_rst": cls.nPROJECT_RST,
            "ctrl_ena": cls.CTRL_ENA,
            "ncrst_out2": cls.nCRST_OUT2,
            "cinc_out3": cls.CINC_OUT3,
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



