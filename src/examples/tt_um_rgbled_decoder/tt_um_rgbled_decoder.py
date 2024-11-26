'''
Created on Nov 23, 2024

Adaptation of Andreas Scharnreitner's testbench to run on 
TT demoboard with SDK
@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

# Copyright 2023 Andreas Scharnreitner
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles
from microcotb.utils import get_sim_time

def time_delta_not(cond:str):
    return f'sim time delta not {cond}'

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")
    clock = Clock(dut.tbspi.sclk, 10, units="us")
    cocotb.start_soon(clock.start())

    #setup
    dut.tbspi.nsel.value = 1
    dut.tbspi.mosi.value = 0

    # reset
    dut._log.info("Reset SPI")
    dut.tbspi.nreset.value = 0
    await ClockCycles(dut.tbspi.sclk, 5)
    dut.tbspi.nreset.value = 1
    await ClockCycles(dut.tbspi.sclk, 5)
    
    #after reset the data should be 0
    assert dut.tbspi.data.value == 0
    #without nsel the data_rdy should be 1 (ready)
    assert dut.tbspi.data_rdy.value == 1, "not ready"

    await ClockCycles(dut.tbspi.sclk, 10)
    
    await FallingEdge(dut.tbspi.sclk)
    dut.tbspi.nsel.value = 0
    await FallingEdge(dut.tbspi.data_rdy)
    dut._log.info("SPI: Writing 0xAA")
    for i in range(8):
        dut.tbspi.mosi.value = i%2
        await ClockCycles(dut.tbspi.sclk, 1)

    dut.tbspi.nsel.value = 1
    await RisingEdge(dut.tbspi.data_rdy)
    
    assert dut.tbspi.data.value == 0xAA

    await ClockCycles(dut.tbspi.sclk, 10)
    
    await FallingEdge(dut.tbspi.sclk)
    dut.tbspi.nsel.value = 0
    await FallingEdge(dut.tbspi.data_rdy)
    dut._log.info("SPI: Writing 0xB3")
    for i in range(8):
        dut.tbspi.mosi.value = (0xB3 >> i)&1
        await ClockCycles(dut.tbspi.sclk, 1)

    dut.tbspi.nsel.value = 1
    await RisingEdge(dut.tbspi.data_rdy)
    
    assert dut.tbspi.data.value == 0xB3

    await ClockCycles(dut.tbspi.sclk, 10)

@cocotb.test()
async def test_rgbled(dut):
    dut._log.info("Start RGBLED test")
    clock = Clock(dut.tbrgbled.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    #setup
    dut.tbrgbled.data_rdy.value = 0

    dut._log.info("Reset RGBLED")
    dut.tbrgbled.nreset.value = 0
    await ClockCycles(dut.tbrgbled.clk, 5)
    dut.tbrgbled.nreset.value = 1
    await ClockCycles(dut.tbrgbled.clk, 5)

    dut._log.info("RGBLED Output Test")
    dut.tbrgbled.data.value = 0x112233445566AA00FF
    dut.tbrgbled.data_rdy.value = 1

    await RisingEdge(dut.tbrgbled.data_rdy)

    tim_start = get_sim_time('us')

    await RisingEdge(dut.tbrgbled.led)
    
    assert (get_sim_time('us') - tim_start) > 50, time_delta_not("> 50") 
    tim_start = get_sim_time('ns')

    await FallingEdge(dut.tbrgbled.led)

    tim_mid = get_sim_time('ns')
    assert (tim_mid - tim_start) > 650, time_delta_not("> 650")
    assert (tim_mid - tim_start) < 950, time_delta_not("< 950")

    await RisingEdge(dut.tbrgbled.led)
    
    assert (get_sim_time('ns') - tim_mid) > 300, time_delta_not("> 300")
    assert (get_sim_time('ns') - tim_mid) < 600, time_delta_not("< 600")
    
    assert (get_sim_time('ns') - tim_start) > 650, time_delta_not("> 650")
    assert (get_sim_time('ns') - tim_start) < 1850, time_delta_not("< 1850")

    for i in range(8):
        await RisingEdge(dut.tbrgbled.led)
    
    tim_start = get_sim_time('ns')

    await FallingEdge(dut.tbrgbled.led)

    tim_mid = get_sim_time('ns')
    assert (tim_mid - tim_start) > 250, time_delta_not("> 250")
    assert (tim_mid - tim_start) < 550, time_delta_not("< 550")

    await RisingEdge(dut.tbrgbled.led)
    
    assert (get_sim_time('ns') - tim_mid) > 700, time_delta_not("> 700")
    assert (get_sim_time('ns') - tim_mid) < 1000, time_delta_not("< 1000")
    
    assert (get_sim_time('ns') - tim_start) > 650, time_delta_not("> 650")
    assert (get_sim_time('ns') - tim_start) < 1850, time_delta_not("< 1850")
    
    # problem here: waiting on internal signal dut.tbrgbled.rgbled_dut.do_res
    # await RisingEdge(dut.tbrgbled.rgbled_dut.do_res)
    #
    # tim_start = get_sim_time('us')
    #
    # await ClockCycles(dut.tbrgbled.clk, 10)
    # await RisingEdge(dut.tbrgbled.led)
    #
    # assert (get_sim_time('us') - tim_start) > 50
    #
    # await ClockCycles(dut.tbrgbled.clk, 10)
    
    # simplified version
    tim_start = get_sim_time('us')
    await ClockCycles(dut.tbrgbled.clk, 10)
    await RisingEdge(dut.tbrgbled.led)
    assert (get_sim_time('us') - tim_start) > 50, time_delta_not("> 50")
    
    await ClockCycles(dut.tbrgbled.clk, 10)
    
    



from ttboard.demoboard import DemoBoard
import ttboard.cocotb.dut as basedut
from microcotb.dut import Wire

class RGBLED(basedut.DUT):
    def __init__(self, data:Wire, data_rdy:Wire):
        super().__init__('RGBLED')
        self.data = data 
        self.data_rdy = data_rdy
        self.led = self.new_slice_attribute(self.tt.uo_out, 0)
        self.nreset = self.rst_n

class TBSPI(basedut.DUT):
    
    def __init__(self, data:Wire, data_rdy:Wire):
        super().__init__('SPI')
        self.data = data 
        self.data_rdy = data_rdy
        self.nreset = self.rst_n
        self.mosi = self.new_bit_attribute(self.tt.ui_in, 0)
        self.sclk = self.new_bit_attribute(self.tt.ui_in, 1)
        self.nsel = self.new_bit_attribute(self.tt.ui_in, 2)
        
class DUT(basedut.DUT):
    def __init__(self):
        super().__init__('RGBDUT')
        self.data = Wire()
        self.data_rdy = self.new_bit_attribute(self.tt.ui_in, 2)
        self.tbrgbled = RGBLED(self.data, self.data_rdy)
        self.tbspi = TBSPI(self.data, self.data_rdy)
        

def load_project(tt:DemoBoard):
    
    if not tt.shuttle.has('tt_um_rgbled_decoder'):
        print("No tt_um_rgbled_decoder available in shuttle?")
        return False
    
    tt.shuttle.tt_um_rgbled_decoder.enable()
    return True

def main():
    tt = DemoBoard.get()
    
    if not load_project(tt):
        return
    
    tt.uio_oe_pico.value = 0 # all inputs
    
    
    dut = DUT()
    dut._log.info("enabled rgbled project, running")
    runner = cocotb.get_runner()
    runner.test(dut)
        
            
