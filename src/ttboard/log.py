'''
Created on Jan 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.util.platform import IsRP2040
import ttboard.util.colors as colors 
import gc 
RPLoggers = dict()
DefaultLogLevel = 20 # info by default
if IsRP2040:
    # no logging support, add something basic
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    class Logger:
        colorMap = {
                10: 'yellow',
                20: 'green',
                30: 'yellow',
                40: 'red'
            }
        def __init__(self, name):
            self.name = name 
            self.loglevel = DefaultLogLevel
        def out(self, s, level:int):
            if self.loglevel <= level:
                print(f'{self.name}: {colors.color(s, self.colorMap[level])}')
            
        def debug(self, s):
            self.out(s, DEBUG)
        def info(self, s):
            self.out(s, INFO)
        def warn(self, s):
            self.out(s, WARN)
        def error(self, s):
            self.out(s, ERROR)
            
    def dumpMem(prefix:str='Free mem'):
        print(f"{prefix}: {gc.mem_free()}")
        
    def getLogger(name:str):
        global RPLoggers
        if name not in RPLoggers:
            RPLoggers[name] = Logger(name)
        return RPLoggers[name]
    
    def basicConfig(level:int):
        global DefaultLogLevel
        global RPLoggers
        DefaultLogLevel = level
        for logger in RPLoggers.values():
            logger.loglevel = level
            
        
else:
    from logging import *
    def dumpMem(prefix:str='Free mem'):
        print(f'{prefix}: infinity')