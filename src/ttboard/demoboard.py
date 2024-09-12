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
import ttboard
import ttboard.util.time as time
from ttboard.globals import Globals
from ttboard.mode import RPMode
from ttboard.pins.pins import Pins
from ttboard.project_mux import Design
from ttboard.config.user_config import UserConfig
import ttboard.util.platform as platform 
from ttboard.boot.demoboard_detect import DemoboardDetect, DemoboardVersion

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
    
    _DemoBoardSingleton_Instance = None 
    
    @classmethod 
    def get(cls):
        if cls._DemoBoardSingleton_Instance is None:
            cls._DemoBoardSingleton_Instance = cls()
            
        return cls._DemoBoardSingleton_Instance
    
    
    
    
    
    def __init__(self, 
                 mode:int=None, 
                 iniFile:str='config.ini',
                 apply_user_config:bool=True):
        '''
            Constructor takes a mode parameter, one of:
            
             * RPMode.SAFE, the default, which has every pin as an INPUT, no pulls
             
             * RPMode.ASIC_RP_CONTROL, for use with ASICs, where it watches the OUTn 
               (configured as inputs) and can drive the INn and tickle the 
               ASIC inputs (configured as outputs)
               
             * RPMode.STANDALONE: where OUTn is an OUTPUT, INn is an input, useful
               for playing with the board _without_ an ASIC onboard
               
            Choose wisely (only STANDALONE has serious contention risk)
        
        '''
        # interfaces 
        self.user_config = UserConfig(iniFile)
        
        log_level = self.user_config.log_level
        if log_level is not None:
            logging.basicConfig(level=log_level)
        
        if mode is not None:
            self.default_mode = mode 
        else:
            self.default_mode = self.user_config.default_mode
            if self.default_mode is None:
                # neither arg and ini file specify mode
                raise AttributeError('MUST specify either mode in .ini DEFAULT or mode argument')
            
            mode = self.default_mode
            
        log.info(f'Demoboard starting up in mode {RPMode.to_string(mode)}')
        
        if self.user_config.force_demoboard:
            versionMap = {
                'tt04': DemoboardVersion.TT04,
                'tt05': DemoboardVersion.TT04,
                'tt06': DemoboardVersion.TT06,
                'tt07': DemoboardVersion.TT06,
                'tt08': DemoboardVersion.TT06,
                
                }
            if self.user_config.force_demoboard in versionMap:
                log.warn(f'Demoboard detection forced to {self.user_config.force_demoboard}')
                DemoboardDetect.force_detection(versionMap[self.user_config.force_demoboard])
            else:
                log.error(f'Unrecognized force_demoboard setting: {self.user_config.force_demoboard}')
            
            
            
            
        self.pins = Globals.pins(mode=mode)
        self.shuttle = Globals.project_mux(self.user_config.force_shuttle)
        
        # config
        self.apply_configs = apply_user_config
        
        # internal
        self.shuttle.design_enabled_callback = self.apply_user_config
        self._clock_pwm = None
        
        self._project_previously_loaded = {}
        self.load_default_project() 
        
        if DemoBoard._DemoBoardSingleton_Instance is None:
            DemoBoard._DemoBoardSingleton_Instance = self 
        
        
    def load_default_project(self):
        if self.user_config.default_project is not None:
            if self.shuttle.has(self.user_config.default_project):
                self.shuttle.get(self.user_config.default_project).enable()
            else:
                log.warn(f'Default project is unknown "{self.user_config.default_project}"')
                
    @property 
    def version(self) -> str:
        return ttboard.VERSION
    
    @property 
    def chip_ROM(self):
        return self.shuttle.chip_ROM
    
    @property 
    def mode(self):
        return self.pins.mode 
    
    @mode.setter 
    def mode(self, setTo:int):
        if self.mode != setTo:
            if self.is_auto_clocking:
                autoClockFreq = self.auto_clocking_freq()
                self.clock_project_stop()
                log.warn(f'Was auto-clocking @ {autoClockFreq} but stopping for mode change')
                
        self.pins.mode = setTo 
        
    @property 
    def mode_str(self):
        return RPMode.to_string(self.mode)
        
    @property 
    def is_auto_clocking(self):
        return self._clock_pwm is not None
    
    @property 
    def auto_clocking_freq(self):
        if not self.is_auto_clocking:
            return 0
        return self._clock_pwm.freq()
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
        if self.is_auto_clocking:
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
        return self.pins.nprojectrst
    
    
    def reset_project(self, putInReset:bool):
        '''
            Utility to mask the logic inversion and 
            make things clear.
            
            reset_project(True) # project is in reset
            reset_project(False) # now it ain't
        '''
        cur_mode = self.project_nrst.mode
        if putInReset:
            if cur_mode != Pins.OUT:
                log.info("Changing reset to output mode")
                self.project_nrst.mode = Pins.OUT
            self.project_nrst(0) # inverted logic
        else:
            # we don't want it in reset.
            # demoboard has MOM switch and pull-ups to default 
            # it in this way, so we just need to make it an input
            # since this pin is on the MUX, we make certain that 
            # the correct bank is selected by writing to it first
            if cur_mode == Pins.OUT:
                log.debug('Taking out of reset')
                self.project_nrst(1) 
            self.project_nrst.mode = Pins.IN
            
    def clock_project_once(self, msDelay:int=0):
        '''
            Utility method to toggle project clock 
            pin twice, optionally with a delay
            between the changes (in ms)
        '''
        log.debug('clock project once')
        if self.is_auto_clocking:
            self.clock_project_stop()
            
        self.pins.project_clk_driven_by_RP2040(True)
        self.project_clk.toggle()
        if msDelay > 0:
            time.sleep_ms(msDelay)
        self.project_clk.toggle()
        
        
    def clock_project_PWM(self, freqHz:int, duty_u16:int=(0xffff/2)):
        '''
            Start an automatic clock for the selected project (using
            PWM).
            @param freqHz: The frequency of the clocking, in Hz, or 0 to disable PWM
            @param duty_u16: Optional duty cycle (0-0xffff), defaults to 50%  
        '''
        if freqHz > 0:
            self.pins.project_clk_driven_by_RP2040(True)
        try:
            self._clock_pwm = self.pins.rp_projclk.pwm(freqHz, duty_u16)
        except  Exception as e:
            log.error(f"Could not set project clock PWM: {e}")
        return self._clock_pwm
    
    def clock_project_stop(self):
        '''
            Stop any started automatic project clocking.  No effect 
            if no clocking started.
        '''
        if self.is_auto_clocking:
            log.debug('PWM auto-clock stop')
            self.clock_project_PWM(0)
            self.project_clk(0) # make certain we are low
        self.pins.project_clk_driven_by_RP2040(False)
    
    def reset_system_clock(self):
        # nothing set in project config, assume we want default system clock
        
        current_sys_clock = platform.get_RP_system_clock()
        def_sys_clock = self.user_config.default_rp_clock
        if def_sys_clock is None:
            def_sys_clock = platform.RP2040SystemClockDefaultHz 
        
        if def_sys_clock != current_sys_clock and def_sys_clock > 0:
            self.clock_project_stop() # ensure we aren't PWMing
            log.info(f'Resetting system clock to default {def_sys_clock}Hz')
            try:
                platform.set_RP_system_clock(def_sys_clock)
            except ValueError:
                log.error(f'Default sys clock setting {def_sys_clock} is invalid?')
    
    def _first_encouter_reset(self, design:Design):
        if design.name not in self._project_previously_loaded:
            self._project_previously_loaded[design.name] = True
            log.info('First time loading: Toggling project reset')
            self.reset_project(True)
            time.sleep_ms(2)
            self.reset_project(False)
    
    def apply_user_config(self, design:Design):
        log.debug(f'Design "{design.name}" loaded, apply user conf')
        
        applyWhenInModeMap = {
            RPMode.ASIC_RP_CONTROL: True,
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
            # nothing to do for specific project, 
            # ensure clocks are all behaving nicely
            
            self.reset_system_clock()
            self.clock_project_stop()
            self._first_encouter_reset(design)
            if design.clock_hz:
                self.clock_project_PWM(design.clock_hz)
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
            
        if projConfig.bidir_direction is None:
            # no bidir direction set, ensure all are inputs
            self.bidir_mode = [Pins.IN]*8
        else:
            dirBits = projConfig.bidir_direction
            log.debug(f'Setting bidir pin direction to {hex(dirBits)}')
            bidirs = self.pins.bidirs 
            
            for i in range(8):
                if dirBits & (1 << i):
                    bidirs[i].mode = Pins.OUT
                else:
                    bidirs[i].mode = Pins.IN
                    
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
                            
        
        current_sys_clock = platform.get_RP_system_clock()
        if projConfig.has('rp_clock_frequency'):
            sys_clk_hz = projConfig.rp_clock_frequency
            if sys_clk_hz != current_sys_clock:
                self.clock_project_stop() # ensure we aren't PWMing
                log.info(f'Setting system clock to {sys_clk_hz}Hz')
                try:
                    platform.set_RP_system_clock(sys_clk_hz)
                except ValueError:
                    log.error(f"Could not set system clock to requested {sys_clk_hz}Hz")
        else:
            self.reset_system_clock()
                    
        if projConfig.has('clock_frequency'):
            if self.mode == RPMode.ASIC_MANUAL_INPUTS:
                log.info('In "manual inputs" mode but clock freq set--setting up for CLK/RST RP ctrl')
                self.pins.project_clk_driven_by_RP2040(True)
            self.clock_project_PWM(projConfig.clock_frequency)
        else:
            self.clock_project_stop()
            
        
        if not startInReset:
            self._first_encouter_reset(design)
            
            
    def dump(self):
        print('\n\nDemoboard status')
        print(f'Demoboard default mode is {RPMode.to_string(self.default_mode)}')
        print(f'Project nRESET pin is {self.project_nrst.mode_str} {self.project_nrst()}')
        
        if self.is_auto_clocking:
            print(f'Project clock PWM enabled and running at {self.auto_clocking_freq}')
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
        if self.is_auto_clocking:
            autoclocking = f', auto-clocking @ {self.auto_clocking_freq}'
        else:
            autoclocking = ''
            
        reset = ''
        if self.shuttle.enabled is not None and not self.project_nrst(): # works whether is input or output
            reset = ' (in RESET)'
            
        shuttle_run = self.shuttle.run
        return f"<DemoBoard in {RPMode.to_string(self.mode)}{autoclocking} {shuttle_run} project '{self.shuttle.enabled}'{reset}>"
    
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


    

