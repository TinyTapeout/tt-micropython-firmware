'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard
from ttboard.cocotb.dut import *
from ttboard.cocotb.clock import *
from ttboard.cocotb.triggers import *
import asyncio

class DUT(DUTWrapper):
    def __init__(self):
        super().__init__()
        self.tt = DemoBoard.get()
        # inputs
        self.display_single_select = self.new_slice_attribute(self.tt.ui_in, 7)
        self.display_single_enable = self.new_slice_attribute(self.tt.ui_in, 6)
        self.input_pulse = self.new_slice_attribute(self.tt.ui_in, 5)
        self.clk_config = self.new_slice_attribute(self.tt.ui_in, 4, 2)
        # outputs
        self.prox_select = self.new_slice_attribute(self.tt.uo_out, 7)
        self.segments = self.new_slice_attribute(self.tt.uo_out, 6, 0)
        
dut = DUT()
clk = Clock(dut.clk, 50, 'us')
clk.start()

async def yo(dut):
    dut.display_single_select.value = 1
    print("3 cycles")
    await ClockCycles(dut.clk, 3)
    dut.display_single_select.value = 0
    print("5 cycles")
    await ClockCycles(dut.clk, 5)
    
    print("100 us")
    await Timer(100, 'us')
    
    