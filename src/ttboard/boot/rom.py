'''
Created on Apr 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import ttboard.util.time as time
from ttboard.boot.shuttle_properties import ShuttleProperties


import ttboard.log as logging
log = logging.getLogger(__name__)

class ChipROM(ShuttleProperties):
    def __init__(self, project_mux):
        super().__init__()
        self.project_mux = project_mux 
        self._contents = None 
        self._pins = project_mux.pins
    
    
    def _send_and_rcv(self, send:int):
        self._pins.input_byte = send 
        time.sleep_ms(1)
        return self._pins.output_byte
        
    @property
    def shuttle(self):
        try:
            return self.contents['shuttle']
        except:
            log.error("ROM has no 'shuttle'")
            return ''
        
    @property 
    def repo(self):
        try:
            return self.contents['repo']
        except:
            log.error("ROM has no 'repo'")
            return ''
    
    @property 
    def commit(self):
        try:
            return self.contents['commit']
        except:
            log.error("ROM has no 'commit'")
            return ''
    
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
        
        # list of expected outputs as
        # (SEND, RCV)
        magic_expects = [(0, 0x78), (129, 0x0)]
        
        for magic_pairs in magic_expects:
            magic = self._send_and_rcv(magic_pairs[0])
            if magic != magic_pairs[1]:
                log.warn(f"No chip rom here? Got 'magic' {hex(magic)} @ {magic_pairs[0]}")
                log.info('Fake reporting at tt03p5 chip')
                self.project_mux.disable()
                return self._contents
        
        rom_data = ''
        for i in range(32, 128):
            byte = self._send_and_rcv(i)
            if byte == 0:
                break
            rom_data += chr(byte)
        
        log.info(f'Got ROM data {rom_data}')

        self._contents = {'shuttle':'tt04', 'commit':'FAKEDATA'}
        if not len(rom_data):
            log.warn("ROM data empty")
        else:
            for l in rom_data.splitlines():
                try:
                    k,v = l.split('=')
                    self._contents[k] = v 
                except:
                    log.warn(f"Issue splitting {l}")
                    pass 
        log.debug(f"GOT ROM: {self._contents}")
        self.project_mux.disable()
        return self._contents
        
        
