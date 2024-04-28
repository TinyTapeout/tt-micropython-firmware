'''
Created on Apr 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
from ttboard.pins.pins import Pins

import ttboard.logging as logging
log = logging.getLogger(__name__)

import ttboard.util.time as time


def die_on_error(msg:str):
    log.error(msg)
    return False 

def run(loops:int=2, note_delay_ms:int=2000):
    tt = DemoBoard.get()
    if not tt.shuttle.has('tt_um_psychogenic_neptuneproportional'):
        return die_on_error("This chip doesn't got neptune on-board!")
        
    if tt.user_config.has_section('tt_um_psychogenic_neptuneproportional'):
        log.info('Found a neptune section in config--letting it handle things')
    else:
        log.info('No neptune section in config--doing it manual style')
        tt.mode = RPMode.ASIC_RP_CONTROL
        tt.reset_project(True) # hold in reset, in case something else is loaded
        # input byte
        # clock speed is lower bits, input comes on in5
        # display mode single/control are bits 6 and 7
        tt.input_byte = 0b11001000
        tt.clock_project_PWM(4000)
        tt.bidir_mode = [Pins.IN]*8
        
    tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
    tt.reset_project(False) # start her up
    
    notes = [
        ('E2', 83),
        ('A2', 110),
        ('D3', 146),
        ('E3', 83*2),
        ('G3', 196),
        ('A3', 220),
        ('B3', 247),
        ('D4', 146*2),
        ('E4', 330),
        ('G4', 196*2),
    ]
    
    pwm = tt.in5.pwm(10)
    for _i in range(loops):
        for n in notes:
            pwm.freq(n[1])
            print(f'"Playing" a note: {n[0]} ({n[1]}Hz)')
            for _j in range(3):
                time.sleep_ms(int(note_delay_ms/3))
                reported_count = tt.bidir_byte
                ratio = n[1]/reported_count
                print(f'   Bidir count: {reported_count} (ratio {ratio:.1f}), Outputs {hex(tt.output_byte)}')
                
            
    
    pwm.deinit() # shut that down
    tt.in5(0) # bring low
            
if __name__ == '__main__':
    run()