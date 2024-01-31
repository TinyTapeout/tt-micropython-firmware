'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
IsRP2040 = False 
try:
    import machine 
    IsRP2040 = True 
except:
    pass