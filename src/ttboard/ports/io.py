'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.types.ioport import IOPort
from ttboard.types.handle import LogicObject


class IO(LogicObject):
    def __init__(self, name:str, read_byte_fn=None, write_byte_fn=None):
        port = IOPort(name, read_byte_fn, write_byte_fn)
        super().__init__(port)
        self.port = port
        
    
    def __repr__(self):
        val = hex(int(self.value)) if self.port.is_readable  else ''
        return f'<IO {self.port.name} {val}>'