'''
Created on Jan 9, 2024

This module provides the DemoBoard class, which is the primary
entry point to all the RP2040 demo pcb functionality, including

    * pins (named, transparently muxed)
    * projects (all shuttle projects and means to enable)
    * basic utilities (auto clocking projects etc)
    

    

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import ttboard.util.time as time
from ttboard.mode import RPMode
from ttboard.pins import Pins
from ttboard.project_mux import ProjectMux, Design
from ttboard.config.user_config import UserConfig

import ttboard.logging as logging
log = logging.getLogger(__name__)

class DemoBoard:
    '''
        The DemoBoard object has 
         * named pins, e.g.
          print(demo.out2()) # read
          demo.in3(1) # write
          demo.uio5.mode = machine.Pin.OUT # config
          demo.uio5(1)
         * named projects
          demo.shuttle.tt_um_urish_simon.enable()
          print(demo.shuttle.tt_um_urish_simon.repo)
         
         * utilities:
          demo.reset_project(True)
          demo.clock_project_PWM(1e6) # clock it at 1MHz
          
        See below.
        
        The most obvious danger of using the RP2040 is _contention_, 
        e.g. the ASIC trying to drive out5 HIGH and the RP shorting it LOW.
        So the constructor for this class takes a mode parameter that 
        is passed to the Pins container, which must be one of the 3 modes 
        of pin init at startup.  See constructor.
        
    
    '''
    def __init__(self, 
                 mode:int=None, 
                 iniFile:str='config.ini',
                 apply_user_config:bool=True):
        '''
            Constructor takes a mode parameter, one of:
            
             * RPMode.SAFE, the default, which has every pin as an INPUT, no pulls
             
             * RPMode.ASIC_ON_BOARD, for use with ASICs, where it watches the OUTn 
               (configured as inputs) and can drive the INn and tickle the 
               ASIC inputs (configured as outputs)
               
             * RPMode.STANDALONE: where OUTn is an OUTPUT, INn is an input, useful
               for playing with the board _without_ an ASIC onboard
               
            Choose wisely (only STANDALONE has serious contention risk)
        
        '''
        # interfaces 
        self.user_config = UserConfig(iniFile)
        
        if mode is not None:
            self.default_mode = mode 
        else:
            self.default_mode = self.user_config.default_mode
            if self.default_mode is None:
                # neither arg and ini file specify mode
                raise AttributeError('MUST specify either mode in .ini DEFAULT or mode argument')
            
            mode = self.default_mode
            
        log.info(f'Demoboard starting up in mode {RPMode.to_string(mode)}')
        
        self.pins = Pins(mode=mode)
        self.shuttle = ProjectMux(self.pins)
        
        # config
        self.apply_configs = apply_user_config
        
        # internal
        self.shuttle.designEnabledCallback = self.apply_user_config
        self._clock_pwm = None
        
        if self.user_config.default_project is not None:
            if self.shuttle.has(self.user_config.default_project):
                self.shuttle.get(self.user_config.default_project).enable()
            else:
                log.warn(f'Default project is unknown "{self.user_config.default_project}"')
        
    @property 
    def mode(self):
        return self.pins.mode 
    
    @mode.setter 
    def mode(self, setTo:int):
        if self.mode != setTo:
            if self.is_auto_clocking:
                autoClockFreq = self._clock_pwm.freq()
                self.clock_project_stop()
                log.warn(f'Was auto-clocking @ {autoClockFreq} but stopping for mode change')
                
        self.pins.mode = setTo 
        
    @property 
    def is_auto_clocking(self):
        return self._clock_pwm is not None
    @property 
    def project_clk(self):
        '''
            Quick access to project clock pin.
            
            project_clk(1) # write
            project_clk.on() # same
            project_clk.toggle()
            
            all the usual pin stuff.
            
            @note: if you've enabled PWM on the clock pin, that's what is returned
            rather than the pin itself.  If you really need the pin while 
            PWM is running, you can get it from pins.rp_projclk
            
            
            @see: clock_project_once(), clock_project_PWM() and clock_project_stop()
        '''
        if self._clock_pwm is not None:
            return self._clock_pwm
        return self.pins.rp_projclk
    
    @property 
    def project_nrst(self):
        '''
            Quick access to project reset pin.
            
            project_nrst(1) # write
            project_nrst.on() # same
            project_nrst.toggle()
            
            all the usual pin stuff.
            
            @see: reset_project()
        '''
        return self.pins.nproject_rst
    
    def reset_project(self, putInReset:bool):
        '''
            Utility to mask the logic inversion and 
            make things clear.
            
            reset_project(True) # project is in reset
            reset_project(False) # now it ain't
        '''
        if putInReset:
            self.project_nrst(0) # inverted logic
        else:
            self.project_nrst(1)
            
    def clock_project_once(self, msDelay:int=0):
        '''
            Utility method to toggle project clock 
            pin twice, optionally with a delay
            between the changes (in ms)
        '''
        self.project_clk.toggle()
        if msDelay > 0:
            time.sleep_ms(msDelay)
        self.project_clk.toggle()
        
        
    def clock_project_PWM(self, freqHz:int, duty_u16:int=(0xffff/2)):
        '''
            Start an automatic clock for the selected project (using
            PWM).
            @param freqHz: The frequency of the clocking, in Hz
            @param duty_u16: Optional duty cycle (0-0xffff), defaults to 50%  
        '''
        self.clock_project_stop()
        if freqHz < 1: # equiv to stop 
            return 
        self._clock_pwm = self.project_clk.pwm(freqHz, duty_u16)
        return self._clock_pwm
    
    def clock_project_stop(self):
        '''
            Stop any started automatic project clocking.  No effect 
            if no clocking started.
        '''
        if self._clock_pwm is None:
            return 
        
        self._clock_pwm.deinit()
        self._clock_pwm = None
    
    
    def apply_user_config(self, design:Design):
        log.debug(f'Design "{design.name}" loaded, apply user conf')
        
        applyWhenInModeMap = {
            RPMode.ASIC_ON_BOARD: True,
            RPMode.ASIC_MANUAL_INPUTS: True
        }
        if not self.apply_configs:
            log.debug(f'apply user conf: disabled')
            # don't wanna
            return 
        
        if self.mode not in applyWhenInModeMap:
            log.debug(f'apply user conf: disallowed in this mode')
            # won't do it in this mode 
            return 
        
        if not self.user_config.has_project(design.name):
            log.debug(f'apply user conf: no user config for project')
            # nothing to do
            return 
        
        projConfig = self.user_config.project(design.name)
        
        
        desiredMode = RPMode.from_string(projConfig.mode)
        if desiredMode is not None:
            log.warn(f'Switching to mode {projConfig.mode} for design "{design.name}"')
            self.mode = desiredMode
        
        # start in reset (project nRST pin)
        # set in project section
        # or use DEFAULT
        # and if not set in either, don't touch
        startInReset = projConfig.start_in_reset
        if startInReset is None:
            startInReset = self.user_config.default_start_in_reset
            
        if startInReset is not None:
            self.reset_project(startInReset)
        
        
        # input byte
        if projConfig.has('input_byte') and self.mode != RPMode.ASIC_MANUAL_INPUTS:
            btVal = projConfig.input_byte
            log.debug(f'Setting input byte to {btVal}')
            self.pins.input_byte = btVal
            
        if projConfig.bidir_direction is not None:
            dirBits = projConfig.bidir_direction
            log.debug(f'Setting bidir pin direction to {hex(dirBits)}')
            bidirs = self.pins.bidirs 
            
            for i in range(8):
                if dirBits & (1 << i):
                    bidirs[i].mode = Pins.OUT
                    
            if projConfig.bidir_byte is not None:
                valBits = projConfig.bidir_byte
                log.debug(f'Also setting bidir byte values {hex(valBits)}')
                for i in range(8):
                    mask = (1 << i) 
                    if (dirBits & mask): # this is actually an output
                        if valBits & mask: # and we want it high
                            bidirs[i](1)
                        else: # nah, want it low
                            bidirs[i](0)
                    
        if projConfig.has('clock_frequency'):
            if self.mode == RPMode.ASIC_MANUAL_INPUTS:
                log.info('In "manual inputs" mode but clock freq set--setting up for CLK/RST RP ctrl')
                self.pins.proj_clk_nrst_driven_by_RP2040(True)
            self.clock_project_PWM(projConfig.clock_frequency)
        else:
            self.clock_project_stop()
            
            
    def dump(self):
        print('\n\nDemoboard status')
        print(f'Demoboard default mode is {RPMode.to_string(self.default_mode)}')
        print(f'Project nRESET pin is {self.project_nrst.mode_str} {self.project_nrst()}')
        
        if self._clock_pwm is not None:
            print(f'Project clock PWM enabled and running at {self._clock_pwm.freq()}')
        else:
            print('Project clock: no PWM auto-clocking enabled')
            
            
        if self.shuttle.enabled is None:
            print('No selected design')
        else:
            print(f'Selected design: {self.shuttle.enabled}')
            
        print()
        self.pins.dump()
        
        print('\n\n')
        
    def __repr__(self):
        if self._clock_pwm:
            autoclocking = f', auto-clocking @ {self._clock_pwm.freq()}'
        else:
            autoclocking = ''
            
        reset = ''
        if self.shuttle.enabled is not None and not self.project_nrst(): # works whether is input or output
            reset = ' (in RESET)'
        return f"<DemoBoard as {RPMode.to_string(self.mode)}{autoclocking}, project '{self.shuttle.enabled}'{reset}>"
    
    def __getattr__(self, name):
        if hasattr(self.pins, name):
            return getattr(self.pins, name)
        raise AttributeError
    
    def __setattr__(self, name, value):
        try:
            pins = getattr(self, 'pins')
            if pins is not None and hasattr(pins, name):
                return setattr(pins, name, value)
        except:
            pass
        
        super().__setattr__(name, value)
        
    def __dir__(self):
        return dir(self.pins)


    

