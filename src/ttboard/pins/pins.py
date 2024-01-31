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
  p = Pins(RPMode.ASIC_ON_BOARD) # monitor/control ASIC
  
  2) play with pins
  print(p.out2()) # read
  p.in3(1) # set
  p.input_byte = 0x42 # set all INn 
  p.uio1.mode = Pins.OUT # set mode
  p.uio1(1) # set output
  
  

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.mode import RPMode, RPModeDEVELOPMENT


from ttboard.pins.upython import Pin
from ttboard.pins.gpio_map import GPIOMap
from ttboard.pins.standard import StandardPin
from ttboard.pins.muxed import MuxedPin, MuxedPinInfo
from ttboard.pins.mux_control import MuxControl



import ttboard.logging as logging
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
            bp.out1() # reads the value
            bp.in3(1) # sets the value
            # can also use normal machine.Pin functions like
            bp.in3.off()
            # or
            bp.in3.irq(...)    
        
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
        
            print(bp.output_byte)
            # or set
            bp.input_byte = 0xAA
        
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
         * RPMode.ASIC_ON_BOARD, for use with ASICs, where it watches the OUTn 
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
        self.muxCtrl = MuxControl(self.muxName, GPIOMap.HK_CSB, Pin.OUT)
        # special case: give access to mux control/HK nCS pin
        self.hk_csb = self.muxCtrl.ctrlpin
        self.pin_hk_csb = self.muxCtrl.ctrlpin.raw_pin 
        
        self._allpins = {'hk_csb': self.hk_csb}
        
        self.mode = mode 
        
    
    @property 
    def all(self):
        return list(self._allpins.values())
    
    
    @property 
    def mode(self):
        return self._mode 
    
    @mode.setter
    def mode(self, setTo:int):
        startupMap = {
            RPModeDEVELOPMENT.STANDALONE: self.begin_standalone,
            RPMode.ASIC_ON_BOARD: self.begin_asiconboard,
            RPMode.ASIC_MANUAL_INPUTS: self.begin_asic_manual_inputs,
            RPMode.SAFE: self.begin_safe
        }
        
        if setTo not in startupMap:
            setTo = RPMode.SAFE 
        
        self._mode = setTo
        log.info(f'Setting mode to {RPMode.to_string(setTo)}')
        beginFunc = startupMap[setTo]
        beginFunc()
        
    
    @property 
    def outputs(self):
        return self.list_port('out')
    
    @property 
    def output_pins(self):
        return self.list_port('pin_out')
    
    @property 
    def output_byte(self):
        return self._read_byte(self.outputs)
    
    @output_byte.setter 
    def output_byte(self, val:int):
        self._write_byte(self.outputs, val)
    
    @property 
    def inputs(self):
        return self.list_port('in')
    
    @property 
    def input_pins(self):
        return self.list_port('pin_in')
    
    @property 
    def input_byte(self):
        return self._read_byte(self.inputs)
    
    
    @input_byte.setter 
    def input_byte(self, val:int):
        self._write_byte(self.inputs, val)
    
    
    @property 
    def bidirs(self):
        return self.list_port('uio')
    
    @property 
    def bidir_pins(self):
        return self.list_port('pin_uio')
        
    @property 
    def bidir_byte(self):
        return self._read_byte(self.bidirs)
    
    @bidir_byte.setter 
    def bidir_byte(self, val:int):
        self._write_byte(self.bidirs, val)
    
        
    def begin_inputs_all(self):
        
        for name,gpio in GPIOMap.all().items():
            if name == self.muxName:
                continue
            p = StandardPin(name, gpio, Pin.IN, pull=GPIOMap.default_pull(name))
            setattr(self, f'pin_{name}', p.raw_pin)
            setattr(self, name, p) # self._pinFunc(p)) 
            self._allpins[name] = p
        
        return
    
    def safe_bidir(self):
        '''
            Reset bidirection pins to safe mode, i.e. inputs
            
        '''
        log.debug('Setting bidirs to safe mode (inputs)')
        for pname in GPIOMap.all().keys():
            if pname.startswith('uio'):
                p = getattr(self, pname)
                p.mode = Pin.IN
                
        
        
    def begin_safe(self):
        log.debug('begin: SAFE')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        self._begin_muxPins()
    
    
    def begin_asiconboard(self):
        log.debug('begin: ASIC_ON_BOARD')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        self.proj_clk_nrst_driven_by_RP2040(True)
        for pname in GPIOMap.all().keys():
            if pname.startswith('in'):
                p = getattr(self, pname)
                if self.dieOnInputControlSwitchHigh:
                    if p():
                        raise ValueError(f'Trying to control {pname} but possible contention (it is reading HIGH)')
                p.mode = Pin.OUT
                
        self._begin_muxPins()
        
    def begin_asic_manual_inputs(self):
        log.debug('begin: ASIC + MANUAL INPUTS')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        # leave clk and reset as inputs, for manual operation
        self.proj_clk_nrst_driven_by_RP2040(False)
        # leave in* as inputs
        self._begin_muxPins()
        
        
    
    def begin_standalone(self):
        log.debug('begin: STANDALONE')
        self.begin_inputs_all()
        self._begin_alwaysOut()
        self.proj_clk_nrst_driven_by_RP2040(True)
        
        for pname in GPIOMap.all().keys():
            if pname.startswith('out'):
                p = getattr(self, pname)
                p.mode = Pin.OUT
                
            if pname.startswith('in'):
                p = getattr(self, pname)
                p.pull = Pin.PULL_DOWN
                
        self._begin_muxPins()
        
    def proj_clk_nrst_driven_by_RP2040(self, rpControlled:bool):
    
        for pname in ['nproject_rst', 'rp_projclk']:
            p = getattr(self, pname)
            if rpControlled:
                p.mode = Pin.OUT
            else:
                p.mode = Pin.IN
            
    def _begin_alwaysOut(self):
        for pname in GPIOMap.always_outputs():
            p = getattr(self, pname)
            p.mode = Pin.OUT 
            
    def _begin_muxPins(self):
        muxedPins = GPIOMap.muxed_pairs()
        modeMap = GPIOMap.muxed_pinmode_map(self.mode)
        for pname, muxPair in muxedPins.items():
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
    def project_clk(self):
        return self.rp_projclk
    
    def _dumpPin(self, p:StandardPin):
        print(f'  {p.name} {p.mode_str} {p()}') 
    def dump(self):
        print(f'Pins configured in mode {RPMode.to_string(self.mode)}')
        print(f'Currently:')
        for pname in sorted(GPIOMap.all().keys()):
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
    
