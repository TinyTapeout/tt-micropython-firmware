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
    tt.shuttle.tt_um_factory_test.enable()

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
print("BOOT: Tiny Tapeout SDK")
import gc

# stash the current value for garbage 
# collection threshold (is -1/when full, by default)
GCThreshold = gc.threshold()
# start very aggressive, to keep thing defragged
# as we read in ini and JSON files, etc
gc.threshold(80000)

import ttboard.log as logging
# logging.ticksStart() # start-up tick delta counter

logging.basicConfig(level=logging.DEBUG, filename='boot.log')


import micropython
from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.demoboard import DemoBoard
# from ttboard.boot.post import PowerOnSelfTest
import ttboard.util.colors as colors

# logging.dumpTicksMsDelta('import')

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


tt = startup()


logging.basicConfig(filename=None)
gc.collect()
colors.color_start('magenta', False)
print("Mem info")
micropython.mem_info()
colors.color_end()


print(tt)
print()

logging.dumpTicksMsDelta('boot done')
print(f"tt.sdk_version={tt.version}")
# end by being so aggressive on collection
gc.threshold(GCThreshold)

# to run tests easily import a module of interest, as below, and then 
# run() it


def run_testbench_basic():
    import microcotb
    import examples.basic as test 
    test.run()
    return test 
    
def run_testbench_factorytest():
    import microcotb
    import examples.tt_um_factory_test as test 
    test.run()
    return test 

def run_testbench_neptune():
    import microcotb
    import examples.tt_um_psychogenic_neptuneproportional as test 
    test.run()
    return test 

# run_testbench_factorytest()
# or
# import examples.tt_um_psychogenic_shaman as test
# import examples.tt_um_rejunity_sn76489 as test
# import examples.tt_um_factory_test as test
# import examples.tt_um_psychogenic_neptuneproportional as test 
# dut = test.tt_um_psychogenic_neptuneproportional.DUT()
# import examples.tt_um_rgbled_decoder as test
# test.run()
# from examples.basic import run

