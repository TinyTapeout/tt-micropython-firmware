'''
Created on Jan 22, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from ttboard.config.parser import ConfigParser
from ttboard.mode import RPMode

import ttboard.logging as logging
log = logging.getLogger(__name__)

class UserProjectConfig:
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

    

class UserConfig:
    def __init__(self, iniFile:str='config.ini'):
        self._inifile = iniFile 
        self._config = ConfigParser()
        self.load(iniFile)
        
    def load(self, file:str):
        try:
            self._config.read(file)
            log.info(f'Loaded config {file}')
        except: # no FileNotFoundError on uPython
            log.warn(f'Could not load config file {file}')
        
    @property 
    def config(self):
        return self._config
    
    @property 
    def default_mode(self):
        if not self.config.has_option('DEFAULT', 'mode'):
            return None 
        
        modeStr = self.config.get('DEFAULT', 'mode')
        return RPMode.from_string(modeStr)
        
    @property
    def default_project(self):
        if self.config.has_option('DEFAULT', 'project'):
            return self.config.get('DEFAULT', 'project')
        return None
    
    @property 
    def default_start_in_reset(self):
        if self.config.has_option('DEFAULT', 'start_in_reset'):
            return self.config.get('DEFAULT', 'start_in_reset')
        return None
        
    
    def has_project(self, name:str):
        if self.config.has_section(name):
            return True 
        return False 
    
    def project(self, name:str):
        if not self.has_project(name):
            return None 
        
        return UserProjectConfig(name, self.config)
    
    
        