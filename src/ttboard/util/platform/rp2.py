'''
Created on Nov 8, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import rp2
import machine

def pin_as_input(gpio_index:int, pull:int=None):
    if pull is not None:
        return machine.Pin(gpio_index, machine.Pin.IN, pull)
    else:
        return machine.Pin(gpio_index, machine.Pin.IN)
def dump_portset(p:str, v:int):
    print(f'ps {p}: {bin(v)}')
    return


@rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH)
def _pio_toggle_pin():
    wrap_target()
    set(pins, 1)
    mov(y, osr)
    label("delay1")
    jmp(y_dec, "delay1")  # Delay
    set(pins, 0)
    mov(y, osr)
    label("delay2")
    jmp(y_dec, "delay2")  # Delay
    wrap()
    
class PIOClock:
    def __init__(self, pin):
        self.freq = 0
        self.pin = pin
        self._current_pio = None 
        
    def start(self, freq_hz:int):
        self.freq = freq_hz 
        
        self.stop()
        if self.freq <= 0:
            return
            
        set_RP_system_clock(100_000_000)
        if self._current_pio is None:
            self._current_pio = rp2.StateMachine(
                0,
                _pio_toggle_pin,
                freq=2000,
                set_base=self.pin,
            )
        
        # Set the delay: 1000 cycles per hz minus 2 cycles for the set/mov instructions
        self._current_pio.put(int(500 * (2 / self.freq) - 2))
        self._current_pio.exec("pull()")
        self._current_pio.active(1)
        
    def stop(self):
        if self._current_pio is None or not self.freq:
            return 
        
        self._current_pio.active(0)
        self.freq = 0
        self._current_pio = None
        self.pin.init(machine.Pin.IN)

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

