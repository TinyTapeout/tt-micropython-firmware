'''
Created on Jan 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import gc
from ttboard.config.parser import ConfigParser
from ttboard.mode import RPMode

import ttboard.log as logging
log = logging.getLogger(__name__)


class UserProjectConfig:
    '''
        Configuration specific to a project, held in a section with the 
        project's shuttle name, e.g.
        
            [tt_um_psychogenic_neptuneproportional]
            # set clock to 4kHz
            clock_frequency = 4000
            # clock config 4k, disp single bits
            ui_in = 0b11001000
            mode = ASIC_RP_CONTROL
        
        You can use this to set:
            - mode (str)
            - start_in_reset (bool)
            - ui_in (int)
            - uio_oe_pico (int)
            - uio_in (int)
            - clock_frequency (int) project clock
            - rp_clock_frequency (int) RP2040 system clock frequency
            
        all keys are optional.
        
        A repr function lets you see the basics, do a print(tt.user_config.tt_um_someproject) to
        see more info.

    '''
    opts = ['mode', 'start_in_reset', 'ui_in',
                         'uio_oe_pico',
                         'uio_in',
                         'clock_frequency',
                         'rp_clock_frequency']
    
    
    def __init__(self, section:str, conf:ConfigParser):
        self.name = section
        for opt in self.opts:
            val = None
            if conf.has_option(section, opt):
                val = conf.get(section, opt)
            
            setattr(self, opt, val)
            
    
    def has(self, name:str):
        return self.get(name) is not None
    
    def get(self, name:str):
        if not hasattr(self, name):
            return None 
        
        return getattr(self, name)
    
    def _properties_dict(self, include_unset:bool=False):
        ret = dict()
        known_attribs = self.opts
        for atr in known_attribs:
            v = self.get(atr)
            if v is not None or include_unset:
                ret[atr] = v
        
        return ret

    def __repr__(self):
        props = self._properties_dict(True)
        return f'<UserProjectConfig {self.name}, {props["clock_frequency"]}Hz, mode: {props["mode"]}>'
    
    def __str__(self):
        property_strs = []
        pdict = self._properties_dict()
        for k in sorted(pdict.keys()):
            property_strs.append(f'  {k}: {pdict[k]}')
        
        properties = '\n'.join(property_strs)
        return f'{self.name}\n{properties}'

class UserConfig:
    '''
        Encapsulates the configuration for defaults and all the projects, in sections.
        The DEFAULT section holds system wide defaults and the default project to load
        on startup.
        
        DEFAULT section may have
        
            # project: project to load by default
            project = tt_um_test
            
            # start in reset (bool)
            start_in_reset = no
            
            # mode can be any of
            #  - SAFE: all RP2040 pins inputs
            #  - ASIC_RP_CONTROL: TT inputs,nrst and clock driven, outputs monitored
            #  - ASIC_MANUAL_INPUTS: basically same as safe, but intent is clear
            mode = ASIC_RP_CONTROL
            
            # log_level can be one of
            #  - DEBUG
            #  - INFO
            #  - WARN
            #  - ERROR
            log_level = INFO
            
            
            # force_shuttle
            # by default, system attempts to figure out which ASIC is on board
            # using the chip ROM.  This can be a problem if you have something
            # connected to the demoboard.  If you want to bypass this step and
            # manually set the shuttle, uncomment this and set the option to
            # a valid shuttle
            # force_shuttle = tt05
            force_shuttle = tt04
            
            
            # force_demoboard
            # System does its best to determine the version of demoboard 
            # its running on.  Override this with 
            # force_demoboard = tt0*
            force_demoboard = tt06
            
            
        Each project section is named [SHUTTLE_PROJECT_NAME]
        and will be an instance of, and described by, UserProjectConfig
    '''
    
    def __init__(self, ini_filepath:str='config.ini'):
        self.inifile_path = ini_filepath 
        conf = ConfigParser()
        conf.read(ini_filepath)
        self._proj_configs = dict()
        for section in conf.sections():
            if section == 'DEFAULT':
                continue 
            self._proj_configs[section] = None # UserProjectConfig(section, conf)
            
            
        def_opts = ['mode', 'project', 'start_in_reset', 'rp_clock_frequency', 'force_shuttle', 'force_demoboard']
        for opt in def_opts:
            val = None
            if conf.has_option('DEFAULT', opt):
                val = conf.get('DEFAULT', opt)
            setattr(self, f'_{opt}', val)
            
            
        conf = None 
        gc.collect()
    
    
        
    def _get_default_option(self, name:str, def_value=None):
        v = getattr(self, f'_{name}')
        if v is None:
            return def_value 
        return v
    @property 
    def filepath(self):
        return self.inifile_path
    @property 
    def default_mode(self):
        mode_str = self._get_default_option('mode')
        if mode_str is None:
            return None 
        
        return RPMode.from_string(mode_str)
        
    @property
    def default_project(self):
        return self._get_default_option('project')
    
    @property 
    def default_start_in_reset(self):
        return self._get_default_option('start_in_reset')
    
    @property 
    def default_rp_clock(self):
        return self._get_default_option('rp_clock_frequency')
    
    @property 
    def force_shuttle(self):
        return self._get_default_option('force_shuttle')
        
    
    @property 
    def force_demoboard(self):
        return self._get_default_option('force_demoboard')
        
    def has_project(self, name:str):
        if name in self._proj_configs:
            return True 
        return False 
    
    def project(self, name:str):
        if not self.has_project(name):
            return None 
        
        if self._proj_configs[name] is None:
            conf = ConfigParser()
            conf.read(self.inifile_path)
            self._proj_configs[name] = UserProjectConfig(name, conf)
            conf = None 
            gc.collect()
        return self._proj_configs[name]
    
    def __getattr__(self, name):
        if self.has_project(name):
            return self.project(name)
    
    @property 
    def sections(self):
        return list(self._proj_configs.keys())
    
    def __dir__(self):
        return self.sections
    
    def __repr__(self):
        return f'<UserConfig {self.filepath}, default project: {self.default_project}>'
    
    def __str__(self):
        def_mode = self._get_default_option('mode')
        section_props = '\n'.join(map(lambda psect: str(self.project(psect)), 
                                 filter(lambda s: s != 'DEFAULT', self.sections)))
        return f'UserConfig {self.filepath}, Defaults:\nproject: {self.default_project}\nmode: {def_mode}\n{section_props}'
    
        