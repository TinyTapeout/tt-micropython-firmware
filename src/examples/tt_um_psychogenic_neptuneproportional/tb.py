'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import math
from ttboard.demoboard import DemoBoard
from ttboard.cocotb.clock import Clock
from ttboard.cocotb.triggers import Timer, ClockCycles # RisingEdge, FallingEdge, Timer, ClockCycles
import ttboard.cocotb as cocotb

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

    
        
# os.environ['COCOTB_RESOLVE_X'] = 'RANDOM'
async def reset(dut):
    dut._log.info(f"reset(dut)")
    dut.display_single_enable.value = 0
    dut.display_single_select.value = 0
    dut.rst_n.value = 1
    dut.clk_config.value = 1 # 2khz clock
    dut._log.info("hold in reset")
    await ClockCycles(dut.clk, 5)
    dut._log.info("reset done")
    dut.input_pulse.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.input_pulse.value = 0
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
   
    
async def startup(dut):
    dut._log.info("starting clock")
    clock = Clock(dut.clk, 500, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)
    dut.input_pulse.value = 0
            
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
    
async def inputPulsesFor(dut, tunerInputFreqHz:int, inputTimeSecs=0.51, sysClkHz=1e3):
    numPulses = tunerInputFreqHz * inputTimeSecs 
    pulsePeriod = 1/tunerInputFreqHz
    pulseHalfCycleUs = round(1e6*pulsePeriod/2.0)
        
    for _pidx in range(math.ceil(numPulses)):
        dut.input_pulse.value = 1
        await Timer(pulseHalfCycleUs, units='us')
        dut.input_pulse.value = 0
        await Timer(pulseHalfCycleUs, units='us')
        
    dispV = await getDisplayValues(dut)
    
    return dispV
    


async def setup_tuner(dut):
    dut._log.info("start")
    await startup(dut)
    

async def note_toggle(dut, freq, delta=0, msg="", toggleTime=4):
    dut._log.info(msg)
    await startup(dut)
    dispValues = await inputPulsesFor(dut, freq + delta, toggleTime)  
    return dispValues
    
    

async def note_e(dut, eFreq=330, delta=0, msg=""):
    dut._log.info(f"E @ {eFreq} delta {delta}")
    dispValues = await note_toggle(dut, freq=eFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['E'] & SegmentMask), "Note E FAIL"
    dut._log.info(f"Note E @ {eFreq} pass")
    return dispValues


    
@cocotb.test()
async def note_e_highfar(dut):
    dispValues = await note_e(dut, eFreq=330, delta=20, msg="little E high/far")
    assert dispValues[0] == (displayProx['hifar'] & ProxSegMask) , "High/far Fail"
    dut._log.info("Note E full pass")



async def note_g(dut, delta=0, msg=""):
    gFreq = 196
    
    dut._log.info(f"G delta {delta}")
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['G'] & SegmentMask), "Note G FAIL"
    dut._log.info("Note G: PASS")
    return dispValues

@cocotb.test()
async def note_g_highclose(dut):
    dispValues = await note_g(dut, delta=3, msg="High/close")
    assert dispValues[0] == (displayProx['hiclose'] & ProxSegMask) , "High/close fail"
    dut._log.info("Note G full pass")
    


async def note_a(dut, delta=0, msg=""):
    aFreq = 110
    
    dut._log.info(f"A delta {delta}")
    dispValues = await note_toggle(dut, freq=aFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['A'] & SegmentMask), "Note A fail"
    dut._log.info("Note A pass")
    return dispValues

@cocotb.test()
async def note_a_exact(dut):
    dispValues = await note_a(dut, delta=0, msg="A exact")
    assert dispValues[0] == (displayProx['exact'] & ProxSegMask) , "exact fail"
    dut._log.info("Note A full pass")

def main():
    from ttboard.cocotb.dut import DUTWrapper
    
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
            
    tt = DemoBoard.get()
    tt.shuttle.tt_um_psychogenic_neptuneproportional.enable()
    tt.clock_project_stop()
    Clock.clear_all()
    dut = DUT()
    dut._log.info("enabled neptune project")
    runner = cocotb.get_runner()
    runner.test(dut)


if __name__ == '__main__':
    main()
