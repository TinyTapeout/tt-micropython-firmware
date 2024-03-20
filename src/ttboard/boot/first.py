'''
Created on Mar 20, 2024

First boot management
This class is used to:
 * detect "first boot" (by presence of FirstBootIniFile, '/first_boot.ini')
 * run tests as specified
 * optionally clear out the first boot init file

The ini file has 4 types of section
[DEFAULT] -- just basic defaults
and 3 others, which all have
 - an optional message, to print out
 - a command, an operation to run
 
[setup] will execute the operation
[run_*] (any number of sections) will run tests, having access to a DemoBoard instance
[onsuccess] assuming all tests are valid, if this section is present the command
can let the system know it should clear out the ini file.

The message is a simple string.
The command is actual evaluated python, however this must be 
  * a function call
  * for a function defined in ttboard.boot.firstboot_operations

[run_*] sections will be executed in alphanumeric sort order.


@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import os
import ttboard.util.platform
import ttboard.util.time as time
from ttboard.config.config_file import ConfigFile
from ttboard.demoboard import DemoBoard
import ttboard.boot.firstboot_operations as fbops

import ttboard.logging as logging
log = logging.getLogger(__name__)

class FirstBootConfig(ConfigFile):
    '''
        Wrapper for the first_boot.ini config file
    '''
    pass

class FirstBootOperation:
    '''
        An executable section from the first boot ini file.
    '''
    def __init__(self, section_name:str, config:FirstBootConfig):
        self.section = section_name 
        self._config = config 
        self.ttdemoboard = None
        self.operation_return_value = None
        
    def has(self, option_name:str):
        return self._config.has_option(self.section, option_name)
    def get(self, option_name:str):
        return self._config.get(self.section, option_name)
    
    def execute(self, run_context:dict) -> bool:
        log.debug(f'Executing {self.section}')
        if not self.has('command'):
            log.warn('No command present')
            return False 
        cmd = self.get('command')
        demoboard = self.ttdemoboard
        try:
            self.operation_return_value = eval(f'fbops.{cmd}', {'fbops':fbops, 
                                                                'demoboard':demoboard, 
                                                                'context':run_context})
        except:
            log.error(f"Error executing {cmd}")
            return False 
        
        return True

class SetupOperation(FirstBootOperation):
    pass 

class RunOperation(FirstBootOperation):
    def __init__(self, demoboard:DemoBoard, section_name:str, config:FirstBootConfig):
        super().__init__(section_name, config)
        self.ttdemoboard = demoboard
        
        
class FirstBoot:
    '''
        The system level manager for first boot functionality
    '''
    
    FirstBootIniFile = '/first_boot.ini'
    
    @classmethod
    def is_first_boot(cls):
        return ttboard.util.platform.isfile(cls.FirstBootIniFile)
            
    @classmethod 
    def initialize(cls):
        fb = cls(cls.FirstBootIniFile)
        if not fb.ready:
            print("ERROR: you shouldn't be calling initialize without an ini file")
            return False 
        
        return fb.run()
        
         
    
    
    def __init__(self, ini_file:str):
        self._config = FirstBootConfig(ini_file)
        self._ready = self._config.is_loaded
        if not self._ready:
            log.error(f'Issue reading {ini_file}')
        else:
            log_level = self.config.log_level
            if log_level is not None:
                logging.basicConfig(level=log_level)
                log.info(f'Set log_level to {log_level}')
            
            
    @property 
    def ready(self):
        return self._ready
    
    @property 
    def config(self) -> ConfigFile:
        return self._config
    
    def run(self):
        abort_runs_on_err = False
        if self.config.has_option('DEFAULT', 'abort_runs_on_error'):
            abort_runs_on_err = self.config.get('DEFAULT', 'abort_runs_on_error')
            
        if self.config.has_option('DEFAULT', 'startup_delay_ms'):
            startup_delay_ms = self.config.get('DEFAULT', 'startup_delay_ms')
            if startup_delay_ms > 0:
                time.sleep_ms(startup_delay_ms)
                log.info(f'Delayed startup by {startup_delay_ms}ms')
        
        context = {'tests':dict()}
        if self.config.has_section('setup'):
            if not SetupOperation('setup', self.config).execute(context):
                log.error('Could not execute setup -- abort!')
                return False
            
        demoboard = DemoBoard()
        num_fails = 0
        keep_running_tests = True
        for section in sorted(self.config.sections):
            if keep_running_tests and section.startswith('run_'):
                context['tests'][section] = True
                if not RunOperation(demoboard, section, self.config).execute(context):
                    log.error(f'Execution of {section} failed')
                    context['tests'][section] = False
                    num_fails += 1
                    if abort_runs_on_err:
                        log.error(f'And abort_runs_on_error is set, aborting.')
                        keep_running_tests = False
                    
        if num_fails:
            if self.config.has_section('onfail'):
                RunOperation(demoboard, 'onfail', self.config).execute(context)
            return False
    
        if self.config.has_section('onsuccess'):
            should_delete_op = RunOperation(demoboard, 'onsuccess', self.config)
            if not should_delete_op.execute(context):
                log.error('Could not execute onsuccess???')
                return False
            
            if should_delete_op.operation_return_value:
                log.warn("First boot is done: unlinking fb config")
                os.unlink(self.FirstBootIniFile)
            
        return True
            
            
                
                    
                
        