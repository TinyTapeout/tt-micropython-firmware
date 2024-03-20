'''
Created on Mar 20, 2024

Anything that's a command in the first_boot.ini file has 
to be defined here.

During run tests, demoboard instance is available through 
get_demoboard()

The function used by [onsuccess] must return true if we
don't want to go through firstboot routine again. 


@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.demoboard import DemoBoard, Pins
import ttboard.util.time as time
from ttboard.mode import RPMode


import ttboard.logging as logging
log = logging.getLogger(__name__)


def get_demoboard() -> DemoBoard:
    return locals()['demoboard']

def setup_somehow():
    # any setup we might need done
    print("nothing much to setup")
    
def firstboot_completed():
    # called when all tests passed.
    # if you return True, the first boot ini file will 
    # be unlinked and we won't come through this again.
    # can only happen if all tests ([run_*] sections)
    # run and return True
    print("Done first boot")
    return True
    
    
def test_bidirs(max_idx:int, delay_interval_ms:int=1):
    # a test, must return True to consider a pass
    tt = get_demoboard()
    print(f'Testing bidirs up to {max_idx} on {tt}')
    
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
    
    errCount = 0
    for i in range(0xff):
        tt.bidir_byte = i 
        time.sleep_ms(update_delay_ms)
        outbyte = tt.output_byte
        if outbyte !=  i:
            log.warn(f'MISMATCH between bidir val {i} and output {outbyte}')
            errCount += 1
    
    # reset everything
    for bp in tt.bidirs:
        bp.mode = Pins.IN
        
    tt.clock_project_stop()
    tt.mode = curMode
    
    if errCount:
        log.error(f'{errCount} ERRORS encountered')
        return False 
    
    log.info('Bi-directional pins acting pretty nicely as inputs!')
    return True

def say_hello(delay_interval_ms:int=100, times:int=1):
    # a test, must return True to consider a pass
    print(f'Saying hello')
    
    hello_values = [0x74, 0x79, 0x30, 0x30, 0x5c, 0, 0x50, 0x10, 0x78, 0x77]
    tt = get_demoboard()
    tt.shuttle.tt_um_test.enable()
    tt.mode = RPMode.ASIC_ON_BOARD # make sure we're controlling everything
    
    tt.in0(0) # want this low
    tt.clock_project_PWM(1e3) # clock it real good
    
    log.info('First boot: saying hello')
    for bp in tt.bidirs:
        bp.mode = Pins.OUT
        bp(0) # start low
    
    for _i in range(times):
        for v in hello_values:
            tt.bidir_byte = v
            time.sleep_ms(delay_interval_ms)
            
            tt.bidir_byte = 0
            time.sleep_ms(int(delay_interval_ms/10))
        
        tt.bidir_byte = 0
        time.sleep_ms(int(delay_interval_ms/2))
        
    
    
    # reset everything
    for bp in tt.bidirs:
        bp.mode = Pins.IN
        
    tt.clock_project_stop()
    
    return True
        
    