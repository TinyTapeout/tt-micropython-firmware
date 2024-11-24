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

import micropython
import gc
gc.threshold(10000)
import ttboard.util.time as time
from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard, Pins
from ttboard.boot.post import PowerOnSelfTest
import ttboard.util.colors as colors

# import examples.tt_um_psychogenic_neptuneproportional.tb as nc

gc.collect()

tt = None
def startup():
    
    # construct DemoBoard
    # either pass an appropriate RPMode, e.g. RPMode.ASIC_RP_CONTROL
    # or have "mode = ASIC_RP_CONTROL" in ini DEFAULT section
    ttdemoboard = DemoBoard()
    print("\n\n")
    print(f"The '{colors.color('tt', 'red')}' object is available.")
    print()
    print(f"Projects may be enabled with {colors.bold('tt.shuttle.PROJECT_NAME.enable()')}, e.g.")
    print("tt.shuttle.tt_um_urish_simon.enable()")
    print()
    print(f"The io ports are named as in Verilog, {colors.bold('tt.ui_in')}, {colors.bold('tt.uo_out')}...")
    print(f"and behave as with cocotb, e.g. {colors.bold('tt.uo_out.value = 0xAA')} or {colors.bold('print(tt.ui_in.value)')}")
    print(f"Bits may be accessed by index, e.g. {colors.bold('tt.uo_out[7]')} (note: that's the {colors.color('high bit!', 'red')}) to read or {colors.bold('tt.ui_in[5] = 1')} to write.")
    print(f"Direction of the bidir pins is set using {colors.bold('tt.uio_oe_pico')}, used in the same manner as the io ports themselves.")
    print("\n")
    print(f"{colors.color('TT SDK v' + ttdemoboard.version, 'cyan')}")
    print("\n\n")
    gc.collect()
    return ttdemoboard

def autoClockProject(freqHz:int):
    tt.clock_project_PWM(freqHz)
    
def stopClocking():
    tt.clock_project_stop()


# Detect the demoboard version
detection_result = '(best guess)'
detection_color = 'red'
if DemoboardDetect.probe():
    # detection was conclusive
    detection_result = ''
    detection_color = 'cyan'
detection_message = 'Detected ' + DemoboardDetect.PCB_str() + ' demoboard ' + detection_result
print(f"{colors.color(detection_message, detection_color)}")



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


gc.collect()
colors.color_start('magenta', False)
print("Mem info")
micropython.mem_info()
colors.color_end()


print(tt)
print()


# import examples.tt_um_factory_test.tt_um_factory_test as ft
# import examples.tt_um_psychogenic_neptuneproportional.tb as np 
# import examples.tt_um_rgbled_decoder.tt_um_rgbled_decoder as rgb

