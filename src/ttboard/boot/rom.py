'''
Created on Apr 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

class ChipROM:
    def __init__(self, project_mux):
        self.project_mux = project_mux 
        self._contents = None 
        self._pins = project_mux.pins
    
    
    def _send_and_rcv(self, send:int):
        self._pins.input_byte = send 
        return self._pins.output_byte
        
    @property
    def shuttle(self):
        return self.contents['shuttle']
    
    @property 
    def repo(self):
        return self.contents['repo']
    
    @property 
    def commit(self):
        return self.contents['commit']
    
    @property 
    def contents(self):
        if self._contents is not None:
            return self._contents 
        
        # select project 0
        self.project_mux.reset_and_clock_mux(0)
        
        self._contents = {
                'shuttle': 'tt03p5',
                'repo': '',
                'commit': ''
        }
        
        magic = self._send_and_rcv(0)
        if magic != 0x78:
            
            return self._contents
        
        rom_data = ''
        for i in range(32, 128):
            byte = self._send_and_rcv(i)
            if byte == 0:
                break
            rom_data += chr(byte)
        
        self._contents = {}
        for l in rom_data.splitlines():
            try:
                k,v = l.split('=')
                self._contents[k] = v 
            except:
                pass 
        
        return self._contents
        
        
