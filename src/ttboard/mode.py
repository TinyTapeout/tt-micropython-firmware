'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
class ModeBase:
    SAFE = 0
    ASIC_ON_BOARD = 1
    ASIC_MANUAL_INPUTS = 2
    
    @classmethod 
    def modemap(cls):
        modeMap = {  
            'SAFE': cls.SAFE,
            'ASIC_ON_BOARD': cls.ASIC_ON_BOARD,
            'ASIC_MANUAL_INPUTS': cls.ASIC_MANUAL_INPUTS
        }
        return modeMap
    
    @classmethod
    def from_string(cls, s:str):
        modeMap = cls.modemap()
        if s is None or not hasattr(s, 'upper'):
            return None
        sup = s.upper()
        if sup not in modeMap:
            # should we raise here?
            return None 
        
        return modeMap[sup]
    
    @classmethod 
    def namemap(cls):
        nameMap = { 
            cls.SAFE: 'SAFE',
            cls.ASIC_ON_BOARD: 'ASIC_ON_BOARD',
            cls.ASIC_MANUAL_INPUTS: 'ASIC_MANUAL_INPUTS',
        }
        return nameMap 
    @classmethod
    def to_string(cls, mode:int):
        nameMap = cls.namemap()
        if mode in nameMap:
            return nameMap[mode]
        
        return 'UNKNOWN'

class RPMode(ModeBase):
    '''
      Poor man's enum, allowing for
      RPMode.MODE notation and code completion
      where MODE is one of:
        SAFE
        ASIC_ON_BOARD
        ASIC_MANUAL_INPUTS
    '''
    pass 

class RPModeDEVELOPMENT(ModeBase):
    '''
        Danger zone.  Includes the 
        STANDALONE mode, which drives outputs, conflicting with any ASIC present,
        so moved here.
    '''
    STANDALONE = 3
    
    
    @classmethod 
    def modemap(cls):
        modeMap = {  
            'SAFE': cls.SAFE,
            'ASIC_ON_BOARD': cls.ASIC_ON_BOARD,
            'ASIC_MANUAL_INPUTS': cls.ASIC_MANUAL_INPUTS,
            'STANDALONE': cls.STANDALONE
        }
        return modeMap
    
    @classmethod 
    def namemap(cls):
        nameMap = { 
            cls.SAFE: 'SAFE',
            cls.ASIC_ON_BOARD: 'ASIC_ON_BOARD',
            cls.ASIC_MANUAL_INPUTS: 'ASIC_MANUAL_INPUTS',
            cls.STANDALONE: 'STANDALONE'
        }
        return nameMap 
    