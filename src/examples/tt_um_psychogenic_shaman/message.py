'''
Created on Apr 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from examples.tt_um_psychogenic_shaman.util import wait_clocks, die_with_error
from examples.tt_um_psychogenic_shaman.shaman import Shaman

import ttboard.log as logging
log = logging.getLogger(__name__)

def prep_block(shaman:Shaman, message_block):
    log.info(f' handle message block (f{message_block}) len {len(message_block)}')
    t = 0
    numSlots = len(message_block)/4
    while t < numSlots:
        #print(message_block[t])
        i = int.from_bytes(bytes(message_block[t*4:(t*4)+4]), 'big')
        for btIdx in range(4):
            daShift = ((3-btIdx)*8)
            byteVal = (i & (0xff << daShift)) >> daShift
            
            numBusyTicks = 0
            while shaman.busy and numBusyTicks < 10000:
                wait_clocks()
                
            if shaman.busy:
                die_with_error('Stuck in busy?')
            
            shaman.clock_in_data(byteVal)
            
        if (t < numSlots - 1 ) and shaman.busy:
            log.warn("hum busy")
            #raise RuntimeError('Should not be busy!')
        
        t += 1
        

def process_message_blocks(shaman:Shaman, message_blocks):
    shaman.start = 1
    wait_clocks(10) # uncertain about the requirement for this and subsequent wait
    shaman.start = 0
    wait_clocks(10) 
    
    
    for block in message_blocks:
        prep_block(shaman, block)

        numBusyTicks = 0
        while (shaman.busy and (not shaman.result_ready)):
            wait_clocks()
            print('.', end='')
            numBusyTicks += 1
        print(f'Processed block in {numBusyTicks} ticks')
        

    print('Waiting until done...')
    numWaitFinalTicks = 0
    while not shaman.result_ready:
        wait_clocks()
        print('x', end='')
        numWaitFinalTicks += 1
        
    print(f'Done after {numWaitFinalTicks}')
        
    
    result_bytes = []
    for _i in range(8*4*2):
        shaman.result_next = 1
        wait_clocks()
        shaman.result_next = 0
        wait_clocks()
        result_bytes.append(shaman.result)
        

    return result_bytes



def message_to_blocks(message: bytearray) -> bytearray:
    """chunk message bytearray into 512 bit block(s) with any required padding"""

    if isinstance(message, str):
        message = bytearray(message, 'ascii')
    elif isinstance(message, bytes):
        message = bytearray(message)
    elif not isinstance(message, bytearray):
        raise TypeError

    # Padding
    length = len(message) * 8 # len(message) is number of BYTES!!!
    message.append(0x80)
    while (len(message) * 8 + 64) % 512 != 0:
        message.append(0x00)

    message += length.to_bytes(8, 'big') # pad to 8 bytes or 64 bits

    assert (len(message) * 8) % 512 == 0, "Padding did not complete properly!"

    # Parsing
    blocks = [] # contains 512-bit chunks of message
    for i in range(0, len(message), 64): # 64 bytes is 512 bits
        blocks.append(message[i:i+64])
        
    return blocks

