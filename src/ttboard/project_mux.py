'''
Created on Jan 9, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com

TODO: This code is now a mess of history
The JSON is used, in github actions, to produce the bin
but it should be refactored into a common baseclass and 
two implementations, one that only ever gets used as 
a fallback and in the UF2 creation.
'''

import json
import re 
import gc
import os
import ttboard.util.time as time
from ttboard.pins.pins import Pins
from ttboard.boot.rom import ChipROM
from ttboard.boot.shuttle_properties import HardcodedShuttle
import ttboard.log as logging
from ttboard.project_design import Serializable, DangerLevel, Design, DesignStub
log = logging.getLogger(__name__)

StrictMemorySaving = False
'''
Fetched with
https://index.tinytapeout.com/tt0X.json?fields=address,clock_hz,title,dange_field

'''
   
class DesignIndex(Serializable):
    SerializedBinSuffix = 'bin'
    BadCharsRe = re.compile(r'[^\w\d\s]+')
    SpaceCharsRe = re.compile(r'\s+')
    
    def __init__(self, projectMux,  src_JSON_file:str=None):
        self._src_json = src_JSON_file
        self._src_serialized_bin = None
        self._project_mux = projectMux
        self._num_projects = 0
        if src_JSON_file is not None:
            self.load_available(src_JSON_file)
        
        
    def serialized_bin_file(self, src_JSON_file):
        serialized_fpath = f'{src_JSON_file}.{self.SerializedBinSuffix}'
        
        try:
            # no os.path on this dumb thing...
            os.stat(serialized_fpath)
        except OSError:
            return None 
        
        return serialized_fpath
        
    def load_serialized(self, serialized_fpath):
        self._src_serialized_bin = serialized_fpath
        if self.from_bin_file(serialized_fpath):
            return True
        
    def load_available(self, src_JSON_file:str=None, force_json:bool=False):
        if src_JSON_file is None:
            if self._src_json is None:
                self._src_json = 'NEVERSET.json'
                return
            src_JSON_file = self._src_json
        else:
            self._src_json = src_JSON_file
        if not force_json:
            binfpath = self.serialized_bin_file(src_JSON_file)
            if binfpath is not None and self.load_serialized(binfpath):
                self._src_serialized_bin = binfpath
                return 
        try:
            with open(src_JSON_file) as fh:
                index = json.load(fh)
                self._num_projects = 0
                for project in index['projects']:
                    project_address = int(project['address'])
                    attrib_name = self.clean_project_name(project)
                    des = Design(self._project_mux, attrib_name, project_address, project)
                    setattr(self, attrib_name, des)
                    self._num_projects += 1
                index = None
        except OSError:
            log.error(f'Could not open shuttle index {src_JSON_file}')
            
        gc.collect()
            
             
    def clean_project_name(self, project:dict):
        attrib_name = project['macro']
        attrib_name = self._wokwi_name_cleanup(attrib_name, project)
            
        return self.serializable_string(attrib_name)
    
        
    def _wokwi_name_cleanup(self, name:str, info:dict):
        # special cleanup for wokwi gen'ed names
        if name.startswith('tt_um_wokwi') and 'title' in info and len(info['title']):
            new_name = self.SpaceCharsRe.sub('_', self.BadCharsRe.sub('', info['title'])).lower()
            if len(new_name):
                name = f'wokwi_{new_name}_{name[-3:]}'
        
        return name 
    @property
    def count(self):
        return self._num_projects
    
    
    def _get_design_attribs(self) -> list:
        
        badlist = ['all', 'names']
        m =  map(lambda x: getattr(self, x), 
                 filter( lambda x: x not in badlist,
                         filter( lambda x: not x.startswith('_'), self.__dict__.keys())))
        des_attribs = list(filter(lambda x: isinstance(x, (Design, DesignStub)), m))
        return des_attribs
    
    
    @property 
    def all(self):
        '''
            all available projects in the shuttle, whether loaded or not 
        '''
        if StrictMemorySaving and self._src_serialized_bin:
            return []
        
        des_attribs = self._get_design_attribs()
        return sorted(des_attribs, key=lambda x: x.count)
    
    
    def find(self, search:str) -> list:
        if self._src_serialized_bin:
            # we can never be certain we have them all loaded as 
            # Design (rather than DesignStub), so scan the whole file,
            # just the once (rather than repeatedly if lazyloading stubs)
            return self.deserialize_find_names(self._src_serialized_bin, search)
        
        return list(filter(lambda p: p.name.find(search) >= 0,  self.all))
    
    
    def get(self, project_name:str) -> Design:
        # not in list of available, maybe it's an integer?
        if isinstance(project_name, int):
            str_name = self.project_name(project_name)
            if str_name is not None:
                return self.get(str_name)
            else:
                return self.load_project(project_name)
                raise AttributeError(f'No project @ address "{project_name}"') 
            
        if hasattr(self, project_name):
            return getattr(self, project_name)
        
        return self.load_project(project_name)
        
        
    def load_all(self, max_allowable_danger=DangerLevel.MEDIUM):
        self.load_project('', force_all=True, max_allowable_danger=max_allowable_danger)
        
    def load_project(self, project_name:str, 
                     force_all:bool=False, max_allowable_danger=DangerLevel.MEDIUM) -> Design:
        # neither a know integer nor a loaded project, but is avail
        if force_all:
            project_address = 0
        else:
            if isinstance(project_name, int):
                project_address = project_name 
                project_name = None
            else:
                project_address = self.project_index(project_name)
            
            if self._src_serialized_bin is not None:
                serialized_fpath = self._src_serialized_bin
            else:
                serialized_fpath = self.serialized_bin_file(self._src_json)
            if serialized_fpath is not None:
                loaded_project = None 
                if project_address is not None:
                    loaded_project = self.deserialize_design_by_address(serialized_fpath, project_address)
                elif project_name is not None and len(project_name):
                    loaded_project = self.deserialize_design_by_name(serialized_fpath, project_name)
                
                if loaded_project is None:
                    raise AttributeError(f'Unknown project') 
                setattr(self, loaded_project.name, loaded_project)
                return loaded_project
        try:
            with open(self._src_json) as fh:
                log.debug(f"LOADING {self._src_json}")
                index = json.load(fh)
                for project in index['projects']:
                    if force_all or int(project['address']) == project_address:
                        # this is our guy
                        if project_name is None or not len(project_name):
                            pname = self._wokwi_name_cleanup(project['macro'], project)
                        else:
                            pname = project_name
                        des = Design(self._project_mux, pname, project["address"], project)
                        if des.danger_level > max_allowable_danger:
                            log.error(f'Design {des.name} danger exceeds max allowed {DangerLevel.level_to_str(max_allowable_danger)}')
                            continue
                        setattr(self, des.name, des)
                        log.debug(f'Loaded project {des.name}')
                        index = None
                        if not force_all:
                            gc.collect()
                            return des
                
                if force_all:
                    return
                        
                    
        except OSError:
            log.error(f'Could not open shuttle index {self._src_json}')
        
        raise AttributeError(f'Unknown project "{project_name}"') 
        
        
    def is_available(self, project_name:str):
        if hasattr(self, project_name):
            return True 
        if StrictMemorySaving and self._src_serialized_bin:
            x = list(filter(lambda x: x.name == project_name, self.find(project_name)))
            return len(x)
        
        return False
    
    def project_index(self, project_name:str) -> int:
        if self.is_available(project_name):
            # return self._available_projects[project_name]
            return getattr(self, project_name).count
        
        return None   
    
    
    def project_name(self, from_address:int) -> str:
        des_attribs = self._get_design_attribs()
        found = list(filter(lambda x: x.count == from_address, des_attribs))
        if len(found):
            return found[0].name
        return None
    
        
    def serialize(self):
        self.load_all()
        bts = bytearray()
        processed = dict()
        for ades in self.all:
            if ades.project_index in processed:
                continue 
            processed[ades.project_index] = True
            pname = self.project_name(ades.project_index)
            ades.name = pname
            try:
                bts += ades.serialize()
            except Exception as e:
                log.error(str(e))
                log.error(f'Problem serializing {str(ades)}')
            
        return bts

    def from_bin_file(self, fpath:str):
        super().from_bin_file(fpath)
        gc.collect()
        return self._num_projects
    
    def deserialize_design_by_address(self, fpath:str, project_address:int) -> Design:
        with open(fpath, 'rb') as bytestream:
            version = self.bin_header_valid(bytestream)
            if not version:
                raise ValueError(f'bad header in {fpath}')
            addrAndSizeBytes = Design.SerializeAddressBytes + Design.SerializePayloadSizeBytes
            
            while True:
                try:
                    addr, size = Design.get_address_and_size_from(bytestream)
                except ValueError:
                    # empty 
                    return None
                if addr == project_address:
                    bytestream.seek(bytestream.tell() - addrAndSizeBytes)
                    des = Design(self._project_mux)
                    des.deserialize(bytestream)
                    bytestream.close()
                    return des
                bytestream.seek(bytestream.tell() + size)
    
    def deserialize_find_names(self, fpath:str, partial_name:str) -> list:
        with open(fpath, 'rb') as bytestream:
            version = self.bin_header_valid(bytestream)
            if not version:
                raise ValueError(f'bad header in {fpath}')
            ret_list = []
            while True:
                start_point = bytestream.tell()
                try:
                    # pass over address and payload size
                    _addr, size = Design.get_address_and_size_from(bytestream)
                except ValueError:
                    # empty 
                    return ret_list
                payload_point = bytestream.tell()
                name = Design.deserialize_string(bytestream)
                if name.find(partial_name) >= 0:
                    bytestream.seek(start_point)
                    des = Design(self._project_mux)
                    des.deserialize(bytestream)
                    setattr(self, des.name, des)
                    ret_list.append(des)
                else:
                    bytestream.seek(payload_point + size)
    
    def deserialize_design_by_name(self, fpath:str, project_name:str) -> Design:
        with open(fpath, 'rb') as bytestream:
            
            version = self.bin_header_valid(bytestream)
            if not version:
                raise ValueError(f'bad header in {fpath}')
            log.info(f'des_by_name from v{version} file {fpath}')
            
            while True:
                
                start_point = bytestream.tell()
                try:
                    # pass over address and payload size
                    _addr, size = Design.get_address_and_size_from(bytestream)
                except ValueError:
                    # empty 
                    return None
                payload_point = bytestream.tell()
                name = Design.deserialize_string(bytestream)
                if name == project_name:
                    bytestream.seek(start_point)
                    des = Design(self._project_mux)
                    des.deserialize(bytestream)
                    bytestream.close()
                    return des
                bytestream.seek(payload_point + size)
        
        
    def deserialize(self, bytestream):
        self._num_projects = 0
        while True:
            aDesign = Design(self._project_mux)
            try:
                aDesign.deserialize(bytestream)
            except:
                # we're done
                bytestream.close()
                gc.collect()
                return
            if not len(aDesign.name):
                raise RuntimeError('empty design name')
            self._num_projects += 1
            if not StrictMemorySaving:
                nm = aDesign.name 
                if not hasattr(self, nm):
                    setattr(self, nm, DesignStub(self, aDesign.count))
            
    def __len__(self):
        return self._num_projects
    
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
            
        self.p.cena(0)
        # let's stay in admin mode from here
        # so we're actually holding this ena low
        # as we were directed
        
        self.enabled = None
        
    def enable(self, design:Design, force:bool=False):
        log.info(f'Enable design {design.name}')
        if design.danger_level != DangerLevel.SAFE:
            if not force:
                log.error(f"Danger level is '{design.danger_level_str}'.")
                log.warn(f"call with force=True to enable")
                return False
        self.reset_and_clock_mux(design.count)
        self.enabled = design
        if self.design_enabled_callback is not None:
            self.design_enabled_callback(design)
            
        return True
            
    
    def reset_and_clock_mux(self, count:int):
        self.p.safe_bidir() # reset bidirectionals to safe mode
        
        self.reset()
        # send the number of pulses required
        for _c in range(count):
            self.p.cinc(1)
            time.sleep_ms(1)
            self.p.cinc(0)
            time.sleep_ms(1)
        
        self.p.cena(1)
        
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
            return self.tt_um_factory_test
        except:
            return None
            
    @property
    def projects(self):
        if self._design_index is None:
            self.shuttle_index_file = self.indexfile_for_shuttle(self.run)
            log.info(f'Loading shuttle file {self.shuttle_index_file}')
                
            self._design_index = DesignIndex(self, src_JSON_file=self.shuttle_index_file)

        return self._design_index
    
    def has(self, project_name:str):
        return self.projects.is_available(project_name)
    
    def get(self, project_name:str) -> Design:
        return self.projects.get(project_name)
    
    
    def find(self, search:str) -> list:
        return self.projects.find(search)
    
    def __getattr__(self, name):
        if hasattr(self, 'projects'):
            if self.projects.is_available(name) or hasattr(self.projects, name):
                return getattr(self.projects, name)
            if StrictMemorySaving:
                return self.projects.load_project(name)
        raise AttributeError(f"What is '{name}'?")
    
    def __getitem__(self, key) -> Design:
        if hasattr(self, 'projects'):
            return self.projects[key]
        raise None
    
    def __len__(self):
        return len(self.projects)
    
    def __str__(self):
        return f'Shuttle {self.run}'
    
    def __repr__(self):
        des_idx = self.projects
        return f'<ProjectMux for {self.run} with {len(des_idx)} projects>'
        
