'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import Timer, ClockCycles # RisingEdge, FallingEdge, Timer, ClockCycles


# get the detected @cocotb tests into a namespace
# so we can load multiple such modules
cocotb.set_runner_scope(__name__)

from ttboard.demoboard import DemoBoard, RPMode

displayNotes = {
            'NA':     0b00000010, # -
            'A':      0b11101110, # A
            'B':      0b00111110, # b
            'C':      0b10011100, # C
            'D':      0b01111010, # d
            'E':      0b10011110, # E
            'F':      0b10001110, # F
            'G':      0b11110110, # g
            }
            
displayProx = {
            'lowfar':       0b00111000,
            'lowclose':     0b00101010,
            'exact':        0b00000001,
            'hiclose':      0b01000110,
            'hifar':        0b11000100

}

SegmentMask = 0xFF
ProxSegMask = 0xFE



@cocotb.test()
async def note_a_exact(dut):
    dispValues = await note_a(dut, delta=0, msg="A exact")
    
    target_value =  (displayProx['exact'] & ProxSegMask)
    assert dispValues[0] == target_value, f"exact fail {dispValues[0]} != {target_value}"
    dut._log.info("Note A full pass")
    
    
    
    
@cocotb.test(skip=False)
async def note_e_highfar(dut):
    dispValues = await note_e(dut, eFreq=330, delta=12, msg="little E high/far")
    target_value =  (displayProx['hifar'] & ProxSegMask)
    assert dispValues[0] == target_value, f"high/far fail {dispValues[0]} != {target_value}"
    dut._log.info("Note E full pass")


@cocotb.test(skip=False)
async def note_g_highclose(dut):
    dispValues = await note_g(dut, delta=3, msg="High/close")
    target_value =  (displayProx['hiclose'] & ProxSegMask)
    assert dispValues[0] == target_value, f"High/close fail {dispValues[0]} != {target_value}"
    dut._log.info("Note G full pass")
    


async def reset(dut):
    dut._log.info(f"reset(dut)")
    dut.display_single_enable.value = 0
    dut.display_single_select.value = 0
    dut.input_pulse.value = 0
    dut.rst_n.value = 0
    dut.clk_config.value = 1 # 2khz clock
    dut._log.debug("hold in reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    dut._log.info("reset done")
   
    
async def startup(dut):
    dut._log.info("starting clock")
    clock = Clock(dut.clk, 500, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)
            
async def getDisplayValues(dut):
    displayedValues = [None, None]
    attemptCount = 0
    while None in displayedValues or attemptCount < 3:
        displayedValues[int(dut.prox_select.value)] = int(dut.segments.value) << 1
        
        await ClockCycles(dut.clk, 1)
        
        attemptCount += 1
        if attemptCount > 100:
            dut._log.error(f"NEVER HAVE {displayedValues}")
            return displayedValues
            
    # dut._log.info(f'Display Segments: {displayedValues} ( [ {bin(displayedValues[0])} , {bin(displayedValues[1])}])')
    return displayedValues
    
async def inputPulsesFor(dut, tunerInputFreqHz:int, inputTimeSecs=0.51):
    
    pulseClock = Clock(dut.input_pulse, 1000.0*(1.0/tunerInputFreqHz), units='ms')
    cocotb.start_soon(pulseClock.start())
    await Timer(inputTimeSecs, 'sec')
    dispV = await getDisplayValues(dut)
    
    return dispV
    


async def setup_tuner(dut):
    dut._log.info("start")
    await startup(dut)
    

async def note_toggle(dut, freq, delta=0, msg="", toggleTime=0.58):
    dut._log.info(msg)
    await startup(dut)
    dispValues = await inputPulsesFor(dut, freq + delta, toggleTime)  
    return dispValues
    
    

async def note_e(dut, eFreq=330, delta=0, msg=""):
    dut._log.info(f"E @ {eFreq} delta {delta}")
    dispValues = await note_toggle(dut, freq=eFreq, delta=delta, msg=msg);
    note_target = (displayNotes['E'] & SegmentMask)
    assert dispValues[1] == note_target, f"Note E FAIL: {dispValues[1]} != {note_target}"
    dut._log.info(f"Note E @ {eFreq} pass ({bin(dispValues[1])})")
    return dispValues




async def note_g(dut, delta=0, msg=""):
    gFreq = 196
    
    dut._log.info(f"G delta {delta}")
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    
    note_target = (displayNotes['G'] & SegmentMask)
    assert dispValues[1] == note_target, f"Note G FAIL: {dispValues[1]} != {note_target}"
    dut._log.info(f"Note G: PASS ({bin(dispValues[1])})")
    return dispValues


async def note_a(dut, delta=0, msg=""):
    aFreq = 110
    
    dut._log.info(f"A delta {delta}")
    dispValues = await note_toggle(dut, freq=aFreq, delta=delta, msg=msg);
    
    note_target = (displayNotes['A'] & SegmentMask)
    assert dispValues[1] == note_target, f"Note A FAIL: {dispValues[1]} != {note_target}"
    dut._log.info(f"Note A pass ({bin(dispValues[1])})")
    return dispValues

    


### DUT class override, so I can get nicely-named aliases
### that match my verilog testbench
import ttboard.cocotb.dut
class DUT(ttboard.cocotb.dut.DUT):
    def __init__(self):
        super().__init__('Neptune')
        
        # inputs
        self.add_bit_attribute('display_single_select',
                                    self.tt.ui_in, 7)
        self.add_bit_attribute('display_single_enable',
                                    self.tt.ui_in, 6)
        self.add_bit_attribute('input_pulse', 
                                    self.tt.ui_in, 5)
        # tt.ui_in[4:2]
        self.add_slice_attribute('clk_config', 
                                    self.tt.ui_in, 4, 2) 
        # outputs
        self.add_bit_attribute('prox_select', self.tt.uo_out, 7)
        # tt.uo_out[6:0]
        self.add_slice_attribute('segments', self.tt.uo_out, 6, 0) 


def main():
    from microcotb.time.value import TimeValue
    
    tt = DemoBoard.get()
    tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
    
    if tt.mode != RPMode.ASIC_RP_CONTROL:
        print("Setting mode to ASIC_RP_CONTROL")
        tt.mode = RPMode.ASIC_RP_CONTROL
    
    # I'll spend the cycles to get pretty timestamps
    TimeValue.ReBaseStringUnits = True
    
    # create runner and DUT, and get tests going
    runner = cocotb.get_runner(__name__)
    dut = DUT()
    dut._log.info(f"enabled neptune project, will test with {runner}")
    runner.test(dut)


if __name__ == '__main__':
    main()
