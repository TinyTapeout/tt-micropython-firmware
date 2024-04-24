'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
RP2040SystemClockDefaultHz = 125000000

IsRP2040 = False 
try:
    import machine 
    IsRP2040 = True 
except:
    pass




if IsRP2040:
    def isfile(file_path:str):
        try:
            f = open(file_path, 'r')
        except OSError:
            return False 
        f.close()
        return True 
    def get_RP_system_clock():
        return machine.freq()
    def set_RP_system_clock(freqHz:int):
        machine.freq(int(freqHz))
else:
    import os.path 
    isfile = os.path.isfile
    def get_RP_system_clock():
        return RP2040SystemClockDefaultHz
    def set_RP_system_clock(freqHz:int):
        print(f"Set machine clock to {freqHz}")