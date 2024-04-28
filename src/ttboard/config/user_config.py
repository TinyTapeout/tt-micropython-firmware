'''
Created on Jan 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.config.parser import ConfigParser
from ttboard.mode import RPMode
from ttboard.config.config_file import ConfigFile

import ttboard.logging as logging
log = logging.getLogger(__name__)

class UserProjectConfig:
    '''
        Configuration specific to a project, held in a section with the 
        project's shuttle name, e.g.
        
            [tt_um_psychogenic_neptuneproportional]
            # set clock to 4kHz
            clock_frequency = 4000
            # clock config 4k, disp single bits
            input_byte = 0b11001000
            mode = ASIC_RP_CONTROL
        
        You can use this to set:
            - mode (str)
            - start_in_reset (bool)
            - input_byte (int)
            - bidir_direction (int)
            - bidir_byte (int)
            - clock_frequency (int) project clock
            - rp_clock_frequency (int) RP2040 system clock frequency
            
        all keys are optional.
        
        A repr function lets you see the basics, do a print(tt.user_config.tt_um_someproject) to
        see more info.

    '''
    def __init__(self, section:str, conf:ConfigParser):
        self.section = section 
        self._config = conf 
        
    @property
    def config(self):
        return self._config
    

    
    def has(self, name:str):
        return  self.config.has_option(self.section, name)
    
    def get(self, name:str):
        if not self.has(name):
            return None 
        return self.config.get(self.section, name)
    

    def __getattr__(self, name):
        return self.get(name)
    
    def _properties_dict(self, include_unset:bool=False):
        ret = dict()
        known_attribs = ['mode', 'start_in_reset', 'input_byte',
                         'bidir_direction',
                         'bidir_byte',
                         'clock_frequency',
                         'rp_clock_frequency'
                         ]
        for atr in known_attribs:
            v = self.get(atr)
            if v is not None or include_unset:
                ret[atr] = v
        
        return ret

    def __repr__(self):
        props = self._properties_dict(True)
        return f'<UserProjectConfig {self.section}, {props["clock_frequency"]}Hz, mode: {props["mode"]}>'
    
    def __str__(self):
        property_strs = []
        pdict = self._properties_dict()
        for k in sorted(pdict.keys()):
            property_strs.append(f'  {k}: {pdict[k]}')
        
        properties = '\n'.join(property_strs)
        return f'{self.section}\n{properties}'

class UserConfig(ConfigFile):
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
        Each project section is named [SHUTTLE_PROJECT_NAME]
        and will be an instance of, and described by, UserProjectConfig
    '''
    
    def __init__(self, ini_filepath:str='config.ini'):
        super().__init__(ini_filepath)
        
    def _get_default_option(self, name:str, def_value=None):
        if not self.has_option('DEFAULT', name):
            return def_value 
        return self.get('DEFAULT', name)
    
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
        
    
    def has_project(self, name:str):
        if self.has_section(name):
            return True 
        return False 
    
    def project(self, name:str):
        if not self.has_project(name):
            return None 
        
        return UserProjectConfig(name, self.ini_file)
    
    def __getattr__(self, name):
        if name in self.sections:
            return self.project(name)
    
    def __dir__(self):
        return self.sections
    def __repr__(self):
        return f'<UserConfig {self.filepath}, default project: {self.default_project}>'
    
    def __str__(self):
        def_mode = self._get_default_option('mode')
        section_props = '\n'.join(map(lambda psect: str(self.project(psect)), 
                                 filter(lambda s: s != 'DEFAULT', self.sections)))
        return f'UserConfig {self.filepath}, Defaults:\nproject: {self.default_project}\nmode: {def_mode}\n{section_props}'
    
        