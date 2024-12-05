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

import ttboard.log as logging
log = logging.getLogger(__name__)

class DemoBoard:
    '''
        The DemoBoard object has 
         * named pins, e.g.
          print(demo.pins.uo_out2()) # read
          demo.ui_in[3] = 1 # write
          demo.pins.uio_in5.mode = machine.Pin.OUT # config
          demo.uio_in[5] = 1
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
        '''
        Get (or create) the TT DemoBoard singleton
        '''
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
        #logging.dumpMem('db init')
        self.user_config = UserConfig(iniFile)
        #logging.dumpMem('user conf loaded')
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
                'tt09': DemoboardVersion.TT06,
                'tt10': DemoboardVersion.TT06,
                
                }
            if self.user_config.force_demoboard in versionMap:
                log.warn(f'Demoboard detection forced to {self.user_config.force_demoboard}')
                DemoboardDetect.force_detection(versionMap[self.user_config.force_demoboard])
            else:
                log.error(f'Unrecognized force_demoboard setting: {self.user_config.force_demoboard}')
            
            
            
            
        self.pins = Globals.pins(mode=mode)
        
        ports = ['uo_out', 'ui_in', 'uio_in', 'uio_out', 'uio_oe_pico']
        for p in ports:
            setattr(self, p, getattr(self.pins, p))
            
        self.shuttle = Globals.project_mux(self.user_config.force_shuttle)
        
        # config
        self.apply_configs = apply_user_config
        
        # internal
        self.shuttle.design_enabled_callback = self.apply_user_config
        self._clock_pwm = None
        self._clock_pio = None 
        
        self._project_previously_loaded = {}
        self.load_default_project() 
        
        if DemoBoard._DemoBoardSingleton_Instance is None:
            DemoBoard._DemoBoardSingleton_Instance = self 
            # clear-out boot prefix
            logging.LoggingPrefix = None
        
        
    def load_default_project(self):
        if self.user_config.default_project is not None:
            if self.shuttle.has(self.user_config.default_project):
                self.shuttle.get(self.user_config.default_project).enable()
            else:
                log.warn(f'Default project is unknown "{self.user_config.default_project}"')
                
    @property 
    def version(self) -> str:
        '''
            SDK version
        '''
        return ttboard.VERSION
    
    @property 
    def chip_ROM(self):
        '''
        Chip ROM object, e.g. tt.chip_ROM.shuttle
        '''
        return self.shuttle.chip_ROM
    
    @property 
    def mode(self):
        '''
            Current RPMode, e.g. RPMode.ASIC_RP_CONTROL.
            An integer.
            @see: mode_str
        '''
        return self.pins.mode 
    
    @mode.setter 
    def mode(self, setTo:int):
        if self.mode != setTo:
            if self.is_auto_clocking:
                autoClockFreq = self.auto_clocking_freq
                self.clock_project_stop()
                log.warn(f'Was auto-clocking @ {autoClockFreq} but stopping for mode change')
                
        self.pins.mode = setTo 
        
    @property 
    def mode_str(self):
        '''
        Textual representation of current mode.
        E.g.
        >>> tt.mode_str
        'ASIC_RP_CONTROL'
        '''

        return RPMode.to_string(self.mode)
        
    @property 
    def is_auto_clocking(self):
        return self._clock_pwm is not None or (self._clock_pio is not None and self._clock_pio.freq)
    
    @property 
    def auto_clocking_freq(self):
        if not self.is_auto_clocking:
            return 0
        if self._clock_pio is not None and self._clock_pio.freq:
            return self._clock_pio.freq
        
        return self._clock_pwm.freq()
    @property 
    def clk(self):
        '''
            Quick access to project clock pin.
            
            clk(1) # write
            clk.on() # same
            clk.toggle()
            
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
    def rst_n(self):
        '''
            Quick access to project reset pin.
            
            rst_n(1) # write
            rst_n.on() # same
            rst_n.toggle()
            
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
        cur_mode = self.rst_n.mode
        if putInReset:
            if cur_mode != Pins.OUT:
                log.info("Changing reset to output mode")
                self.rst_n.mode = Pins.OUT
            self.rst_n(0) # inverted logic
        else:
            # we don't want it in reset.
            # demoboard has MOM switch and pull-ups to default 
            # it in this way, so we just need to make it an input
            # since this pin is on the MUX, we make certain that 
            # the correct bank is selected by writing to it first
            if cur_mode == Pins.OUT:
                log.debug('Taking out of reset')
                self.rst_n(1) 
            self.rst_n.mode = Pins.IN
            
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
        self.clk.toggle()
        if msDelay > 0:
            time.sleep_ms(msDelay)
        self.clk.toggle()
        
    def _clock_pwm_deinit(self):
        if self._clock_pwm is None:
            return 
        
        self._clock_pwm.deinit()
        self._clock_pwm = None 
        
    def clock_project_PWM(self, freqHz:int, duty_u16:int=(0xffff/2), quiet:bool=False):
        '''
            Start an automatic clock for the selected project (using
            PWM).
            @param freqHz: The frequency of the clocking, in Hz, or 0 to disable PWM
            @param duty_u16: Optional duty cycle (0-0xffff), defaults to 50%  
        '''
        if freqHz > 0:
            self.pins.project_clk_driven_by_RP2040(True)
            
        
        if freqHz <= 0:
            self._clock_pwm_deinit()
            
            if self._clock_pio is not None:
                self._clock_pio.stop()
            return 
        
        if freqHz < 3:
            # make sure we're not PWMing
            self._clock_pwm_deinit()
                
            if self._clock_pio is None:
                self._clock_pio = platform.PIOClock(self.pins.rp_projclk.raw_pin)
            
            self._clock_pio.start(freqHz)
            log.info(f"Clocking at {freqHz}Hz using PIO clock")
        else:
            # make sure we're not PIOing
            if self._clock_pio is not None:
                self._clock_pio.stop()
            try:
                rp2040_sys_clock = self._get_best_rp2040_freq(freqHz)
                platform.set_RP_system_clock(rp2040_sys_clock)
                self._clock_pwm = self.pins.rp_projclk.pwm(freqHz, duty_u16)
            except  Exception as e:
                log.error(f"Could not set project clock PWM: {e}")
                
            actual_freq = self._clock_pwm.freq()
            if abs(actual_freq - freqHz) > 1:
                log.warn(f"Requested {freqHz}Hz clock, actual: {actual_freq}Hz")
            else:
                log.info(f"Clocking at {actual_freq}Hz")
            
        return self._clock_pwm
    
    def clock_project_stop(self):
        '''
            Stop any started automatic project clocking.  No effect 
            if no clocking started.
        '''
        if self.is_auto_clocking:
            log.debug('PWM auto-clock stop')
            self.clock_project_PWM(0)
            self.clk(0) # make certain we are low
        self.pins.project_clk_driven_by_RP2040(False)
        
    def reset_system_clock(self):
        '''
            Reset the RP2040 system clock to value set in config.ini
            if present, or RP2040SystemClockDefaultHz
        '''
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
    
    
    def _get_best_rp2040_freq(self, freq:int, max_rp2040_freq:int=133_000_000):
        # Scan the allowed RP2040 frequency range for a frequency
        # that will divide to the target frequency well
        min_rp2040_freq = 48_000_000
    
        if freq > max_rp2040_freq // 2:
            raise ValueError("Requested frequency too high")
        if freq <= min_rp2040_freq // (2**24 - 1):
            raise ValueError("Requested frequency too low")
    
        best_freq = 0
        best_fracdiv = 2000000000
        best_div = 0
    
        rp2040_freq = min(max_rp2040_freq, freq * (2**24 - 1))
        if rp2040_freq > 136_000_000:
            rp2040_freq = (rp2040_freq // 2_000_000) * 2_000_000
        else:
            rp2040_freq = (rp2040_freq // 1_000_000) * 1_000_000
    
        while rp2040_freq >= 48_000_000 and rp2040_freq >= 1.9 * freq:
            next_rp2040_freq = rp2040_freq - 1_000_000
            if next_rp2040_freq > 136_000_000:
                next_rp2040_freq = rp2040_freq - 2_000_000
    
            # Work out the closest multiple of 2 divisor that could be used
            pwm_divisor = max((rp2040_freq // (2 * freq)) * 2, 2)
            if abs(int(rp2040_freq / pwm_divisor + 0.5) - freq) > abs(
                int(rp2040_freq / (pwm_divisor + 2) + 0.5) - freq
            ):
                pwm_divisor += 2
    
            # Check if the target freq will be acheived
            fracdiv = abs(rp2040_freq / freq - pwm_divisor)
            if freq == rp2040_freq // pwm_divisor:
                return rp2040_freq
            elif fracdiv < best_fracdiv:
                best_fracdiv = fracdiv
                best_freq = rp2040_freq
                best_div = pwm_divisor
    
            rp2040_freq = next_rp2040_freq
    
        if best_fracdiv >= 1.0 / 256:
            print(f"freq_jitter_free={best_freq // best_div}")
    
        return best_freq
    
    
    
    def _first_encouter_reset(self, design:Design):
        if design.name not in self._project_previously_loaded:
            self._project_previously_loaded[design.name] = True
            log.info('First time loading: Toggling project reset')
            self.reset_project(True)
            time.sleep_ms(2)
            self.reset_project(False)
    
    def apply_user_config(self, design:Design):
        '''
            Called by shuttle (project mux) when loading a project.
            Will ensure a sane state and apply any relevant section
            in the config.ini
            
        '''
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
        if projConfig.has('ui_in') and self.mode != RPMode.ASIC_MANUAL_INPUTS:
            btVal = projConfig.ui_in
            log.debug(f'Setting input byte to {btVal}')
            self.ui_in.value = btVal
            
        if projConfig.uio_oe_pico is None:
            # no bidir direction set, ensure all are inputs
            self.uio_oe_pico.value = 0 # all in
        else:
            self.uio_oe_pico.value = projConfig.uio_oe_pico
            log.debug(f'Setting bidir pin direction to {hex(self.uio_oe_pico.value)}')
                    
            if projConfig.uio_in is not None:
                valBits = projConfig.uio_in
                log.debug(f'Also setting bidir byte values {hex(valBits)}')
                for i in range(8):
                    mask = (1 << i) 
                    if (self.uio_oe_pico.value & mask): # this is actually an output
                        if valBits & mask: # and we want it high
                            self.uio_in[i] = 1
                        else: # nah, want it low
                            self.uio_in[i] = 1
                            
        
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
        '''
            Prints out current state of the GPIO
        '''
        print('\n\nDemoboard status')
        print(f'Demoboard default mode is {RPMode.to_string(self.default_mode)}')
        print(f'Project nRESET pin is {self.rst_n.mode_str} {self.rst_n()}')
        
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
        if self.shuttle.enabled is not None and not self.rst_n(): # works whether is input or output
            reset = ' (in RESET)'
            
        shuttle_run = self.shuttle.run
        return f"<DemoBoard in {RPMode.to_string(self.mode)}{autoclocking} {shuttle_run} project '{self.shuttle.enabled}'{reset}>"

    def __setattr__(self, name:str, value):
        if hasattr(self, name) and name in ['ui_in', 'uio_in', 'uio_oe_pico', 'uo_out', 'uio_out']:
            port = getattr(self, name)
            port.value = value 
            return
        super().__setattr__(name, value)