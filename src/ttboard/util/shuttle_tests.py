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



def clock_and_compare_output(tt:DemoBoard, read_bidirs:bool, max_idx:int, delay_interval_ms:int):
    err_count = 0
    for i in range(max_idx):
        tt.clock_project_once()
        time.sleep_ms(delay_interval_ms)
        out_byte = tt.uo_out.value
        
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
            bidir_byte = tt.uio_in.value 
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
    tt.ui_in.value = 1
    tt.clock_project_stop()
    tt.reset_project(False)
    
    err =  clock_and_compare_output(tt, read_bidirs, max_idx, delay_interval_ms)
    if err is not None:
        # error encountered, we're done here
        return err 
    
    
    # test that reset actually resets
    log.info('RP2040 test project reset')
    
    # make sure we're not exactly on 
    if tt.uo_out.value == 0:
        for _i in range(5):
            tt.clock_project_once()
            
        if tt.uo_out.value == 0:
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

def factory_test_clocking_04(tt:DemoBoard, max_idx:int=128, delay_interval_ms:int=1):
    return factory_test_clocking(tt, True, max_idx, delay_interval_ms)
    
