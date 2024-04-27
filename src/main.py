'''
Created on Jan 9, 2024

Code here, in main.py, runs on every power-up.

You can put anything you like in here, including any utility functions 
you might want to have access to when connecting to the REPL.  

If you want to use the SDK, all
you really need is something like
  
      tt = DemoBoard()

Then you can 
    # enable test project
    tt.shuttle.tt_um_test.enable()

and play with i/o as desired.

This code accesses the PowerOnSelfTest functions to:

    * check if the project clock button was held during powerup;
    * if so, run a basic test of the bidir pins (and implicitly of 
      the mux, output reads etc); and
    * and check if this was a first boot, to run special codes in
      such cases


@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import ttboard.util.time as time
from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard, Pins
from ttboard.boot.post import PowerOnSelfTest


tt = None
def startup():
    
    # construct DemoBoard
    # either pass an appropriate RPMode, e.g. RPMode.ASIC_RP_CONTROL
    # or have "mode = ASIC_RP_CONTROL" in ini DEFAULT section
    ttdemoboard = DemoBoard()

    
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
    
    return ttdemoboard

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
        
    

def test_neptune():
    tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
    for i in range(20, 340, 10):
        tt.in5.pwm(i)
        time.sleep_ms(1000)
        print(f'Input at {i}Hz, outputs are {hex(tt.output_byte)}')
    
    tt.in5.pwm(0) # disable pwm


# check if this is the first boot, if so, 
# handle that
if PowerOnSelfTest.first_boot():
    print('First boot!')
    PowerOnSelfTest.handle_first_boot()
    


# take a look at project user button state at startup
# all this "raw" pin access should happen before the DemoBoard object 
# is instantiated
run_post_tests = PowerOnSelfTest.dotest_buttons_held()
# or get a dict with PowerOnSelfTest.read_all_pins()


tt = startup()

# run a test if clock button held high 
# during startup
if run_post_tests:
    print('\n\nDoing startup test!')
    wait_count = 0
    while PowerOnSelfTest.dotest_buttons_held() and wait_count < 10:
        print("Waiting for button release...")
        time.sleep_ms(250)
        wait_count += 1
    
    post = PowerOnSelfTest(tt)
    if not post.test_bidirs():
        print('ERRORS encountered while running POST bidir test!')
    else:
        print('Startup test GOOD')
        tt.load_default_project()
    print('\n\n')

#tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
print(tt)
print()
