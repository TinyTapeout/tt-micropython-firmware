'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
RP2040SystemClockDefaultHz = 125000000

IsRP2040 = False 
try:
    import machine 
    IsRP2040 = True 
except:
    pass




if IsRP2040:
    '''
        low-level machine related methods.
        
        
        
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
        output nibble, that could in theory interfere with this.
        If you use the tt.shuttle to select/enable projects, it 
        ensures that the mux is set to let these pins out as you'd 
        expect.  If you're down in the weeds and want to make sure 
        or play with this, you can use
            tt.muxCtrl.mode_admin() 
                to send out 1/2/3 to the asic mux, and
            tt.muxCtrl.mode_project_IO()
                to behave normally.
        
    '''
    
    def isfile(file_path:str):
        try:
            f = open(file_path, 'r')
        except OSError:
            return False 
        f.close()
        return True 
    def get_RP_system_clock():
        return machine.freq()
    def set_RP_system_clock(freqHz:int):
        machine.freq(int(freqHz))
    
    @micropython.native
    def write_input_byte(val):
        # low level machine stuff
        # move the value bits to GPIO spots
        # low nibble starts at 9 | high nibble at 17 (-4 'cause high nibble)
        val = ((val & 0xF) << 9) | ((val & 0xF0) << 17-4)
        # xor with current GPIO values, and mask to keep only input bits
        val = (machine.mem32[0xd0000010] ^ val) & 0x1E1E00
        # val is now be all the input bits that have CHANGED:
        # writing to 0xd000001c will flip any GPIO where a 1 is found
        machine.mem32[0xd000001c] = val
        
    @micropython.native
    def read_input_byte():
        # just read the high and low nibbles from GPIO and combine into a byte
        return ( (machine.mem32[0xd0000004] & (0xf << 17)) >> (17-4)) | ((machine.mem32[0xd0000004] & (0xf << 9)) >> 9)
    
    @micropython.native
    def write_bidir_byte(val):
        # low level machine stuff
        # move the value bits to GPIO spots
        # for bidir, all uio bits are in a line starting 
        # at GPIO 21
        val = (val << 21)
        # xor with current GPIO values, and mask to keep only input bits
        val = (machine.mem32[0xd0000010] ^ val) & 0x1FE00000
        # val is now be all the bits that have CHANGED:
        # writing to 0xd000001c will flip any GPIO where a 1 is found,
        # only applies immediately to pins set as output 
        machine.mem32[0xd000001c] = val
        
        
    @micropython.native
    def read_bidir_byte():
        # just read the high and low nibbles from GPIO and combine into a byte
        return (machine.mem32[0xd0000004] & (0xff << 21)) >> 21
        
    @micropython.native
    def write_output_byte(val):
        # low level machine stuff
        # move the value bits to GPIO spots
        # for bidir, all uio bits are in a line starting 
        # at GPIO 21
        val = ((val & 0xF) << 5) | ((val & 0xF0) << 13-4)
        # xor with current GPIO values, and mask to keep only input bits
        val = (machine.mem32[0xd0000010] ^ val) & 0x1E1E0
        # val is now be all the bits that have CHANGED:
        # writing to 0xd000001c will flip any GPIO where a 1 is found,
        # only applies immediately to pins set as output 
        machine.mem32[0xd000001c] = val
    
    @micropython.native
    def read_output_byte():
        # just read the high and low nibbles from GPIO and combine into a byte
        return ( (machine.mem32[0xd0000004] & (0xf << 13)) >> (13-4)) | ((machine.mem32[0xd0000004] & (0xf << 5)) >> 5)
    
    
else:
    import os.path 
    isfile = os.path.isfile
    def get_RP_system_clock():
        return RP2040SystemClockDefaultHz
    def set_RP_system_clock(freqHz:int):
        print(f"Set machine clock to {freqHz}")