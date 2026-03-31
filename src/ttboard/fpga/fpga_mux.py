'''
Created on Aug 25, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import os
from ttboard.boot.shuttle_properties import HardcodedShuttle
import ttboard.log as logging
log = logging.getLogger(__name__)
import ttboard.fpga.fabricfoxv2 as fpgaloader
class BitStream:
    def __init__(self, loader, filepath:str, name:str, clock_hz:int=100):
        self._filepath = filepath
        self._name = name
        self._loader = loader
        self._clock_hz = clock_hz
    
    @property 
    def name(self):
        return self._name
    @property 
    def file(self):
        return self._filepath
    
    def enable(self, force:bool=False):
        self._loader.enable(self, force)
        
    @property 
    def clock_hz(self):
        return self._clock_hz
    
    def __repr__(self):
        return f'<FPGA BitStream {self.name}>'
    def __str__(self):
        return f'FPGA:{self.name}'
    
class BitStreamIndex:
    def __init__(self, loader, dirpath:str):
        self._dirpath = dirpath 
        self._streams_by_name = {}
        try:
            for f in os.listdir(dirpath):
                if f.endswith('.bin'):
                    short_name = f.replace('.bin', '')
                    bs = BitStream(loader, f'{dirpath}/{f}', short_name)
                    self._streams_by_name[short_name] = bs
                    setattr(self, short_name, bs)
        except:
            pass
                
    def is_available(self, name:str):
        return  name in self._streams_by_name
    
    def get(self, name:str):
        return self._streams_by_name[name]
        
    def __len__(self):
        return len(list(self._streams_by_name.keys()))
    

class FPGAMux:
    '''
        Interface to list and load fpga bitstreams 
        tt.shuttle
        
        Can do 
            tt.shuttle.mystream.enable()
            tt.shuttle.enabled
            to see which project is currently enabled.
    
    '''
    def __init__(self, pins, bitstream_dir:str='/bitstreams'):
        self._bitstream_dir = bitstream_dir
        self.p = pins
        self.enabled = None
        self.design_enabled_callback = None
        self._shuttle_props = HardcodedShuttle('FPGA')
        self._design_index = None
        
    def reset(self):
        self.enabled = None
        
    def disable(self):
        self.reset_and_clock_mux(0)
        self.enabled = None
        
    def enable(self, design:BitStream, force:bool=False):
        log.info(f'Enable design {design.name}')
        self.reset_and_clock_mux()
        self.enabled = design
        
        fpgaloader.spi_transferPIO(design.file)
        
        if self.design_enabled_callback is not None:
            self.design_enabled_callback(design)
            
        return True
            
    
    def reset_and_clock_mux(self, count:int=None):
        self.p.safe_bidir() # reset bidirectionals to safe mode
        
        self.reset()
        
    @property 
    def run(self) -> str:
        return 'FPGA'
    
    
            
    @property
    def projects(self):
        
        if self._design_index is None:
            self._design_index = BitStreamIndex(self, self._bitstream_dir)

        return self._design_index
    
    def has(self, project_name:str):
        return self.projects.is_available(project_name)
    
    def get(self, project_name:str) -> BitStream:
        return self.projects.get(project_name)
    
    
    def find(self, search:str) -> list:
        return self.projects.find(search)
    
    def __getattr__(self, name):
        if hasattr(self, 'projects'):
            if self.projects.is_available(name) or hasattr(self.projects, name):
                return getattr(self.projects, name)
        raise AttributeError(f"What is '{name}'?")
    
    def __len__(self):
        return len(self.projects)
    
    def __str__(self):
        return f'Shuttle FPGA'
    
    def __repr__(self):
        des_idx = self.projects
        return f'<ProjectMux for FPGA with {len(des_idx)} projects>'
    