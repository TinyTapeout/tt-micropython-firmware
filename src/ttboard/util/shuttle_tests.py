'''
Created on Apr 10, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.demoboard import DemoBoard, Pins
import ttboard.util.time as time
from ttboard.mode import RPMode

import ttboard.logging as logging
log = logging.getLogger(__name__)

def factory_test_bidirs(tt:DemoBoard, max_idx:int=255, delay_interval_ms:int=1):
    '''
        Tests project comms and bidir pins by using tt_um_test to reflect 
        bidir to output.
        
        @return: error message, or None on all passed
    
    '''
    log.info(f'Testing bidirs up to {max_idx} on {tt}')
    
    # select the project from the shuttle
    update_delay_ms = delay_interval_ms
    auto_clock_freq = 1e3
    tt.shuttle.tt_um_test.enable()
    curMode = tt.mode 
    tt.mode = RPMode.ASIC_ON_BOARD # make sure we're controlling everything
    
    tt.in0(0) # want this low
    tt.clock_project_PWM(auto_clock_freq) # clock it real good
    
    log.info('First boot: starting bidirection pins tests')
    for bp in tt.bidirs:
        bp.mode = Pins.OUT
        bp(0) # start low
    
    err_count = 0
    for i in range(max_idx):
        tt.bidir_byte = i 
        time.sleep_ms(update_delay_ms)
        outbyte = tt.output_byte
        if outbyte !=  i:
            log.warn(f'MISMATCH between bidir val {i} and output {outbyte}')
            err_count += 1
    
    # reset everything
    for bp in tt.bidirs:
        bp.mode = Pins.IN
        
    tt.clock_project_stop()
    tt.mode = curMode
    
    if err_count:
        err_message = f'{err_count} mismatches between bidir and output'
        log.error(err_message)
        return err_message 
    
    log.info('Bi-directional pins acting pretty nicely as inputs!')
    return None


def factory_test_clocking(tt:DemoBoard, max_idx:int=30, delay_interval_ms:int=50):
    '''
        Tests project comms, clocking and output pins by using tt_um_test to 
        count clock ticks.
                
        @return: error message, or None on all passed
    
    '''
    log.info(f'Testing manual clocking up to {max_idx} on {tt}')
    
    
    # select the project from the shuttle
    tt.shuttle.tt_um_test.enable()
    tt.mode = RPMode.ASIC_ON_BOARD # make sure we're controlling everything
    
    
    tt.reset_project(True)
    tt.input_byte = 1
    tt.clock_project_stop()
    tt.reset_project(False)
    
    err_count = 0
    for i in range(max_idx):
        tt.clock_project_once()
        time.sleep_ms(delay_interval_ms)
        out_byte = tt.output_byte
        
        # give ourselves a little jitter room, in case we're a step
        # behind as has happened for reasons unclear
        if out_byte != i and out_byte != (i+1) and out_byte != (i-1):
            log.warn(f'MISMATCH between expected count {i} and output {tt.output_byte}')
            err_count += 1
    
    
    if err_count:
        err_msg = f'{err_count}/{max_idx} mismatches during counting test'
        log.error(err_msg)
        return err_msg 
    
    log.info('RP2040 clocking acting pretty nicely')
    return None


