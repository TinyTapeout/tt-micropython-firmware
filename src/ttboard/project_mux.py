'''
Created on Jan 9, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import json
import ttboard.util.time as time
from ttboard.pins import Pins

import ttboard.logging as logging
log = logging.getLogger(__name__)

class Design:
    def __init__(self, projectMux, projindex:int, info:dict):
        self.mux = projectMux
        self.project_index = projindex
        self.count = int(projindex)
        self.name = info['macro']
        self.repo = info['repo']
        self.commit = info['commit']
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
    def __init__(self, projectMux,  srcJSONFile:str='shuttle_index.json'):
        self._shuttle_index = dict()
        self._project_count = 0
        with open(srcJSONFile) as fh:
            index = json.load(fh)
            for project in index["mux"]:
                des = Design(projectMux, project, index["mux"][project])
                self._shuttle_index[des.name] = des
                setattr(self, des.name, des)
                self._project_count += 1
             
    
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
    def __init__(self, pins:Pins):
        self.p = pins 
        self._design_index = None
        self.enabled = None
        self.designEnabledCallback = None
    
    def reset(self):
        log.debug('Resetting project mux')
        self.p.cinc(0)
        self.p.ncrst(0)
        self.p.ctrl_ena(0)
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
        if self.designEnabledCallback is not None:
            self.designEnabledCallback(design)
            
    
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
        
        self.p.ctrl_ena(1)
        self.p.muxCtrl.mode_project_IO() 
        
    @property
    def projects(self):
        if self._design_index is None:
            self._design_index = DesignIndex(self)

        return self._design_index
    
    
    def has(self, project_name:str):
        return hasattr(self.projects, project_name)
    
    def get(self, project_name:str) -> Design:
        return getattr(self.projects, project_name)
    
    def __getattr__(self, name):
        if hasattr(self.projects, name):
            return getattr(self.projects, name)
        raise AttributeError
        