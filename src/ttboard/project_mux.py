'''
Created on Jan 9, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import json
import ttboard.util.time as time
from ttboard.pins import Pins
from ttboard.boot.rom import ChipROM

import ttboard.logging as logging
log = logging.getLogger(__name__)

'''
Fetched with
https://index.tinytapeout.com/tt03p5.json?fields=repo,address,commit,clock_hz
https://index.tinytapeout.com/tt04.json?fields=repo,address,commit,clock_hz

'''
class Design:
    def __init__(self, projectMux, projindex:int, info:dict):
        self.mux = projectMux
        self.project_index = projindex
        self.count = int(projindex)
        self.name = info['macro']
        self.repo = info['repo']
        self.commit = info['commit']
        self.clock_hz = info['clock_hz']
        self._all = info
        
    def enable(self):
        self.mux.enable(self)
        
    def disable(self):
        self.mux.disable()
        
    def __str__(self):
        return self.name 
    
    def __repr__(self):
        return f'<Design {self.project_index}: {self.name}>'
        
class DesignIndex:
    def __init__(self, projectMux,  src_JSON_file:str='shuttle_index.json'):
        self._shuttle_index = dict()
        self._project_count = 0
        try:
            with open(src_JSON_file) as fh:
                index = json.load(fh)
                for project in index["projects"]:
                    des = Design(projectMux, project["address"], project)
                    self._shuttle_index[des.name] = des
                    setattr(self, des.name, des)
                    self._project_count += 1
        except OSError:
            log.error(f'Could not open shuttle index {src_JSON_file}')
             
    
    @property
    def count(self):
        return self._project_count
                
    @property 
    def names(self):
        return self._shuttle_index.keys()
    
    @property 
    def all(self):
        return self._shuttle_index.values()
    
    def get(self, project_name:str) -> Design:
        return self._shuttle_index[project_name]
                
        
class ProjectMux:
    def __init__(self, pins:Pins, shuttle_index_file:str=None):
        self.p = pins 
        self._design_index = None
        self.enabled = None
        self.design_enabled_callback = None
        self.shuttle_index_file = shuttle_index_file
        self._chip_rom = None
    
    def reset(self):
        log.debug('Resetting project mux')
        self.p.cinc(0)
        self.p.ncrst(0)
        self.p.cena(0)
        time.sleep_ms(10)
        self.p.ncrst(1)
        time.sleep_ms(10)
        self.enabled = None
        
    def disable(self):
        log.info(f'Disable (selecting project 0)')
        self.reset_and_clock_mux(0)
        self.enabled = None
        
    def enable(self, design:Design):
        
        log.info(f'Enable design {design.name}')
        self.reset_and_clock_mux(design.count)
        self.enabled = design
        if self.design_enabled_callback is not None:
            self.design_enabled_callback(design)
            
    
    def reset_and_clock_mux(self, count:int):
        self.p.safe_bidir() # reset bidirectionals to safe mode
        
        # enable admin pins through hw mux
        self.p.muxCtrl.mode_admin() 
        
        self.reset()
        # send the number of pulses required
        for _c in range(count):
            self.p.cinc(1)
            time.sleep_ms(1)
            self.p.cinc(0)
            time.sleep_ms(1)
        
        self.p.cena(1)
        self.p.muxCtrl.mode_project_IO() 
        
    @property 
    def pins(self) -> Pins:
        return self.p
    
    @property 
    def chip_ROM(self) -> ChipROM:
        if self._chip_rom is None:
            self._chip_rom = ChipROM(self)
        
        return self._chip_rom
    
    @property 
    def run(self) -> str:
        '''
            The shuttle run, eg 'tt04'
        '''
        return self.chip_ROM.shuttle
    
    
    @property 
    def factory_test(self) -> Design:
        try:
            shuttle = self.chip_ROM.shuttle
            if  shuttle == 'tt03p5':
                return self.tt_um_test
            return self.tt_um_factory_test
        
        except:
            pass 
        return None
            
    @property
    def projects(self):
        if self._design_index is None:
            if self.shuttle_index_file is None:
                log.debug('No shuttle index file specified, loading rom')
                rom = self.chip_ROM
                log.info(f'Chip reported by ROM is {rom.shuttle} commit {rom.commit}')
                shuttle_file = f'/shuttles/{rom.shuttle}.json'
                self.shuttle_index_file = shuttle_file
                
            
            log.info(f'Loading shuttle file {self.shuttle_index_file}')
                
            self._design_index = DesignIndex(self, src_JSON_file=self.shuttle_index_file)

        return self._design_index
    
    
    def has(self, project_name:str):
        return hasattr(self.projects, project_name)
    
    def get(self, project_name:str) -> Design:
        return getattr(self.projects, project_name)
    
    def __getattr__(self, name):
        if hasattr(self.projects, name):
            return getattr(self.projects, name)
        raise AttributeError
        