'''
Created on Apr 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import ttboard.util.time as time
from ttboard.boot.shuttle_properties import ShuttleProperties
from ttboard.boot.demoboard_detect import DemoboardDetect, DemoboardCarrier


import ttboard.log as logging
log = logging.getLogger(__name__)

class ChipROM(ShuttleProperties):
    def __init__(self, project_mux):
        super().__init__()
        self.project_mux = project_mux 
        self._contents = None 
        self._pins = project_mux.pins
        self._rom_data = None
    
    
    def _send_and_rcv(self, send:int):
        self._pins.ui_in.value = send 
        time.sleep_ms(1)
        return  self._pins.uo_out.value
        
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
        
        self._contents = {
                'shuttle': 'unknown',
                'repo': '',
                'commit': ''
        }
        if not DemoboardDetect.CarrierPresent:
            log.warn("No carrier present, skipping chiprom")
            return self._contents
        
        if DemoboardDetect.CarrierVersion != DemoboardCarrier.TT_CARRIER:
            if DemoboardDetect.CarrierVersion == DemoboardCarrier.FPGA:
                self._contents['shuttle'] = 'FPGA'
            
            return self._contents
        
        # select project 0
        self.project_mux.reset_and_clock_mux(0)
        
        
        # list of expected outputs as
        # (SEND, RCV)
        magic_expects = [(0, 0x78), (129, 0x0)]
        
        for magic_pairs in magic_expects:
            magic = self._send_and_rcv(magic_pairs[0])
            if magic != magic_pairs[1]:
                log.warn(f"No chip rom here? Got 'magic' {hex(magic)} @ {magic_pairs[0]}")
                log.info('Fake reporting at tt04 chip')
                self.project_mux.disable()
                return self._contents
        
        rom_data = ''
        for i in range(32, 128):
            byte = self._send_and_rcv(i)
            if byte == 0:
                break
            rom_data += chr(byte)
        self._rom_data = rom_data

        if not len(rom_data):
            log.warn("ROM data empty")
        else:
            log.info(f'Got ROM data\n{rom_data}')
            for l in rom_data.splitlines():
                try:
                    k,v = l.split('=')
                    self._contents[k] = v 
                except:
                    log.warn(f"Issue splitting {l}")
                    pass 
        log.debug(f"Parsed ROM contents: {self._contents}")
        self.project_mux.disable()
        return self._contents
        
        
