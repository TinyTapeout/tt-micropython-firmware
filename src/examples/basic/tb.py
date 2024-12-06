'''
Created on Dec 6, 2024

A basic set of samples to get going with 
cocotb tests on TT demoboards.

You need:
  * a few @cocotb.test() functions
  * a little bit of setup, and to call the runner

The @cocotb.test() functions are pretty regular.

The run() function is where more TT-specific stuff happens.
Check at the bottom.


@see: ttboard.cocotb.dut for the base class you 
can override for custom DUTs (has utility methods 
and nifty callbacks)

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from microcotb.utils import get_sim_time

# get the detected @cocotb tests into a namespace
# so we can load multiple such modules
cocotb.set_runner_scope(__name__)
    
from ttboard.demoboard import DemoBoard, RPMode
from ttboard.cocotb.dut import DUT 

# utility method, called by actual tests
async def do_reset(dut:DUT, num_cycles:int=10):
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1

    dut.uio_oe_pico.value = 0 # all inputs on RP2 side
    dut.ui_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, num_cycles)
    dut.rst_n.value = 1
    


# all tests are detected with @cocotb.test():
@cocotb.test()
async def test_timer(dut:DUT):
    
    # start up a clock, on the clk signal
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    await do_reset(dut) # always the same, so in its own async function
    
    await Timer(120, 'us')
    
    assert dut.rst_n.value == 1, "rst_n should be HIGH"
    



@cocotb.test()
async def test_clockcycles(dut:DUT):
    
    # start up a clock, on the clk signal
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    await do_reset(dut) # always the same, so in its own async function
    
    for i in range(256):
        dut.ui_in.value = i 
        await ClockCycles(dut.clk, 5)
        
    assert dut.ui_in.value == i, "ui_in should be our last i"
    
    
    dut._log.info(f"Total sim 'runtime': {get_sim_time('ms')}ms")
    
@cocotb.test()
async def test_multiclocks(dut:DUT):
    # start up a clock, on the clk signal
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # startup another clock, on our aliased bit "signal" (ui_in[0])
    clock = Clock(dut.input_pulse, 1, units="ms")
    cocotb.start_soon(clock.start())
    
    await do_reset(dut) # always the same, so in its own async function
    
    # wait for it to go up and down a few times
    for i in range(5):
        await RisingEdge(dut.input_pulse)
        dut._log.info(f"on {i} uio_in is: {int(dut.uio_in.value)}")
        await FallingEdge(dut.input_pulse)
        dut._log.info(f"off")
    
    keepWaiting = True 
    while keepWaiting:
        # we want to have just started counting up
        await RisingEdge(dut.input_pulse)
        
        # and we want to make sure the value is small
        # enough that we won't wrap around
        if dut.uo_out.value < 100:
            keepWaiting = False 
    
    # ok, we're good... capture the value of uo_out
    # right now
    out_val = dut.uo_out.value
    
    # and clock the project a few times to see it increment
    for i in range(10):
        assert dut.uo_out.value == (out_val + i), "out val increments"
        dut._log.info(f"uo_out is now {(out_val + i)}")
        await ClockCycles(dut.clk, 1)
        
    
    
def run():
    
    # get the demoboard singleton
    tt = DemoBoard.get()
    # We are testing a project, check it's on
    # this board
    if not tt.shuttle.has('tt_um_factory_test'):
        print("My project's not here!")
        return False
    
    # enable it
    tt.shuttle.tt_um_factory_test.enable()
    
    # we want to be able to control the I/O
    # set the mode
    if tt.mode != RPMode.ASIC_RP_CONTROL:
        print("Setting mode to ASIC_RP_CONTROL")
        tt.mode = RPMode.ASIC_RP_CONTROL
    
    # bidirs all inputs
    tt.uio_oe_pico.value = 0 # all inputs
    
    # get a runner
    runner = cocotb.get_runner(__name__)
    
    # here's our DUT... you could subclass this and 
    # do cool things, like rename signals or access 
    # bits and slices
    dut = DUT() # basic TT DUT, with dut._log, dut.ui_in, etc
    
    # say we want to treat a single bit, ui_in[0], as a signal,
    # to use as a named input, so we can do 
    # dut.input_pulse.value = 1, or use it as a clock... easy:
    dut.add_bit_attribute('input_pulse', tt.ui_in, 0)
    # now dut.input_pulse can be used like any other dut wire
    # there's also an add_slice_attribute to access chunks[4:2]
    # by name. 
    
    # run all the @cocotb.test()
    runner.test(dut)
