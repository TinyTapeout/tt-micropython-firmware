'''
Created on Mar 20, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from ttboard.config.parser import ConfigParser

import ttboard.logging as logging
log = logging.getLogger(__name__)

class ConfigFile:
    
    @classmethod 
    def string_to_loglevel(cls, loglevname:str):
        conv_map = {
                'debug': logging.DEBUG,
                'info': logging.INFO,
                'warn': logging.WARN,
                'warning': logging.WARN,
                'error': logging.ERROR
            }
        
        if loglevname.lower() in conv_map:
            return conv_map[loglevname.lower()]
        
        return None
    
    def __init__(self, ini_file:str):
        self._inifile_path = ini_file 
        self._ini_file = ConfigParser()
        self._ini_file_loaded = False
        self.load(ini_file)
        
    def load(self, filepath:str):
        self._inifile_path = filepath 
        self._ini_file_loaded = False
        try:
            self._ini_file.read(filepath)
            self._ini_file_loaded = True
            log.info(f'Loaded config {filepath}')
        except: # no FileNotFoundError on uPython
            log.warn(f'Could not load config file {filepath}')
    
    @property 
    def is_loaded(self):
        return self._ini_file_loaded
    
    @property 
    def ini_file(self) -> ConfigParser:
        return self._ini_file
    
    @property 
    def sections(self):
        return self.ini_file.sections()
    
    def has_section(self, section_name:str) -> bool:
        return self.ini_file.has_section(section_name)
    
    def has_option(self, section_name:str, option_name:str) -> bool:
        return self.ini_file.has_option(section_name, option_name)
    
    def get(self, section_name:str, option_name:str):
        return self.ini_file.get(section_name, option_name)
        
    @property 
    def log_level(self):
        if not self.ini_file.has_option('DEFAULT', 'log_level'):
            return None 
        
        levstr = self.ini_file.get('DEFAULT', 'log_level')
        return self.string_to_loglevel(levstr)
    
    