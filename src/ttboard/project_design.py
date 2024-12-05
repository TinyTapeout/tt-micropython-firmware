'''
Created on Dec 4, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import ttboard.log as logging
log = logging.getLogger(__name__)

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
                cval = ord(c)
                if cval >= ord('0') and cval <= ord('9'):
                    news += c
                elif cval < ord('A') or cval > ord('z'):
                    news += '_'
                else:
                    news += c
            return news
        
    @classmethod 
    def deserialize_string(cls, bytestream):
        slen = cls.deserialize_int(bytestream, cls.BytesForStringLen)
        sbytes = bytestream.read(slen)
        try:
            return sbytes.decode(cls.StringEncoding)
        except Exception as e:
            log.error(f"Error deser string {e} (len {slen}) @ position {bytestream.tell()}: {sbytes}")
            return ''
    
    @classmethod
    def deserialize_int(cls, bytestream, num_bytes):
        bts = bytestream.read(num_bytes)
        if len(bts) != num_bytes:
            raise ValueError('empty')
        v = int.from_bytes(bts, cls.ByteOrder)
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
