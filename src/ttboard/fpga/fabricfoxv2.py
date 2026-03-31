'''

FPGA breakout bitstream configurator.

Both PIO and SPI bit bang work to program Lattice FPGAs over the 
control and mux lines, as defined in the fabricfox FPGA breakout
project

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import rp2
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import utime
from ttboard.pins.gpio_map import GPIOMap
DoDummyClocks = True
def pin_indices():
    '''
        returns map of pin ID (GPIO #)
    '''
    return {
            'sck': GPIOMap.MNG03, # mng03,
            'mosi': GPIOMap.MNG00, # mng 00,
            'ss': GPIOMap.MNG02, # mng02,
            'reset': GPIOMap.ctrl_reset()
        }

def pin_objects():
    '''
        returns map of pin objects
    '''
    indices = pin_indices()
    return {
            'sck': GPIOMap.get_raw_pin(indices['sck'], Pin.OUT),
            'mosi': GPIOMap.get_raw_pin(indices['mosi'], Pin.OUT),
            'ss':  GPIOMap.get_raw_pin(indices['ss'], Pin.OUT),
            'reset':GPIOMap.get_raw_pin(indices['reset'], Pin.OUT),
        }
    


# Simple PIO to do writes over SPI

# PIO program for SPI write-only (8 bits, SCK on Pin 1, MOSI on Pin 2)
@rp2.asm_pio(
    sideset_init=(rp2.PIO.OUT_LOW),  # SCK idle low (CPOL=0)
    out_init=(rp2.PIO.OUT_LOW),      # MOSI idle low
    out_shiftdir=rp2.PIO.SHIFT_LEFT,  # 
    autopull=True,                   # Automatically pull 8 bits from FIFO
    pull_thresh=8,                   # Pull 8 bits at a time
    fifo_join=rp2.PIO.JOIN_TX        # Optimize for TX FIFO
)
def spi_write():
    wrap_target()
    set(x, 7) .side(0)               # Initialize loop counter to 7 (for 8 bits), SCK low
    label("bitloop")
    out(pins, 1) .side(0) [1]        # Output 1 bit to MOSI, SCK low, delay 1 cycle
    nop() .side(1) [1]               # SCK high, delay 1 cycle (data sampled here)
    jmp(x_dec, "bitloop") .side(0)   # Decrement X, loop if not zero, SCK low
    wrap()




def fpga_reset(ss, reset):
    # xtra
    reset.low()
    ss.low()
    utime.sleep_us(15000)  # Small delay to ensure reset
    reset.high()
    utime.sleep_us(15000)  # delay to ensure slave ready, minimum 1200us
    


def spi_transferPIO(filepath: str, freq: int = 1_000_000):
    """
    Transfer all bytes from a file over SPI using PIO.
    
    Args:
        filepath (str): Path to the file to transmit.
        freq (int): SPI clock frequency in Hz (default 1 MHz).
    """
    # Initialize pins
    pins = pin_objects()
    pins_idx = pin_indices()
    
    reset = pins['reset']
    ss = pins['ss']
    
    reset.high()


    # Calculate PIO frequency (2 cycles per bit, 8 bits per byte)
    pio_freq = freq * 2 * 8  # e.g., 1 MHz SPI -> 16 MHz PIO
    print(f"Configuring PIO with frequency: {pio_freq} Hz")

    # Configure PIO state machine
    sm = StateMachine(0, spi_write, freq=pio_freq, sideset_base=Pin(pins_idx['sck']), 
                      out_base=Pin(pins_idx['mosi']))
    
    # Clear FIFO and ensure state machine is reset
    sm.restart()
    sm.active(1)  # Activate state machine
    print("State machine activated")

    try:
        # Open file in binary read mode
        with open(filepath, 'rb') as f:
            # Set SS low to start SPI transaction
            fpga_reset(ss, reset)
            
            
            if DoDummyClocks:
                # release CS
                ss.high()
                utime.sleep_us(2000)  
                # send 8 dummy clocks
                sm.put(0)
                
                # wait until sent
                utime.sleep_us(20) 
                while sm.tx_fifo() != 0:
                    utime.sleep_us(2)
                    
                
                # actually select
                ss.low()
                utime.sleep_us(2000) 
            
            
            print("SS low, starting transmission")
            
            # Read file in chunks
            chunk_size = 128  # Reduced chunk size to avoid FIFO overflow
            byte_count = 0
            termination_bytes_to_send = 6
            while True:
                data = f.read(chunk_size)
                if not data:  # End of file
                    for _i in range(termination_bytes_to_send):
                        
                        while sm.tx_fifo() != 0:
                            utime.sleep_us(1)
                            
                        sm.put(0)
                    break
                        
                # print(f"Sending {len(data)} bytes")
                # Send each byte to PIO TX FIFO
                for byte in data:
                    # Wait if FIFO is full (tx_fifo() returns free slots, 0 means full)
                    
                    sm.put(byte & 0xff, 24) # LEFT shift of the 32 bits, must push up 24 to see byte
                    while sm.tx_fifo() != 0:
                        utime.sleep_us(1)  # Small delay to prevent tight loop
                    byte_count += 1
                    #if byte_count % 128 == 0:
                    #    print(f"Sent {byte_count} bytes, TX FIFO free slots: {sm.tx_fifo()}")

            # Wait for FIFO to drain
            while sm.tx_fifo():
                print(f"Waiting for FIFO to drain, free slots: {sm.tx_fifo()}")
                utime.sleep_us(10)

            print(f"Transmission complete, total bytes: {byte_count}")

    except OSError as e:
        print(f"Error accessing file: {e}")
    finally:
        # Deactivate state machine and set SS high
        sm.active(0)
        ss.high()
        sm.restart()
        sm = None
        # sck.init(mode=Pin.OUT, pull=None)
        # mosi.init(mode=Pin.OUT)

        
        print("State machine deactivated, SS high")
        
    




def spi_send(sck, mosi, val, delay_us=1):
    sck.low()
    for i in range(8):
        if val & (1 << (7 - i)):
            mosi.high()
        else:
            mosi.low()
        sck.high()
        utime.sleep_us(delay_us)
        sck.low()
        utime.sleep_us(delay_us)

        
def spi_transferBitBang(filepath: str, freq: int = 1_000_000):
    """
    Transfer all bytes from a file over SPI using PIO.
    
    Args:
        filepath (str): Path to the file to transmit.
        freq (int): SPI clock frequency in Hz (default 1 MHz).
    """
    # Initialize pins
    pins = pin_objects()
    
    reset = pins['reset']
    ss = pins['ss']
    sck = pins['sck']
    mosi = pins['mosi']
    reset.high()


    
    try:
        # Open file in binary read mode
        with open(filepath, 'rb') as f:
            # Set SS low to start SPI transaction
            fpga_reset(ss, reset)
            
            
            if DoDummyClocks:
                # release CS
                ss.high()
                utime.sleep_us(2000)  
                # send 8 dummy clocks
                spi_send(sck, mosi, 0)
                
                # wait until sent
                utime.sleep_us(20) 
                    
                
                # actually select
                ss.low()
                utime.sleep_us(2000) 
            
            
            print("SS low, starting transmission")

            # Read file in chunks
            chunk_size = 128  # Reduced chunk size to avoid FIFO overflow
            byte_count = 0
            termination_bytes_to_send = 6
            while True:
                data = f.read(chunk_size)
                if not data:  # End of file
                    for _i in range(termination_bytes_to_send):
                        
                        spi_send(sck, mosi, 0)
                    break
                        
                # print(f"Sending {len(data)} bytes")
                # Send each byte to PIO TX FIFO
                for byte in data:
                    # Wait if FIFO is full (tx_fifo() returns free slots, 0 means full)
                    spi_send(sck, mosi, byte)
                    byte_count += 1
            print(f"Transmission complete, total bytes: {byte_count}")

    except OSError as e:
        print(f"Error accessing file: {e}")
    finally:
        # Deactivate state machine and set SS high
        # sck.init(mode=Pin.OUT, pull=None)
        # mosi.init(mode=Pin.OUT)
        ss.high()
        
        
        print("State machine deactivated, SS high")
        
    return {
        'ss': ss,
        'sck': sck,
        'reset': reset,
        'mosi': mosi,
    }


# Example usage
if __name__ == "__main__":
    # Example: Transfer contents of 'data.bin' at 1 MHz
    spi_transferPIO("/bitstreams/data.bin", freq=1_000_000)