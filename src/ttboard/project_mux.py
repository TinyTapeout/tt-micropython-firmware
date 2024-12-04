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
    
    def bin_header_valid(self, bytestream):
        version = self.deserialize_int(bytestream, 1)
        header = bytestream.read(5)
        if header == b'TTSER':
            return version
    
    def from_bin_file(self, fpath:str):
        with open(fpath, 'rb') as f:
            version = self.bin_header_valid(f)
            if not version:
                raise ValueError(f'bad header in {fpath}')
            log.info(f'Deserializing from v{version} file {fpath}')
            self.deserialize(f)
            f.close()
        
        
    @classmethod 
    def serializable_string(cls, s:str):
        try:
            _enc = bytearray(s, cls.StringEncoding)
            return s
        except:
            news = ''
            for i in range(len(s)):
                c = s[i]
                if ord(c) < ord('A') or ord(c) > ord('z'):
                    news += '_'
                else:
                    news += c
            return news
        
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
        
        try:
            enc = bytearray(s, cls.StringEncoding)
        except:
            enc = bytearray(cls.serializable_string(s), cls.StringEncoding)
        bts += enc
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
    SerializePayloadSizeBytes = 1
    SerializeAddressBytes = 2
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
        
    @classmethod 
    def get_address_and_size_from(cls, bytestream):
        
        addr = cls.deserialize_int(bytestream, cls.SerializeAddressBytes)
        size = cls.deserialize_int(bytestream, cls.SerializePayloadSizeBytes)
        return (addr, size)
    
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
        payload_data = [
            
                self.name,
                self.danger_level,
                [self.clock_hz, self.SerializeClockBytes]
                
            ]
        
        payload_bytes = self.serialize_list(payload_data)
        
        header = [
                [self.project_index, self.SerializeAddressBytes],
                [len(payload_bytes), self.SerializePayloadSizeBytes],
            ]
        all_data = self.serialize_list(header) + payload_bytes
        return all_data
        
    def deserialize(self, bytestream):
        
        addr, _size = self.get_address_and_size_from(bytestream)
        self.count = addr
        self.name = self.deserialize_string(bytestream)
        self.macro = self.name
        self.danger_level = self.deserialize_int(bytestream, 1)
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
    def __init__(self, design_index, address:int):
        self.design_index = design_index
        self.count = address
        # self.name = projname 
        self._des = None
    
    def _lazy_load(self):
        des = self.design_index.load_project(self.project_index)
        setattr(self.design_index, des.name, des)
        self._des = des
        return des
    
    @property 
    def project_index(self):
        return self.count
    
    def __getattr__(self, name:str):
        if hasattr(self, '_des') and self._des is not None:
            des = self._des
        else:
            des = self._lazy_load()
        return getattr(des, name)
    
    def __repr__(self):
        return f'<Design {self.project_index} (uninit)>'
    
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
                    des = Design(self, attrib_name, project_address, project)
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
    
    
    @property 
    def all(self):
        '''
            all available projects in the shuttle, whether loaded or not 
        '''
        badlist = ['all', 'names']
        
        m =  map(lambda x: getattr(self, x), 
                 filter( lambda x: x not in badlist,
                         filter( lambda x: not x.startswith('_'), self.__dict__.keys())))
        des_attribs = list(filter(lambda x: isinstance(x, (Design, DesignStub)), m))
        return sorted(des_attribs, key=lambda x: x.count)
    
    
    def get(self, project_name:str) -> Design:
        
        # not in list of available, maybe it's an integer?
        if isinstance(project_name, int):
            str_name = self.project_name(project_name)
            if str_name is not None:
                return self.get(str_name)
            else:
                raise AttributeError(f'No project @ address "{project_name}"') 
            
        if hasattr(self, project_name):
            return getattr(self, project_name)
        
        
        raise AttributeError(f'Unknown project "{project_name}"') 
        
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
                return self.deserialize_design(serialized_fpath, project_address)
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
        return hasattr(self, project_name)
        # return project_name in self._available_projects
    
    def project_index(self, project_name:str) -> int:
        if self.is_available(project_name):
            # return self._available_projects[project_name]
            return getattr(self, project_name).count
        
        return None   
    
    
    def project_name(self, from_address:int) -> str:
        des_attribs = list(filter(lambda x: isinstance(x, (Design, DesignStub)), 
                                  map(lambda x: getattr(self, x), dir(self))))
        
        found = list(filter(lambda x: x.count == from_address, des_attribs))
        if len(found):
            return found[0].name
        return None
    
    def find(self, search:str) -> list:
        return list(filter(lambda p: p.name.find(search) >= 0,  self.all))
    
        
    def serialize(self):
        self.load_all()
        bts = bytearray()
        for ades in self.all:
            pname = self.project_name(ades.project_index)
            assert ades.name == pname, f'{ades.name} {pname}'
            ades.name = pname
            bts += ades.serialize()
            
        return bts

    def from_bin_file(self, fpath:str):
        super().from_bin_file(fpath)
        gc.collect()
        return self._num_projects
    
    def deserialize_design(self, fpath:str, project_address:int) -> Design:
        with open(fpath, 'rb') as bytestream:
            version = self.bin_header_valid(bytestream)
            if not version:
                raise ValueError(f'bad header in {fpath}')
            log.info(f'Deserializing from v{version} file {fpath}')
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
            nm = aDesign.name 
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
        return self.projects.get(project_name)
    
    
    def find(self, search:str) -> list:
        return self.projects.find(search)
    
    def __getattr__(self, name):
        if hasattr(self, 'projects'):
            if self.projects.is_available(name) or hasattr(self.projects, name):
                return getattr(self.projects, name)
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
        
