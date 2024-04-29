# Clock speed test, Michael Bell
# This test clocks the tt_um_test design at a high frequency
# and checks the counter has incremented by the correct amount
# 

import machine
import rp2
import time

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard

# PIO program to drive the clock.  Put a value n and it clocks n+1 times
# Reads 0 when done.
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32, autopush=True, push_thresh=32)
def clock_prog():
    out(x, 32)              .side(0)
    label("clock_loop")
    nop()                   .side(1)
    jmp(x_dec, "clock_loop").side(0)
    in_(null, 32)           .side(0)

# Select design, don't apply config so the PWM doesn't start.
tt = DemoBoard(apply_user_config=False)
tt.shuttle.tt_um_test.enable()

# Setup the PIO clock driver
sm = rp2.StateMachine(0, clock_prog, sideset_base=machine.Pin(0))
sm.active(1)

def run_test(freq, fast=False):
    # Multiply requested project clock frequency by 2 to get RP2040 clock
    freq *= 2
    
    if freq > 350_000_000:
        raise ValueError("Too high a frequency requested")
    
    if freq > 266_000_000:
        rp2.Flash().set_divisor(4)

    machine.freq(freq)

    try:
        # Run 1 clock
        print("Clock test... ", end ="")
        sm.put(1)
        sm.get()
        print(f" done. Value: {tt.output_byte}")

        errors = 0
        for _ in range(10):
            last = tt.output_byte
            
            # Run clock for approx 0.25 or 1 second, sending a multiple of 256 clocks plus 1.
            clocks = (freq // 2048) * 256 if fast else (freq // 512) * 256
            t = time.ticks_us()
            sm.put(clocks)
            sm.get()
            t = time.ticks_us() - t
            print(f"Clocked for {t}us: ", end = "")
                
            # Check the counter has incremented by 1.
            if tt.output_byte != (last + 1) & 0xFF:
                print("Error: ", end="")
                errors += 1
            print(tt.output_byte)
            
            if not fast:
                # Sleep so the 7-seg display can be read
                time.sleep(0.5)
    finally:
        if freq > 133_000_000:
            machine.freq(133_000_000)
            if freq > 266_000_000:
                rp2.Flash().set_divisor(2)
        
    return errors

if __name__ == "__main__":
    freq = 66_000_000
    while True:
        print(f"\nRun at {freq/1000000}MHz project clock\n")
        errors = run_test(freq, True)
        if errors > 0: break
        freq += 2_000_000