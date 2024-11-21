'''
Created on Apr 10, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.demoboard import DemoBoard, Pins
import ttboard.util.time as time
from ttboard.mode import RPMode

import ttboard.log as logging
log = logging.getLogger(__name__)

def factory_test_bidirs_03p5(tt:DemoBoard, max_idx:int=255, delay_interval_ms:int=1):
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
    tt.mode = RPMode.ASIC_RP_CONTROL # make sure we're controlling everything
    
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


def clock_and_compare_output(tt:DemoBoard, read_bidirs:bool, max_idx:int, delay_interval_ms:int):
    err_count = 0
    for i in range(max_idx):
        tt.clock_project_once()
        time.sleep_ms(delay_interval_ms)
        out_byte = tt.output_byte
        
        # give ourselves a little jitter room, in case we're a step
        # behind as has happened for reasons unclear
        max_val = i+1
        min_val = i-1
        
        if out_byte >= min_val and out_byte <= max_val:
            # close enough
            log.debug(f'Clock count {i}, got {out_byte}')
        else:
            log.warn(f'MISMATCH between expected count {i} and output {out_byte}')
            err_count += 1
            
        if read_bidirs:
            bidir_byte = tt.bidir_byte 
            if bidir_byte >= min_val and bidir_byte <= max_val:
                # close enough
                log.debug(f'Clock count {i}, got bidir {bidir_byte}')
            else:
                log.warn(f'MISMATCH between expected count {i} and bidir {bidir_byte}')
                err_count += 1
                
    
    
    if err_count:
        err_msg = f'{err_count}/{max_idx} mismatches during counting test'
        log.error(err_msg)
        return err_msg 
    
    log.info('RP2040 clocking acting pretty nicely')
    return None
    


def factory_test_clocking(tt:DemoBoard, read_bidirs:bool, max_idx:int=128, delay_interval_ms:int=1):
    log.info(f'Testing manual clocking up to {max_idx} on {tt}')
    
    # select the project from the shuttle
    tt.shuttle.factory_test.enable()
    tt.mode = RPMode.ASIC_RP_CONTROL # make sure we're controlling everything
    
    
    tt.reset_project(True)
    tt.input_byte = 1
    tt.clock_project_stop()
    tt.reset_project(False)
    
    err =  clock_and_compare_output(tt, read_bidirs, max_idx, delay_interval_ms)
    if err is not None:
        # error encountered, we're done here
        return err 
    
    
    # test that reset actually resets
    log.info('RP2040 test project reset')
    
    # make sure we're not exactly on 
    if tt.output_byte == 0:
        for _i in range(5):
            tt.clock_project_once()
            
        if tt.output_byte == 0:
            log.warn("Something is off: clocked a few times, still reporting 0")
            
            
    tt.reset_project(True)
    time.sleep_ms(10)
    tt.reset_project(False)
    err =  clock_and_compare_output(tt, read_bidirs, 0xf, delay_interval_ms)
    if err is not None:
        log.error(f'Problem with clocking test post-reset: {err}')
        return err 
    
    log.info('RP2040: reset well behaved!')
    return None 
        
    
    
    
    



def factory_test_clocking_03p5(tt:DemoBoard, max_idx:int=128, delay_interval_ms:int=1):
    return factory_test_clocking(tt, False, max_idx, delay_interval_ms)
    
def factory_test_clocking_04(tt:DemoBoard, max_idx:int=128, delay_interval_ms:int=1):
    return factory_test_clocking(tt, True, max_idx, delay_interval_ms)
    
