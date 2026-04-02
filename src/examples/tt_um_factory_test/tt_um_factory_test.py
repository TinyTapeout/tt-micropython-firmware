'''
Created on Nov 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import gc
from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from microcotb.time.value import TimeValue
import microcotb as cocotb
from microcotb.utils import get_sim_time
gc.collect()


# get the detected @cocotb tests into a namespace
# so we can load multiple such modules
cocotb.set_runner_scope(__name__)

@cocotb.test()
async def test_loopback(dut):
    '''
        Not in reset, ui_in == 0: mirrors uio_in to outputs uo_out
    '''
    dut._log.info("Start loopback test")

    clock = Clock(dut.clk, 2, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1

    # ui_in[0] == 0: Copy bidirectional pins to outputs
    dut.uio_oe_pico.value = 0xff # all outputs from us
    dut.ui_in.value = 0b0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    for i in range(256):
        dut.uio_in.value = i
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == i, f"uio value unstable {dut.uio_out.value} != {i}"

    dut._log.info("test_loopback passed")


@cocotb.test(timeout_time=100, timeout_unit='us', expect_fail=True, skip=True)
@cocotb.parametrize(
    clk_period=[10,125], 
    timer_t=[101, 200])
async def test_timeout(dut, clk_period:int, timer_t:int):
    clock = Clock(dut.clk, clk_period, units="us")
    cocotb.start_soon(clock.start())
    # will timeout before the timer expires, hence expect_fail=True above
    await Timer(timer_t, 'us')
    
@cocotb.test(expect_fail=True, skip=True)
async def test_should_fail(dut):
    
    dut._log.info("Will fail with msg")

    assert dut.rst_n.value == 0, f"rst_n ({dut.rst_n.value}) == 0"






@cocotb.test()
async def test_counter(dut):
    '''
        Not in reset, ui_in[0] == 1, uo_out and uio_out should count up with clock
    
    '''
    dut._log.info("Start counter test")

    clock = Clock(dut.clk, 2, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("Testing counter")
    for i in range(256):
        assert dut.uo_out.value == dut.uio_out.value, f"uo_out != uio_out"
        assert int(dut.uo_out.value) == i, f"uio value not incremented correctly {dut.uio_out.value} != {i}"
        await ClockCycles(dut.clk, 1)
        
    
    dut._log.info("test_counter passed")
    
    
@cocotb.test()
async def test_project_reset(dut):
    
    dut._log.info("Start proj reset test")
    clock = Clock(dut.clk, 2, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    
    if dut.uo_out.value == 0:
        await ClockCycles(dut.clk, 10)
        assert dut.uo_out.value != 0, f'uo_out did not advance from 0'
    
    
    dut._log.info(f'Prior to reset uo_out count is at {int(dut.uo_out.value)}')
    # ok now our count is non-zero
    # do reset
    
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    # only check a few values, the point is we started back at zero
    for i in range(0xf):
        assert dut.uo_out.value == dut.uio_out.value, f"uo_out != uio_out"
        assert int(dut.uo_out.value) == i, f"uio value not incremented correctly {dut.uio_out.value} != {i}"
        await ClockCycles(dut.clk, 1)
        
    
    dut._log.info("reset test passed")
    
@cocotb.test(skip=True)
async def test_edge_triggers(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 2, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info(f"Testing counter, waiting on rising edge of bit 5 at {get_sim_time('us')}us")
    await RisingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.uo_out.value)}")
    
    dut._log.info(f"Now await falling edge")
    await FallingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.uo_out.value)}")
    
    dut._log.info("test_edge_triggers passed")



@cocotb.test(skip=True)
async def test_will_skip(dut):
    dut._log.info("This should not be output!")


@cocotb.test()
async def test_input_mirror(dut):
    clock = Clock(dut.clk, 2, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)

    # leave RESET low for this mode
    # fact test: assign uo_out  = ~rst_n ? ui_in : ui_in[0] ? cnt : uio_in;
    # uo_out: in reset, mirrors ui_in 
    # uo_out: not reset, either counts or mirrors uio_in (bidir in)
    dut._log.info("Testing input mirror ")
    in_value = 0
    for i in range(8):
        in_value |= (1<<i)
        dut.ui_in.value = in_value
        await ClockCycles(dut.clk, 2)
        
        assert dut.uo_out.value == in_value, f"uo_out != {in_value} ({dut.uo_out.value})"
        
    dut.ui_in.value = 0
    
        
    
    
def main():
    import ttboard.cocotb.dut
    
    class DUT(ttboard.cocotb.dut.DUT):
        def __init__(self):
            super().__init__('FactoryTest')
            self.tt = DemoBoard.get()
            # inputs
            self.add_bit_attribute('some_bit', self.tt.uo_out, 5)
    
    tt = DemoBoard.get()
    tt.shuttle.tt_um_factory_test.enable()
    
    if tt.mode != RPMode.ASIC_RP_CONTROL:
        print("Setting mode to ASIC_RP_CONTROL")
        tt.mode = RPMode.ASIC_RP_CONTROL
        
    tt.uio_oe_pico.value = 0 # all inputs
    
    
    TimeValue.ReBaseStringUnits = True # I like pretty strings
    
    
    runner = cocotb.get_runner(__name__)
    
    dut = DUT()
    dut._log.info(f"enabled factory test project.  Will test with {runner}")
    
    runner.test(dut)
    
    
    # show the user we're still running factory test
    tt.mode = RPMode.ASIC_RP_CONTROL
    tt.clock_project_PWM(15)
    tt.ui_in.value = 1
    
    return runner