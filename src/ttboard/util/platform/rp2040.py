'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com

    low-level machine related methods.
    @note: Register magic is based on "2.3.1.7. List of Registers" 
    from the rp2040_datasheet.pdf
    
    Have some read_ and write_ for in/bidir/out ports
    NOTE: [mappings] that these rely on GPIO pin mappings that 
    are specific to TT 4/5 demoboard layout
    
    The read_ will only return bits for GPIO that are set 
    as INPUTs
    The write_ will write values to all GPIO but these will only
    impact GPIO that are setup as OUTPUTs.  For input gpio, this 
    value will be remembered and apply should the pin be turned
    into an output.
    
    NOTE: [muxing] there is a MUX on some pins of the low 
    output nibble on TT04/05 demoboards, that could in theory
    interfere with this.
    If you use the tt.shuttle to select/enable projects, it 
    ensures that the mux is set to let these pins out as you'd 
    expect.  If you're down in the weeds and want to make sure 
    or play with this, you can use
        tt.muxCtrl.mode_admin() 
            to send out 1/2/3 to the asic mux, and
        tt.muxCtrl.mode_project_IO()
            to behave normally.
    
    The machine native stuff below uses 
    direct access to mem32 to go fastfastfast
    but this is pretty opaque.  For ref, here are 
    relevant registers from 2.3.1.7. List of Registers
        0x004 GPIO_IN Input value for GPIO pins
        0x010 GPIO_OUT GPIO output value
        0x014 GPIO_OUT_SET GPIO output value set
        0x018 GPIO_OUT_CLR GPIO output value clear
        0x01c GPIO_OUT_XOR GPIO output value XOR
        0x020 GPIO_OE GPIO output enable
        0x024 GPIO_OE_SET GPIO output enable set
        0x028 GPIO_OE_CLR GPIO output enable clear
        0x02c GPIO_OE_XOR GPIO output enable XOR
    
'''
import rp2
import machine 

@micropython.native
def write_ui_in_byte(val):
    # dump_portset('ui_in', val)
    # low level machine stuff
    # move the value bits to GPIO spots
    # low nibble starts at 9 | high nibble at 17 (-4 'cause high nibble)
    val = ((val & 0xF) << 9) | ((val & 0xF0) << 17-4)
    # xor with current GPIO values, and mask to keep only input bits
    # 0x1E1E00 == 0b111100001111000000000 so GPIO 9-12 and 17-20
    val = (machine.mem32[0xd0000010] ^ val) & 0x1E1E00
    # val is now be all the input bits that have CHANGED:
    # writing to 0xd000001c will flip any GPIO where a 1 is found
    machine.mem32[0xd000001c] = val
    
@micropython.native
def read_ui_in_byte():
    # just read the high and low nibbles from GPIO and combine into a byte
    return ( (machine.mem32[0xd0000004] & (0xf << 17)) >> (17-4)) | ((machine.mem32[0xd0000004] & (0xf << 9)) >> 9)


@micropython.native
def write_uio_byte(val):
    # dump_portset('uio', val)
    # low level machine stuff
    # move the value bits to GPIO spots
    # for bidir, all uio bits are in a line starting 
    # at GPIO 21
    val = (val << 21)
    val = (machine.mem32[0xd0000010] ^ val) & 0x1FE00000
    # val is now be all the bits that have CHANGED:
    # writing to 0xd000001c will flip any GPIO where a 1 is found,
    # only applies immediately to pins set as output 
    machine.mem32[0xd000001c] = val
    
    
@micropython.native
def read_uio_byte():
    return (machine.mem32[0xd0000004] & (0xff << 21)) >> 21

@micropython.native
def read_uio_outputenable():
    # GPIO_OE register, masked for our bidir pins
    return (machine.mem32[0xd0000020] & 0x1FE00000) >> 21
    
    
@micropython.native
def write_uio_outputenable(val):
    # dump_portset('uio_oe', val)
    # GPIO_OE register, clearing bidir pins and setting any enabled
    val = (val << 21)
    machine.mem32[0xd0000020] = (machine.mem32[0xd0000020] & ((1 << 21) - 1)) | val
    
@micropython.native
def write_uo_out_byte(val):
    # dump_portset('uo_out', val)
    # low level machine stuff
    # move the value bits to GPIO spots
    
    val = ((val & 0xF) << 5) | ((val & 0xF0) << 13-4)
    val = (machine.mem32[0xd0000010] ^ val) & 0x1E1E0
    # val is now be all the bits that have CHANGED:
    # writing to 0xd000001c will flip any GPIO where a 1 is found,
    # only applies immediately to pins set as output 
    machine.mem32[0xd000001c] = val

@micropython.native
def read_uo_out_byte():
    
    # sample code to deal with differences between 
    # PCBs, not actually required as we didn't move anything
    # after all!
    # global PCBVERSION_TT06
    # all_io = machine.mem32[0xd0000004]
    #if PCBVERSION_TT06 is None:
    #    import ttboard.boot.demoboard_detect as dbdet
    #    PCBVERSION_TT06 = True if dbdet.DemoboardDetect.PCB == dbdet.DemoboardVersion.TT06 else False
    
    #if PCBVERSION_TT06:
    #    # gpio output bits are
    #    # 0x1e1e0 == 0b11110000111100000 so GPIO5-8 and GPIO 13-17
    #    val =  ((all_io & (0xf << 13)) >> (13 - 4)) | ((all_io & (0xf << 5)) >> 5)
    #else:
    # just read the high and low nibbles from GPIO and combine into a byte
    return ( (machine.mem32[0xd0000004] & (0xf << 13)) >> (13-4)) | ((machine.mem32[0xd0000004] & (0xf << 5)) >> 5)


@micropython.native
def read_clock():
    # clock is on GPIO 0
    return (machine.mem32[0xd0000010] & 1)
   
@micropython.native
def write_clock(val):
    # not a huge optimization, as this is a single bit, 
    # but 5% or so counts when using the microcotb tests
    if val:
        machine.mem32[0xd0000014] = 1 # set bit 0
    else:
        machine.mem32[0xd0000018] = 1 # clear bit 0
    
    
