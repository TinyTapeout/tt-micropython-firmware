'''
Created on Jan 9, 2024

Michael Bell's tests, migrated to ttboard OO SDK.

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import time
from ttboard.demoboard import DemoBoard, RPMode

tt = DemoBoard(RPMode.ASIC_ON_BOARD)

def test_design_tnt_counter():
    tt.shuttle.tt_um_test.enable()
    
    #reset
    tt.nproject_rst(0)

    # enable the internal counter of test design
    tt.in0(1)
    time.sleep_ms(100)

    # take out of reset
    tt.nproject_rst(1)

    # clock it forever
    while True:
        tt.project_clk(0) # shortcut to tt.project_clk(0)
        time.sleep_ms(100)
        tt.project_clk(1)
        time.sleep_ms(100)
        print(hex(tt.output_byte & 0x0f)) # could do ...out0(), out1() etc

def test_design_loopback():
    # select design
    tt.shuttle.tt_um_loopback.enable()

    # toggle user in 0 forever
    p = tt.pins # save some typing
    while True:
        p.in0(0)
        time.sleep_ms(500)
        print(p.out0(), p.out1(), p.out2(), p.out3())
        p.in0(1)
        time.sleep_ms(500)
        print(p.out0(), p.out1(), p.out2(), p.out3())

def test_design_vga():
    # select design
    tt.shuttle.tt_um_loopback.enable()
    
    p = tt.pins # save some typing
    # reset
    p.nproject_rst(0)
    time.sleep_ms(1)
    p.nproject_rst(1)

    # toggle clock
    while True:
        p.project_clk.value(0)
        p.project_clk.value(1)
        print(p.out0(), p.out1(), p.out2(), p.out3())

def test_design_powergate_add():
    # select design
    tt.shuttle.tt_um_power_test.enable()

    # toggle user in 0 forever
    while True:
        tt.in0(0)
        time.sleep_ms(100)
        print(tt.out0(), tt.out1(), tt.out2(), tt.out3())
        tt.in0(1)
        time.sleep_ms(100)
        print(tt.out0(), tt.out1(), tt.out2(), tt.out3())

def test_design_powergate_ringosc():
    # select design
    tt.shuttle.tt_um_ringosc_cnt_pfet.enable()

    # toggle user in 0 forever
    while True:
        time.sleep_ms(100)
        print(tt.out0(), tt.out1(), tt.out2(), tt.out3())

if __name__ == '__main__':
    test_design_tnt_counter()