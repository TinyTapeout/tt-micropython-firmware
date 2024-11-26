'''
Created on Jan 6, 2024

Main purposes of this module are to:

  * provide named access to pins
  * provide a consistent and transparent interface 
    to standard and MUXed pins
  * provide utilities to handle logically related pins as ports (e.g. all the 
    INn pins as a list or a byte)
  * augment the machine.Pin to give us access to mode, pull etc
  * handle init sanely
  
TLDR
  1) get pins
  p = Pins(RPMode.ASIC_RP_CONTROL) # monitor/control ASIC
  
  2) play with pins
  print(p.pins.uo_out2()) # read
  p.ui_in[3] = 1 # set
  p.ui_in.value = 0x42 # set all INn 
  p.pins.uio_in1.mode = Pins.OUT # set mode
  p.uio_in[1] = 1 # set output
  
  

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.mode import RPMode, RPModeDEVELOPMENT

import ttboard.util.platform as platform
from ttboard.pins.upython import Pin
import ttboard.pins.gpio_map as gp
from ttboard.pins.standard import StandardPin
from ttboard.pins.muxed import MuxedPin, MuxedPinInfo
from ttboard.pins.mux_control import MuxControl

from ttboard.ports.io import IO as VerilogIOPort
from ttboard.ports.oe import OutputEnable as VerilogOEPort


import ttboard.log as logging
log = logging.getLogger(__name__)



class Pins:
    '''
        This object handles setup and provides uniform named
        access to all logical pins, along with some utilities.
        See below for actual direction configuration of various pins.
        
        Tab-completion in a REPL will show you all the matching 
        named attributes, and auto-complete as usual.
        
        # Pins:
        For regular read/writes to pins, access them on this object
        by name, as a function.  An empty call is a read, a call with 
        a parameter is a write.  E.g.
        
            bp = Pins(...)
            bp.pins.uo_out1() # reads the value
            bp.ui_in[3] = 1 # sets the value
            # can also use normal machine.Pin functions like
            bp.pins.ui_in3.off()
            # or
            bp.pins.ui_in3.irq(...)    
        
        Though you shouldn't need it (the pin objects support everything 
        machine.Pin does), if you want low-level access to the 
        bare machine.Pin object, it is also available by simply 
        prepending the name with "pin_", e.g.
        
            bp.pin_out1.irq(handler=whatever, trigger=Pin.IRQ_FALLING)
        
        Just beware if accessing the muxed pins (e.g. cinc_out3).
        
        # Named Ports and Utilities:
        In addition to single pin access, named ports are available for 
        input, output and bidirectional pins.
        
            bp.inputs is an array of [in0, in1, ... in7]
            bp.outputs is an array of [out0, out1, ... out7]
            bp.bidir is an array of [uio0, uio1, ... uio7]
        
        You may also access arrays of the raw machine.Pin by using _pins, e.g
            bp.input_pins
        
        Finally, the _byte properties allow you to read or set the entire 
        port as a byte
        
            print(bp.uo_out.value)
            # or set
            bp.ui_in.value = 0xAA
        
        # Pin DIRECTION
        So, from the RP2040's perspective, is out2 configured to read (an 
        input) or to write (an output)?
        
        These signals are all named according to the TT ASIC.  So, 
        under normal/expected operation, it is the ASIC that writes to OUTn 
        and reads from INn. The bidirs... who knows.
        
        What you DON'T want is contention, e.g. the ASIC trying to 
        drive out5 HIGH and the RP shorting it LOW.
        
        So this class has 3 modes of pin init at startup:
         * RPMode.SAFE, the default, which has every pin as an INPUT, no pulls
         * RPMode.ASIC_RP_CONTROL, for use with ASICs, where it watches the OUTn 
           (configured as inputs) and can drive the INn and tickle the 
           ASIC inputs (configured as outputs)
         * RPMode.STANDALONE: where OUTn is an OUTPUT, INn is an input, useful
           for playing with the board _without_ an ASIC onboard
           
        To override the safe mode default, create the instance using
        p = Pins(mode=Pins.MODE_LISTENER) # for example.
        
        
        
    '''
    # convenience: aliasing here    
    IN = Pin.IN
    IRQ_FALLING = Pin.IRQ_FALLING
    IRQ_RISING = Pin.IRQ_RISING
    OPEN_DRAIN = Pin.OPEN_DRAIN
    OUT = Pin.OUT
    PULL_DOWN = Pin.PULL_DOWN
    PULL_UP = Pin.PULL_UP
    
    # MUX pin is especial...
    muxName = 'hk_csb' # special pin
    
    
    def __init__(self, mode:int=RPMode.SAFE):
        self.dieOnInputControlSwitchHigh = True
        self._mode = None
        self._allpins = {}
        if gp.GPIOMap.demoboard_uses_mux():
            self.muxCtrl = MuxControl(self.muxName, gp.GPIOMap.mux_select(), Pin.OUT)
            # special case: give access to mux control/HK nCS pin
            self.hk_csb = self.muxCtrl.ctrlpin
            self.pin_hk_csb = self.muxCtrl.ctrlpin.raw_pin 
            self._allpins['hk_csb'] = self.hk_csb
        
        self._init_ioports()
        self.mode = mode 
        
        
    
    def _init_ioports(self):
        # Note: these are named according the the ASICs point of view
        # we can write ui_in, we read uo_out
        port_defs = [
            ('uo_out',  8, platform.read_output_byte, None),
            ('ui_in',   8, platform.read_input_byte, platform.write_input_byte),
            ('uio_in',  8, platform.read_bidir_byte, platform.write_bidir_byte),
            ('uio_out', 8, platform.read_bidir_byte, None)
            ]
        self._ports = dict()
        for pd in port_defs:
            setattr(self, pd[0], VerilogIOPort(*pd))
            
            
        self.uio_oe_pico = VerilogOEPort('uio_oe_pico', 8, 
                                         platform.read_bidir_outputenable, 
                                         platform.write_bidir_outputenable)
        
        
    
    @property 
    def demoboard_uses_mux(self):
        return gp.GPIOMap.demoboard_uses_mux()
    
    @property 
    def all(self):
        return list(self._allpins.values())
    
    
    @property 
    def mode(self):
        return self._mode 
    
    @mode.setter
    def mode(self, set_mode:int):
        startupMap = {
            RPModeDEVELOPMENT.STANDALONE: self.begin_standalone,
            RPMode.ASIC_RP_CONTROL: self.begin_asiconboard,
            RPMode.ASIC_MANUAL_INPUTS: self.begin_asic_manual_inputs,
            RPMode.SAFE: self.begin_safe
        }
        
        if set_mode not in startupMap:
            set_mode = RPMode.SAFE 
        
        self._mode = set_mode
        log.info(f'Setting mode to {RPMode.to_string(set_mode)}')
        beginFunc = startupMap[set_mode]
        beginFunc()
        if set_mode == RPMode.ASIC_RP_CONTROL:
            self.ui_in.byte_write = platform.write_input_byte
            self.uio_in.byte_write = platform.write_bidir_byte
        else:
            self.ui_in.byte_write = None 
            self.uio_in.byte_write = None
            
        
    def begin_inputs_all(self):
        
        log.debug(f'Begin inputs all with {gp.GPIOMap}')
        always_out = gp.GPIOMap.always_outputs()
        for name,gpio in gp.GPIOMap.all().items():
            if name == self.muxName:
                continue
            p_type = Pin.IN
            if always_out.count(name) > 0:
                p_type = Pin.OUT
            p = StandardPin(name, gpio, p_type, pull=gp.GPIOMap.default_pull(name))
            setattr(self, f'pin_{name}', p.raw_pin)
            setattr(self, name, p) # self._pinFunc(p)) 
            self._allpins[name] = p
        
        return
    
    def safe_bidir(self):
        '''
            Reset bidirection pins to safe mode, i.e. inputs
            
        '''
        log.debug('Setting bidirs to safe mode (inputs)')
        for pname in gp.GPIOMap.all().keys():
            if pname.startswith('uio'):
                p = getattr(self, pname)
                p.mode = Pin.IN
                
        
        
    def begin_safe(self):
        log.debug('begin: SAFE')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        self._begin_muxPins()
    
    
    def begin_asiconboard(self):
        log.debug('begin: ASIC_RP_CONTROL')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        unconfigured_pins = []
        for pname in gp.GPIOMap.all().keys():
            if pname.startswith('ui_in'):
                p = getattr(self, pname)
                if self.dieOnInputControlSwitchHigh:
                    if p():
                        log.warn(f'Trying to control {pname} but possible contention (it is reading HIGH)')
                        unconfigured_pins.append(pname)
                        continue 
                p.mode = Pin.OUT
        
        if len(unconfigured_pins):
            log.error(f'Following pins have not be set as outputs owing to contention: {",".join(unconfigured_pins)}')
        self._begin_muxPins()
        # needs to be after mux because reset now muxed
        self.project_clk_driven_by_RP2040(True)
        
    def begin_asic_manual_inputs(self):
        log.debug('begin: ASIC + MANUAL INPUTS')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        # leave in* as inputs
        self._begin_muxPins()
        # leave clk and reset as inputs, for manual operation
        # needs to be after mux, because reset now muxed
        self.project_clk_driven_by_RP2040(False)
        
        
    
    def begin_standalone(self):
        log.debug('begin: STANDALONE')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        
        for pname in gp.GPIOMap.all().keys():
            if pname.startswith('uo_out'):
                p = getattr(self, pname)
                p.mode = Pin.OUT
                
            if pname.startswith('ui_in'):
                p = getattr(self, pname)
                p.pull = Pin.PULL_DOWN
                
        self._begin_muxPins()
        # needs to be after mux, because reset now muxed
        self.project_clk_driven_by_RP2040(True)
        
    def project_clk_driven_by_RP2040(self, rpControlled:bool):
        for pname in ['rp_projclk']:
            p = getattr(self, pname)
            if rpControlled:
                p.mode = Pin.OUT
            else:
                p.mode = Pin.IN
                
            
    def _begin_alwaysOut(self):
        for pname in gp.GPIOMap.always_outputs():
            p = getattr(self, pname)
            p.mode = Pin.OUT 
            
    def _begin_muxPins(self):
        if not gp.GPIOMap.demoboard_uses_mux():
            return 
        muxedPins = gp.GPIOMap.muxed_pairs()
        modeMap = gp.GPIOMap.muxed_pinmode_map(self.mode)
        for pname, muxPair in muxedPins.items():
            log.debug(f'Creating muxed pin {pname}')
            mp = MuxedPin(pname, self.muxCtrl, 
                          getattr(self, pname),
                          MuxedPinInfo(muxPair[0],
                                       0, modeMap[muxPair[0]]),
                          MuxedPinInfo(muxPair[1],
                                       1, modeMap[muxPair[1]])
                          )
            self.muxCtrl.add_muxed(mp)
            self._allpins[pname] = mp
            setattr(self, muxPair[0], getattr(mp, muxPair[0]))
            setattr(self, muxPair[1], getattr(mp, muxPair[1]))
            # override bare pin attrib
            setattr(self, pname, mp)
            
    # aliases
    @property 
    def clk(self):
        return self.rp_projclk
    
    @property 
    def nproject_rst(self):
        # had to munge the name because nproject_rst
        # is now in hardware MUX group, alias
        # allows use of old name with_underscore
        return self.nprojectrst
    
    @property 
    def ctrl_ena(self):
        # had to munge name, now going through hw mux
        return self.cena
    
    def _dumpPin(self, p:StandardPin):
        print(f'  {p.name} {p.mode_str} {p()}') 
    def dump(self):
        print(f'Pins configured in mode {RPMode.to_string(self.mode)}')
        print(f'Currently:')
        for pname in sorted(gp.GPIOMap.all().keys()):
            self._dumpPin(getattr(self, pname))
    
    
    
    def list_port(self, basename:str):
        retVal = []
        
        for i in range(8):
            pname = f'{basename}{i}'
            if hasattr(self, pname):
                retVal.append(getattr(self,pname))
        
        return retVal
    
    def _read_byte(self, pinList:list):
        v = 0
        for i in range(8):
            bit = pinList[i]()
            if bit:
                v |= (1 << i)
                
        return v 
    
    def _write_byte(self, pinList:list, value:int):
        v = int(value)
        for i in range(8):
            if v & (1 << i):
                pinList[i](1)
            else:
                pinList[i](0)
    
