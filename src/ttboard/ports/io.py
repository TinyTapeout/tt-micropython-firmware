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
        
    
        self.byte_read = read_byte_fn 
        self.byte_write = write_byte_fn
    
    @property 
    def is_readable(self):
        return self.port.is_readable 
    
    @property 
    def is_writeable(self):
        return self.port.is_readable
    
    @property 
    def byte_read(self):
        return self.port.byte_read
    @byte_read.setter 
    def byte_read(self, func):
        self.port.byte_read = func
    @property 
    def byte_write(self):
        return self.port.byte_write
    
    @byte_write.setter 
    def byte_write(self, func):
        self.port.byte_write = func
        
    
    def __repr__(self):
        val = hex(int(self.value)) if self.port.is_readable  else ''
        return f'<IO {self.port.name} {val}>'
    
    def __str__(self):
        return str(self.value)