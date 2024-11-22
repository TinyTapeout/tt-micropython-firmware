# Clock speed test, Michael Bell
# This test clocks the tt_um_test design at a high frequency
# and checks the counter has incremented by the correct amount

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
    irq(4)                  .side(1)
    jmp(x_dec, "clock_loop").side(0)
    irq(clear, 4)           .side(0)
    in_(null, 32)           .side(0)

@rp2.asm_pio(autopush=True, push_thresh=32, in_shiftdir=rp2.PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_RX)
def read_prog():
    in_(pins, 2)

# Select design, don't apply config so the PWM doesn't start.
tt = DemoBoard(apply_user_config=False)
tt.shuttle.tt_um_test.enable()

# Setup the PIO clock driver
sm = rp2.StateMachine(0, clock_prog, sideset_base=machine.Pin(0))
sm.exec("irq(clear, 4)")
sm.active(1)

# Setup the PIO counter read
sm_rx = rp2.StateMachine(1, read_prog, in_base=machine.Pin(3))

# Setup read DMA
dst_data = bytearray(8192)
d = rp2.DMA()

# Read using the SM1 RX DREQ
c = d.pack_ctrl(inc_read=False, treq_sel=5)

# Read from the SM1 RX FIFO
d.config(
    read=0x5020_0024,
    write=dst_data,
    count=len(dst_data)//4,
    ctrl=c,
    trigger=False
)

def start_rx():
    # Reset the SM
    sm_rx.active(0)
    while sm_rx.rx_fifo() > 0: sm_rx.get()
    sm_rx.restart()
    
    # Wait until out0 changes from its current value
    if machine.Pin(3).value():
        sm_rx.exec("wait(0, pin, 0)")
    else:
        sm_rx.exec("wait(1, pin, 0)")
        
    # Re-activate SM, it will block until the wait command completes
    sm_rx.active(1)


# Frequency for the RP2040, the design is clocked at half this frequency
def run_test(freq):
    # Multiply requested project clock frequency by 2 to get RP2040 clock
    freq *= 2
    
    if freq > 266_000_000:
        raise ValueError("Too high a frequency requested")
    
    machine.freq(freq)

    try:
        # Run 64 clocks
        print("Clock test... ", end ="")
        start_rx()
        sm.put(63)
        sm.get()
        print(f" done. Value now: {tt.uo_out.value}")

        # Print the values read back for inspection
        for j in range(4):
            readings = sm_rx.get()
            for i in range(16):
                val = (readings >> (i*2)) & 0x3
                print(val, end = " ")
        print()
        sm_rx.active(0)
        
        total_errors = 0

        for _ in range(10):
            last = tt.uo_out.value
            
            # Setup the read SM and DMA transfer into the verification buffer
            start_rx()
            d.config(write=dst_data, trigger=True)
            
            # Run clock for enough time to fill the buffer
            t = time.ticks_us()
            sm.put(1024*17)
            sm.get()
            t = time.ticks_us() - t
            print(f"Clocked for {t}us: ", end = "")
            
            # Print the first 16 values in the DMA'd buffer
            for j in range(0,4):
                readings = dst_data[j]
                for i in range(4):
                    val = (readings >> (i*2)) & 0x3
                    print(val, end = " ")
                    
            # Check the counter has incremented by 1, as we sent a
            # multiple of 256 clocks plus one more
            if tt.uo_out.value != (last + 1) & 0xFF:
                print("Error: ", end="")
            print(tt.uo_out.value)
            
            # Check the read data from the counter continuously increases
            def verify(count, expected_val, retry):
                errors = 0
                
                for j in range(2,len(dst_data)):
                    readings = dst_data[j]
                    for i in range(4):
                        val = (readings >> (i*2)) & 0x3
                        if count == 1 and val != expected_val:
                            if retry:
                                return -1
                            else:
                                print(f"Error at {j}:{i} {val} should be {expected_val}")
                                errors += 1
                        count += 1
                        if count == 2:
                            expected_val = (expected_val + 1) & 0x3
                            count = 0
                    if errors > 10: break
                return errors
                    
            expected_val = dst_data[2] & 0x3
            errors = verify(1, expected_val, True)
            if errors == -1:
                expected_val = (dst_data[2] >> 2) & 0x3
                errors = verify(0, expected_val, False)
            
            total_errors += errors
            if errors > 10:
                return total_errors

    finally:
        # Remove overclock
        if freq > 133_000_000:
            machine.freq(133_000_000)
            
    return total_errors

if __name__ == "__main__":
    freq = 50_000_000
    while True:
        print(f"\nRun at {freq/1000000}MHz project clock\n")
        errors = run_test(freq)
        if errors > 10: break
        freq += 1_000_000
