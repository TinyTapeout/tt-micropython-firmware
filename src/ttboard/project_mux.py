'''
Created on Jan 9, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import json
import re 
import ttboard.util.time as time
from ttboard.pins import Pins
from ttboard.boot.rom import ChipROM
from ttboard.boot.shuttle_properties import HardcodedShuttle
import ttboard.logging as logging
log = logging.getLogger(__name__)

'''
Fetched with
https://index.tinytapeout.com/tt03p5.json?fields=repo,address,commit,clock_hz,title
https://index.tinytapeout.com/tt04.json?fields=repo,address,commit,clock_hz,title

'''
class Design:
    BadCharsRe = re.compile(r'[^\w\d\s]+')
    SpaceCharsRe = re.compile(r'\s+')
    def __init__(self, projectMux, projindex:int, info:dict):
        self.mux = projectMux
        self.project_index = projindex
        self.count = int(projindex)
        self.macro = info['macro']
        self.name = info['macro']
        self.repo = info['repo']
        self.commit = info['commit']
        self.clock_hz = info['clock_hz']
        # special cleanup for wokwi gen'ed names
        if self.name.startswith('tt_um_wokwi') and 'title' in info and len(info['title']):
            new_name = self.SpaceCharsRe.sub('_', self.BadCharsRe.sub('', info['title'])).lower()
            if len(new_name):
                self.name = f'wokwi_{new_name}'
        
        self._all = info
        
    def enable(self):
        self.mux.enable(self)
        
    def disable(self):
        self.mux.disable()
        
    def __str__(self):
        return f'{self.name} ({self.project_index}) @ {self.repo}'
    
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
                    attrib_name = des.name
                    if attrib_name in self._shuttle_index:
                        log.info(f'Already have a "{attrib_name}" here...')
                        attempt = 1
                        augmented_name = f'{attrib_name}_{attempt}'
                        while augmented_name in self._shuttle_index:
                            attempt += 1
                            augmented_name = f'{attrib_name}_{attempt}'
                        
                        attrib_name = augmented_name
                        des.name = augmented_name
                    self._shuttle_index[attrib_name] = des
                    setattr(self, attrib_name, des)
                    self._project_count += 1
        except OSError:
            log.error(f'Could not open shuttle index {src_JSON_file}')
             
    
    @property
    def count(self):
        return self._project_count
                
    @property 
    def names(self):
        return sorted(self._shuttle_index.keys())
    
    @property 
    def all(self):
        return sorted(self._shuttle_index.values(), key=lambda p: p.name)
    
    def get(self, project_name:str) -> Design:
        if project_name in self._shuttle_index:
            return self._shuttle_index[project_name]
        
        # maybe it's an integer?
        try: 
            des_idx = int(project_name)
            for des in self.all:
                if des.count == des_idx:
                    return des 
        except ValueError:
            pass 
        
        raise ValueError(f'Unknown project "{project_name}"')
        
    def __len__(self):
        return len(self._shuttle_index)
    
    def __getitem__(self, idx:int) -> Design:
        return self.get(idx)
                
    def __repr__(self):
        return f'<DesignIndex {len(self)} projects>'
        
class ProjectMux:
    '''
        Interface to list and load projects, appears as 
        tt.shuttle
        
        Can do 
            tt.shuttle.tt_um_whatevername.enable()
            tt.shuttle[projectindex].enable()
        and 
            tt.shuttle.enabled
            to see which project is currently enabled.
    
    '''
    @classmethod 
    def indexfile_for_shuttle(cls, shuttle_name:str):
        return f'/shuttles/{shuttle_name}.json'
    
    
    def __init__(self, pins:Pins, shuttle_run:str=None):
        self.p = pins 
        self._design_index = None
        self.enabled = None
        self.design_enabled_callback = None
        self._shuttle_props = None
        if shuttle_run is not None:
            log.info(f'shuttle run hardcoded to "{shuttle_run}"')
            self._shuttle_props = HardcodedShuttle(shuttle_run)
    
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
        if self.p.demoboard_uses_mux:
            # enable admin pins through hw mux
            self.p.muxCtrl.mode_admin() 
            
        self.p.cena(0)
        # let's stay in admin mode from here
        # so we're actually holding this ena low
        # as we were directed
        #if self.p.demoboard_uses_mux:
        #    self.p.muxCtrl.mode_project_IO()
        
        self.enabled = None
        
    def enable(self, design:Design):
        log.info(f'Enable design {design.name}')
        self.reset_and_clock_mux(design.count)
        self.enabled = design
        if self.design_enabled_callback is not None:
            self.design_enabled_callback(design)
            
    
    def reset_and_clock_mux(self, count:int):
        self.p.safe_bidir() # reset bidirectionals to safe mode
        
        if self.p.demoboard_uses_mux:
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
        if self.p.demoboard_uses_mux:
            self.p.muxCtrl.mode_project_IO() 
        
    @property 
    def pins(self) -> Pins:
        return self.p
    
    @property 
    def chip_ROM(self) -> ChipROM:
        if self._shuttle_props is None:
            log.debug('No shuttle specified, loading rom')
            self._shuttle_props = ChipROM(self)
        
        return self._shuttle_props
    
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
            self.shuttle_index_file = self.indexfile_for_shuttle(self.run)
            log.info(f'Loading shuttle file {self.shuttle_index_file}')
                
            self._design_index = DesignIndex(self, src_JSON_file=self.shuttle_index_file)

        return self._design_index
    
    def has(self, project_name:str):
        return hasattr(self.projects, project_name)
    
    def get(self, project_name:str) -> Design:
        return getattr(self.projects, project_name)
    
    def find(self, search:str) -> list:
        return list(filter(lambda p: p.name.find(search) >= 0,  self.all))
    
    def __getattr__(self, name):
        if hasattr(self, 'projects') and hasattr(self.projects, name):
            return getattr(self.projects, name)
        raise AttributeError(f"What is '{name}'?")
    
    def __getitem__(self, key) -> Design:
        if hasattr(self, 'projects'):
            return self.projects[key]
        raise None
    
    
    def __str__(self):
        return f'Shuttle {self.run}\n{self.all}'
    
    def __repr__(self):
        des_idx = self.projects
        return f'<ProjectMux for {self.run} with {len(des_idx)} projects>'
        