'''
Created on Nov 8, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import os.path 
isfile = os.path.isfile

class PIOClock:
    def __init__(self, pin):
        self.freq = 0
        self.pin = pin
        
    def start(self, freq_hz:int):
        self.freq = freq_hz 
        print(f"(mock) PIO clock @ {freq_hz}Hz")
        
    def stop(self):
        self.freq = 0
        print("PIO clock stop")
def pin_as_input(gpio_index:int, pull:int=None):
    from ttboard.pins.upython import Pin
    return Pin(gpio_index, Pin.IN, pull=pull)
def get_RP_system_clock():
    return RP2040SystemClockDefaultHz
def set_RP_system_clock(freqHz:int):
    global RP2040SystemClockDefaultHz
    print(f"Set machine clock to {freqHz}")
    RP2040SystemClockDefaultHz = freqHz
    
_inbyte = 0
def write_ui_in_byte(val):
    global _inbyte 
    print(f'Sim write_input_byte {val}')
    _inbyte = val

def read_ui_in_byte():
    print('Sim read_output_byte')
    return _inbyte


_uio_byte = 0
def write_uio_byte(val):
    global _uio_byte
    print(f'Sim write_bidir_byte {val}')
    _uio_byte = val

    
    
def read_uio_byte():
    print('Sim read_output_byte')
    return _uio_byte

_outbyte = 0
def write_uo_out_byte(val):
    global _outbyte 
    print(f'Sim write_output_byte {val}')
    _outbyte = val

def read_uo_out_byte():
    global _outbyte 
    v = _outbyte 
    #_outbyte += 1
    print('Sim read_output_byte')
    return v

_uio_oe_pico = 0
def read_uio_outputenable():
    print('Sim read_bidir_outputenable')
    return _uio_oe_pico

def write_uio_outputenable(val):
    global _uio_oe_pico
    print(f'Sim write_bidir_outputenable {val}')
    _uio_oe_pico = val

_clk_pin = 0
def read_clock():
    return _clk_pin
   
def write_clock(val):
    global _clk_pin
    _clk_pin = val
        
    