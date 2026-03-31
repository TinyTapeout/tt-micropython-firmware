'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.util.platform import IsRP2
if IsRP2:
    from machine import Pin
else:
    # give us some fake Pin to play with
    from ttboard.pins.desktop_pin import Pin 
    