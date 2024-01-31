'''
Created on Jan 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.util.platform import IsRP2040

from time import *
if not IsRP2040:
    def sleep_ms(v):
        sleep(v/1000)

    def sleep_us(v):
        sleep(v/1000000)
