'''
Created on Jan 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.util.platform import IsRP2
import ttboard.util.colors as colors 
import ttboard.util.time as time
import gc 
RPLoggers = dict()
DefaultLogLevel = 20 # info by default
LoggingPrefix = 'BOOT'
if IsRP2:
    # no logging support, add something basic
    DEBUG   = 10
    INFO    = 20
    WARN    = 30
    WARNING = 30
    ERROR   = 40
    class Logger:
        OutFile = None 
        colorMap = {
                10: 'yellow',
                20: 'green',
                30: 'yellow',
                40: 'red'
            }
        
        @classmethod 
        def set_out_file(cls, path_to:str=None):
            if cls.OutFile is not None:
                cls.OutFile.close()
                cls.OutFile = None 
                
            if path_to is not None:
                cls.OutFile = open(path_to, 'w')
                
        
        def __init__(self, name):
            self.name = name 
            self.loglevel = DefaultLogLevel
        
        def out(self, s, level:int):
            global LoggingPrefix
            if self.loglevel <= level:
                if LoggingPrefix:
                    prefix = LoggingPrefix
                else:
                    prefix = self.name
                if self.OutFile is not None:
                    print(f'{prefix}: {s}', file=self.OutFile)
                    
                print(f'{prefix}: {colors.color(s, self.colorMap[level])}')
        
        def debug(self, s):
            self.out(s, DEBUG)
        def info(self, s):
            self.out(s, INFO)
        def warn(self, s):
            self.out(s, WARN)
        def warning(self, s):
            self.out(s, WARNING)
        def error(self, s):
            self.out(s, ERROR)
            
        def getChild(self, nm):
            return getLogger(f'{self.name}.{nm}')
            
    def dumpMem(prefix:str='Free mem'):
        print(f"{prefix}: {gc.mem_free()}")
    
    DeltaTicksStart = time.ticks_ms()
    def dumpTicksMs(msg:str='ticks'):
        print(f"{msg}: {time.ticks_ms()}")
        
    def ticksStart():
        global DeltaTicksStart
        DeltaTicksStart = time.ticks_ms()
        
    def dumpTicksMsDelta(msg:str='ticks'):
        tnow = time.ticks_ms()
        print(f"{msg}: {time.ticks_diff(tnow, DeltaTicksStart)}")
        
    def getLogger(name:str):
        global RPLoggers
        if name not in RPLoggers:
            RPLoggers[name] = Logger(name)
        return RPLoggers[name]
    
    def basicConfig(level:int=None, filename:str=None):
        global DefaultLogLevel
        global RPLoggers
        
        if level is not None:
            DefaultLogLevel = level
            for logger in RPLoggers.values():
                logger.loglevel = level
        
        Logger.set_out_file(filename)
        
            
        
            
        
            
            
        
else:
    from logging import *
    def dumpMem(prefix:str='Free mem'):
        print(f'{prefix}: infinity')
    def dumpTicksMs(msg:str='ticks ms'):
        print(f"{msg}: 0")
    
    def ticksStart():
        return 
        
    def dumpTicksMsDelta(msg:str='ticks'):
        print(f"{msg}: 0")