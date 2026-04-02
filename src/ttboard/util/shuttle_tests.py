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

def exercise_factory_test():
    import microcotb
    import examples.tt_um_factory_test as test 
    runner = test.run()
    err_msgs = []
    for atest in runner.tests_to_run.values():
        if atest.failed:
            err_msgs.append(f'{atest.name} failed: {atest.failed_msg}')
            log.info(err_msgs[-1])
            
    if len(err_msgs):
        return '|'.join(err_msgs)
    
    return None 

def factory_test_clocking(tt:DemoBoard, read_bidirs:bool, max_idx:int=128, delay_interval_ms:int=1):
    log.info(f'Performing factory test on {tt}')
    return exercise_factory_test()
    
