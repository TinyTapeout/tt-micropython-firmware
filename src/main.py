'''
Created on Jan 9, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import ttboard.util.time as time
from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard
from ttboard.pins.gpio_map import GPIOMap

# Pin import to provide access in REPL
# to things like tt.uio3.mode = Pin.OUT
from ttboard.pins.upython import Pin

tt = None
startup_with_clock_high = False
def startup():
    global tt, startup_with_clock_high
    
    # take a look at project clock pin on startup
    # make note if it was HIGH
    clkPin = Pin(GPIOMap.RP_PROJCLK, Pin.IN)
    startup_with_clock_high = clkPin()
    
    # construct DemoBoard
    # either pass an appropriate RPMode, e.g. RPMode.ASIC_ON_BOARD
    # or have "mode = ASIC_ON_BOARD" in ini DEFAULT section
    tt = DemoBoard()

    
    print("\n\n")
    print("The 'tt' object is available.")
    print()
    print("Projects may be enabled with tt.shuttle.PROJECT_NAME.enable(), e.g.")
    print("tt.shuttle.tt_um_urish_simon.enable()")
    print()
    print("Pins may be accessed by name, e.g. tt.out3() to read or tt.in5(1) to write.")
    print("Config of pins may be done using mode attribute, e.g. ")
    print("tt.uio3.mode = Pins.OUT")
    print("\n\n")

def autoClockProject(freqHz:int):
    tt.clock_project_PWM(freqHz)
    
def stopClocking():
    tt.clock_project_stop()

def test_design_tnt_counter():
    # select the project from the shuttle
    tt.shuttle.tt_um_test.enable()
    
    #reset
    tt.reset_project(True)

    # enable the internal counter of test design
    tt.in0(1)

    # take out of reset
    tt.reset_project(False)
    
    print('Running tt_um_test, printing output...Ctrl-C to stop')
    time.sleep_ms(300)
    
    tt.clock_project_PWM(10)
    try:
        while True:
            print(hex(tt.output_byte & 0x0f)) # could do ...out0(), out1() etc
            time.sleep_ms(100)
    except KeyboardInterrupt:
        tt.clock_project_stop()
        
def test_bidirs(sleepTimeMillis:int=1):
    # select the project from the shuttle
    tt.shuttle.tt_um_test.enable()
    curMode = tt.mode 
    tt.mode = RPMode.ASIC_ON_BOARD # make sure we're controlling everything
    
    tt.in0(0) # want this low
    tt.clock_project_PWM(1e3) # clock it real good
    
    for bp in tt.bidirs:
        bp.mode = Pin.OUT
        bp(0) # start low
    
    errCount = 0
    for i in range(0xff):
        tt.bidir_byte = i 
        time.sleep_ms(sleepTimeMillis)
        outbyte = tt.output_byte
        if outbyte !=  i:
            print(f'MISMATCH between bidir val {i} and output {outbyte}')
            errCount += 1
    
    if errCount:
        print(f'{errCount} ERRORS encountered??!')
    else:
        print('Bi-directional pins acting pretty nicely as inputs!')
        
    # reset everything
    tt.mode = curMode
    
    return errCount
            
    

def test_neptune():
    tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
    for i in range(20, 340, 10):
        tt.in5.pwm(i)
        time.sleep_ms(1000)
        print(f'Input at {i}Hz, outputs are {hex(tt.output_byte)}')
    
    tt.in5.pwm(0) # disable pwm

startup()

# run a test if clock button held high 
# during startup
if startup_with_clock_high:
    print('\n\nDoing startup test!')
    if test_bidirs():
        print('ERRORS encountered!')
    else:
        print('Startup test GOOD')
    print('\n\n')

#tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
print(tt)
