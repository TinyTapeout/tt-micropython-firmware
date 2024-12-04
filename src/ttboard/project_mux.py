'''
Created on Jan 9, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
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
log = logging.getLogger(__name__)


'''
Fetched with
https://index.tinytapeout.com/tt04.json?fields=address,clock_hz,title

'''
class DangerLevel:
    SAFE=0
    UNKNOWN=1
    MEDIUM=2
    HIGH=3
    
    @classmethod 
    def string_to_level(cls, s:str):
        smap = {
                'safe': cls.SAFE,
                'unknown': cls.UNKNOWN,
                'medium': cls.MEDIUM,
                'HIGH': cls.HIGH
            }
        if s in smap:
            return smap[s]
        return cls.UNKNOWN
    
    @classmethod
    def level_to_str(cls, level:int):
        strs = [   
            'safe',
            'unknown',
            'medium',
            'high'
            
            ]
        if level >= len(strs):
            return 'high'
        return strs[level]
    
class Serializable:
    SerializerVersion = 1
    BytesForStringLen = 1
    StringEncoding = 'ascii'
    ByteOrder = 'big'
    
    def __init__(self):
        pass
    
    def to_bin_file(self, fpath:str):
        with open(fpath, 'wb') as f:
            f.write(self.serialize_int(self.SerializerVersion, 1))
            f.write(b'TTSER')
            f.write(self.serialize())
            f.close()
            
    def from_bin_file(self, fpath:str):
        with open(fpath, 'rb') as f:
            version = self.deserialize_int(f, 1)
            header = f.read(5)
            if header != b'TTSER':
                raise ValueError(f'bad header {header} in {fpath}')
            log.info(f'Deserializing from v{version} file {fpath}')
            self.deserialize(f)
        
    @classmethod 
    def deserialize_string(cls, bytestream):
        slen = cls.deserialize_int(bytestream, cls.BytesForStringLen)
        sbytes = bytestream.read(slen)
        return sbytes.decode(cls.StringEncoding)
    
    @classmethod
    def deserialize_int(cls, bytestream, num_bytes):
        bts = bytestream.read(num_bytes)
        if len(bts) != num_bytes:
            raise ValueError('empty')
        v = int.from_bytes(bts, cls.ByteOrder)
        # print(f"THE BTS {bts} {v}")
        return v

    
    @classmethod
    def serialize_string(cls, s:str):
        slen = len(s)
        bts = slen.to_bytes(cls.BytesForStringLen, cls.ByteOrder)
        bts += bytearray(s, cls.StringEncoding)
        return bts
    
    @classmethod 
    def serialize_int(cls, i:int, num_bytes):
        return i.to_bytes(num_bytes, cls.ByteOrder)
    
    @classmethod
    def serialize_list(cls, l:list):
        bts = bytearray()
        for element in l:
            if isinstance(element, str):
                bts += cls.serialize_string(element)
            elif isinstance(element, int):
                bts += cls.serialize_int(element, 1)
            elif isinstance(element, list):
                if len(element) != 2:
                    raise RuntimeError(f'Expecting 2 elements in {element}')
                if not isinstance(element[0], int):
                    raise RuntimeError(f'Expecting int as first in {element}')
                if not isinstance(element[1], int):
                    raise RuntimeError(f'Expecting size as second in {element}')
                bts += cls.serialize_int(element[0], element[1])
            else:
                RuntimeError(f'Unknown serialize {element}')
        return bts
                
                    
                
    def serialize(self):
        raise RuntimeError('Override me')
    
    def deserialize(self, bytestream):
        raise RuntimeError('Override me')

class Design(Serializable):
    SerializeClockBytes = 4
    def __init__(self, projectMux, projname:str='NOTSET', projindex:int=0, info:dict=None):
        super().__init__()
        self.mux = projectMux
        self.count = int(projindex)
        self.name = projname
        
        self.danger_level = DangerLevel.HIGH
        self.macro = projname 
        self.repo = ''
        self.commit = ''
        self.clock_hz = -1
        self._all = info
        if info is None:
            return 
        
        self.macro = info['macro']
        
        if 'danger_level' in info:
            self.danger_level = DangerLevel.string_to_level(info['danger_level'])
        else:
            self.danger_level = DangerLevel.SAFE
        
        if 'repo' in info:
            self.repo = info['repo']
            
        if 'commit' in info:
            self.commit = info['commit']
        self.clock_hz = int(info['clock_hz'])
        
    @property 
    def project_index(self):
        return self.count 
    
    @property 
    def danger_level_str(self):
        return DangerLevel.level_to_str(self.danger_level)
    
    def enable(self, force:bool=False):
        return self.mux.enable(self, force)
        
    def disable(self):
        self.mux.disable()
        
    def serialize(self):
        data = [
                self.name,
                self.danger_level,
                [self.count, 2],
                [self.clock_hz, self.SerializeClockBytes]
            
            ]
        # print(f"Serializing {data}")
        return self.serialize_list(data)
        
    def deserialize(self, bytestream):
        self.name = self.deserialize_string(bytestream)
        self.macro = self.name
        self.danger_level = self.deserialize_int(bytestream, 1)
        self.count = self.deserialize_int(bytestream, 2)
        self.clock_hz = self.deserialize_int(bytestream, self.SerializeClockBytes)
        # print(str(self))
    def __str__(self):
        return f'{self.name} ({self.count}) @ {self.repo}'
    
    def __repr__(self):
        if self.danger_level == DangerLevel.SAFE:
            dangermsg = ''
        else:
            dangermsg = f' danger={self.danger_level_str}'
        
        return f'<Design {self.count}: {self.name}{dangermsg}>'
        

class DesignStub:
    '''
        A yet-to-be-loaded design, just a pointer that will 
        auto-load the design if accessed.
        Has a side effect of replacing itself as an attribute
        in the design index so this only happens once.
    '''
    def __init__(self, design_index, projname):
        self.design_index = design_index 
        self.name = projname 
        self._des = None
    
    def _lazy_load(self):
        des = self.design_index.load_project(self.name)
        setattr(self.design_index, self.name, des)
        self._des = des
        return des
    
    @property 
    def project_index(self):
        return self.design_index.project_index(self.name) 
    
    def __getattr__(self, name:str):
        if hasattr(self, '_des') and self._des is not None:
            des = self._des
        else:
            des = self._lazy_load()
        return getattr(des, name)
    
    def __dir__(self):
        des = self._lazy_load()
        return dir(des)
    
    def __repr__(self):
        return f'<Design {self.project_index}: {self.name} (uninit)>'
    
class DesignIndex(Serializable):
    SerializedBinSuffix = '.bin'
    BadCharsRe = re.compile(r'[^\w\d\s]+')
    SpaceCharsRe = re.compile(r'\s+')
    
    def __init__(self, projectMux,  src_JSON_file:str='shuttle_index.json'):
        self._src_json = src_JSON_file
        self._project_mux = projectMux
        self._project_count = 0
        self._shuttle_index = dict()
        self._available_projects = dict()
        
        self.load_available(src_JSON_file)
        
    def load_serialized(self, src_JSON_file):
        serialized_fpath = f'{src_JSON_file}{self.SerializedBinSuffix}'
        try:
            # no os.path on this dumb thing...
            os.stat(serialized_fpath)
        except OSError:
            return False
        
        if self.from_bin_file(serialized_fpath):
            return True
        
    def load_available(self, src_JSON_file:str=None):
        if src_JSON_file is None:
            src_JSON_file = self._src_json
            
        if self.load_serialized(src_JSON_file):
            return 
            
        self._shuttle_index = dict()
        self._available_projects = dict()
        try:
            with open(src_JSON_file) as fh:
                index = json.load(fh)
                for project in index['projects']:
                    attrib_name = project['macro']
                    project_address = int(project['address'])
                    
                    if attrib_name in self._available_projects:
                        log.info(f'Already have a "{attrib_name}" here...')
                        attempt = 1
                        augmented_name = f'{attrib_name}_{attempt}'
                        while augmented_name in self._available_projects:
                            attempt += 1
                            augmented_name = f'{attrib_name}_{attempt}'
                        
                        attrib_name = augmented_name
                        
                    attrib_name = self._wokwi_name_cleanup(attrib_name, project)
                    self._available_projects[attrib_name] = int(project_address)
                    # setattr(self, attrib_name, DesignStub(self, attrib_name))
                    self._project_count += 1
                index = None
        except OSError:
            log.error(f'Could not open shuttle index {src_JSON_file}')
            
        gc.collect()
            
             
    
                
    def _wokwi_name_cleanup(self, name:str, info:dict):
        
        # special cleanup for wokwi gen'ed names
        if name.startswith('tt_um_wokwi') and 'title' in info and len(info['title']):
            new_name = self.SpaceCharsRe.sub('_', self.BadCharsRe.sub('', info['title'])).lower()
            if len(new_name):
                name = f'wokwi_{new_name}'
        
        return name 
    @property
    def count(self):
        return self._project_count
                
    @property 
    def names(self):
        return sorted(self._available_projects.keys())
    
    
    @property 
    def all(self):
        '''
            all available projects in the shuttle, whether loaded or not 
        '''
        return list(map(
            lambda p: self._shuttle_index[p] if p in self._shuttle_index else DesignStub(self, p), 
            sorted(self._available_projects.keys())))
    @property 
    def all_loaded(self):
        '''
            all the projects that have been lazy-loaded, basically
            anything you've actually enabled or accessed in any way.
        '''
        return sorted(self._shuttle_index.values(), key=lambda p: p.name)
    
    
    def get(self, project_name:str) -> Design:
        if not self.is_available(project_name):
            # not in list of available, maybe it's an integer?
            try: 
                des_idx = int(project_name)
                for des in self._available_projects.items():
                    if des[1] == des_idx:
                        return self.get(des[0]) 
            except ValueError:
                pass
            raise AttributeError(f'Unknown project "{project_name}"') 
        
        from_shut = self._get_from_shuttle_index(project_name)
        if from_shut is not None:
            return from_shut
        
        return self.load_project(project_name)
        
    def load_all(self, max_allowable_danger=DangerLevel.MEDIUM):
        self.load_project('', force_all=True, max_allowable_danger=max_allowable_danger)
        
    def load_project(self, project_name:str, 
                     force_all:bool=False, max_allowable_danger=DangerLevel.MEDIUM) -> Design:
        # neither a know integer nor a loaded project, but is avail
        if force_all:
            project_address = 0
        else:
            project_address = self._available_projects[project_name]
        try:
            with open(self._src_json) as fh:
                log.debug(f"LOADING {self._src_json}")
                index = json.load(fh)
                for project in index['projects']:
                    if force_all or int(project['address']) == project_address:
                        # this is our guy
                        if not len(project_name):
                            pname = self._wokwi_name_cleanup(project['macro'], project)
                        else:
                            pname = project_name
                        des = Design(self._project_mux, pname, project["address"], project)
                        if des.danger_level > max_allowable_danger:
                            log.error(f'Design {des.name} danger exceeds max allowed {DangerLevel.level_to_str(max_allowable_danger)}')
                            continue
                        self._shuttle_index[des.name] = des
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
        return project_name in self._available_projects
    
    def project_index(self, project_name:str) -> int:
        if self.is_available(project_name):
            return self._available_projects[project_name]
        
        return None    
    
    
        
    def serialize(self):
        self.load_all()
        bts = bytearray()
        for ades in self.all:
            bts += ades.serialize()
            
        return bts

    def from_bin_file(self, fpath:str):
        self._available_projects = dict()
        self._shuttle_index = dict()
        super().from_bin_file(fpath)
        return len(self._available_projects)
        
    def deserialize(self, bytestream):
        
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
            # print(f'Deserialized {aDesign}')
            self._shuttle_index[aDesign.name] = aDesign
            self._available_projects[aDesign.name] = aDesign.count 
            setattr(self, aDesign.name, aDesign)
            
            

    def _get_from_shuttle_index(self, name:str):
        if name in self._shuttle_index:
            if self._shuttle_index[name] is None:
                return DesignStub(self, name)
            return self._shuttle_index[name]
        
        return None
    
    def __len__(self):
        return len(self._available_projects)
    def __getattrXXXDEAD__(self, name:str):
        if name == '_shuttle_index':
            if '_shuttle_index' in self.__dict__:
                return self.__dict__['_shuttle_index']
            raise AttributeError
        elif name in self.__dict__:
            return self.__dict__[name]
        from_shuttle_idx = self._get_from_shuttle_index(name)
        if from_shuttle_idx is not None:
            return from_shuttle_idx
        
        return self.get(name)
    
    def __getitem__(self, idx:int) -> Design:
        return self.get(idx)
    
    def __dir__(self):
        return self.names
                
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
        return getattr(self.projects, project_name)
    
    def find(self, search:str) -> list:
        return list(filter(lambda p: p.name.find(search) >= 0,  self.all))
    
    def __getattr__(self, name):
        if hasattr(self, 'projects'):
            if self.projects.is_available(name) or hasattr(self.projects, name):
                return getattr(self.projects, name)
        raise AttributeError(f"What is '{name}'?")
    
    def __getitem__(self, key) -> Design:
        if hasattr(self, 'projects'):
            return self.projects[key]
        raise None
    
    def __dirXXX__(self):
        names = []
        if hasattr(self, 'projects'):
            names = self.projects.names
            
        return sorted(set(
                list(dir(type(self))) + \
                list(self.__dict__.keys()) + names))

    
    
    def __len__(self):
        return len(self.projects)
    
    def __str__(self):
        return f'Shuttle {self.run}'
    
    def __repr__(self):
        des_idx = self.projects
        return f'<ProjectMux for {self.run} with {len(des_idx)} projects>'
        