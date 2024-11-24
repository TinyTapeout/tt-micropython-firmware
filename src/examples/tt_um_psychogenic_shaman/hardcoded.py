'''
Created on Apr 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard
from .message import message_to_blocks, process_message_blocks
from .shaman import Shaman


import ttboard.log as logging
log = logging.getLogger(__name__)

DefaultMessageToEncode = 'you are my very nice friend'

def result_map(reslist:list):
    return list(map(lambda x: hex(x), reslist))

def run(msg_to_encode:str=DefaultMessageToEncode):
    tt = DemoBoard.get()
    shaman = Shaman(tt)
    
    if tt.shuttle.run != 'tt05':
        print(f"Shaman isn't actually on shuttle {tt.shuttle.run}, sorry!")
        return False
    
    print("Selecting shaman project")
    tt.shuttle.tt_um_psychogenic_shaman.enable()
    
    tt.reset_project(True)
    tt.uio_oe_pico.value = 0b11001100
    
    tt.reset_project(False)
    
    

    
    
    message_blocks = message_to_blocks(msg_to_encode)
    print(f"Will encode:\n'{msg_to_encode}'")
    print("first: sequential load")
    res_1 = encode_standard(shaman, message_blocks)
    print(f"Result: {result_map(res_1)}")
    tt.reset_project(True)
    tt.reset_project(False)
    res_2 = encode_parallel(shaman, message_blocks)
    print(f"Result: {result_map(res_2)}")
    
    errs = 0
    if len(res_1) == len(res_2):
        for i in range(len(res_1)):
            if res_1[i] != res_2[i]:
                print(f"Difference in byte {i}: {res_1[i]} != {res_2[i]}")
                errs += 1
            else:
                log.info(f'{hex(res_1[i])} == {hex(res_2[i])}')
    if errs:
        return False 
    
    print("Results Match!")
    return True

def encode_standard(shaman:Shaman, message_blocks:list):
    shaman.parallel_load = 0 
    return process_message_blocks(shaman, message_blocks)

def encode_parallel(shaman:Shaman, message_blocks:list):
    shaman.parallel_load = 1
    return process_message_blocks(shaman, message_blocks)
    

