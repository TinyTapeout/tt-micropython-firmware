'''
Created on Apr 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import binascii
import ttboard.util.time as time
from ttboard.boot.shuttle_properties import ShuttleProperties
from ttboard.boot.demoboard_detect import DemoboardDetect, DemoboardCarrier
from ttboard.pins.upython import Pin


import ttboard.log as logging
log = logging.getLogger(__name__)

# 7-segment encoding of 't' -- the shuttle name always starts with "tt"
# so the first two ROM bytes are both this value (used by the
# address-mode magic check; the clocked path validates by CRC32).
ROM_MAGIC_BYTE = 0x78

ROM_LENGTH = 256
ROM_DESCRIPTOR_START = 32
ROM_DESCRIPTOR_END = 128

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
        
        # select project 0 (the ROM)
        self.project_mux.reset_and_clock_mux(0)

        descriptor = self._read_via_clock()
        if descriptor is None:
            descriptor = self._read_via_address()

        if descriptor is not None:
            self._parse_descriptor(descriptor)

        log.debug(f"Parsed ROM contents: {self._contents}")
        self.project_mux.disable()
        return self._contents

    def _read_via_clock(self):
        '''
        Sequential ROM read: pulse rst_n low so the address counter
        resets to 0, then toggle clk to walk through the bytes.
        Returns the descriptor block, or None if the trailing CRC32
        doesn't match.
        '''
        pins = self._pins
        pins.project_clk_driven_by_RP2(True)
        pins.rp_projclk(0)
        # Force a falling edge on rst_n so the address counter
        # is guaranteed to reset to 0 (rst_n may already be low).
        pins.nprojectrst.mode = Pin.OUT
        pins.nprojectrst(1)
        pins.nprojectrst(0)

        rom_bytes = bytearray(ROM_LENGTH)
        rom_bytes[0] = pins.uo_out.value
        for i in range(1, ROM_LENGTH):
            pins.rp_projclk(1)
            pins.rp_projclk(0)
            rom_bytes[i] = pins.uo_out.value

        # release reset; on-board pull-up takes rst_n high
        pins.nprojectrst.mode = Pin.IN

        # Older chips ignore rst_n/clk and just output ROM[ui_in], so every
        # byte comes back as ROM[0]. Check this before CRC so the log
        # distinguishes it from a genuine CRC failure.
        if all(b == rom_bytes[0] for b in rom_bytes[:8]):
            log.warn(f"Clock-mode ROM stuck at {hex(rom_bytes[0])} (likely pre-tt10 chip)")
            return None

        expected_crc = int.from_bytes(rom_bytes[-4:], 'little')
        actual_crc = binascii.crc32(rom_bytes[:-4])
        if actual_crc != expected_crc:
            log.warn(f"Clock-mode ROM CRC mismatch: {hex(actual_crc)} != {hex(expected_crc)}")
            return None
        log.info("Read ROM via clock toggling")
        return bytes(rom_bytes[ROM_DESCRIPTOR_START:ROM_DESCRIPTOR_END])

    def _read_via_address(self):
        '''
        Fallback: drive ui_in to the desired address (rst_n high) and
        sample uo_out for each byte. Returns the descriptor block, or
        None if the magic bytes don't match.
        '''
        for addr, expected in [(0, ROM_MAGIC_BYTE), (129, 0x0)]:
            magic = self._send_and_rcv(addr)
            if magic != expected:
                log.warn(f"No chip rom here? Got 'magic' {hex(magic)} @ {addr}")
                log.info('Fake reporting at tt04 chip')
                return None
        log.info("Read ROM via ui_in addressing")
        descriptor = bytearray(ROM_DESCRIPTOR_END - ROM_DESCRIPTOR_START)
        for i in range(len(descriptor)):
            descriptor[i] = self._send_and_rcv(ROM_DESCRIPTOR_START + i)
        return bytes(descriptor)

    def _parse_descriptor(self, descriptor:bytes):
        rom_data = ''
        for b in descriptor:
            if b == 0:
                break
            rom_data += chr(b)
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
