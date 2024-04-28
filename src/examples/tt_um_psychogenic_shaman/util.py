'''
Created on Apr 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import ttboard.logging as logging
log = logging.getLogger(__name__)

import ttboard.util.time as time


def wait_clocks(num:int=1):
    for _i in range(num):
        time.sleep_ms(1)
        
def die_with_error(msg:str):
    log.error(msg)
    raise Exception(msg)