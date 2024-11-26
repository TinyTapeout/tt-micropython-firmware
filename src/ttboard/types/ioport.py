'''
Created on Nov 20, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.types.range import Range
import ttboard.log as logging
log = logging.getLogger(__name__)

class Port:    
    def __init__(self, name:str, read_byte_fn=None, write_byte_fn=None):
        self.name = name 
        self.byte_read = read_byte_fn 
        self.byte_write = write_byte_fn
    
    @property 
    def is_readable(self):
        return self.byte_read is not None 
    
    @property 
    def is_writeable(self):
        return self.byte_write is not None 
        
    def set_signal_val_int(self, vint:int):
        if self.byte_write is None:
            log.error(f'writes not supported on {self.name}')
            return
        self.byte_write(vint)
        
    def set_signal_val_binstr(self, vstr:str):
        if self.byte_write is None:
            log.error(f'writes not supported on {self.name}')
            return 
        self.byte_write(int(vstr, 2))
        
        
    def get_signal_val_binstr(self):
        if self.byte_read is None:
            log.error(f'reads not supported on {self.name}')
            return
        v = self.byte_read()
        return f'{v:08b}'
    
    def get_name_string(self):
        return self.name
    
    def get_type_string(self):
        return 'byte' # not sure what to return here
    
    def get_definition_name(self):
        return self.get_name_string()
    
    def get_range(self):
        return (7, 0, Range.RANGE_DOWN)
    
    def get_const(self) -> bool:
        return False
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Port):
            return NotImplemented
        return self.byte_read() == other.byte_read()
    
    


class IOPort(Port):
    pass

class OEPort(Port):
    pass