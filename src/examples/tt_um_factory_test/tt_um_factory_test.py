'''
Created on Nov 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import math
import gc
from ttboard.demoboard import DemoBoard
gc.collect()
print(f'mf tb: {gc.mem_free()}')
from ttboard.cocotb.clock import Clock
print(f'mf tb: {gc.mem_free()}')
from ttboard.cocotb.triggers import Timer, ClockCycles # RisingEdge, FallingEdge, Timer, ClockCycles

print(f'mf tb: {gc.mem_free()}')
import ttboard.cocotb as cocotb

@cocotb.test()
async def test_loopback(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
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

@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("Testing counter")
    for i in range(256):
        assert dut.uo_out.value == dut.uio_out.value, f"uio value unstable {dut.uio_out.value}?"
        assert int(dut.uo_out.value) == i, f"uio value not incremented correctly {dut.uio_out.value} != {i}"
        await ClockCycles(dut.clk, 1)
        
    
    dut._log.info("test_counter passed")
        
        
def main():
    # import examples.tt_um_factory_test.tt_um_factory_test as ft
    from ttboard.cocotb.dut import DUT


    tt = DemoBoard.get()
    tt.shuttle.tt_um_factory_test.enable()
    tt.clock_project_stop()
    tt.uio_oe_pico.value = 0 # all inputs
    Clock.clear_all()
    
    
    dut = DUT()
    dut._log.info("enabled factory test project, running")
    runner = cocotb.get_runner()
    runner.test(dut)